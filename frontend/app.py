# frontend/app.py
import uuid
import requests
import streamlit as st

API_URL = "http://localhost:8000"

st.set_page_config(page_title="ResearchMind", page_icon="🧠", layout="wide")

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🧠 ResearchMind")
    st.caption("AI Research Agent with Persistent Memory")

    # Session management
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    new_id = st.text_input("Session ID", value=st.session_state.session_id)
    if new_id != st.session_state.session_id:
        st.session_state.session_id = new_id
        st.session_state.messages = []
        st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🆕 New session"):
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("🗑 Clear"):
            try:
                requests.delete(f"{API_URL}/session/{st.session_state.session_id}")
                st.session_state.messages = []
                st.success("Cleared!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    # Stored memories panel
    st.divider()
    st.subheader("📚 Stored Memories")
    try:
        mems = requests.get(
            f"{API_URL}/memories/{st.session_state.session_id}"
        ).json()
        if mems:
            for m in mems:
                with st.expander(m["query"][:60] + "..."):
                    st.caption(m["created_at"])
                    st.write(m["summary"][:300] + "...")
        else:
            st.caption("No memories yet for this session.")
    except Exception:
        st.caption("API not reachable.")


# ── Load existing history on first render ────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
    try:
        history = requests.get(
            f"{API_URL}/history/{st.session_state.session_id}"
        ).json()
        for msg in history:
            st.session_state.messages.append(
                {"role": msg["role"], "content": msg["content"], "source": ""}
            )
    except Exception:
        pass

# ── Chat display ─────────────────────────────────────────────────────────────
st.title("ResearchMind")
st.caption(f"Session: `{st.session_state.session_id}`")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and msg.get("source"):
            badge = "🧠 From Memory" if msg["source"] == "memory" else "🔍 Fresh Search"
            st.markdown(f"`{badge}`")
        st.markdown(msg["content"])
        if msg.get("citations"):
            with st.expander("📎 Sources"):
                for url in msg["citations"]:
                    st.markdown(f"- [{url}]({url})")

# ── Input ─────────────────────────────────────────────────────────────────────
if prompt := st.chat_input("Ask me to research anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt, "source": ""})

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Researching..."):
            try:
                resp = requests.post(
                    f"{API_URL}/research",
                    json={
                        "query": prompt,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=60,
                ).json()

                badge = (
                    "🧠 From Memory"
                    if resp.get("source") == "memory"
                    else "🔍 Fresh Search"
                )
                st.markdown(f"`{badge}`")
                st.markdown(resp["response"])

                if resp.get("citations"):
                    with st.expander("📎 Sources"):
                        for url in resp["citations"]:
                            st.markdown(f"- [{url}]({url})")

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": resp["response"],
                        "source": resp.get("source", "web"),
                        "citations": resp.get("citations", []),
                    }
                )
            except Exception as e:
                st.error(f"Error: {e}")