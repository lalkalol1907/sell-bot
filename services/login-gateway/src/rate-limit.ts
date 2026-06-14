import type { Redis } from "ioredis";

export type RateLimitStore = {
  increment(key: string, windowMs: number): Promise<number>;
};

export class RedisRateLimitStore implements RateLimitStore {
  constructor(private readonly redis: Redis) {}

  async increment(key: string, windowMs: number): Promise<number> {
    const redisKey = `rl:${key}`;
    const count = await this.redis.incr(redisKey);
    if (count === 1) {
      await this.redis.pexpire(redisKey, windowMs);
    }
    return count;
  }
}

export async function checkRateLimit(
  store: RateLimitStore,
  key: string,
  limit: number,
  windowMs: number,
): Promise<boolean> {
  const count = await store.increment(key, windowMs);
  return count <= limit;
}
