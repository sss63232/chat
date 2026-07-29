import type { FlagRule, FlagValue } from "./types";

export function stableBucket(userId: string | undefined, flagKey: string): number {
  const input = userId ? `${userId}:${flagKey}` : flagKey;
  let hash = 2166136261;
  for (let i = 0; i < input.length; i += 1) {
    hash ^= input.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return Math.abs(hash) % 100;
}

export function isFlagValueEnabled(
  value: FlagValue,
  userId: string | undefined,
  flagKey: string
): boolean {
  if (typeof value === "boolean") return value;
  const bucket = stableBucket(userId, flagKey);
  return bucket < value.rollout;
}

export function isRuleActiveForEnvironment(
  rule: FlagRule,
  environment?: string
): boolean {
  if (!rule.environments || rule.environments.length === 0) return true;
  if (!environment) return false;
  return rule.environments.includes(environment);
}

export function isRuleActiveForDate(rule: FlagRule, now: Date): boolean {
  if (rule.startAt && now < new Date(rule.startAt)) return false;
  if (rule.endAt && now > new Date(rule.endAt)) return false;
  return true;
}
