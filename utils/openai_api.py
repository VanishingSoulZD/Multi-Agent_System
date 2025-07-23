import os

from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
)

model = "accounts/fireworks/models/llama4-scout-instruct-basic"


def chat_with_gpt(messages):
    response = client.chat.completions.create(
        messages=messages,
        model=model,
        temperature=0.7,
        max_tokens=500,
    )
    return response.choices[0].message.content
