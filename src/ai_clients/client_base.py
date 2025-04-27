# 导入模块
from abc import ABC, abstractmethod

# AI 客户端基类
class ClientBase(ABC):
    # 初始化
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url  
        # 创建客户端
        self.client = self.GetClient()
    
    # TODO: 获取客户端
    @abstractmethod
    def GetClient(self):
        pass
