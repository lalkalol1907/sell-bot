import { Redis } from "ioredis";
import type { AppConfig } from "./config.js";

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
