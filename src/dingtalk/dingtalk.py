
# 导入 dingtalk_stream 模块
import dingtalk_stream

from src.dingtalk.handle import ChatBotHandler, CardCallbackHandler
# 钉钉类


class NewDingTalk:
    # 初始化
    def __init__(self, logger, client_id: str, client_secret: str, card_template_id_user_config: str, card_template_id_call_tools: str):
        # 获取配置
        self.client_id = client_id
        self.client_secret = client_secret
        self.card_template_id_user_config = card_template_id_user_config
        self.card_template_id_call_tools = card_template_id_call_tools

        # 创建钉钉客户端
        self.logger = logger
        self.client = self.create_client()

    # 创建钉钉客户端
    def create_client(self) -> dingtalk_stream.DingTalkStreamClient:
        try:
            # 创建凭证
            credential = dingtalk_stream.Credential(
                self.client_id, self.client_secret)
            # 创建钉钉客户端
            return dingtalk_stream.DingTalkStreamClient(credential)
        except Exception as e:
            self.logger.error(f"创建钉钉客户端失败: {e}")
            raise e

    def register_callback_handler(self):
        chatbot_handler = ChatBotHandler(
            self.logger, self.card_template_id_user_config, self.card_template_id_call_tools)

        self.client.register_callback_handler(
            dingtalk_stream.ChatbotMessage.TOPIC, chatbot_handler
        )
        self.client.register_callback_handler(
            dingtalk_stream.CallbackHandler.TOPIC_CARD_CALLBACK, CardCallbackHandler(
                self.logger, self.client,  chatbot_handler)
        )
