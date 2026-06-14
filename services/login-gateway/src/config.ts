export type GatewayConfig = {
  botToken: string;
  coreAddr: string;
  loginEngineAddrs: string[];
  internalToken: string;
  redisUrl: string;
  loginRouteTtlSec: number;
};

function parseLoginAddrs(raw: string | undefined): string[] {
  const value = raw?.trim();
  if (!value) {
    return ["worker-engine:50053"];
  }
  const addrs = value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
  if (addrs.length === 0) {
    throw new Error("WORKER_LOGIN_GRPC_ADDR must contain at least one address");
  }
  return addrs;
}

export function loadGatewayConfig(env: Record<string, string | undefined> = process.env): GatewayConfig {
  const botToken = env.BOT_TOKEN?.trim();
  if (!botToken) {
    throw new Error("BOT_TOKEN is required");
  }

  const redisUrl = env.REDIS_URL?.trim();
  if (!redisUrl) {
    throw new Error("REDIS_URL is required");
  }

  return {
    botToken,
    coreAddr: env.CORE_GRPC_ADDR ?? "core:50051",
    loginEngineAddrs: parseLoginAddrs(env.WORKER_LOGIN_GRPC_ADDR),
    internalToken: env.INTERNAL_GRPC_TOKEN ?? "",
    redisUrl,
    loginRouteTtlSec: Number(env.LOGIN_ROUTE_TTL_SEC ?? "600"),
  };
}
