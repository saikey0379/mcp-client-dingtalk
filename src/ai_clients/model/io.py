# 导入抽象基类
from abc import ABC, abstractmethod

# AI 客户端基类


class ClientAIBase(ABC):
    # 初始化
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        # 创建客户端
        self.client = None

    @abstractmethod
    async def get_response_ai_calls_async(self, user_model: str, messages: list, available_tools: list):
        pass
