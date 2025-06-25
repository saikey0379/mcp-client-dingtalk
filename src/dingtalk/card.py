import json
import requests
import dingtalk_stream

from src.tools.string import FormatJsonString
from src.user.model.user import User
from src.dingtalk.const import DINGTALK_OPENAPI_ENDPOINT


def create_card_call_tools(card_template_id_call_tools, user, tool_call_id, tool_call_name, tool_call_args, client_mcp, dingtalk_client, incoming_message):
    card_template_id = card_template_id_call_tools   # 卡片平台上自己搭建的卡片模板 id
    card_data = {
        "user_id": user.user_id,
        "server_name": client_mcp.get_server_and_tool_name(tool_call_name)[0],
        "tool_call_id": tool_call_id,
        "tool_call_name": client_mcp.get_server_and_tool_name(tool_call_name)[1],
        "tool_call_args": f"{FormatJsonString(tool_call_args)}",
        "request": f"{FormatJsonString(tool_call_args)}",
        "description": client_mcp.get_tool_description(tool_call_name),
        "status_input": "normal",
    }

    if incoming_message.conversation_type == "2":
        card_data["inform"] = f"@{user.user_name}"

    card_instance_id = create_and_deliver_card(
        user, dingtalk_client, incoming_message, card_template_id, card_data)
    return card_instance_id


def generate_card_update(inform: str, status_action: str):
    # cardUpdateOptions
    cardUpdateOptions = {
        "updateCardDataByKey": True,
    }

    card_request = {
        "cardUpdateOptions": cardUpdateOptions,
        "cardData": {
            "cardParamMap": {
                "status_input": "disabled",
                "status_action": status_action,
                "inform": inform,
            }
        },
    }
    return card_request


def create_and_deliver_card(
    user: User,
    dingtalk_client: dingtalk_stream.DingTalkStreamClient,
    incoming_message: dingtalk_stream.ChatbotMessage,
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
    card_replier = dingtalk_stream.CardReplier(
        dingtalk_client, incoming_message)
    access_token = dingtalk_client.get_access_token()
    if not access_token:
        raise Exception(
            "CardResponder.send_card failed, cannot get dingtalk access token")

    card_instance_id = card_replier.gen_card_id(incoming_message)
    body = {
        "cardTemplateId": card_template_id,
        "outTrackId": card_instance_id,
        "cardData": {"cardParamMap": card_data},
        "callbackType": "STREAM",
        "imGroupOpenSpaceModel": {"supportForward": True},
        "imRobotOpenSpaceModel": {"supportForward": True},
    }

    # 2：群聊，1：单聊
    if incoming_message.conversation_type == "2":
        body["openSpaceId"] = "dtv1.card//{spaceType}.{spaceId}".format(
            spaceType="IM_GROUP", spaceId=incoming_message.conversation_id
        )
        body["imGroupOpenDeliverModel"] = {
            "robotCode": dingtalk_client.credential.client_id,
        }

        body["imGroupOpenDeliverModel"]["atUserIds"] = {
            incoming_message.sender_staff_id: incoming_message.sender_nick,
        }
        body["imGroupOpenDeliverModel"]["atMobiles"] = [user.mobile]

        body["imGroupOpenDeliverModel"]["recipients"] = [
            incoming_message.sender_staff_id]

        # 增加托管extension
        if incoming_message.hosting_context is not None:
            body["imGroupOpenDeliverModel"]["extension"] = {
                "hostingRepliedContext": json.dumps(
                    {"userId": incoming_message.hosting_context.user_id}
                )
            }
    elif incoming_message.conversation_type == "1":
        body["openSpaceId"] = "dtv1.card//{spaceType}.{spaceId}".format(
            spaceType="IM_ROBOT", spaceId=incoming_message.sender_staff_id
        )
        body["imRobotOpenDeliverModel"] = {"spaceType": "IM_ROBOT"}

        # 增加托管extension
        if incoming_message.hosting_context is not None:
            body["imRobotOpenDeliverModel"]["extension"] = {
                "hostingRepliedContext": json.dumps(
                    {"userId": incoming_message.hosting_context.user_id}
                )
            }

    url = DINGTALK_OPENAPI_ENDPOINT + "/v1.0/card/instances/createAndDeliver"
    try:
        response_text = ""
        body = {**body, **kwargs}

        response = requests.post(
            url, headers=card_replier.get_request_header(access_token), json=body
        )
        response_text = response.text

        response.raise_for_status()
    except Exception as e:
        raise Exception(
            f"CardReplier.create_and_deliver_card failed, error={e}, response.text={response_text}")

    return card_instance_id
