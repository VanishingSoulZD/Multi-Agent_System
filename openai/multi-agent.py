import asyncio
import os
import random

import litellm
from agents import (
    Agent,
    Runner,
    GuardrailFunctionOutput,
    function_tool,
    RunContextWrapper,
    ModelSettings,
    SQLiteSession,
    input_guardrail,
    output_guardrail,
    set_tracing_disabled,
    TResponseInputItem, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered,
)
from agents.extensions.models.litellm_model import LitellmModel
from agents.extensions.visualization import draw_graph
from pydantic import BaseModel

litellm.drop_params = True
set_tracing_disabled(True)
api_key = os.getenv('FIREWORKS_API_KEY')
# model = 'fireworks_ai/accounts/fireworks/models/llama4-scout-instruct-basic'
model = 'fireworks_ai/accounts/fireworks/models/qwen3-235b-a22b-instruct-2507'
print(f"LiteLLM provider fireworks {api_key=}, {model=}")


@function_tool
def get_weather(city: str) -> str:
    """returns weather info for the specified city."""
    print(f"[info] get_weather {city=}")
    return f"The weather in {city} is sunny."


# guardrail
# input guardrail, 禁止回答数学问题
class MathGuardrailOutput(BaseModel):
    is_math: bool
    reasoning: str


math_guardrail_agent = Agent(
    name='Math guardrail agent',
    instructions='Check if the user is asking about math.',
    output_type=MathGuardrailOutput,
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)


@input_guardrail
async def math_input_guardrail(
        ctx: RunContextWrapper[None],
        agent: Agent, input_data: str | list[TResponseInputItem]) -> GuardrailFunctionOutput:
    result = await Runner.run(
        starting_agent=math_guardrail_agent,
        input=input_data,
        context=ctx.context,
    )
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_math,
    )


# output guardrail, 禁止回答政治相关内容
class PoliticalGuardrailOutput(BaseModel):
    is_political: bool
    reasoning: str


political_guardrail_agent = Agent(
    name='Political guardrail agent',
    instructions='Check if the output includes any political related content.',
    output_type=PoliticalGuardrailOutput,
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)


@output_guardrail
async def political_output_guardrail(
        ctx: RunContextWrapper[None],
        agent: Agent, output: str,
) -> GuardrailFunctionOutput:
    result = await Runner.run(
        starting_agent=political_guardrail_agent,
        input=output,
    )
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_political,
    )


class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]


calendar_agent = Agent(
    name='Calendar extractor',
    instructions='Extract calendar events from text',
    handoff_description='Extract calendar events from text',
    output_type=CalendarEvent,
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)

history_tutor_agent = Agent(
    name='History tutor',
    instructions='Specialist agent for historical questions.',
    handoff_description='You provide assistance with historical queries. Explain important events and context clearly.',
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)


@function_tool
def how_many_jokes() -> int:
    joke_num = random.randint(1, 5)
    print(f"[info] how_many_jokes {joke_num=}")
    return joke_num


joke_agent = Agent(
    name='joke agent',
    instructions='First call the `how_many_jokes` tool, then tell that many jokes.',
    handoff_description='you tell user jokes',
    tools=[how_many_jokes],
    model_settings=ModelSettings(
        tool_choice='required',
    ),
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)

# agent as tool
english_to_chinese_agent = Agent(
    name='english_to_chinese_agent',
    instructions='you are a translator good at translate english to chinese',
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)

translate_agent = Agent(
    name='Translate Agent',
    instructions='translate message to specify language with tools',
    handoff_description='translate language',
    tools=[
        english_to_chinese_agent.as_tool(
            tool_name='translate_english_to_chinese',
            tool_description="Translate the user's message from english to chinese",
        ),
    ],
    model_settings=ModelSettings(
        tool_choice='required',
    ),
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
)

starting_agent = Agent(
    name='Starting agent',
    instructions='请总是用中文回答用户的问题，回答要简洁。请优先利用工具回答问题。',
    model=LitellmModel(
        api_key=api_key,
        model=model,
    ),
    input_guardrails=[
        math_input_guardrail,
    ],
    output_guardrails=[
        political_output_guardrail,
    ],
    handoffs=[
        translate_agent,
        history_tutor_agent,
        calendar_agent,
        joke_agent,
    ],
    tools=[
        # WebSearchTool,
        get_weather,
    ],
)


async def main():
    # visual
    draw_graph(starting_agent, 'starting_agent')

    # automatic conversation management
    session = SQLiteSession('conversation_1')

    while True:
        user_input = input('User: ')
        if user_input in ['quit', 'exit', 'q']:
            print('Assistant: Goodbye!')
            break

        try:
            result = await Runner.run(
                # result = Runner.run_streamed(
                starting_agent=starting_agent,
                input=user_input,
                session=session,
            )
            # normal question
            # 北京今天的天气怎么样？
            # 你能告诉我几个笑话吗？
            # 将这个英文句子翻译为中文：Are you OK?
            # 中国古代历史朝代秦朝的首都是哪里？
            # 帮我提取日程，小明和小黄周日去海边。
            print(f"Assistant: {result.final_output}")

        except InputGuardrailTripwireTriggered as e:
            # 我有一个数学题：1+1=？，答案是多少？
            print(f"Assistant: 抱歉，你的输入被禁止回答，理由：{e.guardrail_result.output.output_info}")
        except OutputGuardrailTripwireTriggered as e:
            # 特朗普爱国吗？
            print(f"Assistant: 抱歉，我被禁止你的回答，理由：{e.guardrail_result.output.output_info}")

        # example: voice agent
        # create a voice pipeline
        # from agents.voice import SingleAgentVoiceWorkflow, VoicePipeline, AudioInput
        # import numpy as np
        # import sounddevice as sd
        #
        # pipeline = VoicePipeline(
        #     workflow=SingleAgentVoiceWorkflow(starting_agent),
        # )
        # # create audio input
        # buffer = np.zeros(24000 * 3, dtype=np.int16)
        # audio_input = AudioInput(buffer=buffer)
        # # run a pipeline
        # result = await pipeline.run(audio_input=audio_input)
        # # create a player
        # player = sd.OutputStream(samplerate=24000, channels=1, dtype=np.int16)
        # player.start()
        # # play the audio stream
        # async for event in result.stream():
        #     if event.type == 'voice_stream_event_audio':
        #         player.write(event.data)


if __name__ == '__main__':
    asyncio.run(main())
