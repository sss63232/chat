# Decisions

## 初始規範

- `ai/` 用於協作知識、架構說明與交接紀錄。
- 所有重要設計決策應以簡潔條列方式記錄。
- 若專案未來引入 Redux，必須把 UI 重要狀態移入 `store/` 或 `src/store/`，避免 duplicate state。
- 每次主要修改後，`ai/currentTask.md` 與 `ai/handoff/latest.md` 必須同步更新。

## 目前決策

- 先建立知識文檔，不變更現有功能行為。
- 本專案目前沒有 `store/` 目錄，因此暫以改善文檔與可追踪狀態為首要任務。
- 專案採用 Next.js App Router 與 TypeScript；即使無 Tailwind package，也以規劃支援 Tailwind 的方向進行。

## Feature Flags

- 前端 feature flag 系統實作於 `frontend/lib/feature-flags/`。
- 預設 flag 定義位於 `frontend/lib/feature-flags/default-flags.ts`，評估引擎與 Provider 在同一目錄下。
- Admin panel 預設隱藏，可透過以下方式開啟：
  - 在瀏覽器 console 執行 `localStorage.setItem("feature-flag-admin-enabled", "true")` 後重新整理。
  - 或將環境變數 `NEXT_PUBLIC_FEATURE_FLAG_ADMIN` 設為 `true` 後重新 build。 
