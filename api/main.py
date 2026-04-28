# api/main.py
import uuid
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.graph import research_graph
from agent.memory import (
    ping_supabase,
    get_conversation_history,
    get_memories,
    supabase,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    ok = ping_supabase()
    if not ok:
        print("⚠️  Supabase ping failed — check credentials")
    else:
        print("✅  Supabase connected")
    yield


app = FastAPI(title="ResearchMind API", lifespan=lifespan)


class ResearchRequest(BaseModel):
    query: str
    session_id: str = ""


class ResearchResponse(BaseModel):
    response: str
    source: str
    citations: list[str]
    session_id: str


@app.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest):
    session_id = req.session_id or str(uuid.uuid4())

    initial_state = {
        "query": req.query,
        "session_id": session_id,
        "memory_results": [],
        "search_results": [],
        "summary": "",
        "response": "",
        "source": "",
        "citations": [],
    }

    try:
        final_state = research_graph.invoke(initial_state)
    except Exception as e:
        err = traceback.format_exc()
        print("=== GRAPH ERROR ===")
        print(err)
        print("===================")
        raise HTTPException(status_code=500, detail=err)

    if not final_state.get("response"):
        print("=== STATE DUMP ===")
        print(final_state)
        print("==================")
        raise HTTPException(status_code=500, detail=str(final_state))

    return ResearchResponse(
        response=final_state["response"],
        source=final_state.get("source", "web"),
        citations=final_state.get("citations", []),
        session_id=session_id,
    )


@app.get("/history/{session_id}")
async def history(session_id: str):
    return get_conversation_history(session_id)


@app.get("/memories/{session_id}")
async def memories(session_id: str):
    return get_memories(session_id)


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    supabase.table("conversations").delete().eq("session_id", session_id).execute()
    supabase.table("research_memories").delete().eq("session_id", session_id).execute()
    return {"deleted": session_id}


@app.get("/health")
async def health():
    db_ok = ping_supabase()
    return {"status": "ok", "supabase": db_ok}