import type { FeatureFlagOverrideMap } from "../types";

export interface FlagSource {
  readonly name: string;
  load(): Promise<FeatureFlagOverrideMap>;
}
