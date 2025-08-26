from ast import Dict, List
import asyncio
from enum import Enum
import json
import logging
import os
from typing import Any, Optional
import uuid
import anyio
import mcp.client.mqtt as mcp_mqtt
from mcp.shared.mqtt import configure_logging
from openai import OpenAI
from openai.types import CompletionUsage
import re
from tool_description import Message, ToolDefinition
from typing import cast
import mcp.types as types


configure_logging(level="DEBUG")
logger = logging.getLogger(__name__)


async def on_mcp_server_discovered(client, server_name):
    logger.info(f"Discovered {server_name}, connecting ...")
    await client.initialize_mcp_server(server_name)


async def on_mcp_connect(client, server_name, connect_result):
    capabilities = client.get_session(server_name).server_info.capabilities
    logger.info(f"Capabilities of {server_name}: {capabilities}")
    if capabilities.prompts:
        prompts = await client.list_prompts(server_name)
        logger.info(f"Prompts of {server_name}: {prompts}")
    if capabilities.resources:
        resources = await client.list_resources(server_name)
        logger.info(f"Resources of {server_name}: {resources}")
        resource_templates = await client.list_resource_templates(server_name)
        logger.info(f"Resources templates of {server_name}: {resource_templates}")
    if capabilities.tools:
        toolsResult = await client.list_tools(server_name)
        tools = toolsResult.tools
        logger.info(f"Tools of {server_name}: {tools}")


async def on_mcp_disconnect(client, server_name):
    logger.info(f"Disconnected from {server_name}")


SERVER_NAME = "ESP32 Demo Server"


from typing import Dict  # <-- Add this import at the top of your file if not present


async def get_mcp_tools(
    mcp_client: mcp_mqtt.MqttTransportClient,
) -> list[dict]:
    """
    获取 MCP 工具列表，并将其转换为可 JSON 序列化的字典列表。
    """

    tool_list: list[dict] = []

    try:
        tools_result = await mcp_client.list_tools(SERVER_NAME)

        if tools_result is False:
            return tool_list

        list_tools_result = cast(types.ListToolsResult, tools_result)
        tools = list_tools_result.tools

        for tool in tools:
            tool_def = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": getattr(tool, "inputSchema", None),
                },
            }
            tool_list.append(tool_def)

    except Exception as e:
        logger.error(f"Get tool list error: {e}")

    return tool_list


def extract_json_from_string(input_string):
    """提取字符串中的 JSON 部分"""
    pattern = r"(\{.*\})"
    match = re.search(pattern, input_string, re.DOTALL)  # 添加 re.DOTALL
    if match:
        return match.group(1)  # 返回提取的 JSON 字符串
    return None


class Action(Enum):
    ERROR = (-1, "错误")
    NOTFOUND = (0, "没有找到函数")
    NONE = (1, "啥也不干")
    RESPONSE = (2, "直接回复")
    REQLLM = (3, "调用函数后再请求llm生成回复")

    def __init__(self, code, message):
        self.code = code
        self.message = message


class ActionResponse:
    def __init__(self, action: Action, result=None, response=None):
        self.action = action  # 动作类型
        self.result = result  # 动作产生的结果
        self.response = response  # 直接回复的内容


