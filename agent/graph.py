# agent/graph.py
from langgraph.graph import StateGraph, END

from agent.state import AgentState
from agent.nodes import (
    check_memory_node,
    router,
    web_search_node,
    summarize_node,
    store_memory_node,
    format_response_node,
)

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register all nodes
    graph.add_node("check_memory", check_memory_node)
    graph.add_node("web_search", web_search_node)
    graph.add_node("summarize", summarize_node)
    graph.add_node("store_memory", store_memory_node)
    graph.add_node("format_response", format_response_node)

    # Entry point
    graph.set_entry_point("check_memory")

    # Conditional edge from check_memory → router decides path
    graph.add_conditional_edges(
        "check_memory",
        router,
        {
            "web_search": "web_search",
            "format_response": "format_response",
        },
    )

    # Web search path: search → summarize → store → format
    graph.add_edge("web_search", "summarize")
    graph.add_edge("summarize", "store_memory")
    graph.add_edge("store_memory", "format_response")

    # Both paths converge at format_response → END
    graph.add_edge("format_response", END)

    return graph.compile()


# Module-level compiled graph (imported by FastAPI)
research_graph = build_graph()