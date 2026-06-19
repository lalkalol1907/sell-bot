import { describe, expect, test } from "bun:test";
import { buildLoginHandoffUrl } from "../src/redis.ts";

describe("buildLoginHandoffUrl", () => {
  test("appends handoff query param", () => {
    const url = buildLoginHandoffUrl("https://login.example.com/miniapp/", "abc123");
    expect(url).toBe("https://login.example.com/miniapp/?handoff=abc123");
  });

  test("preserves existing query params", () => {
    const url = buildLoginHandoffUrl("https://login.example.com/miniapp/?x=1", "abc123");
    expect(url).toBe("https://login.example.com/miniapp/?x=1&handoff=abc123");
  });
});
