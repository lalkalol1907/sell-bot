import { Hono } from "hono";
import type { AppConfig } from "../config.js";

export function createHealthRoutes(config: AppConfig) {
  const app = new Hono();

  app.get("/health", (c) =>
    c.json({ status: "ok", login_engines: config.loginEngineAddrs.length }),
  );

  app.get("/metrics", (c) =>
    c.text(
      "# HELP http_gateway_up HTTP gateway is running\n# TYPE http_gateway_up gauge\nhttp_gateway_up 1\n",
      200,
      { "Content-Type": "text/plain; version=0.0.4" },
    ),
  );

  return app;
}
