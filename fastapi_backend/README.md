# FastAPI Backend

這個目錄提供一個和現有 Spring Boot 後端等價的 FastAPI 版本，保留同一組 API 路徑與主要回傳格式，方便前端直接切換。

## 功能

- `POST /api/sessions`
- `GET /api/sessions?userId=...`
- `GET /api/sessions/{sessionId}/messages`
- `POST /api/chat/{sessionId}/send`
- `POST /api/chat/{sessionId}/stream`
- `GET /health`

## 環境變數

以下都有預設值，不設定也能直接在本機開發：

- `MONGO_URI=mongodb://localhost:27017`
- `MONGO_DATABASE=chatgpt`
- `MINIO_ENDPOINT=http://localhost:9000`
- `MINIO_ACCESS_KEY=minioadmin`
- `MINIO_SECRET_KEY=minioadmin`
- `MINIO_BUCKET=chatgpt`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL=gemma3:4b`

## 啟動

```bash
cd fastapi_backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

前端如果要改接 FastAPI，可以把 `NEXT_PUBLIC_API_BASE` 設成 `http://localhost:8000`。
