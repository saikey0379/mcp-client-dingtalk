# 导入异步io
import asyncio
# 导入日志
import logging
# 导入app
from app import App
# 导入钉钉配置检查
from src.dingtalk import CheckDingTalkConfig
# 导入ai配置检查
from src.ai_clients.clients import CheckAIConfig
# 导入mcp配置检查
from src.mcp_servers import CheckMCPServerConfig

# 检查配置
def CheckConfig():
    # 检查钉钉配置
    if not CheckDingTalkConfig():
        logging.error("DingTalk client_id or client_secret is not set")
        return
    # 检查ai配置
    if not CheckAIConfig():
        logging.error("AI client_id or client_secret is not set")
        return
    # 检查mcp配置
    if not CheckMCPServerConfig():
        logging.error("MCPServer is not set")
        return
    return True
        
# 主函数
def main():
    # 检查配置
    if not CheckConfig():
        logging.error("Config is not set")
        return
    # 启动app
    app=App()
    asyncio.run(app.start())

if __name__ == "__main__":
    main()

