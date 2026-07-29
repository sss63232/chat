import type { FeatureFlagOverrideMap, FlagSource } from "../types";

export class ApiSource implements FlagSource {
  readonly name = "api";

  // 本階段不回傳任何 override，僅保留介面。
  async load(): Promise<FeatureFlagOverrideMap> {
    return {};
  }
}
