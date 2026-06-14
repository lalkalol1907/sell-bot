import type { Redis } from "ioredis";

export function pickEngineAddress(
  addresses: readonly string[],
  seed: number,
  counter: number,
): string {
  if (addresses.length === 0) {
    throw new Error("login engine pool requires at least one address");
  }
  const index = Math.abs((counter + seed) % addresses.length);
  return addresses[index]!;
}

const ROUTE_PREFIX = "login:route:";

export async function pinLoginRoute(
  redis: Redis,
  loginId: string,
  engineAddr: string,
  ttlSec: number,
): Promise<void> {
  await redis.set(`${ROUTE_PREFIX}${loginId}`, engineAddr, "EX", ttlSec);
}

export async function resolveLoginRoute(redis: Redis, loginId: string): Promise<string | null> {
  return redis.get(`${ROUTE_PREFIX}${loginId}`);
}

export async function clearLoginRoute(redis: Redis, loginId: string): Promise<void> {
  await redis.del(`${ROUTE_PREFIX}${loginId}`);
}
