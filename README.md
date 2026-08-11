# Rune

An autonomous research agent that plans, researches, synthesizes, and verifies —
like a research analyst you can delegate to.

## Architecture

```
User query (React)
  |
  v
POST /query (FastAPI, streams via SSE)
  |
  v
LangGraph state machine:

  planner --> research --> synthesis --> critique
                 ^                          |
                 |__________________________|
                   (loops back if critique fails,
                    up to MAX_CRITIQUE_ITERATIONS times)

  research node calls web search (Tavily) + FAISS long-term memory directly;
  FAISS memory is also exposed standalone via an MCP server for external clients
  all nodes log to a shared trace, streamed step-by-step to the client via SSE
  and saved to Postgres for session replay
```

**Layers**
1. **Presentation** — React (sidebar, chat thread, trace panel, input bar, voice input/output)
2. **API Gateway** — FastAPI (`/query`, `/sessions`, `/sessions/{id}`, `/tts`, `/stt`, `/auth/*`)
3. **Orchestration** — LangGraph (the 4-node graph above), streamed via `stream_query()` — each
   node's output is yielded to the client as it completes, not after full graph completion
4. **Protocol** — MCP server wrapping FAISS retrieval
5. **Reasoning** — Gemini (different temperature per node, see `app/agents/config.py`)
6. **Tools** — web search, FAISS retrieval
7. **Voice** — Sarvam STT (`saaras:v3`) for voice input, Sarvam TTS (`bulbul:v3`) for voice output
8. **Data** — FAISS (vector memory), PostgreSQL hosted on Neon (users, sessions, message history)
9. **Auth** — JWT (email/password) + Google OAuth, protecting `/query`, `/sessions`, `/tts`, `/stt`
10. **Observability** — trace logging on every node, request-scoped logging with unique request IDs

## Why the critique loop matters

The critique node isn't just a final check — it can send the graph *back* to
research if it finds unsupported claims or gaps, up to a configurable retry
limit before giving up gracefully. This conditional routing (not a fixed
pipeline) is what makes this an "agentic" system rather than a linear script.

## Security

Scraped web content passed into the LLM during the research step is treated
as untrusted input — prompt injection mitigations are applied before that
content reaches the model, so instructions embedded in a scraped page can't
hijack the agent's behavior.

## Setup

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in GOOGLE_API_KEY, DATABASE_URL, SARVAM_API_KEY, etc.
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Run the eval set
```bash
cd backend
python -m eval.run_eval
```
Outputs `eval/results.json` — 18 queries covering clean questions, multi-hop
synthesis, and deliberately ambiguous/false-premise queries (testing whether
Rune asks for clarification instead of hallucinating an answer).

### Run the MCP server standalone
```bash
cd backend
python -m app.mcp_server.server
```

## Live deployment
Live at https://rune-umber.vercel.app. Frontend on Vercel, backend on Render,
Postgres on Neon. Env vars are managed via each platform's secret manager,
never committed to git.

## Known limitations / next steps
- Test coverage is currently light (a handful of pytest tests) — broader
  node/tool-level testing is the next priority.
- CORS is currently wide open (`allow_origins="*"`) — needs tightening to the
  actual frontend origin before this would be production-ready.
- No refresh tokens or token revocation on the JWT auth, and no rate limiting
  specifically on login attempts (rate limiting elsewhere in the API uses
  slowapi).
- The FAISS index and the research cache are both single-process — a
  multi-instance deployment would need a shared store (e.g. Redis) instead.

## Stack
React (Vercel) · FastAPI (Render) · LangGraph · Gemini · FAISS · MCP ·
PostgreSQL (Neon) · Sarvam (STT/TTS)