class ConversationalAgent:
    def __init__(
        self,
        model_name,
        llm: OpenAI,
        mcp_client: Optional[mcp_mqtt.MqttTransportClient] = None,
    ):

        self.llm = llm

        self.model_name = model_name

        self.mcp_client = mcp_client

        self.dialogue: List[Message] = []

        self.logger = logger

        self.loop = asyncio.get_event_loop()

        self.tools: List[Dict] = []

    async def init(self):
        tools = await get_mcp_tools(self.mcp_client) if self.mcp_client else []
        self.tools = tools
        self.dialogue.append(
            Message(
                role="system",
                content="""
                在这个对话中，你将扮演一个情感助手。
                你有视觉能力，当你被问 “你看看我今天打扮得怎么样”、“你看看我这件衣服是什么牌子的” 等视觉相关问题时，你可以调用 "explain_photo" 这个工具，
                这个工具可以给主人拍摄一张照片，然后针对此照片做出评价，并将评价返回给你。
                根据我提供的问题，生成一个富有温度的回应。
                """,
            )
        )

    def call_openai(self, query, functions=None):
        try:
            # Convert Message objects to dicts before sending to OpenAI
            def message_to_dict(msg):
                d = msg.__dict__.copy()
                # Remove None values for OpenAI compatibility
                return {k: v for k, v in d.items() if v is not None}

            messages_payload = [message_to_dict(m) for m in self.dialogue]
            messages_payload.append(
                message_to_dict(Message(role="user", content=query))
            )
            stream = self.llm.chat.completions.create(
                model=self.model_name,
                messages=messages_payload,
                stream=True,
                tools=functions,
            )

            for chunk in stream:
                # 检查是否存在有效的choice且content不为空
                if getattr(chunk, "choices", None):
                    yield (
                        chunk.choices[0].delta.content,
                        chunk.choices[0].delta.tool_calls,
                    )
                # 存在 CompletionUsage 消息时，生成 Token 消耗 log
                elif isinstance(getattr(chunk, "usage", None), CompletionUsage):
                    usage_info = getattr(chunk, "usage", None)
                    logger.info(
                        f"Token 消耗：输入 {getattr(usage_info, 'prompt_tokens', '未知')}，"
                        f"输出 {getattr(usage_info, 'completion_tokens', '未知')}，"
                        f"共计 {getattr(usage_info, 'total_tokens', '未知')}"
                    )

        except Exception as e:
            logger.error(f"Error in function call streaming: {e}")

    async def handle_llm_function_call(
        self,
        function_call_data: Dict[str, Any],
    ) -> Optional[ActionResponse]:
        """处理LLM函数调用"""
        try:
            # 处理单函数调用
            function_name = function_call_data["name"]
            arguments = function_call_data.get("arguments", {})

            # 如果arguments是字符串，尝试解析为JSON
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments) if arguments else {}
                except json.JSONDecodeError:
                    self.logger.error(f"无法解析函数参数: {arguments}")
                    return ActionResponse(
                        action=Action.ERROR,
                        response="无法解析函数参数",
                    )

            self.logger.debug(f"调用函数: {function_name}, 参数: {arguments}")

            # 执行工具调用（需要等待协程完成）
            result = await self.mcp_client.call_tool(
                SERVER_NAME, function_name, arguments
            )
            return ActionResponse(action=Action.REQLLM, result=result)

        except Exception as e:
            self.logger.error(f"处理function call错误: {e}")
            return ActionResponse(action=Action.ERROR, response=str(e))

    async def _handle_function_result(self, result, function_call_data):
        if result.action == Action.REQLLM:
            call_result = cast(types.CallToolResult, result.result)
            text = call_result.content
            if text is not None and len(text) > 0:
                function_id = function_call_data["id"]
                function_name = function_call_data["name"]
                function_arguments = function_call_data["arguments"]
                self.dialogue.append(
                    Message(
                        role="assistant",
                        tool_calls=[
                            {
                                "id": function_id,
                                "function": {
                                    "arguments": (
                                        "{}"
                                        if function_arguments == ""
                                        else function_arguments
                                    ),
                                    "name": function_name,
                                },
                                "type": "function",
                                "index": 0,
                            }
                        ],
                    )
                )

                self.dialogue.append(
                    Message(
                        role="tool",
                        tool_call_id=(
                            str(uuid.uuid4()) if function_id is None else function_id
                        ),
                        content=text,
                    )
                )
            res = await self.chat("请根据以上工具调用结果，回复用户")
            return res
        else:
            pass

    async def chat(self, query) -> str:

        # Load tools and set to self.tools
        tools = await get_mcp_tools(self.mcp_client) if self.mcp_client else {}
        llm_responses = self.call_openai(query, tools)

        # 处理流式响应
        response_message = []
        tool_call_flag = False
        function_name = None
        function_id = None
        function_arguments = ""
        content_arguments = ""

        for response in llm_responses:

            content, tools_call = response

            if "content" in response:
                content = response["content"]
                tools_call = None

            if content is not None and len(content) > 0:
                content_arguments += content

            if not tool_call_flag and content_arguments.startswith("<tool_call>"):
                # print("content_arguments", content_arguments)
                tool_call_flag = True

            if tools_call is not None and len(tools_call) > 0:
                tool_call_flag = True
                if tools_call[0].id is not None:
                    function_id = tools_call[0].id
                if tools_call[0].function.name is not None:
                    function_name = tools_call[0].function.name
                if tools_call[0].function.arguments is not None:
                    function_arguments += tools_call[0].function.arguments

            if content is not None and len(content) > 0:
                if not tool_call_flag:
                    response_message.append(content)

        # 处理function call
        if tool_call_flag:
            bHasError = False
            if function_id is None:
                a = extract_json_from_string(content_arguments)
                if a is not None:
                    try:
                        content_arguments_json = json.loads(a)
                        function_name = content_arguments_json["name"]
                        function_arguments = json.dumps(
                            content_arguments_json["arguments"], ensure_ascii=False
                        )
                        function_id = str(uuid.uuid4().hex)
                    except Exception as e:
                        bHasError = True
                        response_message.append(a)
                else:
                    bHasError = True
                    response_message.append(content_arguments)
                if bHasError:
                    self.logger.error(f"function call error: {content_arguments}")
            if not bHasError:
                # 如需要大模型先处理一轮，添加相关处理后的日志情况
                if len(response_message) > 0:
                    text_buff = "".join(response_message)
                    self.dialogue.append(Message(role="assistant", content=text_buff))
                response_message.clear()
                self.logger.debug(
                    f"function_name={function_name}, function_id={function_id}, function_arguments={function_arguments}"
                )
                function_call_data = {
                    "name": function_name,
                    "id": function_id,
                    "arguments": function_arguments,
                }

                # 使用统一工具处理器处理所有工具调用
                result = await self.handle_llm_function_call(function_call_data)
                respon = await self._handle_function_result(result, function_call_data)
                response_message.append(respon)

        # 存储对话内容
        if len(response_message) > 0:
            text_buff = "".join(response_message)
            self.tts_MessageText = text_buff
            self.dialogue.append(Message(role="assistant", content=text_buff))

        return text_buff


