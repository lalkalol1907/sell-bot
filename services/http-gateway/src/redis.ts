import crypto from "node:crypto";
import { Redis } from "ioredis";
import type { AppConfig } from "./config.js";

const HANDOFF_PREFIX = "login:handoff:";
const HANDOFF_TTL_SEC = 30 * 60;

export type LoginHandoffPayload = {
  seller_id: number;
  tg_user_id: number;
};

export class LoginHandoff {
  constructor(private redis: Redis) {}

  async create(sellerId: number, tgUserId: number): Promise<string> {
    const token = crypto.randomBytes(32).toString("hex");
    const payload: LoginHandoffPayload = { seller_id: sellerId, tg_user_id: tgUserId };
    await this.redis.set(`${HANDOFF_PREFIX}${token}`, JSON.stringify(payload), "EX", HANDOFF_TTL_SEC);
    return token;
  }

  async resolve(token: string): Promise<LoginHandoffPayload | null> {
    if (!token) return null;
    const raw = await this.redis.get(`${HANDOFF_PREFIX}${token}`);
    if (!raw) return null;
    try {
      const payload = JSON.parse(raw) as LoginHandoffPayload;
      if (!payload.seller_id) return null;
      return payload;
    } catch {
      return null;
    }
  }
}

export function buildLoginHandoffUrl(baseUrl: string, token: string): string {
  const url = new URL(baseUrl);
  url.searchParams.set("handoff", token);
  return url.toString();
}

let redis: Redis | null = null;

export function getRedis(config: AppConfig): Redis {
  if (!redis) {
    redis = new Redis(config.redisUrl, { maxRetriesPerRequest: 3, lazyConnect: true });
  }
  return redis;
}

export class RateLimiter {
  constructor(private redis: Redis) {}

  async allow(key: string, limit: number, windowMs: number): Promise<boolean> {
    const redisKey = `rl:${key}`;
    const count = await this.redis.incr(redisKey);
    if (count === 1) {
      await this.redis.pexpire(redisKey, windowMs);
    }
    return count <= limit;
  }
}

const ROUTE_PREFIX = "login:route:";

export class LoginRouting {
  constructor(
    private redis: Redis,
    private ttlSec: number,
  ) {}

  async pin(loginId: string, engineAddr: string): Promise<void> {
    await this.redis.set(`${ROUTE_PREFIX}${loginId}`, engineAddr, "EX", this.ttlSec);
  }

  async resolve(loginId: string): Promise<string | null> {
    return this.redis.get(`${ROUTE_PREFIX}${loginId}`);
  }

  async clear(loginId: string): Promise<void> {
    await this.redis.del(`${ROUTE_PREFIX}${loginId}`);
  }

  static pickEngineAddress(addresses: string[], seed: number, counter: number): string {
    if (addresses.length === 0) {
      throw new Error("login engine pool requires at least one address");
    }
    const index = Math.abs(counter + seed) % addresses.length;
    return addresses[index]!;
  }
}

export class LoginEnginePool {
  private counter = 0;

  constructor(private addresses: string[]) {}

  get size() {
    return this.addresses.length;
  }

  pickForNewSession(seed: number): string {
    const addr = LoginRouting.pickEngineAddress(this.addresses, seed, this.counter);
    this.counter += 1;
    return addr;
  }
}
