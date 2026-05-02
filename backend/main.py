from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import asyncio

from chatbot import chatbot, model

app = FastAPI(title="LangGraph Chatbot API")


class ChatRequest(BaseModel):
    message: str
    thread_id: str
    run_name: Optional[str] = "chat_turn"


class TitleRequest(BaseModel):
    messages: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """Stream AI response tokens back to the frontend."""
    from langchain_core.messages import HumanMessage, AIMessage

    config = {
        "configurable": {"thread_id": req.thread_id},
        "metadata": {"thread_id": req.thread_id},
        "run_name": req.run_name,
    }

    def generate():
        for message_chunk, metadata in chatbot.stream(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
            stream_mode="messages",
        ):
            if isinstance(message_chunk, AIMessage) and message_chunk.content:
                yield message_chunk.content

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/chat/history/{thread_id}")
def get_history(thread_id: str):
    """Return the message history for a given thread."""
    from langchain_core.messages import HumanMessage, AIMessage

    state = chatbot.get_state(config={"configurable": {"thread_id": thread_id}})
    messages = state.values.get("messages", [])

    result = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        result.append({"role": role, "content": msg.content})

    return {"messages": result}


@app.post("/title")
def generate_title(req: TitleRequest):
    """Generate a short conversation title using the LLM."""
    title = model.invoke(
        f"Generate a title within five words on this conversation: {req.messages}"
    ).content
    return {"title": title}
