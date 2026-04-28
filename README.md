# ResearchMind 🧠

> An AI agent that researches any topic, stores findings with vector embeddings,
> and recalls past research across sessions — all on free tiers.

## Architecture

```
User Query
   │
   ▼
check_memory_node  ──── Supabase pgvector cosine search
   │
   ├─ memory hit ──────► format_response_node ──► Response (🧠 From Memory)
   │
   └─ miss ────────────► web_search_node (Tavily)
                              │
                         summarize_node (Groq llama-3.3-70b)
                              │
                         store_memory_node (Gemini embeddings + Supabase)
                              │
                         format_response_node ──► Response (🔍 Fresh Search)
```

## Tech Stack

| Component | Tool | Free Tier |
|---|---|---|
| Agent framework | LangGraph | Open source |
| LLM | Groq llama-3.3-70b-versatile | Free tier |
| Embeddings | Gemini text-embedding-004 | 1500 req/day |
| Vector DB | Supabase pgvector | 500MB |
| Web search | Tavily | 1000/month |
| Backend | FastAPI | Open source |
| Frontend | Streamlit | Open source |

## Setup

```bash
git clone <your-repo>
cd researchmind
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 1. Copy and fill environment variables
cp .env.example .env

# 2. Run the Supabase schema
# Paste database/schema.sql into your Supabase SQL editor

# 3. Start the API
uvicorn api.main:app --reload

# 4. Start the frontend (new terminal)
streamlit run frontend/app.py
```

## How It Works

1. Your query is embedded with Gemini text-embedding-004 (768 dimensions)
2. Supabase pgvector runs a cosine similarity search across past research
3. If similarity > 0.75, the cached summary is returned instantly (🧠)
4. Otherwise Tavily searches the web, Groq summarizes, and the result is
   stored back to Supabase for next time (🔍)

## License

MIT