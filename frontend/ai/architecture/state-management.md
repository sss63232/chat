# State Management

## 目前狀態流

`app/page.tsx` 目前使用 local React state：

- `userId`
- `title`
- `sessions`
- `activeSessionId`
- `messages`
- `content`
- `file`
- `loading`
- `error`
- `backend`

這表示目前沒有集中式 Redux store，也沒有共用 selector。

## 建議 Redux 結構

若要遵循專案規則，應建立以下 slice：

- `sessionSlice`
  - `sessions`
  - `activeSessionId`
  - `selectedSession`
- `messageSlice`
  - `messages`
  - `isStreaming`
  - `sendError`
- `uiSlice`
  - `loading`
  - `error`
- `backendSlice`
  - `backendTarget`
  - `apiBaseUrl`

## 重要原則

- Avoid duplicate state source：不要在 component 裡再維護一份 Redux 也有的狀態。
- Use selectors：讓 component 只讀取所需欄位。
- Keep async flow in thunks 或 middleware：將 fetch / stream call 放在 Redux async logic，而不是直接塞進 component。
- Keep UI-only state separate：若 `content` 只用於輸入框，可考慮繼續保留 local state，但要避免與 Redux 共享的 state 重複。

## 推薦實作步驟

1. 建立 `store/` 或 `src/store/` 目錄。
2. 新增 `store/index.ts` 與 `store/slices/*.ts`。
3. 先將 `sessions`、`messages`、`backend` 與 `loading/error` 移入 Redux。
4. 保留 `content`、`file` 做為純 UI local state，直到需要跨頁面共享再遷移。