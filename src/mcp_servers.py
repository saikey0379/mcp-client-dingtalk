# 导入json
import json
# 导入异步io
import asyncio
# 导入列表
from typing import List
# 导入mcp
from mcp import ClientSession
# 导入sse客户端
from mcp.client.sse import sse_client
# 导入配置
from src.config import GetConfig
# 导入日志
from src.logger import GetLogger

# mcp服务器会话
class MCPServerSession:
    # 初始化
    def __init__(self,session,is_healthy):
        self.session = session
        self.is_healthy = is_healthy

# 全局变量
AppMCPServers = None

# mcp服务器管理类
class MCPServers:
    # 初始化
    def __init__(self):
        self.logger = None
        # 加载配置
        self.configs = {}
        # 创建所有 MCP 服务器会话
        self.mcp_sessions = {}
        # 获取工具映射
        self.tool_mapping = {}
        # 获取所有可用工具
        self.available_tools = []
        # 初始化
        self.initialize()
    # 初始化
    def initialize(self):
        # 获取日志
        self.logger = GetLogger().logger
        # 加载配置
        self.configs = self.load_config()

    # 加载配置
    def load_config(self):
        # 获取配置
        mcpServersConfig = GetConfig().get_config()["mcp"]["mcpServers"]
        # 解析配置
        json_config = json.loads(mcpServersConfig)
        # 创建配置
        configs = {}
        configs = {server: config for server, config in json_config["mcpServers"].items()}
        # 遍历配置
        return configs
    
    # 管理mcp服务器会话
    async def ManageSessions(self):
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
                    session =  await session_context.__aenter__()
                    # 初始化
                    await session.initialize()
                    # 创建会话
                    self.mcp_sessions[server_name] = MCPServerSession(session,is_healthy=True)
                    # 刷新已获取工具
                    await self.FlushFetchedTools()
                    self.logger.info(f"McpServer[{server_name}] is initialized")
                except Exception as e:
                    # 日志
                    self.logger.error(f"McpServer[{server_name}] initialize failed, response: {e}")
                # 初始化次数加1
                mcp_servers_initial_times[server_name] += 1

    # 刷新已获取工具
    async def FlushFetchedTools(self):
        # 获取工具映射
        self.tool_mapping, self.available_tools = await asyncio.gather(self.FetchMcpToolMapping(), self.FetchAvailableTools())

    # 获取工具映射
    async def FetchMcpToolMapping(self) -> List[dict]:
        # 遍历会话
        for server_name,session in list(self.mcp_sessions.items()):
            # 如果会话健康
            if session.is_healthy:
                try:
                    # 获取工具列表并建立映射
                    response = await session.session.list_tools()
                    # 遍历工具
                    for tool in response.tools:
                        # 添加服务器前缀
                        prefixed_name = f"{server_name}_{tool.name}"  # 为工具名添加服务器前缀
                        # 添加工具映射
                        self.tool_mapping[prefixed_name] = (server_name, tool.name)
                except Exception as e:
                    # 设置会话不健康
                    self.logger.error(f"McpServer[{server_name}] is not healthy, response: {e}")
                    session.is_healthy = False

        # 返回工具映射
        return self.tool_mapping

    # 获取所有可用工具
    async def FetchAvailableTools(self) -> list:
        # 遍历会话
        for server_name,session in list(self.mcp_sessions.items()):
            # 如果会话健康
            if session.is_healthy:
                try:
                    # 获取工具列表
                    response = await session.session.list_tools()
                    # 遍历工具
                    for tool in response.tools:
                        # 添加服务器前缀
                        prefixed_name = f"{server_name}_{tool.name}"
                        # 添加工具
                        self.available_tools.append({
                            "type": "function",
                            "function": {
                            "name": prefixed_name,
                            "description": tool.description,
                            "parameters": tool.inputSchema,
                            },
                        })
                except Exception as e:
                    # 设置会话不健康
                    self.logger.error(f"McpServer[{server_name}] is not healthy, response: {e}")
                    session.is_healthy = False
        # 返回可用工具
        return self.available_tools
    
    # 刷新会话
    async def FlushAllSessions(self):
        for server_name in self.mcp_sessions:
            self.mcp_sessions[server_name].is_healthy = False
        # 刷新会话
        await self.FlushFetchedTools()
    # 关闭会话
    async def shutdown_session(self, server_name):
        if server_name in self.mcp_sessions:
            self.mcp_sessions[server_name].is_healthy = False
            await self.FlushFetchedTools()
    # 健康检查
    async def HealthCheck(self):
        while True:
            # 等待30秒
            await asyncio.sleep(30)
            # 关闭会话列表
            sessions_to_shutdown = []
            # 遍历会话
            for server_name,mcp_server_session in list(self.mcp_sessions.items()):
                if mcp_server_session.is_healthy:
                    try:
                        # 发送心跳
                        await mcp_server_session.session.send_ping()
                        # 日志
                        self.logger.debug(f"McpServer[{server_name}] is healthy")
                    except Exception as e: 
                        # 关闭会话
                        sessions_to_shutdown.append(server_name)
                        # 日志
                        self.logger.error(f"McpServer[{server_name}] is not healthy, response: {e}")
            # 关闭会话
            for server_name in sessions_to_shutdown:
                await self.shutdown_session(server_name)
                self.logger.error(f"McpServer[{server_name}] is not healthy, shutdown session")
# 检查 MCP 服务器配置
def CheckMCPServerConfig():
    # 检查配置
    config = GetConfig().get_config()
    if config["mcp"]["mcpServers"] == "":
        raise Exception("MCPServer is not set")        
    return True

# 获取 MCP 服务器管理类
def GetMCPServers():
    # 定义 MCP 服务器管理类全局变量
    global AppMCPServers
    # 如果 MCP 服务器管理类为空
    if AppMCPServers is None:
        # 创建 MCP 服务器管理类
        AppMCPServers = MCPServers()
    # 返回 MCP 服务器管理类
    return AppMCPServers
