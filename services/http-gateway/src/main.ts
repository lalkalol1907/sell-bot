import { createApp } from "./app.js";
import { loadConfig } from "./config.js";

const config = loadConfig();
const app = createApp(config);

const server = Bun.serve({
  port: config.port,
  hostname: "0.0.0.0",
  fetch: app.fetch,
});

console.log(`http-gateway listening on :${config.port}`);

process.on("SIGINT", () => {
  server.stop(true);
  process.exit(0);
});

process.on("SIGTERM", () => {
  server.stop(true);
  process.exit(0);
});
