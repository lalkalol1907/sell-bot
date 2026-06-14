import path from "node:path";
import { createGatewayDeps, handleLoginRoute } from "./routes/login.js";

const port = Number(process.env.PORT ?? "8080");
const botToken = process.env.BOT_TOKEN ?? "";
const coreAddr = process.env.CORE_GRPC_ADDR ?? "core:50051";
const loginAddr = process.env.WORKER_LOGIN_GRPC_ADDR ?? "worker-engine:50053";
const internalToken = process.env.INTERNAL_GRPC_TOKEN ?? "";

if (!botToken) {
  console.error("BOT_TOKEN is required");
  process.exit(1);
}

const deps = createGatewayDeps({
  botToken,
  coreAddr,
  loginAddr,
  internalToken,
});

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
  port,
  async fetch(req) {
    const url = new URL(req.url);

    if (req.method === "GET" && url.pathname === "/health") {
      return new Response(JSON.stringify({ status: "ok" }), {
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

console.log(`login-gateway listening on :${server.port}`);
