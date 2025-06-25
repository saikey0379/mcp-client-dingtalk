import json
import asyncio
# 导入状态


class MCPService:
    # 初始化
    def __init__(self, logger, client_user, mcp_client, service_card):
        self.logger = logger
        self.client_user = client_user
        self.mcp_client = mcp_client
        self.service_card = service_card

    # 查询
    async def query(self, user_name: str, user_id: str, query: str, conversationType: str) -> str:
        try:
            user = self.client_user.get_user_by_id(user_id)
            user_model = user.model
        except Exception as e:
            self.logger.error(f"用户{user_name}[{user_id}]，配置查询失败：{str(e)}")
            return f"用户{user_name}[{user_id}]，配置查询失败：{str(e)}"

        user_prompt = self.client_user.get_user_prompt(user_id)
        user_prompt.append(query)

        try:
            self.logger.info(f"用户{user_name}[{user_id}]，请求LLM...")
            # 获取工具
            ai_client = self.client_user.get_user_client_ai(user_id)

            response_pre_query = await ai_client.get_response_tool_calls(user_model, query, self.mcp_client.available_tools)
            if response_pre_query is None:
                self.logger.info(f"用户{user_name}[{user_id}]LLM结果为空，请求完成")
                return f"用户{user_name}[{user_id}]，LLM结果为空，请求完成"

        except Exception as e:
            self.logger.error(f"用户{user_name}[{user_id}]，请求LLM失败：{str(e)}")
            return f"用户{user_name}[{user_id}]，请求LLM失败：{str(e)}"

        message_pre_query = response_pre_query.choices[0].message
        user_prompt.append(message_pre_query.content)

        if message_pre_query.tool_calls is None:
            self.logger.info(f"用户{user_name}[{user_id}]，请求未匹配MCP-Tools，请求完成")
            return str(message_pre_query.content)

        self.logger.info(
            f"用户{user_name}[{user_id}]，请求匹配MCP-Tools[{message_pre_query.tool_calls}]")
        # 处理工具调用
        for tool_call in message_pre_query.tool_calls:
            # 获取工具名称
            mapping_tool_name = tool_call.function.name
            # 获取工具参数
            tool_args = json.loads(tool_call.function.arguments)
            tool_template = self.mcp_client.mapping_tools[mapping_tool_name]
            # 创建钉钉确认标签
            try:
                self.logger.info(
                    f"用户{user_name}，工具[{mapping_tool_name}]调用,创建卡片]")

                user_decision = self.service_card.card.create_card(
                    conversationType, user_name, user_id, mapping_tool_name, tool_args, tool_template)
            except asyncio.TimeoutError:
                self.logger.info(
                    f"用户{user_name}，超时未确认工具[{mapping_tool_name}]调用")
                return "超时未确认，操作已中止"
            except Exception as e:
                self.logger.error(f"用户{user_name}，创建卡片失败：{str(e)}")
                return "创建卡片失败，操作已中止"

            # 如果用户确认，则调用工具
            if user_decision == "确认":
                self.service_card.card.update_card(
                    mapping_tool_name, tool_args)
            if user_decision == "取消":
                self.logger.info(f"用户{user_name}，取消工具[{mapping_tool_name}]调用")
                continue

            # 调用工具
            result = await self.mcp_client.mcp_call_tool(mapping_tool_name, tool_args)
            #    user_content.append(f"用户{user_name}，调用工具[{tool_call}]完成,结果[{result}]".encode("utf-8"))
            #   self.logger.info(f"用户{user_name}，调用工具[{tool_name}]完成，结果[{result}]")
            # elif user_decision == "取消":
            #    user_content.append(f"用户{user_name}，取消工具[{tool_name}]调用".encode("utf-8"))
            #    self.logger.info(f"用户{user_name}，取消工具[{tool_name}]调用")
            #    continue
            user_prompt.append(
                json.dumps([
                    {
                        "role": "assistant",
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {"name": mapping_tool_name, "arguments": json.dumps(tool_args)},
                        }],
                    },
                    {"role": "tool", "tool_call_id": tool_call.id,
                     "content": str(result)},
                ])
            )

            # 获取工具调用后的最终回复
            response = await ai_client.get_response_tool_calls(user_model, str(user_prompt.get_prompt()), self.mcp_client.available_tools)

            message = response.choices[0].message
            user_prompt.append(message.content)
            return message.content


def NewMCPService(logger, client_user, mcp_client, service_card):
    return MCPService(logger, client_user, mcp_client, service_card)
