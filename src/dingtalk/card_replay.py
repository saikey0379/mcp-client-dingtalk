from typing import Callable
import asyncio

from app.state import app_state

from src.user.model.user import User
from src.utils.string import FormatJsonString
from src.dingtalk.card import CardReplier, AICardReplier


def create_card_call_tools(dingtalk_client, user, card_template_id_call_tools, tool_call_id, tool_call_name, tool_call_args, client_mcp):
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

    card_instance = CardReplier(
        dingtalk_client, app_state.logger, user
    )
    incoming_message = app_state.service_user.get_chat_session(user.user_id)
    if incoming_message.conversation_type == "2":
        card_data["inform"] = f"@{user.user_name}"

    card_instance_id = card_instance.create_and_deliver_card(
        card_template_id, card_data, support_forward=True)
    return card_instance_id


def update_card_call_tools(inform: str, status_action: str):
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


def create_card_ai_results(dingtalk_client, user, card_template_id):
    content_key = "content"
    card_data = {content_key: ""}
    card_instance = AICardReplier(
        dingtalk_client, app_state.logger, user
    )
    card_instance_id = card_instance.start(card_template_id, card_data)
    return card_instance_id, card_instance


async def update_card_ai_results(card_instance_id, card_instance, user):
    # 卡片模板 ID
    # 该模板只用于测试使用，如需投入线上使用，请导入卡片模板 json 到自己的应用下

    # 先投放卡片: https://open.dingtalk.com/document/orgapp/create-and-deliver-cards
    # card_instance_id = card_instance.create_and_deliver_card(
    #    card_template_id, card_data
    # )
    # card_instance_id = create_and_deliver_card(
    #    user, dingtalk_client, appState.service_user.get_chat_session(user.user_id), card_template_id, card_data)

    content_key = "content"

    # 再流式更新卡片: https://open.dingtalk.com/document/isvapp/api-streamingupdate
    async def callback(content_value: str):
        return await card_instance.async_streaming(
            card_instance_id,
            content_key=content_key,
            content_value=content_value,
            append=False,
            finished=False,
            failed=False,
        )

    try:
        full_content_value = await stream_update_card_ai_results(
            user, callback
        )
        await card_instance.async_streaming(
            card_instance_id,
            content_key=content_key,
            content_value=full_content_value,
            append=False,
            finished=True,
            failed=False,
        )
    except Exception as e:
        await card_instance.async_streaming(
            card_instance_id,
            content_key=content_key,
            content_value="",
            append=False,
            finished=False,
            failed=True,
        )
        raise e


async def stream_update_card_ai_results(user: User, callback: Callable[[str], None]):
    user_chat_history = app_state.service_user.get_user_chat_history(
        user.user_id)
    client_ai = app_state.service_user.get_user_client_ai(user.user_id)

    responses = client_ai.get_client().chat.completions.create(
        model=app_state.service_user.get_user_model_by_user_id(
            user.user_id),
        messages=user_chat_history,
        stream=True,
    )

    full_content = ""  # with incrementally we need to merge output.
    length = 0
    response_count = 0
    
    for response in responses:
        response_count += 1
        
        if response.choices[0].delta.content is not None:
            full_content += response.choices[0].delta.content
        full_content_length = len(full_content)
        
        if full_content_length - length > 20:
            await callback(full_content)
            length = full_content_length
        
        # 每处理10个响应就让出控制权，避免阻塞事件循环
        if response_count % 10 == 0:
            await asyncio.sleep(0.01)  # 短暂让出控制权

    await callback(full_content)
    return full_content
