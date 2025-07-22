import asyncio
import threading
import signal
import sys
from flask import Flask, jsonify

from app.const import APP_NAME

from app.config import app_args, app_config
from app.logger import app_logger
from app.state import app_state

from src.dingtalk.dingtalk import NewDingTalk


class App:
    # 初始化
    def __init__(self):
        # 获取参数
        self.args = app_args
        # 获取配置
        self.config = app_config
        # 获取日志
        self.logger = app_logger.logger
        # 获取state
        self.state = app_state
        # 创建app
        self.dingtalk = None
        self.tasks = []  # 存储所有任务，便于取消

        self.flask_app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        #    @self.flask_app.route('/dingtalk/card/continue', methods=['POST'])
        #    def card_callback():
        #        data = request.json
        #        card_instance_id = data.get("card_instance_id")
        #        print(f"card_instance_id: {card_instance_id}")
        #        if card_instance_id in self.state.card_instance_map:
        #            del self.state.card_instance_map[card_instance_id]

        # 处理传入的数据
        #        self.logger.info(f"Received card callback: {data}")
        #        # 返回一个成功响应
        #        return jsonify({'status': 'success'}), 200

        @self.flask_app.route('/healthz', methods=['GET'])
        def healthz():
            # 返回一个成功响应
            return jsonify({'status': 'success'}), 200

    async def cleanup(self):
        """清理所有任务"""
        self.logger.info("Starting cleanup...")
        
        # 取消所有任务
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        self.logger.info("Cleanup completed")

    # 启动
    async def start(self):
        # 初始化
        self.logger.info(f"APP[{APP_NAME}] initialized")

        check_result, error_message = self.config.check()
        if not check_result:
            self.logger.error(error_message)
            return

        mcp_client = self.state.mcp_client
        
        # 创建Mcp异步会话管理任务
        self.logger.info(f"APP[{APP_NAME}] start mcp-client management")
        mcp_management_task = asyncio.create_task(mcp_client.start_management())
        self.tasks.append(mcp_management_task)
        
        # 创建Mcp异步健康检查任务
        self.logger.info(f"APP[{APP_NAME}] start mcp-client healthcheck")
        mcp_health_check_task = asyncio.create_task(mcp_client.start_health_check())
        self.tasks.append(mcp_health_check_task)

        # 创建钉钉客户端
        self.logger.info(f"APP[{APP_NAME}] start dingtalk client")
        self.dingtalk = NewDingTalk(
            self.logger,
            self.config.dingtalk["client_id"],
            self.config.dingtalk["client_secret"],
            self.config.dingtalk["card_template_id_user_config"],
            self.config.dingtalk["card_template_id_call_tools"],
            self.config.dingtalk["card_template_id_ai_result"]
        )
        self.dingtalk.register_callback_handler()
        dingtalk_task = asyncio.create_task(self.dingtalk.client.start())
        self.tasks.append(dingtalk_task)
        
        try:
            # 等待所有任务
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except asyncio.CancelledError:
            self.logger.info("Main task cancelled, starting cleanup...")
            await self.cleanup()
        except Exception as e:
            self.logger.error(f"Error in main task: {e}")
            await self.cleanup()


# 主函数
def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\nReceived signal {signum}, shutting down gracefully...")
    sys.exit(0)

def main():
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动app
    app = App()
    app.logger.info(f"APP[{APP_NAME}] starting...")

    threading.Thread(target=lambda: app.flask_app.run(
        host='0.0.0.0', port=8000, use_reloader=False), daemon=True).start()

    try:
        asyncio.run(app.start())
    except KeyboardInterrupt:
        app.logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")

    app.logger.info(f"APP[{APP_NAME}] exiting!")


if __name__ == "__main__":
    main()
