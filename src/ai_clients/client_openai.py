# 导入模块
from openai import AsyncOpenAI
# 导入ai客户端基类
from src.ai_clients.client_base import ClientBase

# OpenAI 客户端
class ClientOpenAI(ClientBase):
    # 初始化
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        # 创建客户端
        self.client = None
    
    # 获取客户端
    def GetClient(self):
        # 如果客户端不存在
        if self.client is None:
            # 创建客户端
            self.client = AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)
        # 返回客户端
        return self.client
    


    
