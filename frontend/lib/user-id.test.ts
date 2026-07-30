import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { resolveUserId } from "./user-id";

describe("resolveUserId", () => {
  it("returns the userId query param", () => {
    assert.equal(resolveUserId("?userId=u2"), "u2");
  });

  it("returns the userId param when other params are present", () => {
    assert.equal(resolveUserId("?foo=bar&userId=u2"), "u2");
  });

  it("trims surrounding whitespace from the param", () => {
    assert.equal(resolveUserId("?userId=%20u3%20"), "u3");
  });

  it("falls back to u1 when search is empty", () => {
    assert.equal(resolveUserId(""), "u1");
  });

  it("falls back to u1 when userId param is missing", () => {
    assert.equal(resolveUserId("?foo=bar"), "u1");
  });

  it("falls back to u1 when userId param is empty", () => {
    assert.equal(resolveUserId("?userId="), "u1");
  });

  it("falls back to u1 when userId param is only whitespace", () => {
    assert.equal(resolveUserId("?userId=%20%20"), "u1");
  });

  it("decodes percent-encoded characters in the param", () => {
    assert.equal(resolveUserId("?userId=a%26b"), "a&b");
  });
});
