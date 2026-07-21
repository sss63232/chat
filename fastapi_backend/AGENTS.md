# AGENTS.md — FastAPI + MCP server

FastAPI 0.116 chat backend (HTTP API on port 8000) and the accompanying
fastmcp 2.x server (MCP tools + resources on port 8001). Inherits the
project-wide gotchas from the root `AGENTS.md` — read both before editing.
Category-loading doctype is Python; all code under `app/` and `mcp_server/`
is typed PEP-604 unions.

## Structure

    fastapi_backend/
    ├── app/
    │   ├── main.py            # FastAPI app + lifespan (Mongo connect, MinIO ensure, CORS)
    │   ├── config.py          # pydantic-settings v2; get_settings() lru_cached
    │   ├── db.py              # Motor AsyncIOMotorClient; module-level client/database globals
    │   ├── models.py          # Pydantic v2 models + TaskStatus enum + *_from_document()
    │   ├── api/               # Routers: chat.py, sessions.py, tasks.py, examples.py
    │   └── services/          # Business logic: chat.py, chat_sessions.py, minio_service.py,
    │                          #   ollama_client.py, tasks.py (change-stream SSE)
    ├── mcp_server/
    │   ├── server.py          # FastMCP 2.x instance; own mcp_lifespan; reuses app/services/*
    │   └── README.md          # Tools/Resources tables, integrations, MCP Inspector usage
    ├── tests/
    │   ├── conftest.py         # mcp_lifespan autouse; @mongodb_available / @services_available
    │   └── test_mcp_tools.py   # Integration tests for every MCP tool + the users://list resource
    ├── scripts/test_mcp.sh
    ├── pytest.ini             # asyncio_mode=auto, testpaths=tests
    ├── requirements.txt       # Pinned fastapi 0.116.1, motor 3.7.1, fastmcp>=2,<3
    ├── Dockerfile.mcp          # MCP-server container image
    └── .venv/                 # Local virtualenv — not committed

## Where to look

| Task | Location |
|---|---|
| Add an HTTP route | `app/api/{chat,sessions,tasks,examples}.py` — `DatabaseDep`/`SettingsDep` Annotated aliases |
| Add MCP tool/resource | `mcp_server/server.py` — register via `mcp.tool(...)` / `mcp.resource(...)`, follow `_to_tool_error` pattern |
| Change a Pydantic model | `app/models.py` — `AppModel` base (populate_by_name, use_enum_values, str_strip_whitespace); also export a `*_from_document()` converter |
| Add an env var | `app/config.py` `Settings` (lower-snake field; `case_sensitive=False`); for MCP add `MCP_*` env in `server.py` |
| Debug SSE / change-stream task | `app/services/tasks.py` — `stream_task_events` / `stream_notebook_task_events` use `database.background_tasks.watch(pipeline, full_document="updateLookup", max_await_time_ms=…)` |
| Wire a new Mongo collection | Initialise in `app/db.py connect_to_mongo()` (indexes go here, not at the call site) |

## Conventions (FastAPI-specific)

- **Two entry points share `app/services/*`.** HTTP (`app/main.py:app`) and
  MCP (`mcp_server/server.py:mcp`) MUST NOT duplicate business logic — push
  logic into a `app/services/*.py` function and call from both. The MCP
  server has its own `mcp_lifespan` (`connect_to_mongo` + `ensure_bucket` +
  `close_httpx_client`) and does **not** start `app.main:app`.
- **Pydantic v2 throughout.** `AppModel` uses `ConfigDict(populate_by_name=True,
  use_enum_values=True, str_strip_whitespace=True)`. Mongo documents are
  converted via `*_from_document()` helpers, not by constructing models
  directly from raw dicts.
- **`get_settings()` is lru_cached.** Do not construct `Settings()` ad-hoc —
  inject via `SettingsDep = Annotated[Settings, Depends(get_settings)]`
  (HTTP) or call `get_settings()` (MCP).
- **`get_database()` raises if unconnected.** Both `main.py` and
  `mcp_server/server.py` call `connect_to_mongo()` in their lifespan before
  any route/tool runs — preserve that order when refactoring lifespans.
- **httpx client is a module-level singleton** in
  `app/services/ollama_client.py` (`_get_httpx_client` / `close_httpx_client`).
  Always close it on shutdown to avoid leaked sockets in tests.
- **SSE helper naming collides on purpose.** `app/services/chat.py::format_sse`
  and `app/services/tasks.py::format_sse` both exist with slightly different
  signatures (task version accepts an optional `event_id`). Don't merge them;
  they live in different modules for a reason.
- **Test guards.** New tests touching live services MUST use the
  `@mongodb_available` / `@services_available` markers from
  `tests/conftest.py` so CI-less local runs skip cleanly when Docker / Ollama
  are down.

## Anti-patterns (FastAPI-specific)

- Do not write business logic in `app/api/*` — call `app/services/*`.
- Do not add `from app.main import app` to `mcp_server/server.py`. They are
  separate processes.
- Do not replace `?replicaSet=rs0` in `MONGO_URI` — change streams break
  silently on standalone Mongo (see root AGENTS.md gotcha).
- Do not construct `httpx.AsyncClient()` per request — use
  `ollama_client._get_httpx_client(settings)` so the singleton is reused.
- Do not run `pytest` from the repo root — `pytest.ini` is in
  `fastapi_backend/`. `cd fastapi_backend && python -m pytest` or set
  `PYTHONPATH=fastapi_backend`.
- No `as Any`-style suppression. PEP-604 unions (`X | None`) are the
  convention — keep it.

## Commands

    # Install (first time)
    python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

    # HTTP API
    uvicorn app.main:app --reload --port 8000

    # MCP server (separate process, default :8001)
    python -m mcp_server.server
    #   MCP_RELOAD=1 python -m mcp_server.server   # auto-reload during dev

    # Tests (requires docker compose up -d + ollama pull gemma3:4b)
    python -m pytest tests -v

    # Pipe-clean against a live MCP server
    curl http://localhost:8001/mcp -X POST -H 'content-type: application/json' \
      -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'

## Notes

- The HTTP API exposes the SSE task endpoints; the MCP tools consume the
  same change-stream events internally — `get_task_status` and
  `get_notebook_progress` poll until terminal status, so raw SSE is never
  surfaced to the MCP client by design.
- `examples.py` router is for demo fixtures — check before extending.
- `scripts/test_mcp.sh` is a smoke script, not a test runner.
