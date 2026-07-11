# AGENTS.md

Guidance for OpenCode sessions working in this repo. Verified against the
codebase on 2026-07-11. Update when commands, structure, or invariants change.

## What this repo is

A dual-backend chat demo. One Next.js frontend can talk to either of two
servers (switchable at runtime in the UI), backed by MongoDB + MinIO + Ollama.

```
fast-minio/
├── frontend/          # Next.js 15 (App Router) — port 3000
├── fastapi_backend/   # FastAPI 0.116  — port 8000
├── src/               # Spring Boot 3.3.2 (Java 17) — port 8080
├── docker-compose.yml # MongoDB (replica set rs0) + MinIO
└── docs/              # start-project.md, overview.md
```

## Repository-specific gotchas (read these before doing anything)

### MongoDB must be a replica set, not standalone

`fastapi_backend/app/config.py` defaults `MONGO_URI` to
`mongodb://localhost:27017/?replicaSet=rs0`. The `/api/tasks` SSE endpoints
rely on MongoDB change streams, which only work against a replica set or
sharded cluster. Standalone MongoDB will silently break task progress
streaming.

`docker-compose.yml` already configures this correctly: the `mongodb` service
runs with `--replSet rs0` and the healthcheck auto-runs `rs.initiate(...)`.
**Do not change the MongoDB image to a vanilla `mongo:7` without
`--replSet`** — the FastAPI task APIs will fail.

### Dual-backend parity is partial, not full

- `fastapi_backend/app/api/` exposes: `chat.py`, `sessions.py`, `tasks.py`, `examples.py`.
- `src/main/java/com/example/chatgpt/controller/` exposes: `ChatController.java`, `SessionController.java` only.

There is **no Spring Boot implementation of `/api/tasks`**. When the frontend
points at Spring, the task UI in FastAPI is unreachable. Don't assume both
backends implement the same surface. See `frontend/ai/architecture/backend.md`
for the user-facing surface.

### No tests, no CI

- No `test_*.py` files under `fastapi_backend/`.
- No `src/test/...` in the Spring Boot module.
- `.github/` contains only personal tool scripts under `java-upgrade/` and `modernize/` — no `workflows/`.
- `pyproject.toml` / `setup.cfg` / `ruff.toml` / `mypy.ini` are absent.
- `.gitignore` lists `pytest_cache`, `mypy_cache`, `ruff_cache` but no config
  files exist to run them.

**Do not** run `pytest`, `mvn test`, `npm test`, or `tsc --noEmit` expecting
coverage. Use the dev servers + curl the live endpoints to verify changes.

### `.claude/skills/` and `.agents/skills/` are empty

Both `code-review` directories are empty placeholders. Don't read into them.

### Frontend has its own AI-collaboration knowledge base

`frontend/ai/` (onboarding.md, decisions.md, knownIssues.md,
architecture/*.md, handoff/latest.md) is a separate knowledge base scoped to
the frontend. When working on the frontend, skim it first — it documents
state-management drift risks, missing Tailwind, and the Redux-vs-local-state
convention. Do not duplicate its content here.

## Commands

### Start order (matters)

1. `docker compose up -d` — MongoDB + MinIO.
2. `ollama pull gemma3:4b` (one-time; verify with `ollama list`).
3. One backend: `cd fastapi_backend && source .venv/bin/activate && uvicorn app.main:app --reload --port 8000` **or** `./mvnw spring-boot:run`.
4. `cd frontend && npm install && npm run dev` (only required on first run / after lockfile change).
5. Open http://localhost:3000.

### Verify a backend is up

- FastAPI: `curl http://localhost:8000/health` → `{"status":"ok"}`
- Spring:  `curl "http://localhost:8080/api/sessions?userId=u1"` → JSON array (empty if no sessions)

### Switch the frontend's active backend

Two ways, both respected:
- UI dropdown labelled `後端目標` (top-left of the page). Selection persists in
  `localStorage` under key `chat-backend-target`.
- Env vars in `frontend/.env.local` (template at `frontend/.env.example`):
  - `NEXT_PUBLIC_DEFAULT_BACKEND=fastapi|spring`
  - `NEXT_PUBLIC_FASTAPI_API_BASE` (default `http://localhost:8000`)
  - `NEXT_PUBLIC_SPRING_API_BASE` (default `http://localhost:8080`)

Env-var changes require restarting `npm run dev` (Next.js inlines
`NEXT_PUBLIC_*` at build time).

Switching backends in the UI clears in-memory sessions and messages
intentionally — see `resetConversationState()` in `frontend/app/page.tsx`.

### Debug launchers

`.vscode/launch.json` has preconfigured "Spring Boot: ChatgptApplication" and
"FastAPI: uvicorn" launch configs. Use them rather than starting servers
manually when stepping through code.

## Entry points

| Concern | File |
|---|---|
| Frontend single page | `frontend/app/page.tsx` (everything — no `src/app/page.tsx` is used; `src/app/api/action/`, `src/app/canary-demo/`, `src/app/client-demo/` exist but are empty/scaffold-only) |
| FastAPI app + lifespan (Mongo connect, MinIO bucket ensure, CORS) | `fastapi_backend/app/main.py` |
| FastAPI Pydantic models + Mongo indexes | `fastapi_backend/app/models.py`, `fastapi_backend/app/db.py` |
| FastAPI config (pydantic-settings, reads `.env`) | `fastapi_backend/app/config.py` |
| FastAPI background-task SSE (change streams) | `fastapi_backend/app/services/tasks.py` |
| Spring Boot main + config | `src/main/java/com/example/chatgpt/ChatgptApplication.java`, `src/main/resources/application.yml` |
| Spring Boot web config (CORS, etc.) | `src/main/java/com/example/chatgpt/config/WebConfig.java` |

## Environment variables

FastAPI (`fastapi_backend/.env`, all have defaults — see `app/config.py`):

```
MONGO_URI=mongodb://localhost:27017/?replicaSet=rs0
MONGO_DATABASE=chatgpt
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=chatgpt
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

Spring Boot: hardcoded in `src/main/resources/application.yml`. Override via
standard Spring properties (`SPRING_DATA_MONGODB_URI`, `MINIO_*`, `OLLAMA_*`).

## Style / workflow conventions to follow

- Match what's already in the file. The codebase mixes Chinese and English in
  docs/comments — that's intentional, don't "fix" it.
- Don't suppress type errors. No `as any`, `@ts-ignore`, `@ts-expect-error`.
- Spring Boot uses Lombok (`@Data`, `@Builder`); keep annotations consistent
  with neighbouring files.
- FastAPI uses `pydantic-settings` v2 with `case_sensitive=False` — env-var
  names are upper-snake but config field names stay lower-snake.
- Do not commit unless explicitly asked.
- No commits on a feature branch are documented as a convention; check `git
  log --oneline -10` before assuming a branch policy.

## Existing instruction files (read these, don't duplicate)

- `CLAUDE.md` — top-level project overview, **but its FastAPI `MONGO_URI`
  example is wrong** (omits `?replicaSet=rs0`). Trust `app/config.py` over
  `CLAUDE.md` for env defaults.
- `docs/start-project.md` — full startup walkthrough, more current than
  `CLAUDE.md` for environment quirks.
- `frontend/ai/onboarding.md` — frontend collaboration workflow.
