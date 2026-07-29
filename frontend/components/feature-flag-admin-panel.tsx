"use client";

import { useEffect, useState } from "react";
import { DEFAULT_FLAGS } from "../lib/feature-flags/default-flags";
import { useFeatureFlagDetail } from "../lib/feature-flags/hooks";
import { useFeatureFlagInternal } from "../lib/feature-flags/provider";
import type { FeatureFlagOverrideMap, FlagRule, FlagValue } from "../lib/feature-flags/types";

const ADMIN_ENABLED_KEY = "feature-flag-admin-enabled";

export function useFeatureFlagAdminEnabled(): boolean {
  const [enabled, setEnabled] = useState(false);
  useEffect(() => {
    if (typeof window === "undefined") return;
    setEnabled(window.localStorage.getItem(ADMIN_ENABLED_KEY) === "true");
    const handler = (e: StorageEvent) => {
      if (e.key === ADMIN_ENABLED_KEY) {
        setEnabled(e.newValue === "true");
      }
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, []);
  return enabled;
}

export function FeatureFlagAdminPanel() {
  const enabled = useFeatureFlagAdminEnabled();
  const [open, setOpen] = useState(false);
  if (!enabled && process.env.NEXT_PUBLIC_FEATURE_FLAG_ADMIN !== "true") return null;

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        style={{
          position: "fixed",
          top: 8,
          right: 8,
          zIndex: 1000,
          padding: "6px 12px",
          background: "#1f2937",
          color: "#f9fafb",
          border: "1px solid #374151",
          borderRadius: 6,
          fontSize: 13,
          fontWeight: 600,
          cursor: "pointer"
        }}
      >
        Feature Flags
      </button>
      {open && (
        <div
          style={{
            position: "fixed",
            top: 40,
            right: 8,
            width: 360,
            maxHeight: "80vh",
            overflow: "auto",
            background: "#111827",
            color: "#e5e7eb",
            border: "1px solid #374151",
            borderRadius: 8,
            padding: 16,
            zIndex: 1001,
            boxShadow: "0 8px 24px rgba(0,0,0,0.4)",
            fontFamily:
              "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
            fontSize: 13
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h3 style={{ margin: 0, color: "#f9fafb", fontSize: 15 }}>Feature Flags</h3>
            <button
              type="button"
              onClick={() => setOpen(false)}
              style={{
                padding: "4px 10px",
                background: "#374151",
                color: "#f9fafb",
                border: "1px solid #4b5563",
                borderRadius: 4,
                cursor: "pointer"
              }}
            >
              Close
            </button>
          </div>
          <FlagList />
        </div>
      )}
    </>
  );
}

function FlagList() {
  const { overrides, setOverrides } = useFeatureFlagInternal();

  const updateRule = (key: string, rule: FlagRule) => {
    setOverrides({ ...overrides, [key]: rule });
  };

  return (
    <div style={{ marginTop: 16 }}>
      {DEFAULT_FLAGS.map((def) => (
        <FlagEditor key={def.key} definition={def} overrides={overrides} onChange={updateRule} />
      ))}
    </div>
  );
}

function FlagEditor({
  definition,
  overrides,
  onChange
}: {
  definition: (typeof DEFAULT_FLAGS)[number];
  overrides: FeatureFlagOverrideMap;
  onChange: (key: string, rule: FlagRule) => void;
}) {
  const detail = useFeatureFlagDetail(definition.key);
  const rule = overrides[definition.key] ?? definition.defaultRule;
  const enabled = rule?.enabled ?? false;
  const isRollout = typeof enabled === "object";
  const rollout = isRollout ? enabled.rollout : 100;

  const setEnabled = (value: FlagValue) => {
    onChange(definition.key, { ...rule, enabled: value });
  };

  const setList = (field: "users" | "environments", raw: string) => {
    const list = raw
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    onChange(definition.key, { ...rule, [field]: list });
  };

  const inputStyle: React.CSSProperties = {
    width: "100%",
    background: "#1f2937",
    color: "#f9fafb",
    border: "1px solid #4b5563",
    borderRadius: 4,
    padding: "4px 6px",
    fontSize: 12
  };

  return (
    <div style={{ borderBottom: "1px solid #374151", padding: "12px 0" }}>
      <div style={{ fontWeight: "bold", color: "#f9fafb" }}>
        {definition.name} ({definition.key})
      </div>
      <div style={{ fontSize: 12, color: "#9ca3af" }}>{definition.description}</div>
      <div style={{ fontSize: 12, marginTop: 4, color: detail.enabled ? "#34d399" : "#f87171" }}>
        Evaluated: {detail.enabled ? "true" : "false"} from {detail.sourceName ?? "default"}
      </div>
      <div style={{ marginTop: 8, display: "flex", gap: 16 }}>
        <label style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <input
            type="checkbox"
            checked={!isRollout && !!enabled}
            onChange={(e) => setEnabled(e.target.checked)}
          />
          Enabled
        </label>
        <label style={{ display: "inline-flex", alignItems: "center", gap: 4 }}>
          <input
            type="checkbox"
            checked={isRollout}
            onChange={(e) => setEnabled(e.target.checked ? { rollout: 0 } : false)}
          />
          Rollout
        </label>
      </div>
      {isRollout && (
        <div style={{ marginTop: 8 }}>
          <label style={{ display: "block" }}>
            <span style={{ color: "#9ca3af" }}>Rollout: {rollout}%</span>
            <input
              type="range"
              min={0}
              max={100}
              value={rollout}
              onChange={(e) => setEnabled({ rollout: parseInt(e.target.value, 10) })}
              style={{ width: "100%", marginTop: 4 }}
            />
          </label>
        </div>
      )}
      <div style={{ marginTop: 8 }}>
        <label style={{ display: "block", color: "#9ca3af" }}>
          Users (comma separated):
          <input
            type="text"
            value={(rule.users ?? []).join(", ")}
            onChange={(e) => setList("users", e.target.value)}
            style={inputStyle}
          />
        </label>
      </div>
      <div style={{ marginTop: 8 }}>
        <label style={{ display: "block", color: "#9ca3af" }}>
          Environments (comma separated):
          <input
            type="text"
            value={(rule.environments ?? []).join(", ")}
            onChange={(e) => setList("environments", e.target.value)}
            style={inputStyle}
          />
        </label>
      </div>
    </div>
  );
}
