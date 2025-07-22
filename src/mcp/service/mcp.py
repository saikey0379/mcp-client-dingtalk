import json
import asyncio
# 导入状态


class MCPService:
    # 初始化
    def __init__(self, logger, client_user, mcp_client, service_card):
        self.logger = logger
        self.client_user = client_user
        self.mcp_client = mcp_client
        self.service_card = service_card

def NewMCPService(logger, client_user, mcp_client, service_card):
    return MCPService(logger, client_user, mcp_client, service_card)
