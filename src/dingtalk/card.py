import requests
import json
import copy
import uuid
import aiohttp
import hashlib
import platform
from enum import Enum, unique

from app.state import app_state
from app.logger import Logger

from src.user.model.user import User
from src.dingtalk.const import DINGTALK_OPENAPI_ENDPOINT


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dingtalk_stream.chatbot import ChatbotMessage
    from dingtalk_stream.stream import DingTalkStreamClient


class CardReplier(object):

    def __init__(
        self,
        dingtalk_client: "DingTalkStreamClient",
        logger: Logger,
        user: User,
    ):
        self.dingtalk_client: "DingTalkStreamClient" = dingtalk_client
        self.incoming_message: "ChatbotMessage" = app_state.service_user.get_chat_session(
            user.user_id)
        self.user: User = user

    @staticmethod
    def gen_card_id(msg: "ChatbotMessage"):
        factor = "%s_%s_%s_%s_%s" % (
            msg.sender_id,
            msg.sender_corp_id,
            msg.conversation_id,
            msg.message_id,
            str(uuid.uuid1()),
        )
        m = hashlib.sha256()
        m.update(factor.encode("utf-8"))
        return m.hexdigest()

    @staticmethod
    def get_request_header(access_token):
        return {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "x-acs-dingtalk-access-token": access_token,
            "User-Agent": (
                "DingTalkStream/1.0 SDK/0.1.0 Python/%s "
                "(+https://github.com/open-dingtalk/dingtalk-stream-sdk-python)"
            )
            % platform.python_version(),
        }

    def create_and_deliver_card(
        self,
        card_template_id: str,
        card_data: dict,
        **kwargs,
    ) -> str:
        """
        创建并发送卡片一步到位，支持传入其他参数以达到投放吊顶场域卡片的效果等等。
        https://open.dingtalk.com/document/orgapp/create-and-deliver-cards
        :param support_forward: 卡片是否支持转发
        :param callback_route_key: HTTP 回调时的 route key
        :param callback_type: 卡片回调模式
        :param recipients: 接收者
        :param card_template_id: 卡片模板 ID
        :param card_data: 卡片数据
        :param at_sender: 是否@发送者
        :param at_all: 是否@所有人
        :param kwargs: 其他参数，如覆盖 openSpaceId，配置动态数据源 openDynamicDataConfig，配置吊顶场域 topOpenSpaceModel、topOpenDeliverModel 等等
        :return: 卡片的实例ID
        """
        access_token = self.dingtalk_client.get_access_token()
        if not access_token:
            raise Exception(
                "CardResponder.send_card failed, cannot get dingtalk access token")

        card_instance_id = self.gen_card_id(self.incoming_message)
        body = {
            "cardTemplateId": card_template_id,
            "outTrackId": card_instance_id,
            "cardData": {"cardParamMap": card_data},
            "callbackType": "STREAM",
            "imGroupOpenSpaceModel": {"supportForward": True},
            "imRobotOpenSpaceModel": {"supportForward": True},
        }

        # 2：群聊，1：单聊
        if self.incoming_message.conversation_type == "2":
            body["openSpaceId"] = "dtv1.card//{spaceType}.{spaceId}".format(
                spaceType="IM_GROUP", spaceId=self.incoming_message.conversation_id
            )
            body["imGroupOpenDeliverModel"] = {
                "robotCode": self.dingtalk_client.credential.client_id,
            }

            body["imGroupOpenDeliverModel"]["atUserIds"] = {
                self.incoming_message.sender_staff_id: self.incoming_message.sender_nick,
            }
            body["imGroupOpenDeliverModel"]["atMobiles"] = [self.user.mobile]

            body["imGroupOpenDeliverModel"]["recipients"] = [
                self.incoming_message.sender_staff_id]

            # 增加托管extension
            if self.incoming_message.hosting_context is not None:
                body["imGroupOpenDeliverModel"]["extension"] = {
                    "hostingRepliedContext": json.dumps(
                        {"userId": self.incoming_message.hosting_context.user_id}
                    )
                }
        elif self.incoming_message.conversation_type == "1":
            body["openSpaceId"] = "dtv1.card//{spaceType}.{spaceId}".format(
                spaceType="IM_ROBOT", spaceId=self.incoming_message.sender_staff_id
            )
            body["imRobotOpenDeliverModel"] = {"spaceType": "IM_ROBOT"}

            # 增加托管extension
            if self.incoming_message.hosting_context is not None:
                body["imRobotOpenDeliverModel"]["extension"] = {
                    "hostingRepliedContext": json.dumps(
                        {"userId": self.incoming_message.hosting_context.user_id}
                    )
                }

        url = DINGTALK_OPENAPI_ENDPOINT + "/v1.0/card/instances/createAndDeliver"
        try:
            response_text = ""
            body = {**body, **kwargs}

            response = requests.post(
                url, headers=self.get_request_header(access_token), json=body
            )
            response_text = response.text

            response.raise_for_status()
        except Exception as e:
            raise Exception(
                f"CardReplier.create_and_deliver_card failed, error={e}, response.text={response_text}")

        return card_instance_id


