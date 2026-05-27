# Backend Architecture

## 目前前端依賴

前端透過環境變數連線到不同後端：

- `NEXT_PUBLIC_FASTAPI_API_BASE`
- `NEXT_PUBLIC_SPRING_API_BASE`
- `NEXT_PUBLIC_DEFAULT_BACKEND`

## 目前 API endpoints

- `GET /api/sessions?userId={userId}`
- `POST /api/sessions`
- `GET /api/sessions/{sessionId}/messages`
- `POST /api/chat/{sessionId}/stream`

## 目前後端角色

- 提供聊天會話列表與歷史訊息
- 建立新會話
- 提供串流型 AI 回覆
- 處理檔案上傳與附件清單

## 待補強

- 加入明確 API 契約與版本說明
- 定義 `SendMessageResponse` 與 `ChatMessage` JSON schema
- 追蹤 `stream` endpoint 的 SSE / chunked 回覆格式
- 確認附件 URL 是否可跨域取用，並兼顧 MinIO 存取設定
