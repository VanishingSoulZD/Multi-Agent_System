from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_tavily import TavilySearch
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

model = init_chat_model(
    model='accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
    model_provider='fireworks',
)

tavily_search = TavilySearch(max_results=1)

research_agent = create_react_agent(
    model=model,
    tools=[tavily_search],
    prompt=(
        "You are a research agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with research-related tasks, DO NOT do any math\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="research_agent",
)


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Divide two numbers."""
    return a / b


math_agent = create_react_agent(
    model=model,
    tools=[add, multiply, divide],
    prompt=(
        "You are a math agent.\n\n"
        "INSTRUCTIONS:\n"
        "- Assist ONLY with math-related tasks\n"
        "- After you're done with your tasks, respond to the supervisor directly\n"
        "- Respond ONLY with the results of your work, do NOT include ANY other text."
    ),
    name="math_agent",
)

supervisor = create_supervisor(
    model=model,
    prompt=(
        "You are a supervisor managing two agents:\n"
        "- a research agent. Assign research-related tasks to this agent\n"
        "- a math agent. Assign math-related tasks to this agent\n"
        "Assign work to one agent at a time, do not call agents in parallel.\n"
        "Do not do any work yourself."
    ),
    agents=[research_agent, math_agent],
    add_handoff_back_messages=True,
    output_mode="full_history",
).compile()

with open("multi-agent_supervisor.png", "wb") as f:
    f.write(supervisor.get_graph().draw_mermaid_png())

input_messages = [
    HumanMessage(
        content="分别找到2023年中国和北京的GDP，然后再做一些数学计算，重新计算北京的GDP占中国的GDP的百分比?"
    )
]
for chunk in supervisor.stream(
        {
            "messages": input_messages,
        }
):
    for k, v in chunk.items():
        print(f"{k}: {v['messages'][-1].content}")