LLM = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",  # 填
)
MODEL_NAME = "qwen-plus"


async def main():
    try:
        async with mcp_mqtt.MqttTransportClient(
            "test_client",
            auto_connect_to_mcp_server=True,
            on_mcp_server_discovered=on_mcp_server_discovered,
            on_mcp_connect=on_mcp_connect,
            on_mcp_disconnect=on_mcp_disconnect,
            mqtt_options=mcp_mqtt.MqttOptions(
                host="127.0.0.1",
            ),
        ) as mcp_client:
            await mcp_client.start()
            await anyio.sleep(3)

            agent = ConversationalAgent(MODEL_NAME, LLM, mcp_client)

            await agent.init()

            print("input 'exit' or 'quit' exit")
            print("input 'tools' show available tools")
            print("=" * 50)

            while True:
                try:
                    user_input = input("\nuser: ").strip()

                    if user_input.lower() in ["exit", "quit"]:
                        break

                    if user_input.lower() == "tools":
                        # print(f"available tools: {len(agent.tools)}")
                        tools = (
                            await get_mcp_tools(agent.mcp_client)
                            if agent.mcp_client
                            else []
                        )

                        for tool in tools:
                            tool_name = getattr(tool, "name", str(tool))
                            tool_desc = getattr(tool, "description", "No description")
                            print(f"- {tool_name}: {tool_desc}")
                        continue

                    if not user_input:
                        continue

                    response = await agent.chat(user_input)
                    print(f"\nAgent: {response}")

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"error: {e}")

    except Exception as e:
        print(f"agent init error: {e}")


if __name__ == "__main__":
    anyio.run(main)
