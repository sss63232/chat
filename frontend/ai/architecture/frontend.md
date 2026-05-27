# Frontend Architecture

## 目前結構

前端核心實作集中在 `app/page.tsx`，它是一個 `use client` 的 React client component。

### 主要功能

- `userId` / `title` / `backend` 選擇
- `sessions` 與 `activeSessionId`
- `messages` 欄位與串流回覆更新
- `content` 與 `file` 附件上傳
- `loading` / `error` UI 狀態

### 優勢

- 單一檔案實作，容易讀懂。
- 即時串流回覆可直接更新 assistant message。
- 動態後端切換支援 FastAPI / Spring Boot。

### 風險

- 所有狀態維持在 local component state，無法跨頁面重用。
- 未來若引入更多頁面或功能，容易造成重複狀態來源。
- 目前沒有封裝 API 呼叫邏輯或 fetch utility。

## 建議方向

1. 建立 Redux store，將以下狀態移入全域：
   - sessions
   - messages
   - activeSessionId
   - backend selection
   - ui loading / error
2. 保留 `app/page.tsx` 為 UI 組件，讓它只負責呈現與事件綁定。
3. 將 API 呼叫邏輯抽成 `lib/api.ts` 或 `services/chat.ts`，減少 component 負擔。
4. 依專案規則優先使用 Function Component + Arrow Function。