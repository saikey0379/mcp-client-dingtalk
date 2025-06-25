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

    # TODO: 获取工具调用
    @abstractmethod
    def get_response_tool_calls(self, user_model: str, query: str, available_tools: list):
        pass
