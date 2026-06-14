import type { LoginStep } from "../grpc/client.js";
import {
  createCatalogClient,
  getLoginStatus,
  getSellerByTgId,
  startPhoneLogin,
  startQRLogin,
  submitCode,
  submitPassword,
} from "../grpc/client.js";
import {
  clearLoginRoute,
  pinLoginRoute,
  resolveLoginRoute,
} from "../login-routing.js";
import { LoginEnginePool } from "../grpc/login-pool.js";
import { getInitDataFromRequest, parseInitData } from "../middleware/auth.js";
import { checkRateLimit, type RateLimitStore } from "../rate-limit.js";
import type { GatewayConfig } from "../config.js";
import type { Redis } from "ioredis";

export type GatewayDeps = {
  catalogClient: ReturnType<typeof createCatalogClient>;
  loginPool: LoginEnginePool;
  redis: Redis;
  rateLimit: RateLimitStore;
  config: GatewayConfig;
};

export function createGatewayDeps(
  config: GatewayConfig,
  redis: Redis,
  rateLimit: RateLimitStore,
): GatewayDeps {
  return {
    catalogClient: createCatalogClient(config.coreAddr),
    loginPool: new LoginEnginePool(config.loginEngineAddrs),
    redis,
    rateLimit,
    config,
  };
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function badRequest(message: string): Response {
  return json({ error: message }, 400);
}

function unauthorized(message = "unauthorized"): Response {
  return json({ error: message }, 401);
}

async function resolveSeller(
  deps: GatewayDeps,
  req: Request,
): Promise<{ sellerId: number } | Response> {
  const initData = getInitDataFromRequest(req);
  const user = parseInitData(initData, deps.config.botToken);
  if (!user) return unauthorized("invalid init data");

  const seller = await getSellerByTgId(deps.catalogClient, user.id);
  if (!seller?.id) {
    return unauthorized("seller not found, run /start in bot first");
  }
  return { sellerId: Number(seller.id) };
}

function toResponse(step: LoginStep) {
  return {
    login_id: step.login_id,
    status: step.status,
    message: step.message,
    worker_id: Number(step.worker_id) || 0,
    qr_url: step.qr_url ?? "",
    qr_expires_at: Number(step.qr_expires_at) || 0,
  };
}

async function startLoginOnEngine(
  deps: GatewayDeps,
  sellerId: number,
  startFn: (client: ReturnType<LoginEnginePool["clientFor"]>) => Promise<LoginStep>,
): Promise<LoginStep> {
  const engineAddr = deps.loginPool.pickForNewSession(sellerId);
  const client = deps.loginPool.clientFor(engineAddr);
  const step = await startFn(client);
  if (step.login_id) {
    await pinLoginRoute(deps.redis, step.login_id, engineAddr, deps.config.loginRouteTtlSec);
  }
  return step;
}

async function withPinnedLoginClient<T>(
  deps: GatewayDeps,
  loginId: string,
  fn: (client: ReturnType<LoginEnginePool["clientFor"]>) => Promise<T>,
): Promise<T> {
  const engineAddr = await resolveLoginRoute(deps.redis, loginId);
  if (!engineAddr) {
    throw new LoginRouteNotFoundError(loginId);
  }
  return fn(deps.loginPool.clientFor(engineAddr));
}

export class LoginRouteNotFoundError extends Error {
  constructor(loginId: string) {
    super(`login route not found for ${loginId}`);
    this.name = "LoginRouteNotFoundError";
  }
}

export async function handleLoginRoute(
  deps: GatewayDeps,
  req: Request,
  pathname: string,
): Promise<Response | null> {
  if (req.method === "POST" && pathname === "/api/login/session") {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;
    return json({ seller_id: resolved.sellerId });
  }

  if (req.method === "POST" && pathname === "/api/login/qr/start") {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;
    const step = await startLoginOnEngine(deps, resolved.sellerId, (client) =>
      startQRLogin(client, resolved.sellerId, deps.config.internalToken),
    );
    return json(toResponse(step));
  }

  if (req.method === "POST" && pathname === "/api/login/phone/start") {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;
    const initData = getInitDataFromRequest(req);
    const user = parseInitData(initData, deps.config.botToken);
    if (!user) return unauthorized();

    if (!(await checkRateLimit(deps.rateLimit, `phone:${user.id}`, 5, 60_000))) {
      return json({ error: "rate limit exceeded" }, 429);
    }

    let body: { phone?: string };
    try {
      body = await req.json();
    } catch {
      return badRequest("invalid json");
    }
    const phone = body.phone?.trim();
    if (!phone || !/^\+?\d{10,15}$/.test(phone.replace(/\s/g, ""))) {
      return badRequest("invalid phone");
    }

    const step = await startLoginOnEngine(deps, resolved.sellerId, (client) =>
      startPhoneLogin(
        client,
        resolved.sellerId,
        phone.startsWith("+") ? phone : `+${phone}`,
        deps.config.internalToken,
      ),
    );
    return json(toResponse(step));
  }

  const codeMatch = pathname.match(/^\/api\/login\/([^/]+)\/code$/);
  if (req.method === "POST" && codeMatch) {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;
    const initData = getInitDataFromRequest(req);
    const user = parseInitData(initData, deps.config.botToken);
    if (!user) return unauthorized();
    if (!(await checkRateLimit(deps.rateLimit, `code:${user.id}`, 10, 60_000))) {
      return json({ error: "rate limit exceeded" }, 429);
    }

    let body: { code?: string };
    try {
      body = await req.json();
    } catch {
      return badRequest("invalid json");
    }
    const code = body.code?.replace(/\s/g, "");
    if (!code) return badRequest("code required");

    try {
      const step = await withPinnedLoginClient(deps, codeMatch[1], (client) =>
        submitCode(client, codeMatch[1], code, deps.config.internalToken),
      );
      if (step.status === "success") {
        await clearLoginRoute(deps.redis, codeMatch[1]);
      }
      return json(toResponse(step));
    } catch (err) {
      if (err instanceof LoginRouteNotFoundError) {
        return json({ error: "login session expired, start again" }, 404);
      }
      throw err;
    }
  }

  const passwordMatch = pathname.match(/^\/api\/login\/([^/]+)\/password$/);
  if (req.method === "POST" && passwordMatch) {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;

    let body: { password?: string };
    try {
      body = await req.json();
    } catch {
      return badRequest("invalid json");
    }
    if (!body.password) return badRequest("password required");

    try {
      const step = await withPinnedLoginClient(deps, passwordMatch[1], (client) =>
        submitPassword(client, passwordMatch[1], body.password!, deps.config.internalToken),
      );
      if (step.status === "success") {
        await clearLoginRoute(deps.redis, passwordMatch[1]);
      }
      return json(toResponse(step));
    } catch (err) {
      if (err instanceof LoginRouteNotFoundError) {
        return json({ error: "login session expired, start again" }, 404);
      }
      throw err;
    }
  }

  const statusMatch = pathname.match(/^\/api\/login\/([^/]+)\/status$/);
  if (req.method === "GET" && statusMatch) {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;

    try {
      const step = await withPinnedLoginClient(deps, statusMatch[1], (client) =>
        getLoginStatus(client, statusMatch[1], deps.config.internalToken),
      );
      if (step.status === "success" || step.status === "error") {
        await clearLoginRoute(deps.redis, statusMatch[1]);
      }
      return json(toResponse(step));
    } catch (err) {
      if (err instanceof LoginRouteNotFoundError) {
        return json({ error: "login session expired, start again" }, 404);
      }
      throw err;
    }
  }

  return null;
}
