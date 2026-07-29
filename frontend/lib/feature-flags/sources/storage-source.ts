import type { FeatureFlagOverrideMap, FlagSource } from "../types";

const STORAGE_KEY = "feature-flag-overrides";

export class StorageSource implements FlagSource {
  readonly name = "storage";

  async load(): Promise<FeatureFlagOverrideMap> {
    if (typeof window === "undefined") return {};
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (!raw) return {};
      return JSON.parse(raw) as FeatureFlagOverrideMap;
    } catch (err) {
      console.warn("[StorageSource] failed to load overrides", err);
      return {};
    }
  }

  static async save(overrides: FeatureFlagOverrideMap): Promise<void> {
    if (typeof window === "undefined") return;
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(overrides));
    } catch (err) {
      console.warn("[StorageSource] failed to save overrides", err);
    }
  }
}
