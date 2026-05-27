# AI Collaboration Onboarding

This folder contains the lightweight AI collaboration infrastructure for the `fast-minio-frontend` project. It is intended to help engineers onboard quickly, maintain architectural continuity, and reduce drift across tasks.

## 目的

- 提升長期協作效率
- 降低 Token 消耗
- 避免 Context Drift
- 建立可持續 Handoff 機制

## 使用方式

1. 任何新任務開始前，先閱讀 `ai/currentTask.md`。
2. 編輯前，檢查 `ai/architecture/*` 與 `ai/decisions.md`。
3. 重要修改完成後，更新 `ai/currentTask.md` 與 `ai/handoff/latest.md`。
4. 發現新問題時，立即記錄到 `ai/knownIssues.md`。

## 文件目錄

- `ai/currentTask.md`：當前任務與下一步狀態。
- `ai/decisions.md`：重要架構決策與範式。
- `ai/knownIssues.md`：現有問題與限制。
- `ai/techStack.md`：專案技術棧。
- `ai/productContext.md`：產品目標與範圍。
- `ai/architecture/`：細分架構說明。
- `ai/handoff/latest.md`：最新交接紀錄。
