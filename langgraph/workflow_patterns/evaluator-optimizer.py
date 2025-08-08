from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing_extensions import Literal
from typing_extensions import TypedDict

llm = init_chat_model(
    model='accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
    model_provider='fireworks',
)


class Feedback(BaseModel):
    grade: Literal["funny", "not funny"] = Field(
        description="Decide if the joke is funny or not."
    )
    feedback: str = Field(
        description="If the joke is not funny, provide feedback on how to improve it."
    )


evaluator = llm.with_structured_output(Feedback)


class State(TypedDict):
    topic: str
    joke: str
    funny_or_not: str
    feedback: str


def generate_joke(state: State):
    if state.get("feedback"):
        response = llm.invoke(
            f"Write a joke about {state['topic']} but take into account the feedback: {state['feedback']}"
        )
    else:
        response = llm.invoke(
            f"Write a joke about {state['topic']}"
        )
    return {"joke": response.content}


def call_evaluator(state: State):
    response = evaluator.invoke(
        f"Grade the joke {state['joke']}"
    )
    return {
        "funny_or_not": response.grade,
        "feedback": response.feedback,
    }


def evaluator_route(state: State):
    if state["funny_or_not"] == "not funny":
        return "Rejected + Feedback"
    elif state["funny_or_not"] == "funny":
        return "Accepted"


optimizer_builder = StateGraph(State)
optimizer_builder.add_node("generate_joke", generate_joke)
optimizer_builder.add_node("call_evaluator", call_evaluator)
optimizer_builder.add_edge(START, "generate_joke")
optimizer_builder.add_edge("generate_joke", "call_evaluator")
optimizer_builder.add_conditional_edges(
    "call_evaluator",
    evaluator_route,
    {
        "Rejected + Feedback": "generate_joke",
        "Accepted": END,
    }
)
optimizer_workflow = optimizer_builder.compile()

with open("evaluator-optimizer.png", "wb") as f:
    f.write(optimizer_workflow.get_graph().draw_mermaid_png())

state = optimizer_workflow.invoke({"topic": "Cats"})
print(f"joke: \n{state['joke']}")
