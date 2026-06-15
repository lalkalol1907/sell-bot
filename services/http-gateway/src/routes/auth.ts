import { Hono } from "hono";
import { deleteCookie, setCookie } from "hono/cookie";
import { validateLoginWidget } from "../auth/telegram.js";
import { JWT_COOKIE_NAME } from "../auth/jwt.js";
import { requireSeller, sellerJson } from "../middleware.js";

export function createAuthRoutes() {
  const app = new Hono();

  app.post("/auth/telegram", async (c) => {
    const config = c.get("config");
    const grpc = c.get("grpc");
    const jwt = c.get("jwt");

    const body = await c.req.json<Record<string, string | number>>();
    const user = validateLoginWidget(body, config.botToken);
    if (!user) {
      return c.json({ error: "invalid telegram auth" }, 401);
    }

    const seller = await grpc.getSellerByTgId(user.id);
    if (!seller?.id) {
      return c.json({ error: "seller not found, run /start in bot first" }, 401);
    }

    const token = await jwt.encode(seller.id, user.id);
    setCookie(c, JWT_COOKIE_NAME, token, {
      httpOnly: true,
      secure: config.isProduction,
      sameSite: "Lax",
      path: "/",
    });

    return c.json(sellerJson(seller));
  });

  app.post("/auth/logout", (c) => {
    deleteCookie(c, JWT_COOKIE_NAME, { path: "/" });
    return c.body(null, 204);
  });

  app.get("/auth/me", requireSeller, async (c) => {
    const grpc = c.get("grpc");
    const sellerId = c.get("sellerId");

    try {
      const seller = await grpc.getSeller(sellerId);
      return c.json(sellerJson(seller));
    } catch {
      return c.json({ error: "unauthorized" }, 401);
    }
  });

  return app;
}
