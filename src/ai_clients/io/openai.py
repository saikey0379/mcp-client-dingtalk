# 导入模块
from openai import AsyncOpenAI
# 导入ai客户端基类
from src.ai_clients.model.io import ClientAIBase

# OpenAI 客户端


class ClientOpenAI(ClientAIBase):
    # 初始化
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        # 创建客户端
        self.client = self.create_client()

    # 获取客户端
    def create_client(self):
        return AsyncOpenAI(
            base_url=self.base_url, api_key=self.api_key)

    async def get_response_tool_calls(self, user_model: str, messages: list, available_tools: list):
        try:
            # 初始化消息列表
            response = await self.client.chat.completions.create(
                model=user_model,
                messages=messages,
                tools=available_tools,
            )
            return response
        except Exception as e:
            raise e


def NewClientOpenAI(api_key: str, base_url: str):
    return ClientOpenAI(api_key, base_url)
