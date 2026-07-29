"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode
} from "react";
import { DEFAULT_FLAGS } from "./default-flags";
import { evaluateFlag, type EvaluateResult } from "./engine";
import { ApiSource } from "./sources/api-source";
import { ConfigSource } from "./sources/config-source";
import { EnvSource } from "./sources/env-source";
import { StorageSource } from "./sources/storage-source";
import type { FeatureFlagContext, FeatureFlagOverrideMap, FlagSource } from "./types";

interface FeatureFlagState {
  context: FeatureFlagContext;
  overrides: FeatureFlagOverrideMap;
  tick: number;
  refresh: () => void;
  setOverrides: (overrides: FeatureFlagOverrideMap) => void;
}

const FeatureFlagContext = createContext<FeatureFlagState | null>(null);

interface FeatureFlagProviderProps {
  children: ReactNode;
  context?: FeatureFlagContext;
}

const SOURCES = [
  new ConfigSource(),
  new EnvSource(),
  new StorageSource(),
  new ApiSource()
];

export function FeatureFlagProvider({
  children,
  context = {}
}: FeatureFlagProviderProps) {
  const [overrides, setOverridesState] = useState<FeatureFlagOverrideMap>({});
  const [tick, setTick] = useState(0);

  const refresh = useCallback(() => setTick((t) => t + 1), []);

  const setOverrides = useCallback(
    async (next: FeatureFlagOverrideMap) => {
      await StorageSource.save(next);
      setOverridesState(next);
      setTick((t) => t + 1);
    },
    []
  );

  useEffect(() => {
    let mounted = true;
    SOURCES[2].load().then((loaded) => {
      if (mounted) setOverridesState(loaded);
    });
    return () => {
      mounted = false;
    };
  }, []);

  // 監聽同源其他 tab 的 storage 變更。
  useEffect(() => {
    const handler = (e: StorageEvent) => {
      if (e.key === "feature-flag-overrides") refresh();
    };
    window.addEventListener("storage", handler);
    return () => window.removeEventListener("storage", handler);
  }, [refresh]);

  const value = useMemo(
    () => ({ context, overrides, tick, refresh, setOverrides }),
    [context, overrides, tick, refresh, setOverrides]
  );

  return (
    <FeatureFlagContext.Provider value={value}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlagInternal(): FeatureFlagState {
  const ctx = useContext(FeatureFlagContext);
  if (!ctx) throw new Error("useFeatureFlag must be used within FeatureFlagProvider");
  return ctx;
}

export async function evaluateFlagInContext(
  key: string,
  context: FeatureFlagContext,
  overrides: FeatureFlagOverrideMap
): Promise<EvaluateResult & { definition: typeof DEFAULT_FLAGS[number] | undefined }> {
  const runtimeSource: FlagSource = {
    name: "runtime",
    async load() {
      return overrides;
    },
  };
  const sources: FlagSource[] = [
    SOURCES[0], // config
    SOURCES[1], // env
    runtimeSource,
    SOURCES[3] // api
  ];
  const result = await evaluateFlag(key, context, sources);
  const definition = DEFAULT_FLAGS.find((f) => f.key === key);
  return { ...result, definition };
}
