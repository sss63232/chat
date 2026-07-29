"use client";

import { useEffect, useState } from "react";
import { DEFAULT_FLAGS } from "./default-flags";
import { evaluateFlagInContext, useFeatureFlagInternal } from "./provider";
import type { FeatureFlagContext, FlagRule } from "./types";

export function useFeatureFlag(
  key: string,
  contextOverride?: Partial<FeatureFlagContext>
): boolean {
  const detail = useFeatureFlagDetail(key, contextOverride);
  return detail.enabled;
}

export interface FeatureFlagDetail {
  enabled: boolean;
  definition: typeof DEFAULT_FLAGS[number] | undefined;
  effectiveRule: FlagRule | undefined;
  sourceName: string | undefined;
}

export function useFeatureFlagDetail(
  key: string,
  contextOverride?: Partial<FeatureFlagContext>
): FeatureFlagDetail {
  const { context, overrides, tick } = useFeatureFlagInternal();
  const [detail, setDetail] = useState<FeatureFlagDetail>({
    enabled: false,
    definition: undefined,
    effectiveRule: undefined,
    sourceName: undefined
  });

  useEffect(() => {
    let cancelled = false;
    evaluateFlagInContext(key, { ...context, ...contextOverride }, overrides).then(
      (result) => {
        if (!cancelled)
          setDetail({
            enabled: result.enabled,
            definition: result.definition,
            effectiveRule: result.effectiveRule,
            sourceName: result.sourceName
          });
      }
    );
    return () => {
      cancelled = true;
    };
  }, [key, context, overrides, contextOverride?.userId, contextOverride?.environment, tick]);

  return detail;
}
