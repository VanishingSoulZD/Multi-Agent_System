import os

from openai import OpenAI, AuthenticationError, RateLimitError, APIError, OpenAIError

from utils.log import LOGD

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_API_BASE"),
)

model = "accounts/fireworks/models/llama4-scout-instruct-basic"


def chat_with_gpt(messages):
    try:
        response = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=0.7,
            max_tokens=500,
        )

        LOGD(f"total_tokens: {response.usage.total_tokens}, "
             f"prompt_tokens: {response.usage.prompt_tokens}, "
             f"completion_tokens: {response.usage.completion_tokens}")
        
        return response.choices[0].message.content
    except AuthenticationError as e:
        return "Authentication Error"
    except RateLimitError as e:
        return "Rate Limit Error"
    except APIError as e:
        return "API Error"
    except OpenAIError as e:
        return "OpenAI Error"
