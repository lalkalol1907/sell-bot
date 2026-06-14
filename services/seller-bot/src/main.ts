import { loadConfig } from "./config.js";
import { createBot } from "./index.js";
import type { Bot } from "grammy";
import { registerWebhook, startHttpServer, startPolling } from "./transport.js";
import type { BotContext } from "./types.js";

let shuttingDown = false;

async function shutdown(
  server: ReturnType<typeof Bun.serve>,
  bot: Bot<BotContext>,
  transport: "polling" | "webhook",
  signal: string,
) {
  if (shuttingDown) return;
  shuttingDown = true;
  console.log(`shutting down (${signal})...`);
  server.stop(true);
  if (transport === "polling") {
    await bot.stop();
  }
  process.exit(0);
}

async function main() {
  const config = loadConfig();
  const bot = await createBot(
    config.token,
    config.coreAddr,
    config.natsUrl,
    config.redisUrl,
    config.loginWebUrl,
  );

  const server = startHttpServer(bot, config);

  if (config.transport === "webhook") {
    if (config.webhookRegisterOnStartup) {
      await registerWebhook(bot, config);
    } else {
      console.log("WEBHOOK_REGISTER_ON_STARTUP=false, skipping setWebhook");
    }
    console.log("webhook mode: horizontally scalable behind load balancer");
  } else {
    console.warn("polling mode: run a single seller-bot replica");
    await startPolling(bot);
  }

  process.on("SIGINT", () => void shutdown(server, bot, config.transport, "SIGINT"));
  process.on("SIGTERM", () => void shutdown(server, bot, config.transport, "SIGTERM"));
}

main().catch((err) => {
  console.error("seller-bot failed to start", err);
  process.exit(1);
});
