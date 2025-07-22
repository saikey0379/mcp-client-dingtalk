# 导入异步io
import asyncio

# 导入mcp
from mcp import ClientSession

# 导入sse客户端
from mcp.client.sse import sse_client

# 导入app配置
from app.config import app_config

# 导入app日志
from app.logger import app_logger
from app.const import APP_NAME

# 导入格式化工具
from src.mcp.model.format import FormatMappingToolName, GetServerAndToolName

# 导入http工具
from src.utils.http import extract_host_port, test_tcp_connectivity


class MCPConnection:
    # 初始化
    def __init__(self, session, is_healthy):
        self.session = session
        self.is_healthy = is_healthy


class MCPManagement:
    # 初始化
    def __init__(self, configs, logger):
        self.logger = logger
        # 加载配置
        self.configs = configs["mcpServers"]
        # 创建所有 MCP 服务器会话
        self.mcp_connections = {}
        # 获取所有可用工具
        self.function_tools = {}
        self.mapping_tools = {}
        self.connection_locks = {}  # 使用锁替代事件，减少竞争
        self.task_states = {}  # 跟踪任务状态，避免重复创建

    async def start_management(self):
        for server_name, config in self.configs.items():
            asyncio.create_task(self._connection_management(server_name, config))
            
    async def _connection_management(self, server_name, config):
        task = asyncio.create_task(self._connection_initialed(server_name, config))
        
        while True:
            try:
                if task.done():
                    if task.cancelled():
                        self.logger.warning(f"Task for {server_name} was cancelled, restarting...")
                        # 等待一段时间再重启，避免立即重启
                        await asyncio.sleep(10)
                        # 创建新任务
                        task = asyncio.create_task(self._connection_initialed(server_name, config))
                        continue
                    elif task.exception():
                        exception = task.exception()
                        self.logger.error(f"Task for {server_name} failed with exception: {exception}")
                        # 等待一段时间再重启
                        await asyncio.sleep(10)
                        # 创建新任务
                        task = asyncio.create_task(self._connection_initialed(server_name, config))
                        continue
                    else:
                        # 任务正常完成
                        self.logger.info(f"Task for {server_name} completed successfully")
                        break  # 任务正常完成，退出循环
                
                await asyncio.sleep(15)
            except asyncio.CancelledError:
                # 管理任务本身被取消
                self.logger.warning(f"Connection management task for {server_name} is being cancelled")
                # 取消子任务
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                break  # 退出循环
            except Exception as e:
                self.logger.error(f"Error in task monitor for {server_name}: {e}")
                await asyncio.sleep(15)
        
        self.logger.info(f"Connection management for {server_name} stopped")
                    
    async def _connection_initialed(self, server_name, config):
        connection_initialized = False
        streams_context = None
        streams = None
        connection_context = None
        connection = None

        while True:  # 外层循环，确保永远重试
            try:                
                if connection_initialized:
                    await asyncio.sleep(10)

                if server_name in self.mcp_connections:
                    if self.mcp_connections[server_name].is_healthy:
                        await asyncio.sleep(30)  # 增加休眠时间到30秒，大幅减少CPU使用
                        continue
                    else:
                        # 清理不健康的连接
                        if server_name in self.mcp_connections:
                            old_connection = self.mcp_connections[server_name]
                            try:
                                old_connection.is_healthy = False
                                if hasattr(old_connection.session, '__aexit__'):
                                    await asyncio.wait_for(
                                        old_connection.session.__aexit__(None, None, None), 
                                        timeout=3.0
                                    )
                            except Exception as e:
                                self.logger.error(f"Error cleaning up unhealthy connection: {e}")
                            finally:
                                del self.mcp_connections[server_name]
                        
                        # 清理其他资源
                        if streams_context:
                            try:
                                await asyncio.wait_for(
                                    streams_context.__aexit__(None, None, None), 
                                    timeout=3.0
                                )
                            except Exception:
                                pass
                        if connection_context:
                            try:
                                await asyncio.wait_for(
                                    connection_context.__aexit__(None, None, None), 
                                    timeout=3.0
                                )
                            except Exception:
                                pass
                        
                        streams_context = None
                        streams = None
                        connection_context = None
                        connection = None

                await self.get_connection_block(server_name)

                # TCP 测试
                host, port = extract_host_port(config["url"])
                if host and port:
                    if not await test_tcp_connectivity(host, port, timeout=3):
                        self.logger.error(
                            f"MCPServer[{server_name}] connect failed ({host}:{port})"
                        )
                        await asyncio.sleep(30)
                        await self.release_connection_block(server_name)
                        continue

                    # SSE 连接建立
                    try:
                        connection_initialized = True
                        streams_context = sse_client(url=config["url"])
                        streams = await asyncio.wait_for(
                            streams_context.__aenter__(), 
                            timeout=10.0
                        )
                        connection_context = ClientSession(*streams)
                        connection = await asyncio.wait_for(
                            connection_context.__aenter__(), 
                            timeout=10.0
                        )
                        await asyncio.wait_for(
                            connection.initialize(), 
                            timeout=10.0
                        )
                        self.mcp_connections[server_name] = MCPConnection(
                            connection, is_healthy=True
                        )
                        await self.release_connection_block(server_name)
                        await self._extend_server_tools(server_name)
                        self.logger.info(
                            f"App[{APP_NAME}] initial mcp-server[{server_name}] success"
                        )
                    except asyncio.TimeoutError:
                        self.logger.error(f"Connection timeout for {server_name}")
                        raise Exception(f"Connection timeout for {server_name}")
                    except Exception as e:
                        self.logger.error(f"Connection error for {server_name}: {e}")
                        # 清理连接资源
                        if connection_context:
                            try:
                                await asyncio.wait_for(
                                    connection_context.__aexit__(type(e), e, e.__traceback__), 
                                    timeout=3.0
                                )
                            except Exception:
                                pass
                        if streams_context:
                            try:
                                await asyncio.wait_for(
                                    streams_context.__aexit__(type(e), e, e.__traceback__), 
                                    timeout=3.0
                                )
                            except Exception:
                                pass
                        raise e
            except asyncio.CancelledError:
                # 任务被取消时，清理资源
                self.logger.warning(f"Task for {server_name} is being cancelled, cleaning up...")
                if server_name in self.mcp_connections:
                    del self.mcp_connections[server_name]
                if connection_context:
                    try:
                        await connection_context.__aexit__(None, None, None)
                    except Exception:
                        pass
                if streams_context:
                    try:
                        await streams_context.__aexit__(None, None, None)
                    except Exception:
                        pass
                break
            except Exception as e:
                self.logger.error(
                    f"App[{APP_NAME}] initial mcp-server[{server_name}] failed, response: {e}"
                )
                connection_initialized = False
                if server_name in self.mcp_connections:
                    del self.mcp_connections[server_name]
                # 清理连接资源
                if connection_context:
                    try:
                        await connection_context.__aexit__(type(e), e, e.__traceback__)
                    except Exception:
                        pass
                if streams_context:
                    try:
                        await streams_context.__aexit__(type(e), e, e.__traceback__)
                    except Exception:
                        pass
                # 增加重试间隔，避免快速重试
                await asyncio.sleep(10)
            finally:
                # 确保锁被释放
                try:
                    await self.release_connection_block(server_name)
                except Exception:
                    pass  # 忽略锁释放错误
                await asyncio.sleep(5)  # 增加休眠时间，减少CPU使用

    def get_function_tools(self):
        function_tools = []
        for server_tools in self.function_tools.values():
            function_tools.append(server_tools)
        return function_tools

    # 刷新已获取工具
    async def _flush_global_tools(self):
        global_function_tools = {}
        global_mapping_tools = {}
        # 获取工具映射
        for server_name in self.configs.keys():
            function_tools, mapping_tools = await self._fetch_server_tools(server_name)
            for tool_name, tool_info in function_tools.items():
                global_function_tools[tool_name] = tool_info
            for tool_name, tool_info in mapping_tools.items():
                global_mapping_tools[tool_name] = tool_info
        self.function_tools = global_function_tools
        self.mapping_tools = global_mapping_tools

    async def _extend_server_tools(self, server_name):
        function_tools, mapping_tools = await self._fetch_server_tools(server_name)
        for tool_name, tool_info in function_tools.items():
            self.function_tools[tool_name] = tool_info
        for tool_name, tool_info in mapping_tools.items():
            self.mapping_tools[tool_name] = tool_info

    # 获取所有可用工具
    async def _fetch_server_tools(self, server_name) -> list:
        mapping_tools = {}
        function_tools = {}
        
        try:
            await self.get_connection_block(server_name)
            
            mcp_connection = self.mcp_connections.get(server_name)
            if mcp_connection is None:
                return {}, {}
            # 如果会话健康
            if mcp_connection.is_healthy:
                try:
                    # 获取工具列表
                    response = await mcp_connection.session.list_tools()
                    # 遍历工具
                    for tool in response.tools:
                        # 添加服务器前缀
                        mapping_tool_name = FormatMappingToolName(
                            server_name, tool.name
                        )
                        # 添加工具
                        function_tools[mapping_tool_name] = {
                            "type": "function",
                            "function": {
                                "name": mapping_tool_name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        }
                        mapping_tools[mapping_tool_name] = tool.description
                        self.logger.info(
                            f"Fetch mcp-server available tool[{server_name}]-[{tool.name}]"
                        )
                except Exception as e:
                    # 设置会话不健康
                    self.logger.error(
                        f"McpServer[{server_name}] is not healthy, response: {e}"
                    )
                    mcp_connection.is_healthy = False
            # 返回可用工具
            return function_tools, mapping_tools
        except Exception as e:
            self.logger.error(f"McpServer[{server_name}] is not healthy, response: {e}")
            return {}, {}
        finally:
            # 确保锁被释放
            try:
                await self.release_connection_block(server_name)
            except Exception:
                pass  # 忽略锁释放错误

    def get_server_and_tool_name(self, mapping_tool_name):
        if mapping_tool_name in self.mapping_tools:
            return GetServerAndToolName(mapping_tool_name)
        else:
            return None, None

    def get_tool_description(self, mapping_tool_name):
        if mapping_tool_name in self.mapping_tools:
            for tool in self.function_tools.values():
                if tool["function"]["name"] == mapping_tool_name:
                    return tool["function"]["description"]
        else:
            return None

    # 调用mcp工具
    async def mcp_call(self, server_name, tool_name, tool_args) -> dict:
        result_call_tool = await self.mcp_call_tool(server_name, tool_name, tool_args)
        # result_call_prompt = await self.mcp_call_prompt(tool_name, tool_args)
        return result_call_tool

    async def mcp_call_tool(self, server_name, tool_name, tool_args) -> dict:
        result = str
        if server_name is None or tool_name is None:
            result = f"工具 {tool_name} 未找到"
            self.logger.error(result)
            return result

        if server_name not in self.mcp_connections:
            result = f"mcp_server[{server_name}]会话 未找到"
            self.logger.error(result)
            return result

        try:
            mcp_connection = self.mcp_connections[server_name]
            call_result = await mcp_connection.session.call_tool(tool_name, tool_args)
            if call_result.isError:
                result = {
                    "content": f"工具 {server_name}.{tool_name} 出错：{str(call_result.error)}"
                }
                self.logger.error(result)
                return result
            else:
                for content in call_result.content:
                    if content.type == "text":
                        result = str(content.text)
        except Exception as e:
            result = f"工具 {server_name}.{tool_name}调用出错：{str(e)}"
            self.logger.error(result)

        return result

    async def get_connection_block(self, server_name):
        if server_name not in self.connection_locks:
            self.connection_locks[server_name] = asyncio.Lock()
        
        # 如果锁已经被获取，等待释放
        if self.connection_locks[server_name].locked():
            self.logger.warning(f"Lock for {server_name} is already acquired, waiting...")
            await asyncio.sleep(1)  # 等待锁释放
        
        await self.connection_locks[server_name].acquire()

    async def release_connection_block(self, server_name):
        if server_name in self.connection_locks and self.connection_locks[server_name].locked():
            self.connection_locks[server_name].release()
        elif server_name in self.connection_locks:
            # 如果锁没有被获取，重置锁状态
            self.connection_locks[server_name] = asyncio.Lock()

    async def start_health_check(self):
        for server_name in self.configs.keys():
            asyncio.create_task(self._health_check_connection(server_name))

    async def _health_check_connection(self, server_name):
        while True:
            await asyncio.sleep(30)  # 增加检查间隔到60秒，大幅减少CPU使用
            
            try:
                mcp_server_connection = self.mcp_connections.get(server_name)
                if mcp_server_connection is None:
                    continue

                if mcp_server_connection.is_healthy:
                    # 直接发送 ping，不获取连接块，避免竞争
                    try:
                        await asyncio.wait_for(
                            mcp_server_connection.session.send_ping(), 
                            timeout=5  # 减少超时时间
                        )
                        self.logger.debug(f"McpServer[{server_name}] is healthy")
                    except (asyncio.TimeoutError, Exception) as e:
                        # 标记连接不健康，让管理任务处理
                        mcp_server_connection.is_healthy = False
                        self.logger.error(f"McpServer[{server_name}] health check failed {e}")
            except asyncio.CancelledError:
                # 健康检查任务被取消
                self.logger.warning(f"Health check task for {server_name} is being cancelled")
                break  # 退出循环
            except Exception as e:
                self.logger.error(f"Health check error for {server_name}: {e}")
        
        self.logger.info(f"Health check for {server_name} stopped")


# 创建mcp服务器管理类
app_mcp_client = MCPManagement(app_config.mcp, app_logger.logger)
