from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8000/v1",
    api_key="local"
)

response = client.chat.completions.create(
    model="local",
    messages=[
        {"role": "system", "content": "回答问题简洁完整"},
        {"role": "user", "content": "介绍一下自己"}
    ]
)

print(response.choices[0].message.content)