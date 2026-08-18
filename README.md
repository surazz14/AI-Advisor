# Plantagenet Planning Advisor

Next.js chatbot UI for the Shire of Plantagenet AI Planning Advisor.

## Stack

- **Next.js** (App Router) + TypeScript + Tailwind
- **React Context** (`ChatContext`) stores:
  - chat messages (conversation context)
  - multiple sessions
  - property facts (address / zone / bushfire demo fields)
  - persistence in `localStorage`

## Run

```bash
nvm use 22   # or any Node 18+
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## What’s included now

- ChatGPT-like layout (sidebar + messages + composer)
- Design tuned for a local planning advisor (teal/navy civic look)
- Suggestion chips for shed / fence / dwelling
- Property context panel (saved into the same React Context)
- Mock assistant replies (until FastAPI + RAG is connected)

## Next steps

1. Connect `sendMessage` to FastAPI `/chat`
2. Replace demo property facts with Mapbox geocoding + WA GIS
3. Return cited answers from LPS No.5 / Local Planning Policies (RAG)
