import type {
  FeatureFlagContext,
  FeatureFlagOverrideMap,
  FlagRule,
  FlagSource
} from "./types";
import {
  isFlagValueEnabled,
  isRuleActiveForDate,
  isRuleActiveForEnvironment
} from "./utils";

export interface EvaluateResult {
  enabled: boolean;
  effectiveRule: FlagRule | undefined;
  sourceName: string | undefined;
}

export async function evaluateFlag(
  key: string,
  context: FeatureFlagContext,
  sources: FlagSource[],
  now = new Date()
): Promise<EvaluateResult> {
  const defaultResult: EvaluateResult = {
    enabled: false,
    effectiveRule: undefined,
    sourceName: undefined
  };

  try {
    const { merged, provenance } = await mergeSources(sources);
    const rule = merged[key];
    if (!rule) return defaultResult;

    const sourceName = provenance[key];

    if (!isRuleActiveForEnvironment(rule, context.environment)) {
      return { enabled: false, effectiveRule: rule, sourceName };
    }
    if (!isRuleActiveForDate(rule, now)) {
      return { enabled: false, effectiveRule: rule, sourceName };
    }

    if (rule.users && rule.users.length > 0 && context.userId && rule.users.includes(context.userId)) {
      return { enabled: true, effectiveRule: rule, sourceName };
    }

    const enabled = isFlagValueEnabled(rule.enabled, context.userId, key);
    return { enabled, effectiveRule: rule, sourceName };
  } catch (err) {
    console.warn(`[FeatureFlagEngine] failed to evaluate ${key}`, err);
    return defaultResult;
  }
}

async function mergeSources(
  sources: FlagSource[]
): Promise<{ merged: FeatureFlagOverrideMap; provenance: Record<string, string> }> {
  const merged: FeatureFlagOverrideMap = {};
  const provenance: Record<string, string> = {};
  for (const source of sources) {
    try {
      const loaded = await source.load();
      for (const key of Object.keys(loaded)) {
        if (loaded[key] !== undefined) {
          merged[key] = loaded[key];
          provenance[key] = source.name;
        }
      }
    } catch (err) {
      console.warn(`[FeatureFlagEngine] source ${source.name} failed`, err);
    }
  }
  return { merged, provenance };
}
