import { Bot, session } from "grammy";
import { RedisAdapter } from "@grammyjs/storage-redis";
import { Redis } from "ioredis";
import {
  createCatalogClient,
  createLeadsClient,
  createWorkersClient,
  deleteProduct,
  getSeller,
  listProducts,
  toggleProduct,
  updateLeadStatus,
} from "./grpc/client.js";
import { subscribeLeadCreated } from "./events/lead-created.js";
import { subscribeWorkerStatus } from "./events/worker-status.js";
import { handleCatalogAdd, handleCatalogFlow, handleStart, mainMenu } from "./handlers/catalog.js";
import { handleCatalogList } from "./handlers/catalog-list.js";
import {
  handleProductEditFlow,
  handleProductEditStart,
  handleSensitivityMenu,
  handleSensitivitySet,
} from "./handlers/catalog-manage.js";
import { handleLeadsList } from "./handlers/leads.js";
import { handleStats } from "./handlers/stats.js";
import {
  handleChatToggle,
  handleWorkerChats,
  handleWorkersList,
} from "./handlers/workers.js";
import { handleWorkerAddResult, handleWorkerAddStart } from "./handlers/worker-add.js";
import type { BotContext, SessionData } from "./types.js";

export type { SessionData, BotContext };

export async function createBot(
  token: string,
  coreAddr: string,
  natsUrl: string,
  redisUrl: string,
  loginWebUrl: string,
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

  bot.command("add_worker", async (ctx) => {
    await handleWorkerAddStart(ctx, loginWebUrl);
  });
  bot.hears("Добавить воркера", async (ctx) => {
    await handleWorkerAddStart(ctx, loginWebUrl);
  });

  bot.on("message:web_app_data", async (ctx) => {
    const data = ctx.message?.web_app_data?.data;
    if (data) {
      await handleWorkerAddResult(ctx, data);
    }
  });

  bot.on("message:text", async (ctx) => {
    if (ctx.session.flow?.startsWith("add_product")) {
      await handleCatalogFlow(ctx, catalogClient);
      return;
    }
    if (ctx.session.flow?.startsWith("edit_product")) {
      await handleProductEditFlow(ctx, catalogClient);
    }
  });

  bot.on("callback_query:data", async (ctx) => {
    const data = ctx.callbackQuery.data;
    const sellerId = ctx.session.sellerId;

    if (data.startsWith("lead:")) {
      const [, status, leadIdRaw] = data.split(":");
      const leadId = Number(leadIdRaw);
      if (!sellerId || !leadId) {
        await ctx.answerCallbackQuery({ text: "Сессия устарела, /start" });
        return;
      }
      try {
        await updateLeadStatus(leadsClient, leadId, sellerId, status);
        const hint = status === "spam" ? " (обучение на спаме)" : "";
        await ctx.answerCallbackQuery({ text: `Лид #${leadId} → ${status}${hint}` });
        await ctx.editMessageReplyMarkup({ reply_markup: undefined });
      } catch (err) {
        console.error("UpdateLeadStatus failed", err);
        await ctx.answerCallbackQuery({ text: "Ошибка обновления лида" });
      }
      return;
    }

    if (data === "catalog:add") {
      await ctx.answerCallbackQuery();
      await handleCatalogAdd(ctx);
      return;
    }

    if (data === "catalog:sensitivity") {
      await ctx.answerCallbackQuery();
      await handleSensitivityMenu(ctx, catalogClient);
      return;
    }

    if (data === "catalog:back") {
      await ctx.answerCallbackQuery();
      await ctx.editMessageReplyMarkup({ reply_markup: undefined });
      return;
    }

    if (data.startsWith("sensitivity:")) {
      const value = data.split(":")[1];
      await handleSensitivitySet(ctx, catalogClient, value);
      return;
    }

    if (data.startsWith("catalog:edit:")) {
      const productId = Number(data.split(":")[2]);
      await handleProductEditStart(ctx, productId);
      return;
    }

    if (data.startsWith("catalog:toggle:")) {
      const productId = Number(data.split(":")[2]);
      if (!sellerId) {
        await ctx.answerCallbackQuery({ text: "Сессия устарела" });
        return;
      }
      const products = await listProducts(catalogClient, sellerId);
      const product = products.find((p) => Number(p.id) === productId);
      if (!product) {
        await ctx.answerCallbackQuery({ text: "Товар не найден" });
        return;
      }
      await toggleProduct(catalogClient, product, sellerId);
      await ctx.answerCallbackQuery({ text: product.is_active ? "Товар на паузе" : "Товар включён" });
      return;
    }

    if (data.startsWith("catalog:delete:")) {
      const productId = Number(data.split(":")[2]);
      if (!sellerId) {
        await ctx.answerCallbackQuery({ text: "Сессия устарела" });
        return;
      }
      await deleteProduct(catalogClient, productId, sellerId);
      await ctx.answerCallbackQuery({ text: "Товар удалён" });
      await ctx.deleteMessage();
      return;
    }

    if (data === "worker:add") {
      await ctx.answerCallbackQuery();
      await handleWorkerAddStart(ctx, loginWebUrl);
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
  await subscribeWorkerStatus(bot, natsUrl, async (ownerSellerId) => {
    try {
      const seller = await getSeller(catalogClient, ownerSellerId);
      return Number(seller.tg_user_id);
    } catch {
      return null;
    }
  });

  return bot;
}
