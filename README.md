# Plantagenet Planning Advisor

Next.js chatbot for the Shire of Plantagenet AI Planning Advisor.

## Stack

- Next.js (App Router) + TypeScript + Tailwind
- React Context for chat sessions, messages, and address
- OpenStreetMap Nominatim for address suggestions

## Run

```bash
nvm use 22
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Features

- Address gate before chat starts
- Nominatim address autocomplete (Australia)
- WebSocket chat client (`SocketProvider` + `ChatSocketClient`)
- Falls back to demo replies if socket backend is offline
- ChatGPT-style chat UI with green theme
- Local session storage in the browser

## Chat WebSocket

Set in `.env.local`:

```env
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws/chat
```

Frontend events:

- `session.hello` — send when address is ready
- `chat.send` — user message
- `chat.assistant` — server reply
- `chat.error` — server error

Until FastAPI is running, the UI shows **Offline · demo replies**.
