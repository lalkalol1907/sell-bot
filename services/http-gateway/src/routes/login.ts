import { Hono } from "hono";
import type { AppConfig } from "../config.js";
import type { GrpcClients } from "../grpc/clients.js";
import type { LoginEnginePool, LoginRouting, RateLimiter } from "../redis.js";
import { createRequireLoginAuth, loginActorKey, loginStepJson } from "../middleware.js";
import type { LoginHandoff } from "../redis.js";

type LoginDeps = {
  config: AppConfig;
  grpc: GrpcClients;
  rateLimiter: RateLimiter;
  loginRouting: LoginRouting;
  loginEnginePool: LoginEnginePool;
  loginHandoff: LoginHandoff;
};

function validPhone(phone: string): boolean {
  return /^\+?\d{10,15}$/.test(phone);
}

function normalizePhone(raw: string): string {
  const trimmed = raw.trim();
  return trimmed.startsWith("+") ? trimmed : `+${trimmed}`;
}

export function createLoginRoutes(deps: LoginDeps) {
  const app = new Hono();
  const requireLoginAuth = createRequireLoginAuth(deps.loginHandoff);

  app.use("/login/*", requireLoginAuth);

  app.post("/login/session", (c) => {
    return c.json({ seller_id: c.get("sellerId") });
  });

  app.post("/login/qr/start", async (c) => {
    const sellerId = c.get("sellerId");
    const step = await startOnEngine(deps, sellerId, (client) =>
      deps.grpc.startQrLogin(client, sellerId),
    );
    return c.json(loginStepJson(step));
  });

  app.post("/login/phone/start", async (c) => {
    const sellerId = c.get("sellerId");
    const actorKey = loginActorKey(c);

    if (!(await deps.rateLimiter.allow(`phone:${actorKey}`, 5, 60_000))) {
      return c.json({ error: "rate limit exceeded" }, 429);
    }

    const body = await c.req.json<{ phone?: string }>();
    const phone = normalizePhone(body.phone ?? "");
    if (!validPhone(phone)) {
      return c.json({ error: "invalid phone" }, 400);
    }

    const step = await startOnEngine(deps, sellerId, (client) =>
      deps.grpc.startPhoneLogin(client, sellerId, phone),
    );
    return c.json(loginStepJson(step));
  });

  app.post("/login/:loginId/code", async (c) => {
    const loginId = c.req.param("loginId");
    const actorKey = loginActorKey(c);

    if (!(await deps.rateLimiter.allow(`code:${actorKey}`, 10, 60_000))) {
      return c.json({ error: "rate limit exceeded" }, 429);
    }

    const body = await c.req.json<{ code?: string }>();
    const code = (body.code ?? "").replace(/\s+/g, "");
    if (!code) {
      return c.json({ error: "code required" }, 400);
    }

    return withPinnedClient(deps, c, loginId, async (client) => {
      const step = await deps.grpc.submitCode(client, loginId, code);
      await clearRouteIfDone(deps.loginRouting, step.status, loginId);
      return c.json(loginStepJson(step));
    });
  });

  app.post("/login/:loginId/password", async (c) => {
    const loginId = c.req.param("loginId");
    const body = await c.req.json<{ password?: string }>();
    const password = body.password ?? "";
    if (!password) {
      return c.json({ error: "password required" }, 400);
    }

    return withPinnedClient(deps, c, loginId, async (client) => {
      const step = await deps.grpc.submitPassword(client, loginId, password);
      await clearRouteIfDone(deps.loginRouting, step.status, loginId);
      return c.json(loginStepJson(step));
    });
  });

  app.get("/login/:loginId/status", async (c) => {
    const loginId = c.req.param("loginId");
    return withPinnedClient(deps, c, loginId, async (client) => {
      const step = await deps.grpc.getLoginStatus(client, loginId);
      await clearRouteIfDone(deps.loginRouting, step.status, loginId);
      return c.json(loginStepJson(step));
    });
  });

  return app;
}

async function startOnEngine(
  deps: LoginDeps,
  sellerId: number,
  fn: (client: any) => Promise<{ login_id: string; status: string; message: string; worker_id: number; qr_url: string; qr_expires_at: number }>,
) {
  const engineAddr = deps.loginEnginePool.pickForNewSession(sellerId);
  const client = deps.grpc.createWorkerLoginClient(engineAddr);
  const step = await fn(client);
  if (step.login_id) {
    await deps.loginRouting.pin(step.login_id, engineAddr);
  }
  return step;
}

async function withPinnedClient(
  deps: LoginDeps,
  c: any,
  loginId: string,
  fn: (client: any) => Promise<Response>,
) {
  const engineAddr = await deps.loginRouting.resolve(loginId);
  if (!engineAddr) {
    return c.json({ error: "login session expired, start again" }, 404);
  }
  const client = deps.grpc.createWorkerLoginClient(engineAddr);
  return fn(client);
}

async function clearRouteIfDone(loginRouting: LoginRouting, status: string, loginId: string) {
  if (status === "success" || status === "error") {
    await loginRouting.clear(loginId);
  }
}
