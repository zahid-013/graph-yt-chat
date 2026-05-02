from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import BaseMessage
import os

load_dotenv()

# ---------------------------------------------------------------------------
# Model
# ---------------------------------------------------------------------------
llm2 = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-3.3-70B-Instruct",
    task="text-generation",
    temperature=0.5,
)
model = ChatHuggingFace(llm=llm2)


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def chat_node(state: ChatState):
    messages = state["messages"]
    response = model.invoke(messages)
    return {"messages": [response]}


checkpointer = InMemorySaver()
# NOTE: InMemorySaver loses state when the server restarts.
# For production, swap this with langgraph.checkpoint.postgres.PostgresSaver
# and provide a DATABASE_URL environment variable.

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)
