from typing import Annotated

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langchain_tavily import TavilySearch
from langgraph.graph import END, MessagesState, StateGraph, START
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from typing_extensions import Literal

model = init_chat_model(
    model='accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
    model_provider='fireworks',
)

tavily_search = TavilySearch(max_results=1)

repl = PythonREPL()


@tool
def python_repl_tool(
        code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        print(f"[debug] Python code: \n{code}\n----\n")
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n\`\`\`python\n{code}\n\`\`\`\nStdout: {result}"
    return (
            result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )


def make_system_prompt(suffix: str) -> str:
    return (
        "You are a helpful AI assistant, collaborating with other assistants."
        " Use the provided tools to progress towards answering the question."
        " If you are unable to fully answer, that's OK, another assistant with different tools "
        " will help where you left off. Execute what you can to make progress."
        " If you or any of the other assistants have the final answer or deliverable,"
        " prefix your response with FINAL ANSWER so the team knows to stop."
        "只有整个任务完成时才应该包含 FINAL ANSWER，如果只是部分任务完成了，不应该包含 FINAL ANSWER。"
        f"\n{suffix}"
    )


def get_next_node(last_message: BaseMessage, goto: str):
    if "FINAL ANSWER" in last_message.content:
        return END
    return goto


research_agent = create_react_agent(
    model=model,
    tools=[tavily_search],
    prompt=make_system_prompt(
        "You can only do research. You are working with a chart generator colleague."
    )
)


def research_node(
        state: MessagesState
) -> Command[Literal["chart_generator", END]]:
    result = research_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "chart_generator")
    return Command(
        update={
            "messages": result["messages"],
        },
        goto=goto,
    )


chart_agent = create_react_agent(
    model=model,
    tools=[python_repl_tool],
    prompt=make_system_prompt(
        "You can only generate charts. 请注意千万不要将生成的图表直接展示，而是将生成的图表保存到png文件中。You are working with a researcher colleague."
    ),
)


def chart_node(
        state: MessagesState
) -> Command[Literal["researcher", END]]:
    result = chart_agent.invoke(state)
    goto = get_next_node(result["messages"][-1], "researcher")
    return Command(
        update={
            "messages": result["messages"],
        },
        goto=goto,
    )


workflow = StateGraph(MessagesState)
workflow.add_node("researcher", research_node)
workflow.add_node("chart_generator", chart_node)
workflow.add_edge(START, "researcher")
graph = workflow.compile()

with open("multi-agent_network.png", "wb") as f:
    f.write(graph.get_graph().draw_mermaid_png())

for chunk in graph.stream(
        {
            "messages": [
                HumanMessage(
                    content="首先获取巴黎过去5天每天的平均气温(一共5个数字)，然后将它们绘制成图表并将png保存到文件中（强制使用非 GUI 后端 Agg）。"
                )
            ],
        },
):
    for k, v in chunk.items():
        print(f"{k}: {v['messages'][-1].content}")
