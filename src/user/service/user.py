from dingtalk_stream.chatbot import ChatbotMessage

from src.user.io.user import ClientUser


class ServiceUser():
    def __init__(self, client_user: ClientUser):
        self.client_user = client_user

    def get_user_by_id(self, user_id: str):
        return self.client_user.get_user_by_id(user_id)

    def get_user_model_by_user_id(self, user_id: str):
        user = self.client_user.get_user_by_id(user_id)
        return user.model

    def set_chat_session(self, incoming_message: ChatbotMessage):
        return self.client_user.set_chat_session(incoming_message)

    def get_chat_session(self, user_id: str):
        return self.client_user.get_chat_session(user_id)

    def flush_chat_session(self, user_id: str):
        return self.client_user.flush_chat_session(user_id)

    def get_user_client_ai(self, user_id: str):
        return self.client_user.get_user_client_ai(user_id)

    def get_user_chat_history(self, user_id: str):
        return self.client_user.get_user_chat_history(user_id)

    def append_user_chat_history(self, user_id: str, message: dict):
        return self.client_user.append_user_chat_history(user_id, message)


def NewServiceUser(client_user: ClientUser):
    return ServiceUser(client_user)
