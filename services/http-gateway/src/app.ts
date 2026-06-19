import { Hono } from "hono";
import { cors } from "hono/cors";
import { JwtSession } from "./auth/jwt.js";
import { loadConfig, type AppConfig } from "./config.js";
import { GrpcClients } from "./grpc/clients.js";
import {
  buildLoginHandoffUrl,
  getRedis,
  LoginEnginePool,
  LoginHandoff,
  LoginRouting,
  RateLimiter,
} from "./redis.js";
import { createAuthRoutes } from "./routes/auth.js";
import { createHealthRoutes } from "./routes/health.js";
import { createLoginRoutes } from "./routes/login.js";
import { createSellerRoutes } from "./routes/seller.js";
import { requireSeller } from "./middleware.js";

export function createApp(config: AppConfig = loadConfig()) {
  const grpc = new GrpcClients(config.coreGrpcAddr, config.internalGrpcToken);
  const jwt = new JwtSession(config.jwtSecret, config.jwtTtlHours);
  const redis = getRedis(config);
  const rateLimiter = new RateLimiter(redis);
  const loginRouting = new LoginRouting(redis, config.loginRouteTtlSec);
  const loginEnginePool = new LoginEnginePool(config.loginEngineAddrs);
  const loginHandoff = new LoginHandoff(redis);

  const app = new Hono();

  app.use("*", async (c, next) => {
    c.set("config", config);
    c.set("grpc", grpc);
    c.set("jwt", jwt);
    await next();
  });

  app.use(
    "/api/*",
    cors({
      origin: config.corsOrigins,
      credentials: true,
      allowMethods: ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
      allowHeaders: ["Content-Type", "X-Telegram-Init-Data", "X-Login-Handoff"],
    }),
  );

  app.route("/", createHealthRoutes(config));

  const api = new Hono();
  api.post("/login/handoff", requireSeller, async (c) => {
    const token = await loginHandoff.create(c.get("sellerId"), c.get("tgUserId"));
    const url = buildLoginHandoffUrl(config.loginWebUrl, token);
    return c.json({ token, url });
  });
  api.route("/", createAuthRoutes());
  api.route("/", createSellerRoutes());
  api.route(
    "/",
    createLoginRoutes({
      config,
      grpc,
      rateLimiter,
      loginRouting,
      loginEnginePool,
      loginHandoff,
    }),
  );

  app.route("/api/v1", api);

  return app;
}
