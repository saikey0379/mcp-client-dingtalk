# 导入ai客户端常量
from src.ai_clients.const import AI_PROVIDER_OPENAI, AI_PROVIDER_DEEPSEEK

# 获取提供者 根据模型名称
def GetProviderByModel(model_name: str) -> str:
    # 模型到提供者的映射
    model_to_provider = {
        "gpt-4o": AI_PROVIDER_OPENAI,
        "gpt-3.5": AI_PROVIDER_OPENAI,
        "deepseek-r1": AI_PROVIDER_DEEPSEEK,
        "gpt-4o-mini": AI_PROVIDER_OPENAI,
        # 可以继续添加其他模型和它们的提供者
    }

    # 使用get方法从字典中查询提供者，如果没有找到，返回None或其他默认值
    provider = model_to_provider.get(model_name, None)
    # 返回提供者
    return provider

