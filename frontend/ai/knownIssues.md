# Known Issues

## 1. Redux store 不存在

目前專案 `app/page.tsx` 使用大量 local state，專案規則提到 Redux 是主要全域狀態來源，但 `store/` 目錄尚未建立，這意味著：

- 狀態分散於 component 內部
- 未來容易產生 duplicate state
- 全域狀態同步與測試困難

## 2. Tailwind CSS 依賴缺失

`package.json` 未包含 Tailwind 相關套件，然而 UI 樣式疑似可能期待 Tailwind 使用模式。需要確認是否要補齊 Tailwind 設定。

## 3. Context drift 風險

`sendMessageStreaming()` 直接將完整 assistant 回覆附加到 local state，沒有任何 token 限制或摘要機制。若後端模型回覆長度變大，會增加 token 消耗與 drift 風險。

## 4. 後端 API contract 目前隱含

前端目前只依賴環境變數指定 `FastAPI` 或 `Spring Boot`，但沒有明確 API 文件或契約版本管理。

## 5. 目前沒有明確 handoff 版本策略

需要補強 `ai/handoff/latest.md` 的更新流程，避免多人交接時漏掉未完成事項。