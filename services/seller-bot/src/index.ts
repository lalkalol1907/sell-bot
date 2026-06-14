import { Bot, session } from "grammy";
import { RedisAdapter } from "@grammyjs/storage-redis";
import { Redis } from "ioredis";
import {
  createCatalogClient,
  createLeadsClient,
  createWorkersClient,
  createWorkerLoginClient,
  updateLeadStatus,
} from "./grpc/client.js";
import { subscribeLeadCreated } from "./events/lead-created.js";
import { handleCatalogAdd, handleCatalogFlow, handleStart, mainMenu } from "./handlers/catalog.js";
import { handleCatalogList } from "./handlers/catalog-list.js";
import { handleLeadsList } from "./handlers/leads.js";
import { handleStats } from "./handlers/stats.js";
import {
  handleChatToggle,
  handleWorkerChats,
  handleWorkersList,
} from "./handlers/workers.js";
import { handleWorkerAddFlow, handleWorkerAddStart } from "./handlers/worker-add.js";
import type { BotContext, SessionData } from "./types.js";

export type { SessionData, BotContext };

export async function createBot(
  token: string,
  coreAddr: string,
  natsUrl: string,
  redisUrl: string,
  workerLoginAddr: string,
  internalGrpcToken = "",
) {
  const bot = new Bot<BotContext>(token);
  const redis = new Redis(redisUrl);

  bot.use(
    session({
      initial: (): SessionData => ({}),
      storage: new RedisAdapter({ instance: redis, ttl: 86400 }),
    }),
  );

  const catalogClient = createCatalogClient(coreAddr);
  const leadsClient = createLeadsClient(coreAddr);
  const workersClient = createWorkersClient(coreAddr);
  const loginClient = createWorkerLoginClient(workerLoginAddr);

  bot.command("start", async (ctx) => {
    await handleStart(ctx, catalogClient);
  });

  bot.hears("Каталог", async (ctx) => {
    await handleCatalogList(ctx, catalogClient);
  });

  bot.command("add_product", handleCatalogAdd);
  bot.hears("Добавить товар", handleCatalogAdd);

  bot.hears("Лиды", async (ctx) => {
    await handleLeadsList(ctx, leadsClient);
  });

  bot.hears("Статистика", async (ctx) => {
    await handleStats(ctx, leadsClient);
  });

  bot.hears("Воркеры", async (ctx) => {
    await handleWorkersList(ctx, workersClient);
  });

  bot.command("add_worker", handleWorkerAddStart);
  bot.hears("Добавить воркера", handleWorkerAddStart);

  bot.on("message:text", async (ctx) => {
    if (ctx.session.flow?.startsWith("add_product")) {
      await handleCatalogFlow(ctx, catalogClient);
      return;
    }
    if (ctx.session.flow?.startsWith("worker_add")) {
      await handleWorkerAddFlow(ctx, loginClient, internalGrpcToken);
      return;
    }
  });

  bot.on("callback_query:data", async (ctx) => {
    const data = ctx.callbackQuery.data;

    if (data.startsWith("lead:")) {
      const [, status, leadIdRaw] = data.split(":");
      const leadId = Number(leadIdRaw);
      const sellerId = ctx.session.sellerId;
      if (!sellerId || !leadId) {
        await ctx.answerCallbackQuery({ text: "Сессия устарела, /start" });
        return;
      }
      try {
        await updateLeadStatus(leadsClient, leadId, sellerId, status);
        await ctx.answerCallbackQuery({ text: `Лид #${leadId} → ${status}` });
        await ctx.editMessageReplyMarkup({ reply_markup: undefined });
      } catch (err) {
        console.error("UpdateLeadStatus failed", err);
        await ctx.answerCallbackQuery({ text: "Ошибка обновления лида" });
      }
      return;
    }

    if (data === "worker:add") {
      await ctx.answerCallbackQuery();
      await handleWorkerAddStart(ctx);
      return;
    }

    if (data.startsWith("worker:chats:")) {
      const workerId = Number(data.split(":")[2]);
      await ctx.answerCallbackQuery();
      await handleWorkerChats(ctx, workersClient, workerId);
      return;
    }

    if (data.startsWith("chat:toggle:")) {
      const parts = data.split(":");
      const workerId = Number(parts[2]);
      const chatId = Number(parts[3]);
      await handleChatToggle(ctx, workersClient, workerId, chatId);
    }
  });

  await subscribeLeadCreated(bot, natsUrl);

  return bot;
}
