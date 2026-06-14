import { webhookCallback } from "grammy";
import type { Bot } from "grammy";
import type { AppConfig } from "./config.js";
import { healthResponse, metricsResponse } from "./metrics.js";
import type { BotContext } from "./types.js";

export async function registerWebhook(bot: Bot<BotContext>, config: AppConfig): Promise<void> {
  if (!config.webhookUrl || !config.webhookSecret) {
    throw new Error("webhook config is incomplete");
  }

  await bot.api.setWebhook(config.webhookUrl, {
    secret_token: config.webhookSecret,
    drop_pending_updates: false,
    allowed_updates: ["message", "callback_query"],
  });
  console.log(`webhook registered: ${config.webhookUrl}`);
}

export async function startPolling(bot: Bot<BotContext>): Promise<void> {
  await bot.api.deleteWebhook({ drop_pending_updates: false });
  bot.start({
    onStart: (info) => {
      console.log(`polling started as @${info.username}`);
    },
  });
}

export function startHttpServer(bot: Bot<BotContext>, config: AppConfig) {
  const webhookHandler =
    config.transport === "webhook" && config.webhookSecret
      ? webhookCallback(bot, "bun", { secretToken: config.webhookSecret })
      : null;

  const server = Bun.serve({
    port: config.httpPort,
    hostname: "0.0.0.0",
    async fetch(req) {
      const url = new URL(req.url);

      if (url.pathname === "/health") {
        return healthResponse();
      }

      if (url.pathname === "/metrics") {
        return metricsResponse();
      }

      if (
        config.transport === "webhook" &&
        req.method === "POST" &&
        url.pathname === config.webhookPath &&
        webhookHandler
      ) {
        return webhookHandler(req);
      }

      return new Response("not found", { status: 404 });
    },
  });

  console.log(
    `http server on :${config.httpPort} (transport=${config.transport}, webhook_path=${config.webhookPath})`,
  );
  return server;
}
