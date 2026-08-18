# Plantagenet Planning Advisor

Next.js chatbot + FastAPI WebSocket backend for the Shire of Plantagenet AI Planning Advisor.

## Stack

- **Frontend:** Next.js (App Router) + TypeScript + Tailwind
- **Backend:** FastAPI + Uvicorn WebSocket (`/ws/chat`)
- Address autocomplete via OpenStreetMap Nominatim
- **Deploy:** Docker + Docker Compose

## Run with Docker (recommended for deploy)

```bash
cp .env.docker.example .env
docker compose up --build
```

- App: [http://localhost:3000](http://localhost:3000)
- API health: [http://localhost:8000/health](http://localhost:8000/health)
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

Stop:

```bash
docker compose down
```

### Production / remote host notes

`NEXT_PUBLIC_WS_URL` is baked into the frontend image at **build** time. Before deploying to a server/domain, set it to a browser-reachable URL, then rebuild:

```env
NEXT_PUBLIC_WS_URL=ws://YOUR_SERVER_IP:8000/ws/chat
# or wss://api.your-domain.com/ws/chat behind TLS
CORS_ORIGINS=http://YOUR_SERVER_IP:3000,https://your-domain.com
```

```bash
docker compose up --build -d
```

## Run frontend (local dev)

```bash
nvm use 22
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Run backend (local dev)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: [http://localhost:8000/health](http://localhost:8000/health)
- Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Chat WS: `ws://localhost:8000/ws/chat`

See [backend/README.md](backend/README.md) for the socket protocol.

## Env (local frontend)

Frontend (`.env.local`):

```env
NOMINATIM_USER_AGENT=PlantagenetPlanningAdvisor/0.1 (your-email@example.com)
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/chat
```

## Features

- Address gate before chat starts
- Nominatim address autocomplete (Australia)
- Live WebSocket chat when FastAPI is running
- Demo fallback replies if the socket backend is offline
- ChatGPT-style UI with green theme
- Local session storage in the browser
- Docker images for web + API
