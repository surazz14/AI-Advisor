# Plantagenet Planning Advisor — FastAPI backend

Chat WebSocket + health API for the Next.js frontend.

## Docker

From the repo root:

```bash
docker compose up --build
```

The API image is built from this `backend/` folder. See the root README for env vars and ports.


## Run

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Chat WS: `ws://localhost:8000/ws/chat`

In the frontend `.env.local`:

```env
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/chat
```

## WebSocket protocol

Client → server:

| type | purpose |
|------|---------|
| `session.hello` | Register session + property address |
| `chat.send` | User message |

Server → client:

| type | purpose |
|------|---------|
| `session.ready` | Hello acknowledged |
| `chat.assistant` | Advisor reply (+ optional citations) |
| `chat.error` | Validation / server error |

## Dummy GIS (temporary)

Two test pins return hard-coded zoning until real GIS is wired:

| Location | Coords | Zone |
|----------|--------|------|
| 22-24 Lowood Road, Mount Barker | -34.63000, 117.66700 | Residential |
| Porongurup | -34.66670, 117.86670 | Environmental conservation reserve |

Matched by coordinates (±0.002) or address text. Replies include a `zone` object.

## RAG chat (simple)

Flow: embed question → search `policy_chunks` in Supabase → reply.

1. Copy env and fill Supabase keys (same as `policy_rag/.env`):

```bash
cp .env.example .env
```

2. Install deps (first run downloads the MiniLM embedding model):

```bash
pip install -r requirements.txt
```

3. Set `GEMINI_API_KEY` for a short written answer (Google Gemini).  
   Without it, the bot returns the top matching clauses.

4. Restart uvicorn and chat from the frontend.

## Next steps

- Wire GIS property facts (zone, bushfire, lot size)
- Stream token chunks if needed (`chat.assistant.delta`)
