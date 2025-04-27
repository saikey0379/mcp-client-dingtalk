import json
# 导入ai客户端
from src.ai_clients.clients import GetAIClients
# 导入ai提供商
from src.ai_clients.provider import GetProviderByModel
# 导入日志
from src.logger import GetLogger
# 导入mcp服务器
from src.mcp_servers import GetMCPServers

# mcp客户端
AppMCPClient = None

# mcp客户端
class MCPClient:
    # 初始化
    def __init__(self):
        self.logger = None
        self.ai_clients = None
        self.initialize()

    def initialize(self):
        # 获取日志
        self.logger = GetLogger().logger
        # 获取ai客户端
        self.ai_clients = GetAIClients()

    async def query(self, user:str,query:str) -> str:
        try:
            user_model="gpt-4o"
            ai_client = GetAIClients().ai_clients[GetProviderByModel(user_model)].GetClient()
            mcp_servers = GetMCPServers()

            self.logger.info(f"用户{user}，调用LLM...")
            messages = [{"role": "user", "content": query}]  # 初始化消息列表   
            response = await ai_client.chat.completions.create(
                model=user_model,
                messages=messages,
                tools=mcp_servers.available_tools,
            )
            self.logger.info(f"用户{user}，LLM调用完成")
            final_text = []  # 存储最终回复内容
            message = response.choices[0].message
            final_text.append(message.content)  # 添加模型的初始回复

            # 处理工具调用
            while message.tool_calls:
                self.logger.info(f"用户{user}，处理工具调用...")
                for tool_call in message.tool_calls:
                    prefixed_name = tool_call.function.name
                    if prefixed_name in mcp_servers.tool_mapping:
                        server_name, original_tool_name = mcp_servers.tool_mapping[prefixed_name]
                        tool_args = json.loads(tool_call.function.arguments)

                        try:
                            if server_name in mcp_servers.mcp_sessions:
                                mcp_server_session = mcp_servers.mcp_sessions[server_name]
                                result = await mcp_server_session.session.call_tool(original_tool_name, tool_args)
                            else:
                                result = {"content": f"工具 {original_tool_name} 未找到"}
                        except Exception as e:
                            self.logger.error(f"调用工具 {original_tool_name} 出错：{str(e)}")
                            result = {"content": f"调用工具 {original_tool_name} 出错：{str(e)}"}

                        final_text.append(f"[调用工具 {prefixed_name} 参数: {tool_args}]")
                        messages.extend([
                            {
                                "role": "assistant",
                                "tool_calls": [{
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {"name": prefixed_name, "arguments": json.dumps(tool_args)},
                                }],
                            },
                            {"role": "tool", "tool_call_id": tool_call.id, "content": str(result)},
                        ])
                    else:
                        self.logger.error(f"工具 {prefixed_name} 未找到")
                        final_text.append(f"工具 {prefixed_name} 未找到")
                self.logger.info(f"用户{user}，处理工具调用完成")
                # 获取工具调用后的后续回复
                response = await ai_client.chat.completions.create(
                    model=user_model,
                    messages=messages,
                    tools=mcp_servers.available_tools,
                )
                message = response.choices[0].message
                if message.content:
                    final_text.append(message.content)

            return "\n".join(final_text)
        except Exception as e:
            self.logger.error(f"查询失败：{str(e)}")
            return f"查询失败：{str(e)}"

# 获取mcp客户端
def GetMCPClient():
    # 定义mcp客户端全局变量
    global AppMCPClient
    # 如果mcp客户端为空
    if AppMCPClient is None:
        # 创建mcp客户端
        AppMCPClient = MCPClient()
    
    # 返回mcp客户端
    return AppMCPClient