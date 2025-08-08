from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field
from typing_extensions import Literal, TypedDict

llm = init_chat_model(
    model='accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
    model_provider='fireworks',
)


class Route(BaseModel):
    step: Literal["joke", "story", "poem"] = Field(
        description="The next step in the routing process."
    )


router = llm.with_structured_output(Route)


class State(TypedDict):
    input: str
    decision: str
    output: str


def call_router(state: State):
    response = router.invoke(
        [
            SystemMessage(
                content="Route the input to story, joke, or poem based on the user's request."
            ),
            HumanMessage(
                content=state["input"],
            )
        ]
    )
    return {"decision": response.step}


def route_decision(state: State):
    if state["decision"] == "joke":
        return "generate_joke"
    elif state["decision"] == "story":
        return "generate_story"
    elif state["decision"] == "poem":
        return "generate_poem"


# 在 Routing 模式下，假定使用不同的专家模型来分别生成 joke/story/poem
def generate_joke(state: State):
    response = llm.invoke(state["input"])
    return {"output": response.content}


def generate_story(state: State):
    response = llm.invoke(state["input"])
    return {"output": response.content}


def generate_poem(state: State):
    response = llm.invoke(state["input"])
    return {"output": response.content}


router_builder = StateGraph(State)
router_builder.add_node("call_router", call_router)
router_builder.add_node("generate_joke", generate_joke)
router_builder.add_node("generate_story", generate_story)
router_builder.add_node("generate_poem", generate_poem)
router_builder.add_edge(START, "call_router")
router_builder.add_conditional_edges(
    "call_router",
    route_decision,
    {
        "generate_joke": "generate_joke",
        "generate_story": "generate_story",
        "generate_poem": "generate_poem",
    }
)
router_builder.add_edge("generate_joke", END)
router_builder.add_edge("generate_story", END)
router_builder.add_edge("generate_poem", END)
router_workflow = router_builder.compile()

with open("routing.png", "wb") as f:
    f.write(router_workflow.get_graph().draw_mermaid_png())

state = router_workflow.invoke({"input": "Write a joke about cats"})
print(f"output: \n{state['output']}")
