# agent/nodes.py
import os
from dotenv import load_dotenv
from tavily import TavilyClient
from groq import Groq

from agent.state import AgentState
from agent.memory import (
    embed_text,
    search_memories,
    store_memory,
    append_conversation,
)

load_dotenv()

tavily = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
GROQ_MODEL = "llama-3.3-70b-versatile"


# ── Node 1 ────────────────────────────────────────────────────────────────────
def check_memory_node(state: AgentState) -> AgentState:
    """Embed the query and search Supabase for similar past research."""
    embedding = embed_text(state["query"])
    results = search_memories(
        query_embedding=embedding,
        threshold=0.75,
        k=3,
        session_id=state.get("session_id"),
    )
    return {**state, "memory_results": results}


# ── Router (conditional edge function, not a node) ────────────────────────────
def router(state: AgentState) -> str:
    if state.get("memory_results"):
        return "format_response"
    return "web_search"


# ── Node 2 ────────────────────────────────────────────────────────────────────
def web_search_node(state: AgentState) -> AgentState:
    """Run a Tavily search and return raw results."""
    results = tavily.search(
        query=state["query"],
        max_results=5,
        include_answer=False,
    )
    return {**state, "search_results": results.get("results", [])}


# ── Node 3 ────────────────────────────────────────────────────────────────────
def summarize_node(state: AgentState) -> AgentState:
    """Use Groq llama-3.3-70b to summarize raw search results."""
    results = state["search_results"]

    # Build a compact context block
    context_parts = []
    citations = []
    for r in results:
        context_parts.append(f"Source: {r['url']}\n{r['content']}")
        citations.append(r["url"])

    context = "\n\n---\n\n".join(context_parts)

    prompt = f"""You are a research assistant. Summarize the following search results
into a clear, well-structured 3-4 paragraph research brief on the topic: "{state['query']}".

Include key insights, important facts, and emerging trends.
Be objective and cite the sources by their URLs naturally in the text where relevant.

SEARCH RESULTS:
{context}

RESEARCH BRIEF:"""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1024,
    )
    summary = response.choices[0].message.content.strip()

    return {**state, "summary": summary, "citations": citations}


# ── Node 4 ────────────────────────────────────────────────────────────────────
def store_memory_node(state: AgentState) -> AgentState:
    """Embed the summary and persist to Supabase, then log conversation."""
    embedding = embed_text(state["summary"])
    store_memory(
        session_id=state["session_id"],
        query=state["query"],
        summary=state["summary"],
        embedding=embedding,
        citations=state["citations"],
    )
    # Log user query + assistant response to conversation history
    append_conversation(state["session_id"], "user", state["query"])
    append_conversation(state["session_id"], "assistant", state["summary"])

    return {**state, "source": "web"}


# ── Node 5 ────────────────────────────────────────────────────────────────────
def format_response_node(state: AgentState) -> AgentState:
    """Format the final response, handling both memory hits and fresh searches."""
    if state.get("memory_results"):
        # Use best memory hit
        best = state["memory_results"][0]
        response = best["summary"]
        citations = best.get("citations") or []
        source = "memory"

        # Still log the conversation
        append_conversation(state["session_id"], "user", state["query"])
        append_conversation(state["session_id"], "assistant", response)
    else:
        response = state.get("summary", "No results found.")
        citations = state.get("citations", [])
        source = state.get("source", "web")

    return {**state, "response": response, "citations": citations, "source": source}