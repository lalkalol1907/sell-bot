import { describe, expect, test } from "bun:test";
import { loadGatewayConfig } from "./config.js";
import { pickEngineAddress } from "./login-routing.js";
import { checkRateLimit, type RateLimitStore } from "./rate-limit.js";

describe("loadGatewayConfig", () => {
  test("parses comma-separated login engines", () => {
    const config = loadGatewayConfig({
      BOT_TOKEN: "token",
      REDIS_URL: "redis://localhost:6379/0",
      WORKER_LOGIN_GRPC_ADDR: "engine-a:50053, engine-b:50053",
    });
    expect(config.loginEngineAddrs).toEqual(["engine-a:50053", "engine-b:50053"]);
  });

  test("requires redis", () => {
    expect(() =>
      loadGatewayConfig({
        BOT_TOKEN: "token",
      }),
    ).toThrow(/REDIS_URL/);
  });
});

describe("pickEngineAddress", () => {
  test("round-robin pick uses all engines", () => {
    const addrs = ["a:1", "b:1", "c:1"];
    const picks = [
      pickEngineAddress(addrs, 1, 0),
      pickEngineAddress(addrs, 1, 1),
      pickEngineAddress(addrs, 1, 2),
    ];
    expect(new Set(picks).size).toBe(3);
  });
});

class MemoryRateLimitStore implements RateLimitStore {
  private counts = new Map<string, number>();

  async increment(key: string, _windowMs: number): Promise<number> {
    const next = (this.counts.get(key) ?? 0) + 1;
    this.counts.set(key, next);
    return next;
  }
}

describe("checkRateLimit", () => {
  test("blocks after limit", async () => {
    const store = new MemoryRateLimitStore();
    expect(await checkRateLimit(store, "user:1", 2, 60_000)).toBe(true);
    expect(await checkRateLimit(store, "user:1", 2, 60_000)).toBe(true);
    expect(await checkRateLimit(store, "user:1", 2, 60_000)).toBe(false);
  });
});
