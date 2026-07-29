import { DEFAULT_FLAGS } from "../default-flags";
import type { FeatureFlagOverrideMap, FlagSource, FlagValue } from "../types";

export class EnvSource implements FlagSource {
  readonly name = "env";

  async load(): Promise<FeatureFlagOverrideMap> {
    const result: FeatureFlagOverrideMap = {};
    for (const flag of DEFAULT_FLAGS) {
      const envKey = `NEXT_PUBLIC_FEATURE_${toUpperSnake(flag.key)}`;
      const raw = process.env[envKey];
      if (!raw) continue;
      const enabled = parseEnvValue(raw);
      if (enabled === undefined) {
        console.warn(`[EnvSource] invalid value for ${envKey}: ${raw}`);
        continue;
      }
      // Env 只覆蓋 enabled，其餘欄位沿用 config。
      result[flag.key] = { enabled };
    }
    return result;
  }
}

function toUpperSnake(camel: string): string {
  return camel.replace(/[A-Z]/g, (letter) => `_${letter}`).toUpperCase();
}

function parseEnvValue(raw: string): FlagValue | undefined {
  if (raw === "true") return true;
  if (raw === "false") return false;
  const match = /^rollout:(\d+)$/.exec(raw);
  if (!match) return undefined;
  const rollout = parseInt(match[1], 10);
  if (rollout < 0 || rollout > 100) return undefined;
  return { rollout };
}
