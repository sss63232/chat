# Context — fast-minio chat demo

## Glossary

- **使用者（User）**：聊天功能的操作者，以 `userId` 字串識別（例如 `u1`）。
  本專案沒有帳號／登入系統；`userId` 只是呼叫端提供的識別字串，用來區分
  不同使用者的會話。在前端，`userId` 的預設來源是網址 query 參數
  （`?userId=u1`），畫面上的輸入框只是可覆寫的預設值。
- **會話（Chat Session）**：屬於單一 User 的一段對話，有標題與建立時間。
- **訊息（Chat Message）**：會話中的一則內容，角色為 `user` 或
  `assistant`，可含附件。
