# FastAPI Backend

這個目錄提供一個和現有 Spring Boot 後端等價的 FastAPI 版本，保留同一組 API 路徑與主要回傳格式，方便前端直接切換。

## 功能

- `POST /api/sessions`
- `GET /api/sessions?userId=...`
- `GET /api/sessions/{sessionId}/messages`
- `POST /api/chat/{sessionId}/send`
- `POST /api/chat/{sessionId}/stream`
- `POST /api/tasks`
- `GET /api/tasks/{taskId}`
- `GET /api/tasks/{taskId}/events`
- `GET /health`

## 非同步任務與 SSE

建立長任務時，後端會先寫入 MongoDB 的 `background_tasks` collection，並回傳 `202 Accepted`：

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-1",
    "taskType": "summary",
    "payload": {
      "sessionId": "SESSION_ID",
      "sourceText": "需要摘要的內容"
    }
  }'
```

前端可用 SSE 訂閱任務變化：

```text
GET /api/tasks/{taskId}/events
```

SSE 使用 MongoDB change streams 監聽任務文件變化，不會對資料庫做固定頻率輪詢。任務文件更新時會推送事件，事件名稱會對應目前狀態：`queued`、`running`、`succeeded`、`failed`、`canceled`，並會在終止狀態後結束連線。

> MongoDB change streams 需要 replica set 或 sharded cluster；standalone MongoDB 不支援。

外部 worker 只需要更新同一筆 document，例如：

```javascript
db.background_tasks.updateOne(
  { _id: ObjectId("TASK_ID") },
  {
    $set: {
      status: "running",
      progress: 50,
      message: "summarizing",
      updatedAt: new Date()
    }
  }
)
```

完成時寫入 `status: "succeeded"`、`progress: 100` 與 `result`；失敗時寫入 `status: "failed"` 與 `error`。

## 環境變數

以下都有預設值，不設定也能直接在本機開發：

- `MONGO_URI=mongodb://localhost:27017/?replicaSet=rs0`
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
