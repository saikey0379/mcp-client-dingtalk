import json
import logging
import requests
import asyncio
import dingtalk_stream
from dingtalk_stream import AckMessage, ChatbotMessage

from app.state import app_state

from src.dingtalk.card_replay import create_card_call_tools, update_card_call_tools, create_card_ai_results, update_card_ai_results
from src.dingtalk.const import MESSAGE_FLUSH_USER, MESSAGE_CONFIG_USER
from src.user.model.user import User


def convert_json_values_to_string(obj: dict) -> dict:
    result = {}
    for key, value in obj.items():
        if isinstance(value, str):
            result[key] = value
        else:
            result[key] = json.dumps(value, ensure_ascii=False)
    return result


class ChatBotHandler(dingtalk_stream.ChatbotHandler):
    def __init__(self, logger: logging.Logger = None, dingtalk_client: dingtalk_stream.DingTalkStreamClient = None, card_template_id_user_config: str = None, card_template_id_call_tools: str = None, card_template_id_ai_result: str = None):
        super(ChatBotHandler, self).__init__()
        if logger:
            self.logger = logger
        self.dingtalk_client = dingtalk_client
        self.card_template_id_user_config = card_template_id_user_config
        self.card_template_id_call_tools = card_template_id_call_tools
        self.card_template_id_ai_result = card_template_id_ai_result

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = dingtalk_stream.ChatbotMessage.from_dict(
            callback.data)
        self.logger.info(f"incoming_message：{incoming_message}")

        user_id = incoming_message.sender_staff_id
        try:
            user = app_state.service_user.get_user_by_id(user_id)
            if user is None:
                self.reply_text(
                    f"用户{user_id}不存在,请输入\"{MESSAGE_CONFIG_USER}\"配置用户...", incoming_message)
                self.logger.error(
                    f"用户{user_id}不存在,请输入\"{MESSAGE_CONFIG_USER}\"配置用户...")
                return AckMessage.STATUS_OK, "OK"
        except Exception as e:  
            self.reply_text(f"用户{user_id}查询失败...", incoming_message)
            self.logger.error(f"用户{user_id}查询失败...{e}")
            return AckMessage.STATUS_OK, "OK"

        app_state.service_user.set_chat_session(
            incoming_message)

        if incoming_message.message_type != "text":
            self.reply_text("我看不懂你在说什么，请输入文字哦", incoming_message)
            return AckMessage.STATUS_OK, "OK"

        user_message = incoming_message.text.content
        if user_message.lstrip() == MESSAGE_FLUSH_USER:
            try:
                app_state.service_user.flush_chat_session(user_id)
            except Exception as e:
                self.reply_text("清除会话失败，请稍后重试", incoming_message)
                self.logger.error(f"清除会话失败...{e}")
                return AckMessage.STATUS_OK, "OK"

            self.reply_text("好的，会话已清除", incoming_message)
            return AckMessage.STATUS_OK, "OK"