@unique
class AICardStatus(str, Enum):
    PROCESSING: str = 1  # 处理中
    INPUTING: str = 2  # 输入中
    EXECUTING: str = 4  # 执行中
    FINISHED: str = 3  # 执行完成
    FAILED: str = 5  # 执行失败


class AICardReplier(CardReplier):

    def __init__(self, dingtalk_client, logger: Logger, user: User):
        super(AICardReplier, self).__init__(dingtalk_client, logger, user)
        self.dingtalk_client: "DingTalkStreamClient" = dingtalk_client
        self.logger: Logger = logger
        self.user: User = user
        self.incoming_message: "ChatbotMessage" = app_state.service_user.get_chat_session(
            user.user_id)

    def start(
        self,
        card_template_id: str,
        card_data: dict,
    ) -> str:
        """
        AI卡片的创建接口
        :param support_forward:
        :param recipients:
        :param card_template_id:
        :param card_data:
        :return:
        """
        card_data_with_status = copy.deepcopy(card_data)
        card_data_with_status["flowStatus"] = AICardStatus.PROCESSING
        return self.create_and_deliver_card(
            card_template_id,
            card_data_with_status,
        )

    async def async_streaming(
        self,
        card_instance_id: str,
        content_key: str,
        content_value: str,
        append: bool,
        finished: bool,
        failed: bool,
    ):
        """
        AI卡片的流式输出
        :param card_instance_id:
        :param content_key:
        :param content_value:
        :param append:
        :param finished:
        :param failed:
        :return:
        """
        access_token = self.dingtalk_client.get_access_token()
        if not access_token:
            self.logger.error(
                "AICardReplier.streaming failed, cannot get dingtalk access token"
            )
            return None

        if self.incoming_message.conversation_type == "2":
            content_value = f"@{self.user.user_name}\n\n{content_value}"

        body = {
            "outTrackId": card_instance_id,
            "guid": str(uuid.uuid1()),
            "key": content_key,
            "content": content_value,
            "isFull": not append,
            "isFinalize": finished,
            "isError": failed,
        }

        url = DINGTALK_OPENAPI_ENDPOINT + "/v1.0/card/streaming"
        try:
            response_text = ''
            async with aiohttp.ClientSession() as session:
                async with session.put(
                    url, headers=self.get_request_header(access_token), json=body
                ) as response:
                    response_text = await response.text()

                    response.raise_for_status()
        except aiohttp.ClientResponseError as e:
            self.logger.error(
                f"AICardReplier.async_streaming failed, HTTP Error: {e.status}, URL: {url}, response.text={response_text}"
            )
        except Exception as e:
            self.logger.error(
                f"CardReplier.async_streaming unexpected error occurred: {e}"
            )
