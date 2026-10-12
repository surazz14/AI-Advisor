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
| `session.hello` | Register session + property address (`address`, `lat`, `lng`, optional `landIds`) |
| `chat.send` | User message (same location fields) |

`landIds` are the Landgate lot ids from the address search — one address can
cover several lots (e.g. 1 Lowood Rd, Mount Barker = 3 lots). When present, the
lot area is the total of those lots and the heritage check covers all of them,
instead of using the lot under the pin. Replies then include `lotCount`.
(A single legacy `landId` is still accepted.)

## Address search

`GET /api/address/search?q=1 Lowood Road Mount Barker` searches Landgate's
Cadastre Address layer (LGATE-002) inside the Shire of Plantagenet bbox.
Supports house numbers (`297 …`), units (`2/297 …`, resolved to the parent lot),
ranges (`22-24 …`) and lot numbers (`Lot 5 …`). Lots sharing one address are
merged into a single result with `landIds` and `lotCount`. Returns 502 if SLIP is down so
the frontend can fall back to Nominatim.

Server → client:

| type | purpose |
|------|---------|
| `session.ready` | Hello acknowledged |
| `chat.assistant` | Advisor reply (+ optional citations) |
| `chat.error` | Validation / server error |

## Citation source links

Document titles and official URLs are mapped by `source_document` in:

`app/services/source_links.py`

Add a new CSV/`source_document` key there when you enable a new policy file.


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

3. Set a free LLM key for written answers (pick one):

| Provider | Env var | Notes |
|----------|---------|--------|
| **Groq** (recommended free) | `GROQ_API_KEY` | Fast Llama — [console.groq.com/keys](https://console.groq.com/keys) |
| **Hugging Face** | `HF_TOKEN` | Free monthly credits — [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) |
| Gemini | `GEMINI_API_KEY` | Optional fallback |

   `LLM_PROVIDER=auto` uses the first available. Without any key, the bot returns the top matching clauses.

   Simple **2-hop RAG** is on by default (`MULTI_HOP=true`): first retrieve → follow-up search for missing topics (e.g. shed + bushfire) → merge → answer. Set `MULTI_HOP=false` to disable.

4. Restart uvicorn and chat from the frontend.

## Next steps

- Wire richer property facts (lot size, bushfire) on top of live SLIP zoning
- Stream token chunks if needed (`chat.assistant.delta`)
