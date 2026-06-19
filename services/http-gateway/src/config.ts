export type AppConfig = {
  port: number;
  botToken: string;
  coreGrpcAddr: string;
  loginEngineAddrs: string[];
  internalGrpcToken: string;
  redisUrl: string;
  natsUrl: string;
  loginRouteTtlSec: number;
  jwtSecret: string;
  jwtTtlHours: number;
  corsOrigins: string[];
  loginWebUrl: string;
  isProduction: boolean;
};

export function loadConfig(): AppConfig {
  const loginEngineAddrs = (process.env.WORKER_LOGIN_GRPC_ADDR ?? "worker-engine:50053")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  if (loginEngineAddrs.length === 0) {
    throw new Error("WORKER_LOGIN_GRPC_ADDR must contain at least one address");
  }

  const corsOrigins = (process.env.CORS_ORIGINS ?? "http://localhost:8081,http://localhost:8082")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return {
    port: Number(process.env.PORT ?? "3000"),
    botToken: process.env.BOT_TOKEN ?? "",
    coreGrpcAddr: process.env.CORE_GRPC_ADDR ?? "core:50051",
    loginEngineAddrs,
    internalGrpcToken: process.env.INTERNAL_GRPC_TOKEN ?? "",
    redisUrl: process.env.REDIS_URL ?? "redis://redis:6379/0",
    natsUrl: process.env.NATS_URL ?? "nats://nats:4222",
    loginRouteTtlSec: Number(process.env.LOGIN_ROUTE_TTL_SEC ?? "600"),
    jwtSecret: process.env.JWT_SECRET ?? "dev-jwt-secret-change-me",
    jwtTtlHours: Number(process.env.JWT_TTL_HOURS ?? "168"),
    corsOrigins,
    loginWebUrl: process.env.LOGIN_WEB_URL ?? "http://localhost:8081/miniapp/",
    isProduction: (process.env.NODE_ENV ?? process.env.RAILS_ENV ?? "development") === "production",
  };
}
