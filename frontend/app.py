import streamlit as st
import requests
import uuid
import os

# ---------------------------------------------------------------------------
# Config — set BACKEND_URL in your deployment env vars or .streamlit/secrets.toml
# ---------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", st.secrets.get("BACKEND_URL", "http://localhost:8000"))
os.environ["LANGSMITH_PROJECT"] = "langgraph-chatbot"


# **************************************** Utility functions *************************

def generate_thread_id():
    return str(uuid.uuid4())


def reset_chat():
    thread_id = generate_thread_id()
    st.session_state["thread_id"] = thread_id
    add_thread(thread_id)
    st.session_state["message_history"] = []


def add_thread(thread_id):
    if thread_id not in st.session_state["chat_threads"]:
        st.session_state["chat_threads"].append(thread_id)


def load_conversation(thread_id: str) -> list[dict]:
    """Fetch conversation history from the backend API."""
    try:
        resp = requests.get(f"{BACKEND_URL}/chat/history/{thread_id}", timeout=10)
        resp.raise_for_status()
        return resp.json().get("messages", [])
    except Exception as e:
        st.error(f"Could not load conversation: {e}")
        return []


def get_title(messages) -> str:
    """Ask the backend to generate a short title for a conversation."""
    try:
        resp = requests.post(
            f"{BACKEND_URL}/title",
            json={"messages": str(messages)},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("title", "Untitled")
    except Exception:
        return "Untitled"


def stream_response(message: str, thread_id: str):
    """Yield streamed tokens from the backend."""
    with requests.post(
        f"{BACKEND_URL}/chat/stream",
        json={"message": message, "thread_id": thread_id},
        stream=True,
        timeout=60,
    ) as resp:
        resp.raise_for_status()
        for chunk in resp.iter_content(chunk_size=None, decode_unicode=True):
            if chunk:
                yield chunk


# **************************************** Session Setup *****************************

if "message_history" not in st.session_state:
    st.session_state["message_history"] = []

if "thread_id" not in st.session_state:
    st.session_state["thread_id"] = generate_thread_id()

if "chat_threads" not in st.session_state:
    st.session_state["chat_threads"] = []

if "thread_titles" not in st.session_state:
    st.session_state["thread_titles"] = {}

add_thread(st.session_state["thread_id"])

st.title("▶️ LangGraph Chatbot")

# **************************************** Sidebar UI ********************************

st.sidebar.title("LangGraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

for thread_id in st.session_state["chat_threads"][::-1]:
    button_label = st.session_state["thread_titles"].get(thread_id, thread_id[:8] + "…")

    if st.sidebar.button(button_label, key=f"btn_{thread_id}"):
        st.session_state["thread_id"] = thread_id
        messages = load_conversation(thread_id)

        # Generate title only once
        if thread_id not in st.session_state["thread_titles"]:
            title = get_title(messages)
            st.session_state["thread_titles"][thread_id] = title

        # Editable title
        modified_title = st.sidebar.text_input(
            "Thread Title",
            value=st.session_state["thread_titles"][thread_id],
            key=f"title_input_{thread_id}",
        )
        st.session_state["thread_titles"][thread_id] = modified_title

        st.session_state["message_history"] = messages

# **************************************** Main Chat UI ******************************

for message in st.session_state["message_history"]:
    with st.chat_message(message["role"]):
        st.text(message["content"])

user_input = st.chat_input("Type here")

if user_input:
    st.session_state["message_history"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.text(user_input)

    with st.chat_message("assistant"):
        ai_message = st.write_stream(
            stream_response(user_input, st.session_state["thread_id"])
        )

    st.session_state["message_history"].append(
        {"role": "assistant", "content": ai_message}
    )
