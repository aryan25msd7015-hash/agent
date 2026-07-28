from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, StateGraph


class AgentState(TypedDict):
    intent: str
    route: str


def _route(state: AgentState) -> AgentState:
    text = state["intent"].lower()
    if text.startswith("automate "):
        state["route"] = "ui_automation"
    elif text.startswith("browse "):
        state["route"] = "browser"
    elif "gdrive" in text and "download" in text:
        state["route"] = "gdrive"
    elif "tableau" in text:
        state["route"] = "tableau"
    else:
        state["route"] = "chat"
    return state


def build_router():
    graph = StateGraph(AgentState)
    graph.add_node("route", _route)
    graph.set_entry_point("route")
    graph.add_edge("route", END)
    return graph.compile()
