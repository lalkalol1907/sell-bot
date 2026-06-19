import type { Context, Next } from "hono";
import { getCookie } from "hono/cookie";
import type { AppConfig } from "./config.js";
import { JwtSession, JWT_COOKIE_NAME } from "./auth/jwt.js";
import type { GrpcClients } from "./grpc/clients.js";
import { validateInitData, type TelegramUser } from "./auth/telegram.js";
import type { LoginHandoff } from "./redis.js";

export async function requireSeller(c: Context, next: Next) {
  const jwt = c.get("jwt") as JwtSession;
  const token = getCookie(c, JWT_COOKIE_NAME);
  const session = await jwt.decode(token);
  if (!session?.seller_id) {
    return c.json({ error: "unauthorized" }, 401);
  }
  c.set("sellerId", session.seller_id);
  c.set("tgUserId", session.tg_user_id);
  await next();
}

export function createRequireLoginAuth(handoff: LoginHandoff) {
  return async function requireLoginAuth(c: Context, next: Next) {
    const config = c.get("config") as AppConfig;
    const grpc = c.get("grpc") as GrpcClients;

    const initData =
      c.req.header("X-Telegram-Init-Data") ?? c.req.header("x-telegram-init-data") ?? "";
    const initUser = validateInitData(initData, config.botToken);
    if (initUser) {
      const seller = await grpc.getSellerByTgId(initUser.id);
      if (!seller?.id) {
        return c.json({ error: "seller not found, run /start in bot first" }, 401);
      }
      c.set("initUser", initUser);
      c.set("sellerId", seller.id);
      c.set("tgUserId", initUser.id);
      await next();
      return;
    }

    const handoffToken =
      c.req.header("X-Login-Handoff") ?? c.req.header("x-login-handoff") ?? c.req.query("handoff") ?? "";
    const payload = await handoff.resolve(handoffToken);
    if (payload) {
      c.set("sellerId", payload.seller_id);
      c.set("tgUserId", payload.tg_user_id);
      await next();
      return;
    }

    return c.json(
      {
        error:
          "open from Telegram or use the Add worker button in the dashboard",
      },
      401,
    );
  };
}

export function loginActorKey(c: Context): string {
  const initUser = c.get("initUser") as TelegramUser | undefined;
  if (initUser?.id) return String(initUser.id);
  const tgUserId = c.get("tgUserId") as number | undefined;
  if (tgUserId) return String(tgUserId);
  return `seller:${c.get("sellerId")}`;
}

export function sellerJson(seller: {
  id: number;
  tg_user_id: number;
  username: string;
  full_name: string;
  sensitivity: string;
  plan: string;
}) {
  return {
    id: seller.id,
    tg_user_id: seller.tg_user_id,
    username: seller.username,
    full_name: seller.full_name,
    sensitivity: seller.sensitivity,
    plan: seller.plan,
  };
}

export function loginStepJson(step: {
  login_id: string;
  status: string;
  message: string;
  worker_id: number;
  qr_url: string;
  qr_expires_at: number;
}) {
  return {
    login_id: step.login_id,
    status: step.status,
    message: step.message,
    worker_id: step.worker_id,
    qr_url: step.qr_url,
    qr_expires_at: step.qr_expires_at,
  };
}

declare module "hono" {
  interface ContextVariableMap {
    config: AppConfig;
    grpc: GrpcClients;
    jwt: JwtSession;
    sellerId: number;
    tgUserId: number;
    initUser: TelegramUser;
  }
}
