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
    story: str
    poem: str
    combined_output: str


def generate_joke(state: State):
    response = llm.invoke(
        f"Write a joke about {state['topic']}"
    )
    return {"joke": response.content}


def generate_story(state: State):
    response = llm.invoke(
        f"Write a story about {state['topic']}"
    )
    return {"story": response.content}


def generate_poem(state: State):
    response = llm.invoke(
        f"Write a poem about {state['topic']}"
    )
    return {"poem": response.content}


def aggregator(state: State):
    combined = (f"joke: \n{state['joke']}\n"
                f"story: \n{state['story']}\n"
                f"poem: \n{state['poem']}\n")
    return {"combined_output": combined}


parallel_builder = StateGraph(State)
parallel_builder.add_node("generate_joke", generate_joke)
parallel_builder.add_node("generate_story", generate_story)
parallel_builder.add_node("generate_poem", generate_poem)
parallel_builder.add_node("aggregator", aggregator)
parallel_builder.add_edge(START, "generate_joke")
parallel_builder.add_edge(START, "generate_story")
parallel_builder.add_edge(START, "generate_poem")
parallel_builder.add_edge("generate_joke", "aggregator")
parallel_builder.add_edge("generate_story", "aggregator")
parallel_builder.add_edge("generate_poem", "aggregator")
parallel_builder.add_edge("aggregator", END)
parallel_workflow = parallel_builder.compile()

with open("parallelization.png", "wb") as f:
    f.write(parallel_workflow.get_graph().draw_mermaid_png())

state = parallel_workflow.invoke({"topic": "cats"})
print(f"combined output: \n{state['combined_output']}")
