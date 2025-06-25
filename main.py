import asyncio
import threading

from app.const import APP_NAME
from app.config import appArgs, appConfig
from app.logger import appLogger
from app.state import appState

from src.dingtalk.dingtalk import NewDingTalk


class App:
    # 初始化
    def __init__(self):
        # 获取参数
        self.args = appArgs
        # 获取配置
        self.config = appConfig
        # 获取日志
        self.logger = appLogger.logger
        # 获取state
        self.state = appState
        # 创建app
        self.dingtalk = None

    # 启动
    async def start(self):
        # 初始化
        self.logger.info(f"APP[{APP_NAME}] initialized")

        check_result = self.config.check()
        if not check_result:
            self.logger.error(check_result)
            return

        mcp_client = self.state.mcp_client
        # 创建Mcp异步会话管理任务
        self.logger.info(f"APP[{APP_NAME}] start mcp-client management")
        mcp_management_thread = threading.Thread(
            target=mcp_client.ManageSessions,
            daemon=True,
            name="McpClientManagementThread"
        )
        mcp_management_thread.start()

        # 创建Mcp异步健康检查任务
        self.logger.info(f"APP[{APP_NAME}] start mcp-client health check")
        mcp_health_check_thread = threading.Thread(
            target=mcp_client.HealthCheck,
            daemon=True,
            name="McpClientHealthCheckThread"
        )
        mcp_health_check_thread.start()

        # 创建钉钉客户端
        self.logger.info(f"APP[{APP_NAME}] start dingtalk client")
        self.dingtalk = NewDingTalk(
            self.logger,
            self.config.dingtalk["client_id"],
            self.config.dingtalk["client_secret"],
            self.config.dingtalk["card_template_id_user_config"],
            self.config.dingtalk["card_template_id_call_tools"],
        )
        self.dingtalk.register_callback_handler()
        await self.dingtalk.client.start()

# 主函数


def main():
    # 启动app
    app = App()
    app.logger.info(f"APP[{APP_NAME}] starting...")
    asyncio.run(app.start())

    app.logger.info(f"APP[{APP_NAME}] exiting!")


if __name__ == "__main__":
    main()
