import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { evaluateFlag } from "./engine";
import type { FeatureFlagOverrideMap, FlagSource } from "./types";

function createSource(name: string, map: FeatureFlagOverrideMap): FlagSource {
  return { name, load: async () => map };
}

const testContext = { userId: "u1", environment: "development" as const };

describe("evaluateFlag", () => {
  it("returns false for unknown flag", async () => {
    const result = await evaluateFlag("unknown", testContext, []);
    assert.equal(result.enabled, false);
    assert.equal(result.effectiveRule, undefined);
  });

  it("returns true for boolean enabled", async () => {
    const source = createSource("config", { foo: { enabled: true } });
    const result = await evaluateFlag("foo", testContext, [source]);
    assert.equal(result.enabled, true);
  });

  it("returns false for boolean disabled", async () => {
    const source = createSource("config", { foo: { enabled: false } });
    const result = await evaluateFlag("foo", testContext, [source]);
    assert.equal(result.enabled, false);
  });

  it("respects user list", async () => {
    const source = createSource("config", {
      foo: { enabled: false, users: ["u1"] }
    });
    const result = await evaluateFlag("foo", testContext, [source]);
    assert.equal(result.enabled, true);
  });

  it("filters by environment", async () => {
    const source = createSource("config", {
      foo: { enabled: true, environments: ["production"] }
    });
    const result = await evaluateFlag("foo", testContext, [source]);
    assert.equal(result.enabled, false);
  });

  it("filters by date", async () => {
    const source = createSource("config", {
      foo: { enabled: true, endAt: "2020-01-01T00:00:00Z" }
    });
    const result = await evaluateFlag("foo", testContext, [source], new Date("2024-01-01"));
    assert.equal(result.enabled, false);
  });

  it("merges sources by priority", async () => {
    const low = createSource("config", { foo: { enabled: false } });
    const high = createSource("storage", { foo: { enabled: true } });
    const result = await evaluateFlag("foo", testContext, [low, high]);
    assert.equal(result.enabled, true);
    assert.equal(result.sourceName, "storage");
  });

  it("percentage rollout is stable for same user", async () => {
    const source = createSource("config", { foo: { enabled: { rollout: 50 } } });
    const r1 = await evaluateFlag("foo", testContext, [source]);
    const r2 = await evaluateFlag("foo", testContext, [source]);
    assert.equal(r1.enabled, r2.enabled);
  });

  it("ignores failing sources", async () => {
    const bad = { name: "bad", load: async () => { throw new Error("boom"); } };
    const good = createSource("config", { foo: { enabled: true } });
    const result = await evaluateFlag("foo", testContext, [bad, good]);
    assert.equal(result.enabled, true);
  });
});
