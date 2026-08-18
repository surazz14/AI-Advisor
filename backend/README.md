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

## Next steps

- Wire GIS property facts (zone, bushfire, lot size)
- Add RAG over LPS No. 5 / local policies
- Stream token chunks if needed (`chat.assistant.delta`)
