# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a dual-backend chat demo that integrates:
- **Frontend**: Next.js (port 3000)
- **Backends**: FastAPI (port 8000) or Spring Boot (port 8080) — switchable at runtime
- **Database**: MongoDB (port 27017)
- **Object Storage**: MinIO (API: 9000, Console: 9001)
- **LLM**: Ollama (port 11434), default model `gemma3:4b`

## Common Commands

### Infrastructure (Docker)
```bash
docker compose up -d          # Start MongoDB and MinIO
docker compose down           # Stop all containers
docker ps                     # Check running containers
```

### Spring Boot Backend
```bash
./mvnw spring-boot:run        # Start (port 8080)
./mvnw compile                # Compile only
```

### FastAPI Backend
```bash
cd fastapi_backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # Start
```

### Frontend
```bash
cd frontend
npm install
npm run dev                   # Start (port 3000)
npm run build                 # Production build
npm run lint                  # Lint
```

### Ollama
```bash
ollama list                   # Check available models
ollama pull gemma3:4b         # Download default model
```

## Architecture

### Dual-Backend Design
Both backends expose the same API surface, allowing the frontend to switch between them:
- `POST /api/sessions` — Create session
- `GET /api/sessions?userId=...` — List sessions
- `GET /api/sessions/{sessionId}/messages` — Get messages
- `POST /api/chat/{sessionId}/send` — Send message (non-streaming)
- `POST /api/chat/{sessionId}/stream` — Send message (SSE streaming)
- `GET /health` — Health check

The frontend stores the active backend in `localStorage` under `chat-backend-target` and reads defaults from env vars:
- `NEXT_PUBLIC_DEFAULT_BACKEND` — `fastapi` or `spring`
- `NEXT_PUBLIC_FASTAPI_API_BASE` — default `http://localhost:8000`
- `NEXT_PUBLIC_SPRING_API_BASE` — default `http://localhost:8080`

### Backend Structures

**FastAPI** (`fastapi_backend/app/`):
- `main.py` — FastAPI app with lifespan (MongoDB connect, MinIO bucket ensure)
- `api/chat.py`, `api/sessions.py` — Route handlers
- `services/chat.py` — Core chat logic (send + stream)
- `services/chat_sessions.py` — Session CRUD
- `services/minio_service.py` — MinIO file upload
- `services/ollama_client.py` — Ollama API client with streaming
- `db.py` — Motor (async MongoDB) connection
- `models.py` — Pydantic models

**Spring Boot** (`src/main/java/com/example/chatgpt/`):
- `ChatgptApplication.java` — Main entry
- `controller/ChatController.java`, `SessionController.java` — REST endpoints
- `service/ChatService.java`, `ChatSessionService.java`, `MinioService.java` — Business logic
- `repository/ChatSessionRepository.java`, `ChatMessageRepository.java` — MongoDB repositories
- `model/ChatSession.java`, `ChatMessage.java`, `MessageRole.java` — Domain models
- `ollama/OllamaClient.java` — Ollama integration
- `config/MinioConfig.java`, `OllamaConfig.java` — External service config

### Frontend
Single-page app in `frontend/app/page.tsx` with:
- Backend selector dropdown
- Session list + creation
- Message display with streaming (SSE via `EventSource` pattern)
- File attachment support

## Environment Variables

### FastAPI Backend (defaults)
```
MONGO_URI=mongodb://localhost:27017
MONGO_DATABASE=chatgpt
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=chatgpt
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

### Spring Boot Backend
See `src/main/resources/application.yml` for configuration.

### Frontend
See `frontend/.env.example` for available environment variables.