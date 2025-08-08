from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

llm = init_chat_model(
    model='accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
    model_provider='fireworks',
)


class State(TypedDict):
    topic: str
    joke: str
    improved_joke: str
    final_joke: str


def generate_joke(state: State):
    response = llm.invoke(
        f"Write a short joke about {state['topic']}.",
    )
    return {"joke": response.content}


def check_punchline(state: State):
    if "?" in state["joke"] or "!" in state["joke"]:
        return "Pass"
    return "Fail"


def improve_joke(state: State):
    response = llm.invoke(
        f"Make this joke funnier by adding wordplay: {state['joke']}.",
    )
    return {"improved_joke": response.content}


def polish_joke(state: State):
    response = llm.invoke(
        f"Add a surprising twist to this joke: {state['improved_joke']}.",
    )


workflow = StateGraph(State)
workflow.add_node("generate_joke", generate_joke)
workflow.add_node("improve_joke", improve_joke)
workflow.add_node("polish_joke", polish_joke)
workflow.add_edge(START, "generate_joke")
workflow.add_conditional_edges(
    "generate_joke",
    check_punchline,
    {
        "Pass": END,
        "Fail": "improve_joke",
    }
)
workflow.add_edge("improve_joke", "polish_joke")
workflow.add_edge("polish_joke", END)
chain = workflow.compile()

with open('prompt_chaining.png', 'wb') as f:
    f.write(chain.get_graph().draw_mermaid_png())

state = chain.invoke({"topic": "cats"})
print(f"Initial joke: \n{state['joke']}")
if "improved_joke" in state:
    print(f"Improved joke: \n{state['improved_joke']}")
    print(f"final joke: \n{state['final_joke']}")