#        if user_message == MESSAGE_CONFIG_USER:
#            card_instance_id = create_card_config_user(
#                self.card_template_id_config_user, user_id, self.dingtalk_client, incoming_message)
#            self.logger.info(
#                f"reply create_card_config_user [card_instance_id={card_instance_id}] user_id={user_id}")
#            return AckMessage.STATUS_OK, "OK"

        try:
            client_ai = app_state.service_user.get_user_client_ai_async(user_id)
        except Exception as e:
            self.reply_text(f"用户{user_id}不存在...", incoming_message)
            self.logger.error(f"用户{user_id}不存在...{e}")
            return AckMessage.STATUS_OK, "OK"

        client_mcp = app_state.mcp_client

        app_state.service_user.append_user_chat_history(
            user_id, {"role": "user", "content": user_message})

        card_instance_id, card_instance = create_card_ai_results(
            self.dingtalk_client, user, self.card_template_id_ai_result)
        user_chat_history = app_state.service_user.get_user_chat_history(
            user_id)
        response_ai = await client_ai.get_response_ai_calls_async(app_state.service_user.get_user_model_by_user_id(user_id), user_chat_history, client_mcp.get_function_tools())
        result = response_ai.choices[0].message

        if result.tool_calls is None:
            await card_instance.async_streaming(
                card_instance_id, "content", result.content, False, True, False)
            return AckMessage.STATUS_OK, "OK"
        else:
            content = "检测到可用工具"

            await card_instance.async_streaming(
                card_instance_id, "content", content, False, True, False)

            time_sleep = len(content) * 0.02
            await asyncio.sleep(time_sleep)

            app_state.service_user.set_user_mcp_tasks(user_id, result.tool_calls)
            tool_call = result.tool_calls[0]    
            tool_call_id = tool_call.id
            tool_call_name = tool_call.function.name
            tool_call_args = tool_call.function.arguments

            card_instance_id = create_card_call_tools(
                self.dingtalk_client, user, self.card_template_id_call_tools, tool_call_id, tool_call_name, tool_call_args, client_mcp)
            self.logger.info(
                    f"reply card [card_instance_id={card_instance_id}] user_id={user_id} tool_call_name={tool_call_name} tool_call_args={tool_call_args}"
            )

        return AckMessage.STATUS_OK, "OK"


