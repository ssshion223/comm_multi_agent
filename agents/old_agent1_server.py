from openai import OpenAI
from tools import bfs_search, BFS_TOOL
import json

TOOLS = [BFS_TOOL]
TOOL_FUNCTIONS= {
    "bfs_search": bfs_search
}
client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="local"
)
messages = [
        {"role": "system", "content": "回答问题简洁完整"},
        {"role": "user", "content": "A到D的路径"}
    ]
response = client.chat.completions.create(
    model="local",
    messages=messages,
    tools=TOOLS
)
message = response.choices[0].message
if message.tool_calls:
    messages.append(message)
    for tool_call in message.tool_calls:
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        result = TOOL_FUNCTIONS[name](**arguments)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(result, ensure_ascii=False)
        })
    response = client.chat.completions.create(
        model="local",
        messages=messages,
        tools=[]
    )
print(response.choices[0].message.content)