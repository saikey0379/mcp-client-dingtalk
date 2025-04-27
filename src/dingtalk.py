
# 导入 dingtalk_stream 模块
import dingtalk_stream
# 导入配置
from src.config import GetConfig
# 导入日志
from src.logger import GetLogger
# 导入mcp客户端
from src.mcp_clients import GetMCPClient

# 钉钉类
class AppDingTalk:
    # 初始化
    def __init__(self):
        # 获取配置
        self.config = GetConfig().get_config()
        # 创建钉钉客户端
        self.client = None
        self.handler = None
        self.initialize()

    # 初始化
    def initialize(self):
        # 创建钉钉客户端
        self.client = self.create_client()  
        self.handler = self.handle_message()
    # 创建钉钉客户端
    def create_client(self) -> dingtalk_stream.DingTalkStreamClient:
        # 创建凭证
        credential = dingtalk_stream.Credential(self.config["dingtalk"]["client_id"], self.config["dingtalk"]["client_secret"])
        # 创建钉钉客户端
        return dingtalk_stream.DingTalkStreamClient(credential)
    
    # 启动
    def handle_message(self):
        # 创建钉钉处理器
        handler = DingTalkHandler(self)

        # 注册钉钉处理器
        self.client.register_callback_handler( 
            # 处理消息
            dingtalk_stream.chatbot.ChatbotMessage.TOPIC, 
            # 处理器
            handler
        )
        return handler

# 检查钉钉配置
def CheckDingTalkConfig():
    # 检查配置
    config = GetConfig().get_config()
    if config["dingtalk"]["client_id"] == "" or config["dingtalk"]["client_secret"] == "":
        raise Exception("DingTalk client_id or client_secret is not set")        
    return True

# 钉钉处理器
class DingTalkHandler(dingtalk_stream.ChatbotHandler):
    # 初始化
    def __init__(self, dingtalk_client):
        super().__init__()
        self.dingtalk_client = dingtalk_client
        self.logger = GetLogger().logger

    # 查询
    async def process(self, callback: dingtalk_stream.CallbackMessage):
        try:
            # 创建钉钉消息
            incoming_message = dingtalk_stream.ChatbotMessage.from_dict(callback.data)
            # 获取消息内容
            query = incoming_message.text.content.strip()
            # 获取用户 ID
            user = {}
            # 获取用户昵称
            if incoming_message.sender_nick is not None:
                user = incoming_message.sender_nick
            # 获取用户唯一标识
            if incoming_message.sender_id is not None:
                user = f"{user}[{incoming_message.sender_id}]"
            else:
                user = "未知用户"

            # 获取用户会话
            mcp_client = GetMCPClient()

            self.logger.info(f"用户{user}，查询中...")
            # 查询  
            response = await mcp_client.query(user, query)
            self.logger.info(f"用户{user}，查询结果返回")
            # 回复
            self.reply_text(response, incoming_message)
            # 返回
            return dingtalk_stream.AckMessage.STATUS_OK, 'OK'
        except Exception as e:
            self.logger.error(f"用户{user}，查询失败：{e}")
            # 返回错误
            return dingtalk_stream.AckMessage.STATUS_ERROR, 'ERROR'
