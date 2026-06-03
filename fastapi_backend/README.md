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
- `GET /api/tasks/notebooks/{notebookId}/events`
- `GET /health`

## 非同步任務與 SSE

建立長任務時，後端會先寫入 MongoDB 的 `background_tasks` collection，並回傳 `202 Accepted`：

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "user-1",
    "notebookId": "notebook-1",
    "taskType": "summary",
    "payload": {
      "sessionId": "SESSION_ID",
      "sourceText": "需要摘要的內容"
    }
  }'
```

前端可用 SSE 訂閱某個 notebook 底下所有任務的進度：

```text
GET /api/tasks/notebooks/{notebookId}/events
```

SSE 使用 MongoDB change streams 監聽任務文件變化，不會對資料庫做固定頻率輪詢。任務文件更新時會推送 notebook 層級摘要，事件名稱為 `progress` 或 `done`；`progress` 事件在任務尚未全部完成時會持續推送，當該 notebook 底下所有任務都進入 `succeeded`、`failed` 或 `canceled` 後，會推送 `done` 並結束連線。

事件資料格式：

```json
{
  "notebookId": "notebook-1",
  "totalTasks": 2,
  "completedTasks": 1,
  "overallProgress": 75,
  "allCompleted": false,
  "latestUpdatedAt": "2026-06-02T12:00:00+00:00",
  "tasks": [
    {
      "id": "6650a1b2c3d4e5f6a7b8c9d0",
      "userId": "user-1",
      "notebookId": "notebook-1",
      "taskType": "summary",
      "status": "running",
      "progress": 75,
      "message": "summarizing",
      "result": null,
      "error": null,
      "createdAt": "2026-06-02T11:00:00+00:00",
      "updatedAt": "2026-06-02T12:00:00+00:00"
    },
    {
      "id": "6650a1b2c3d4e5f6a7b8c9d1",
      "userId": "user-1",
      "notebookId": "notebook-1",
      "taskType": "summary",
      "status": "succeeded",
      "progress": 100,
      "message": "completed",
      "result": {},
      "error": null,
      "createdAt": "2026-06-02T10:00:00+00:00",
      "updatedAt": "2026-06-02T10:30:00+00:00"
    }
  ]
}
```

如果需要追蹤單一任務，仍可使用：

```text
GET /api/tasks/{taskId}/events
```

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