# 导入异步io
import asyncio
# 导入配置
from src.config import GetArgs,GetConfig
# 导入日志
from src.logger import GetLogger
# 导入钉钉处理器
from src.dingtalk import AppDingTalk
# 导入ai客户端
from src.ai_clients.clients import GetAIClients
# 导入mcp服务器
from src.mcp_servers import GetMCPServers
# 导入mcp客户端
from src.mcp_clients import GetMCPClient

# 创建app
class App:
    # 初始化
    def __init__(self):
        # 获取参数
        self.args = None
        # 获取配置
        self.config = None
        # 获取日志
        self.logger = None
        # 创建钉钉客户端
        self.app = None
        # 创建ai客户端
        self.ai_clients = None
        # 创建mcp客户端
        self.mcp_clients = None
        # 创建mcp服务器
        self.mcp_servers = None
        # 初始化
        self.initialize()

    def initialize(self):
        # 获取参数
        self.args = GetArgs().get_args()
        # 获取配置
        self.config = GetConfig().get_config()
        # 获取日志
        self.logger = GetLogger().logger
        # 初始化ai客户端
        self.ai_clients = GetAIClients()
        # 初始化mcp客户端
        self.mcp_clients = GetMCPClient()

    # 启动
    async def start(self):
        self.logger.info("APP[mcp-client-dingtalk] initialized")

        # 创建McpServer
        self.mcp_servers = GetMCPServers()
        # 创建McpServer管理异步任务
        task_mcp_server_management = self.mcp_servers.ManageSessions()
        # 创建McpServer健康检查异步任务
        task_mcp_server_health_check = self.mcp_servers.HealthCheck()
    
        # 创建钉钉客户端
        dingtalk_client = AppDingTalk()
        # 创建钉钉客户端异步任务
        task_dingtalk_client = dingtalk_client.client.start()
        # 启动
        self.logger.info("APP[mcp-client-dingtalk] start mcp-server management")
        self.logger.info("APP[mcp-client-dingtalk] start mcp-server health check")
        self.logger.info("APP[mcp-client-dingtalk] start dingtalk client")

        # 启动异步任务
        await asyncio.gather(
            task_mcp_server_management,
            task_mcp_server_health_check,
            task_dingtalk_client
        )
        self.logger.info("APP[mcp-client-dingtalk] exit!")