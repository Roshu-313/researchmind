# agent/memory.py
import os
import requests
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# ---------- clients ----------
supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_ANON_KEY"],
)


def embed_text(text: str) -> list[float]:
    """Return a 768-dim vector truncated from gemini-embedding-001."""
    api_key = os.environ["GEMINI_API_KEY"]
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-embedding-001:embedContent?key={api_key}"
    )
    payload = {
        "model": "models/gemini-embedding-001",
        "content": {"parts": [{"text": text}]},
        "taskType": "RETRIEVAL_DOCUMENT",
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    # Truncate to 768 dims to match Supabase vector(768) column
    return resp.json()["embedding"]["values"][:768]


def search_memories(
    query_embedding: list[float],
    threshold: float = 0.75,
    k: int = 3,
    session_id: str | None = None,
) -> list[dict]:
    result = supabase.rpc(
        "match_research_memories",
        {
            "query_embedding": query_embedding,
            "similarity_threshold": threshold,
            "match_count": k,
            "filter_session_id": session_id,
        },
    ).execute()
    return result.data or []


def store_memory(
    session_id: str,
    query: str,
    summary: str,
    embedding: list[float],
    citations: list[str],
) -> None:
    supabase.table("research_memories").insert(
        {
            "session_id": session_id,
            "query": query,
            "summary": summary,
            "embedding": embedding,
            "citations": citations,
        }
    ).execute()


def append_conversation(session_id: str, role: str, content: str) -> None:
    supabase.table("conversations").insert(
        {"session_id": session_id, "role": role, "content": content}
    ).execute()


def get_conversation_history(session_id: str) -> list[dict]:
    result = (
        supabase.table("conversations")
        .select("role, content, created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .execute()
    )
    return result.data or []


def get_memories(session_id: str) -> list[dict]:
    result = (
        supabase.table("research_memories")
        .select("query, summary, citations, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=True)
        .execute()
    )
    return result.data or []


def ping_supabase() -> bool:
    try:
        supabase.table("conversations").select("id").limit(1).execute()
        return True
    except Exception:
        return False