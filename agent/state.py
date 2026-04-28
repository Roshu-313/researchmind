# agent/state.py
from typing import TypedDict

class AgentState(TypedDict):
    query: str
    session_id: str
    memory_results: list[dict]
    search_results: list[dict]
    summary: str
    response: str
    source: str          # "memory" | "web"
    citations: list[str]