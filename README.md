# LangGraph Chatbot — Deployment Guide

## Project Structure

```
langgraph-chatbot/
├── backend/
│   ├── chatbot.py        # LangGraph graph (your original logic)
│   ├── main.py           # FastAPI wrapper exposing HTTP endpoints
│   ├── requirements.txt
│   └── Procfile
└── frontend/
    ├── app.py            # Streamlit UI (calls backend via HTTP)
    ├── requirements.txt
    ├── Procfile
    └── .streamlit/
        └── secrets.toml  # Set BACKEND_URL here (never commit)
```

---

## What Changed & Why

| Before | After |
|--------|-------|
| Frontend imports backend directly | Frontend calls backend over HTTP |
| Single process | Two separate deployable services |
| `from chatbots.ui_chat_backend import chatbot` | `requests.post(BACKEND_URL + "/chat/stream")` |

The backend now exposes three endpoints:
- `GET  /health` — health check
- `POST /chat/stream` — streams AI tokens
- `GET  /chat/history/{thread_id}` — returns message history
- `POST /title` — generates a short thread title

---

## ⚠️ Important Caveat: InMemorySaver

The backend uses `InMemorySaver`, which means **chat history is lost when the backend restarts**.
For persistent memory, swap it with `PostgresSaver`:

```python
# backend/chatbot.py
from langgraph.checkpoint.postgres import PostgresSaver
import os

checkpointer = PostgresSaver.from_conn_string(os.environ["DATABASE_URL"])
```

Railway and Render both offer free Postgres add-ons.

---

## Deployment: Railway (Recommended — Both Services in One Place)

### Step 1 — Push to GitHub
Push `backend/` and `frontend/` as two separate repos (or a monorepo).

### Step 2 — Deploy Backend
1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select your backend repo
3. Add environment variables:
   - `HUGGINGFACEHUB_API_TOKEN` = your HF token
   - `LANGSMITH_API_KEY` = your LangSmith key (optional)
4. Railway auto-detects the Procfile and deploys
5. Copy the generated URL (e.g. `https://my-backend.up.railway.app`)

### Step 3 — Deploy Frontend
1. New Service → Deploy from GitHub → select frontend repo
2. Add environment variable:
   - `BACKEND_URL` = the URL from Step 2
3. Done!

---

## Deployment: Free Split (Render + Streamlit Community Cloud)

### Backend → Render
1. [render.com](https://render.com) → New Web Service → connect GitHub
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add env vars: `HUGGINGFACEHUB_API_TOKEN`
5. Copy the `.onrender.com` URL

### Frontend → Streamlit Community Cloud
1. [share.streamlit.io](https://share.streamlit.io) → New app → connect GitHub
2. Main file: `app.py`
3. In **Secrets**, add:
   ```toml
   BACKEND_URL = "https://your-backend.onrender.com"
   ```

---

## Local Development

```bash
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your API keys
uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
pip install -r requirements.txt
# Set BACKEND_URL=http://localhost:8000 in .streamlit/secrets.toml
streamlit run app.py
```

---

## Environment Variables Reference

| Variable | Service | Description |
|----------|---------|-------------|
| `HUGGINGFACEHUB_API_TOKEN` | Backend | Required for Llama 3.3 |
| `LANGSMITH_API_KEY` | Backend | Optional tracing |
| `BACKEND_URL` | Frontend | Full URL of deployed backend |
| `DATABASE_URL` | Backend | Optional — for persistent Postgres checkpointer |
