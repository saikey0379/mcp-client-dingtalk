# 导入List数据类型
from typing import List
# 导入配置  
from src.config import GetConfig
# 导入ai客户端基类
from src.ai_clients.client_base import ClientBase
# 导入ai客户端openai
from src.ai_clients.client_openai import ClientOpenAI
# 导入ai客户端常量
from src.ai_clients.const import AI_PROVIDER_OPENAI

# AI 客户端全局变量
AppAIClients = None

# AI 客户端管理类
class AIClients:
    # 初始化
    def __init__(self):
        # 配置  
        self.config_ai_clients = None
        # 加载 AI 客户端
        self.ai_clients = None
        # 初始化
        self.initialize()

    # 初始化
    def initialize(self):
        # 获取配置
        self.config_ai_clients = GetConfig().get_config()["ai-keys"]
        # 加载 AI 客户端
        self.ai_clients = self.load_ai_clients()
    
    # 加载 AI 客户端
    def load_ai_clients(self) -> List[ClientBase]:
        # 创建 AI 客户端列表
        ai_clients = {}
        # 遍历 AI 客户端
        for ai_client_name, ai_client_config in self.config_ai_clients.items():
            # 如果 AI 客户端提供者为 OpenAI
            if ai_client_name == AI_PROVIDER_OPENAI:
                ai_clients[ai_client_name] = ClientOpenAI(ai_client_config["api_key"], ai_client_config["api_base"])
        # 返回 AI 客户端
        return ai_clients
    
    # 获取 AI 客户端
    def get_ai_client(self, provider_name: str) -> ClientBase:
        # 如果 AI 客户端不存在
        if self.ai_clients[provider_name] is None:
            # 抛出错误
            raise ValueError(f"Unsupported provider: {provider_name}")
        # 返回 AI 客户端
        return self.ai_clients[provider_name]

# 检查 AI 客户端配置
def CheckAIConfig():
    # 遍历 AI 客户端
    for _, ai_client_config in GetConfig().get_config()["ai-keys"].items():
        if ai_client_config["api_key"] == "" or ai_client_config["api_base"] == "":
            raise Exception("AI client_id or client_secret is not set")        
    return True

# 获取 AI 客户端 单例
def GetAIClients() -> AIClients:
    # 定义 AI 客户端全局变量
    global AppAIClients
    # 如果 AI 客户端为空
    if AppAIClients is None:
        # 创建 AI 客户端
        AppAIClients = AIClients()
    # 返回 AI 客户端
    return AppAIClients
        
