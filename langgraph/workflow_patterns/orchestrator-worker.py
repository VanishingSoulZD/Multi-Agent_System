import operator
from typing import Annotated

from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

llm = init_chat_model(
    model='accounts/fireworks/models/qwen3-235b-a22b-instruct-2507',
    model_provider='fireworks',
)


class Section(BaseModel):
    name: str = Field(
        description="Name for this section of the report."
    )
    description: str = Field(
        description="Brief overview of the main topics and concepts to be covered in this section."
    )


class Sections(BaseModel):
    sections: list[Section] = Field(
        description="Sections of the report."
    )


planner = llm.with_structured_output(Sections)


class State(TypedDict):
    topic: str
    sections: list[Section]
    completed_sections: Annotated[
        list, operator.add
    ]
    final_report: str


class WorkerState(TypedDict):
    section: Section
    completed_sections: Annotated[
        list, operator.add
    ]


def orchestrator(state: State):
    response = planner.invoke(
        [
            SystemMessage(
                content="Generate a plan for the report.",
            ),
            HumanMessage(
                content=f"Here is the report topic: {state['topic']}."
            )
        ]
    )
    return {"sections": response.sections}


def worker_call(state: WorkerState):
    response = llm.invoke(
        [
            SystemMessage(
                content="Write a report section following the provided name and description. Include no preamble for each section. Use markdown formatting."
            ),
            HumanMessage(
                content=f"Here is the section name: {state['section'].name} and description: {state['section'].description}"
            )
        ]
    )
    return {"completed_sections": [response.content]}


def assign_workers(state: State):
    return [Send("worker_call", {"section": s}) for s in state["sections"]]


def synthesizer(state: State):
    completed_sections = state["completed_sections"]
    final_report = "".join(completed_sections)
    return {"final_report": final_report}


orchestrator_worker_builder = StateGraph(State)
orchestrator_worker_builder.add_node("orchestrator", orchestrator)
orchestrator_worker_builder.add_node("worker_call", worker_call)
orchestrator_worker_builder.add_node("synthesizer", synthesizer)
orchestrator_worker_builder.add_edge(START, "orchestrator")
orchestrator_worker_builder.add_conditional_edges(
    "orchestrator",
    assign_workers,
    ["worker_call"]
)
orchestrator_worker_builder.add_edge("worker_call", "synthesizer")
orchestrator_worker_builder.add_edge("synthesizer", END)
orchestrator_worker = orchestrator_worker_builder.compile()

with open("orchestrator-worker.png", "wb") as f:
    f.write(orchestrator_worker.get_graph().draw_mermaid_png())

state = orchestrator_worker.invoke(
    input={"topic": "Create a report on LLM scaling laws."}
)
print(f"final_report: \n{state['final_report']}")
