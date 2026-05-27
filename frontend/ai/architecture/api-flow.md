# API Flow

## 使用流程

1. 使用者輸入 `userId`。
2. 點擊「讀取會話」時，前端呼叫：
   - `GET ${apiBase}/api/sessions?userId={userId}`
3. 選擇會話時，前端呼叫：
   - `GET ${apiBase}/api/sessions/{sessionId}/messages`
4. 建立新會話時，前端呼叫：
   - `POST ${apiBase}/api/sessions`
   - Body: `{ userId, title }`
5. 送出訊息時，前端呼叫：
   - `POST ${apiBase}/api/chat/{sessionId}/stream`
   - Body: FormData with `content` and optional `file`

## 串流架構

- `sendMessageStreaming()` 以 `fetch` 取得 `res.body.getReader()`。
- 逐行解析 SSE-like event streams：
  - `event: delta`
  - `event: done`
  - `data:` lines
- `delta` 事件即時 append assistant content。
- `done` 事件回傳最終 `SendMessageResponse`，並修正暫存訊息 id / content。

## 重要 API contract

### `SendMessageResponse`

- `sessionId`
- `userMessageId`
- `assistantMessageId`
- `assistantContent`
- `attachmentUrls[]`

### `ChatSession`

- `id`
- `userId`
- `title`
- `createdAt`

### `ChatMessage`

- `id`
- `sessionId`
- `role`: `user` | `assistant`
- `content`
- `attachmentUrls[]`
- `createdAt`

## 建議補強

- 明確定義 `stream` endpoint 的 event schema。
- 針對錯誤情況定義 fallback flow。
- 將 API 呼叫抽成可重用 service，避免 component 直接呼叫 `fetch`。