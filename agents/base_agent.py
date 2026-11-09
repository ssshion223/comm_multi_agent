from typing import Any
from openai import AsyncOpenAI
from config.configuration import llm_api_key, llm_url, llm_model
import json
import inspect
llm_client = AsyncOpenAI(
    base_url=llm_url,
    api_key=llm_api_key
)
class BaseAgent:
    def __init__(
        self,
        name: str,
        client: AsyncOpenAI,
        model: str,
        system_prompt: str,
        tools: list,
        tool_functions: dict,
        max_steps: int = 8
    ):
        self.name = name
        self.client = client
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools
        self.tool_functions = tool_functions
        self.max_steps = max_steps

    async def run(self, user_input: str):
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]
        # for step in self.max_steps:

        return await self._run_tool_loop(messages)
    async def _run_tool_loop(self, messages: Any):
        response = await self._llm_call(messages, self.tools)
        message = response.choices[0].message
        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                message = await self._execute_tool(tool_call)
                messages.append(message)
            response = await self._llm_call(messages, self.tools)
        return response.choices[0].message.content
    async def _execute_tool(self, tool_call):
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        result = self.tool_functions[name](**arguments)
        if inspect.isawaitable(result):
            result = await result
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        }
    async def _llm_call(self, messages: Any, tools: list):
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools
        )
