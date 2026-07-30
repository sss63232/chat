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

## Markdown + KaTeX 渲染

- Chat 訊息（user 與 assistant）統一使用 `components/markdown-content.tsx` 渲染。
  - 套件：`react-markdown`、`remark-gfm`、`remark-math`、`rehype-katex`、`rehype-highlight`。
  - 實作重點：元件用 `React.memo` 包覆；`katexOptions` 設為 `{ throwOnError: false, strict: "ignore" }`，避免單條語法錯誤中斷整頁。
- KaTeX 與 highlight.js 的 CSS 在 `app/layout.tsx` 統一 import，不在 `components/markdown-content.tsx` 內引入。
  - 原因：`components/` 位於 `app/` 的 global-CSS 邊界之外；把 CSS 留在 layout 可讓 `node:test` + `tsx` 直接 import 元件，不需要 CSS loader。
- 前端測試使用 `node:test` + `tsx`，並透過 `tsconfig.test.json` 指定 `jsx: react-jsx`。
  - 原因：根目錄 `tsconfig.json` 的 `jsx: preserve` 是 Next.js 所需；`tsx` 在該設定下會走 classic JSX，導致測試失敗。
  - 執行指令：`npm test`。
- Markdown 驗收 fixture 採用真實檔案 `app/markdown-demo/sample.md`，而非 TS template literal。
  - 原因：反斜線與 backtick 在 template literal 中容易轉義錯誤，真實 `.md` 檔案可避免 corrupted content。 
