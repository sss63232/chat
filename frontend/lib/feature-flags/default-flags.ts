import type { FeatureFlagDefinition } from "./types";

export const DEFAULT_FLAGS: FeatureFlagDefinition[] = [
  {
    key: "taskPanel",
    name: "Task Panel",
    description: "在聊天介面顯示背景任務面板",
    defaultRule: { enabled: false }
  },
  {
    key: "streamingResponse",
    name: "Streaming Response",
    description: "使用 SSE 串流回應",
    defaultRule: { enabled: true }
  },
  {
    key: "newBackendToggle",
    name: "New Backend Toggle",
    description: "測試後端切換 UI 的實驗性改版",
    defaultRule: { enabled: { rollout: 0 }, environments: ["development"] }
  }
];

export const DEFAULT_FLAG_KEYS = DEFAULT_FLAGS.map((f) => f.key);
