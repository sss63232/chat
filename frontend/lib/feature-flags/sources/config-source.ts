import { DEFAULT_FLAGS } from "../default-flags";
import type { FeatureFlagOverrideMap, FlagSource } from "../types";

export class ConfigSource implements FlagSource {
  readonly name = "config";

  async load(): Promise<FeatureFlagOverrideMap> {
    return DEFAULT_FLAGS.reduce<FeatureFlagOverrideMap>((acc, def) => {
      acc[def.key] = def.defaultRule;
      return acc;
    }, {});
  }
}