class CardCallbackHandler(dingtalk_stream.CallbackHandler):
    def __init__(self, logger: logging.Logger = None, dingtalk_client: dingtalk_stream.DingTalkStreamClient = None, card_template_id_call_tools: str = None, card_template_id_ai_result: str = None, chatbot_handler: ChatBotHandler = None):
        super(dingtalk_stream.CallbackHandler, self).__init__()
        self.dingtalk_client = dingtalk_client
        self.chatbot_handler = chatbot_handler
        self.card_template_id_call_tools = card_template_id_call_tools
        self.card_template_id_ai_result = card_template_id_ai_result
        self.active_tasks = set()  # 跟踪活跃任务
        
        if logger:
            self.logger = logger

    async def process(self, callback: dingtalk_stream.CallbackMessage):
        incoming_message = dingtalk_stream.CardCallbackMessage.from_dict(
            callback.data)
        self.logger.info(
            f"card callback message: {incoming_message.to_dict()}")

        user_id = incoming_message.user_id

        try:
            user = app_state.service_user.get_user_by_id(user_id)
            if user is None:
                inform = f"用户{user_id}不存在,请输入\"{MESSAGE_CONFIG_USER}\"配置用户..."
                self.logger.error(inform)
                return AckMessage.STATUS_OK, update_card_call_tools(inform, "")
        except Exception as e:
            inform = f"用户{user_id}查询失败..."
            self.logger.error(f"{inform}...{e}")
            return AckMessage.STATUS_OK, update_card_call_tools(inform, "")

        card_private_data = incoming_message.content.get("cardPrivateData", {})
        params = card_private_data.get("params", {})
        inform = params.get("inform", "")

        user_id_request = params.get("user_id", "")
        if user_id_request == "":
            inform = f"{inform} 抱歉，无法确认用户信息，请重新配置用户"
            self.logger.info(f"inform: {inform}")
            return AckMessage.STATUS_OK, update_card_call_tools(inform, "")

        if user_id != user_id_request:
            inform = f"{inform} 抱歉，您没有该卡片的权限"
            self.logger.info(f"inform: {inform}")
            return AckMessage.STATUS_OK, update_card_call_tools(inform, "")

        action = params.get("action", "")
        if action == "agree":
            # 创建任务并跟踪
            task = asyncio.create_task(self.handle_action(params))
            self.active_tasks.add(task)
            task.add_done_callback(self.active_tasks.discard)  # 任务完成后自动清理
        elif action != "reject":
            inform = f"{inform} 请确认您的操作是否正确"

        status_action = action

        # Return immediately
        return AckMessage.STATUS_OK, update_card_call_tools(inform, status_action)

    async def handle_action(self, params,):
        user_id = params.get("user_id", "")

        message = app_state.service_user.get_chat_session(user_id)

        try:
            user = app_state.service_user.get_user_by_id(user_id)
            if user is None:
                self.logger.error(
                    f"用户{user_id}不存在,请输入\"{MESSAGE_CONFIG_USER}\"配置用户...")
                result = f"用户{user_id}不存在,请输入\"{MESSAGE_CONFIG_USER}\"配置用户..."
                reply_markdown("result", result, message, user)
                return
        except Exception as e:
            self.logger.error(f"用户{user_id}查询失败...{e}")

            result = f"用户{user_id}查询失败...{e}"
            reply_markdown("result", result, message, user)
            return

        server_name = params.get("server_name", {})
        tool_call_name = params.get("tool_call_name", {})

        card_instance_id, card_instance = create_card_ai_results(
            self.dingtalk_client, user, self.card_template_id_ai_result)

        if params.get("local_tool_call_args", {}) != {} and params.get("local_tool_call_args", {}) != "local_tool_call_args":
            app_state.service_user.append_user_chat_history(
                user_id, {"role": "user", "content": f"修改查询请求为{params.get('local_tool_call_args', {})}"})
            tool_call_args = json.loads(params.get("local_tool_call_args", {}))
        else:
            tool_call_args = json.loads(params.get("tool_call_args", {}))

        try:
            resp = await app_state.mcp_client.mcp_call(server_name, tool_call_name, tool_call_args)
            app_state.service_user.custom_mcp_task(user_id)
            
            tool_call_id = params.get("tool_call_id", {})
            app_state.service_user.append_user_chat_history(user_id,
                                                           {"role": "assistant", "tool_calls": [{
                                                               "id": tool_call_id,
                                                               "type": "function",
                                                               "function": {"name": tool_call_name, "arguments": json.dumps(tool_call_args)},
                                                           }]})
            app_state.service_user.append_user_chat_history(
                user_id, {"role": "tool", "tool_call_id": tool_call_id, "content": str(resp)})

            # 创建任务并跟踪
            task = asyncio.create_task(update_card_ai_results(
                card_instance_id, card_instance, user))
            self.active_tasks.add(task)
            task.add_done_callback(self.active_tasks.discard)  # 任务完成后自动清理
            
            tool_calls = app_state.service_user.get_user_mcp_tasks(user_id)
            if len(tool_calls) > 0:
                tool_call = tool_calls[0]
                tool_call_id = tool_call.id
                tool_call_name = tool_call.function.name
                tool_call_args = tool_call.function.arguments
            
                card_instance_id = create_card_call_tools(
                    self.dingtalk_client, user, self.card_template_id_call_tools, tool_call_id, tool_call_name, tool_call_args, app_state.mcp_client)
                self.logger.info(
                    f"reply card [card_instance_id={card_instance_id}] user_id={user_id} tool_call_name={tool_call_name} tool_call_args={tool_call_args}"
                )

        except Exception as e:
            card_instance.fail(card_instance_id, {
                "content": f"调用工具 {server_name}.{tool_call_name} 出错：{str(e)}"})
            return


def reply_markdown(title: str,
                   text: str,
                   incoming_message: ChatbotMessage, user: User):
    request_headers = {
        'Content-Type': 'application/json',
        'Accept': '*/*',
    }
    values = {
        'msgtype': 'markdown',
        'markdown': {
            'title': title,
            'text': text,
        },
        'at': {
            'atUserIds': [incoming_message.sender_staff_id],
            "isAtAll": False
        }
    }
    if incoming_message.conversation_type == "2":
        values['at']['atMobiles'] = [user.mobile]
        values['markdown']['text'] = f"@{user.mobile}\n\n{text}"

    try:
        response_text = ''
        response = requests.post(incoming_message.session_webhook,
                                 headers=request_headers,
                                 data=json.dumps(values))
        response_text = response.text

        response.raise_for_status()
    except Exception as e:
        raise Exception(
            f'reply markdown failed, error={e}, response.text={response_text}')
    return response.json()
