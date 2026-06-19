import { describe, expect, test } from "bun:test";
import { Hono } from "hono";
import type { Context, Next } from "hono";

describe("api route middleware scoping", () => {
  test("login routes are not blocked by seller JWT middleware", async () => {
    const requireSeller = async (c: Context) => c.json({ error: "unauthorized" }, 401);

    const requireInitData = async (c: Context, next: Next) => {
      const initData = c.req.header("X-Telegram-Init-Data") ?? "";
      if (!initData) {
        return c.json({ error: "invalid init data" }, 401);
      }
      await next();
    };

    const seller = new Hono();
    seller.use("/seller/*", requireSeller);
    seller.get("/seller/stats", (c) => c.json({ scope: "seller" }));

    const login = new Hono();
    login.use("/login/*", requireInitData);
    login.post("/login/session", (c) => c.json({ scope: "login" }));
    login.post("/login/qr/start", (c) => c.json({ scope: "qr" }));

    const api = new Hono();
    api.route("/", seller);
    api.route("/", login);

    const app = new Hono();
    app.route("/api/v1", api);

    const blocked = await app.request("/api/v1/login/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    expect(blocked.status).toBe(401);
    expect(await blocked.json()).toEqual({ error: "invalid init data" });

    const ok = await app.request("/api/v1/login/qr/start", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Telegram-Init-Data": "test",
      },
    });
    expect(ok.status).toBe(200);
    expect(await ok.json()).toEqual({ scope: "qr" });
  });
});
