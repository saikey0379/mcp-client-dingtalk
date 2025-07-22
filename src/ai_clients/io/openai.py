# 导入模块
from openai import OpenAI, AsyncOpenAI
# 导入ai客户端基类
from src.ai_clients.model.io import ClientAIBase
# OpenAI 客户端


class ClientOpenAI(ClientAIBase):
    # 初始化
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        # 创建客户端
        self.client_async = self.create_client_async()
        self.client = self.create_client()

    def create_client(self):
        return OpenAI(
            base_url=self.base_url, api_key=self.api_key)

    # 获取客户端
    def create_client_async(self):
        return AsyncOpenAI(
            base_url=self.base_url, api_key=self.api_key)

    # 获取ai响应
    def get_client(self):
        return self.client

    # 获取ai响应
    async def get_response_ai_calls_async(self, user_model: str, messages: list, available_tools: list):
        try:
            # 初始化消息列表
            response = await self.client_async.chat.completions.create(
                model=user_model,
                messages=messages,
                tools=available_tools,
            )
            return response
        except Exception as e:
            raise e


def NewClientOpenAI(api_key: str, base_url: str):
    return ClientOpenAI(api_key, base_url)
