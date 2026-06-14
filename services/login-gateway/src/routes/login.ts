import type { LoginStep } from "../grpc/client.js";
import {
  createCatalogClient,
  createLoginClient,
  getLoginStatus,
  getSellerByTgId,
  startPhoneLogin,
  startQRLogin,
  submitCode,
  submitPassword,
} from "../grpc/client.js";
import { getInitDataFromRequest, parseInitData } from "../middleware/auth.js";
import { checkRateLimit } from "../rate-limit.js";

export type GatewayConfig = {
  botToken: string;
  coreAddr: string;
  loginAddr: string;
  internalToken: string;
};

export type GatewayDeps = {
  catalogClient: ReturnType<typeof createCatalogClient>;
  loginClient: ReturnType<typeof createLoginClient>;
  config: GatewayConfig;
};

export function createGatewayDeps(config: GatewayConfig): GatewayDeps {
  return {
    catalogClient: createCatalogClient(config.coreAddr),
    loginClient: createLoginClient(config.loginAddr),
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
    const step = await startQRLogin(
      deps.loginClient,
      resolved.sellerId,
      deps.config.internalToken,
    );
    return json(toResponse(step));
  }

  if (req.method === "POST" && pathname === "/api/login/phone/start") {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;
    const initData = getInitDataFromRequest(req);
    const user = parseInitData(initData, deps.config.botToken);
    if (!user) return unauthorized();

    if (!checkRateLimit(`phone:${user.id}`, 5, 60_000)) {
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

    const step = await startPhoneLogin(
      deps.loginClient,
      resolved.sellerId,
      phone.startsWith("+") ? phone : `+${phone}`,
      deps.config.internalToken,
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
    if (!checkRateLimit(`code:${user.id}`, 10, 60_000)) {
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

    const step = await submitCode(
      deps.loginClient,
      codeMatch[1],
      code,
      deps.config.internalToken,
    );
    return json(toResponse(step));
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

    const step = await submitPassword(
      deps.loginClient,
      passwordMatch[1],
      body.password,
      deps.config.internalToken,
    );
    return json(toResponse(step));
  }

  const statusMatch = pathname.match(/^\/api\/login\/([^/]+)\/status$/);
  if (req.method === "GET" && statusMatch) {
    const resolved = await resolveSeller(deps, req);
    if (resolved instanceof Response) return resolved;

    const step = await getLoginStatus(
      deps.loginClient,
      statusMatch[1],
      deps.config.internalToken,
    );
    return json(toResponse(step));
  }

  return null;
}
