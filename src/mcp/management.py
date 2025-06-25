# 导入异步io
import asyncio
# 导入列表
from typing import List
# 导入mcp
from mcp import ClientSession
# 导入sse客户端
from mcp.client.sse import sse_client

# 导入app配置
from app.config import appConfig
# 导入app日志
from app.logger import appLogger
from app.const import APP_NAME

# 导入格式化工具
from src.mcp.model.format import FormatMappingToolName, GetServerAndToolName


class MCPClientSession:
    # 初始化
    def __init__(self, session, is_healthy):
        self.session = session
        self.is_healthy = is_healthy


class MCPClient:
    # 初始化
    def __init__(self, configs, logger):
        self.logger = logger
        # 加载配置
        self.configs = configs["mcpServers"]
        # 创建所有 MCP 服务器会话
        self.mcp_sessions = {}
        # 获取所有可用工具
        self.available_tools = []
        self.mapping_tools = {}

    def ManageSessions(self):
        asyncio.run(self._manage_sessions())

    # 管理mcp服务器会话
    async def _manage_sessions(self):
        # mcp服务器初始化次数
        mcp_servers_initial_times = {}
        while True:
            try:
                # 等待1秒
                await asyncio.sleep(1)
            except Exception as e:
                self.logger.error(f"ManageSessions error: {e}")
            # 遍历配置
            for server_name, config in self.configs.items():
                # 如果会话健康,跳过
                if server_name in self.mcp_sessions and self.mcp_sessions[server_name].is_healthy:
                    continue
                # 如果初始化次数大于0,等待30秒
                if server_name not in mcp_servers_initial_times:
                    mcp_servers_initial_times[server_name] = 0
                if mcp_servers_initial_times[server_name] > 0:
                    await asyncio.sleep(30)

                try:
                    # 创建 SSE 客户端并进入上下文
                    streams_context = sse_client(url=config["url"])
                    # 创建 SSE 客户端
                    streams = await streams_context.__aenter__()
                    # 创建会话
                    session_context = ClientSession(*streams)
                    # 创建会话
                    session = await session_context.__aenter__()
                    # 初始化
                    await session.initialize()
                    # 创建会话
                    self.mcp_sessions[server_name] = MCPClientSession(
                        session, is_healthy=True)
                    # 刷新已获取工具
                    await self._flush_fetched_tools()
                    self.logger.info(
                        f"App[{APP_NAME}] initial mcp-server[{server_name}] success")
                except Exception as e:
                    # 日志
                    self.logger.error(
                        f"App[{APP_NAME}] initial mcp-server[{server_name}] failed, response: {e}")
                # 初始化次数加1
                mcp_servers_initial_times[server_name] += 1

    # 刷新已获取工具
    async def _flush_fetched_tools(self):
        # 获取工具映射
        self.available_tools, self.mapping_tools = await self._fetch_available_tools()

    # 获取所有可用工具
    async def _fetch_available_tools(self) -> list:
        mapping_tools = {}
        available_tools = []
        # 遍历会话
        for server_name, session in list(self.mcp_sessions.items()):
            # 如果会话健康
            if session.is_healthy:
                try:
                    # 获取工具列表
                    response = await session.session.list_tools()
                    # 遍历工具
                    for tool in response.tools:
                        # 添加服务器前缀
                        mapping_tool_name = FormatMappingToolName(
                            server_name, tool.name)
                        # 添加工具
                        available_tools.append({
                            "type": "function",
                            "function": {
                                "name": mapping_tool_name,
                                "description": tool.description,
                                "parameters": tool.inputSchema,
                            },
                        })
                        mapping_tools[mapping_tool_name] = tool.description
                except Exception as e:
                    # 设置会话不健康
                    self.logger.error(
                        f"McpServer[{server_name}] is not healthy, response: {e}")
                    session.is_healthy = False
        # 返回可用工具
        return available_tools, mapping_tools

    # 刷新会话
    async def _flush_all_sessions(self):
        for server_name in self.mcp_sessions:
            self.mcp_sessions[server_name].is_healthy = False
        # 刷新会话
        await self._flush_fetched_tools()
    # 关闭会话

    async def _shutdown_session(self, server_name):
        if server_name in self.mcp_sessions:
            self.mcp_sessions[server_name].is_healthy = False
            await self._flush_fetched_tools()

    def HealthCheck(self):
        asyncio.run(self._health_check())

    # 健康检查
    async def _health_check(self):
        while True:
            # 等待30秒
            await asyncio.sleep(30)
            # 关闭会话列表
            sessions_to_shutdown = []
            # 遍历会话
            for server_name, mcp_server_session in list(self.mcp_sessions.items()):
                if mcp_server_session.is_healthy:
                    try:
                        # 发送心跳
                        await mcp_server_session.session.send_ping()
                        # 日志
                        self.logger.debug(
                            f"McpServer[{server_name}] is healthy")
                    except Exception as e:
                        # 关闭会话
                        sessions_to_shutdown.append(server_name)
                        # 日志
                        self.logger.error(
                            f"McpServer[{server_name}] is not healthy, response: {e}")
            # 关闭会话
            for server_name in sessions_to_shutdown:
                await self.shutdown_session(server_name)
                self.logger.error(
                    f"McpServer[{server_name}] is not healthy, shutdown session")

    def get_server_and_tool_name(self, mapping_tool_name):
        if mapping_tool_name in self.mapping_tools:
            return GetServerAndToolName(mapping_tool_name)
        else:
            return None, None

    def get_tool_description(self, mapping_tool_name):
        if mapping_tool_name in self.mapping_tools:
            for tool in self.available_tools:
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

        if server_name not in self.mcp_sessions:
            result = f"mcp_server[{server_name}]会话 未找到"
            self.logger.error(result)
            return result

        try:
            mcp_server_session = self.mcp_sessions[server_name]
            call_result = await mcp_server_session.session.call_tool(tool_name, tool_args)
            if call_result.isError:
                result = {
                    "content": f"工具 {server_name}.{tool_name} 出错：{str(call_result.error)}"}
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


# 创建mcp服务器管理类
appMCPClient = MCPClient(
    appConfig.mcp,
    appLogger.logger
)
