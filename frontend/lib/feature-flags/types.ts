export type FlagValue = boolean | { rollout: number };

export interface FlagRule {
  enabled: FlagValue;
  users?: string[];
  environments?: string[];
  startAt?: string;
  endAt?: string;
}

export interface FeatureFlagDefinition {
  key: string;
  name: string;
  description?: string;
  defaultRule: FlagRule;
}

export interface FeatureFlagContext {
  userId?: string;
  environment?: "development" | "preview" | "production";
}

export type FeatureFlagOverrideMap = Record<string, FlagRule | undefined>;

export type { FlagSource } from "./sources/types";
