import path from "node:path";
import { Redis } from "ioredis";
import { loadGatewayConfig } from "./config.js";
import { createGatewayDeps, handleLoginRoute } from "./routes/login.js";
import { RedisRateLimitStore } from "./rate-limit.js";

const config = loadGatewayConfig();
const redis = new Redis(config.redisUrl);
const deps = createGatewayDeps(config, redis, new RedisRateLimitStore(redis));

const staticRoot = path.resolve(import.meta.dir, "../web/dist");

async function serveStatic(pathname: string): Promise<Response | null> {
  const safePath = pathname === "/" ? "/index.html" : pathname;
  const filePath = path.join(staticRoot, safePath);
  if (!filePath.startsWith(staticRoot)) return null;
  const file = Bun.file(filePath);
  if (await file.exists()) {
    return new Response(file);
  }
  const index = Bun.file(path.join(staticRoot, "index.html"));
  if (await index.exists()) {
    return new Response(index, { headers: { "Content-Type": "text/html" } });
  }
  return null;
}

const server = Bun.serve({
  port: Number(process.env.PORT ?? "8080"),
  hostname: "0.0.0.0",
  async fetch(req) {
    const url = new URL(req.url);

    if (req.method === "GET" && url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok", login_engines: config.loginEngineAddrs.length }), {
        headers: { "Content-Type": "application/json" },
      });
    }

    if (req.method === "GET" && url.pathname === "/metrics") {
      return new Response(
        "# HELP login_gateway_up Login gateway is running\n# TYPE login_gateway_up gauge\nlogin_gateway_up 1\n",
        { headers: { "Content-Type": "text/plain; version=0.0.4" } },
      );
    }

    if (url.pathname.startsWith("/api/")) {
      try {
        const apiResponse = await handleLoginRoute(deps, req, url.pathname);
        if (apiResponse) return apiResponse;
        return new Response(JSON.stringify({ error: "not found" }), { status: 404 });
      } catch (err) {
        console.error("api error", err);
        return new Response(JSON.stringify({ error: "internal error" }), { status: 500 });
      }
    }

    const staticResponse = await serveStatic(url.pathname);
    if (staticResponse) return staticResponse;

    return new Response("Not Found", { status: 404 });
  },
});

console.log(
  `login-gateway listening on :${server.port} (engines=${config.loginEngineAddrs.length}, redis=${config.redisUrl})`,
);

process.on("SIGINT", () => {
  redis.disconnect();
  server.stop(true);
  process.exit(0);
});

process.on("SIGTERM", () => {
  redis.disconnect();
  server.stop(true);
  process.exit(0);
});
