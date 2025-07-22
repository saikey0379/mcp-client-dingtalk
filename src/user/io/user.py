# 导入模块
from sqlalchemy.orm import Session
from dingtalk_stream.chatbot import ChatbotMessage

from src.user.model.user import User
from src.ai_clients.io.openai import NewClientOpenAI
from src.ai_clients.model.const import AI_PROVIDER_OPENAI
from src.ai_clients.model.io import ClientAIBase

from app.config import DEFAULT_PROVIDER_NAME, DEFAULT_API_KEY, DEFAULT_API_BASE

class ClientUser:
    # 初始化
    def __init__(self, rdb_session: Session):
        self.rdb_session = rdb_session
        self.users_client_ai = {}
        self.users_chat_history = {}
        self.users_chat_session = {}
        self.users_mcp_tasks = {}

    def get_user_by_id(self, user_id: str):
        try:
            return self.rdb_session.query(User).filter(User.user_id == user_id).first()
        except Exception as e:
            raise e

    def get_chat_session(self, user_id: str):
        return self.users_chat_session[user_id]

    def set_chat_session(self, incoming_message: ChatbotMessage):
        self.users_chat_session[incoming_message.sender_staff_id] = incoming_message

    def flush_chat_session(self, user_id: str):
        if user_id in self.users_chat_session:
            del self.users_chat_session[user_id]
        if user_id in self.users_chat_history:
            del self.users_chat_history[user_id]
        if user_id in self.users_client_ai:
            del self.users_client_ai[user_id]
        if user_id in self.users_mcp_tasks:
            del self.users_mcp_tasks[user_id]

    def init_user_chat_history(self, user_id: str):
        if user_id not in self.users_chat_history:
            user = self.get_user_by_id(user_id)

            self.users_chat_history[user_id] = [
                {
                    "role": "system",
                    "content": f"你是一名{user.role}，请使用{user.language}语言回答用户的问题",
                }
            ]

    def get_user_chat_history(self, user_id: str):
        self.init_user_chat_history(user_id)

        return self.users_chat_history[user_id]

    def append_user_chat_history(self, user_id: str, message: dict):
        self.init_user_chat_history(user_id)

        user_chat_history = self.users_chat_history[user_id]
        user_chat_history.append(message)

        self.users_chat_history[user_id] = user_chat_history

    def get_user_client_ai(self, user_id: str):
        if user_id not in self.users_client_ai:
            try:
                self.users_client_ai[user_id] = self._new_client_io(
                    self.get_user_by_id(user_id)
                )
            except Exception as e:
                raise e
        return self.users_client_ai[user_id]

    def get_user_client_ai_async(self, user_id: str):
        if user_id not in self.users_client_ai:
            try:
                self.users_client_ai[user_id] = self._new_client_io(
                    self.get_user_by_id(user_id)
                )
            except Exception as e:
                raise e
        return self.users_client_ai[user_id]

    def delete_user_client_ai(self, user_id: str):
        if self.users_client_ai[user_id] is not None:
            del self.users_client_ai[user_id]

    def get_user_mcp_tasks(self, user_id: str):
        if user_id not in self.users_mcp_tasks:
            self.users_mcp_tasks[user_id] = []
        return self.users_mcp_tasks[user_id]

    def set_user_mcp_tasks(self, user_id: str, tasks: list):
        self.users_mcp_tasks[user_id] = tasks

    def custom_mcp_task(self, user_id: str):
        if user_id not in self.users_mcp_tasks:
            self.users_mcp_tasks[user_id] = []
        self.users_mcp_tasks[user_id] = self.users_mcp_tasks[user_id][1:]

    @staticmethod
    def _new_client_io(user: User) -> ClientAIBase:
        provider_name = user.provider_name if user.provider_name else DEFAULT_PROVIDER_NAME
        api_key = user.api_key if user.api_key else DEFAULT_API_KEY
        base_url = user.base_url if user.base_url else DEFAULT_API_BASE

        try:
            switcher = {AI_PROVIDER_OPENAI: NewClientOpenAI(api_key, base_url)}
            return switcher.get(provider_name)
        except Exception as e:
            raise e


def NewClientUser(rdb_session: Session):
    return ClientUser(rdb_session)
