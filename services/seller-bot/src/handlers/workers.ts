import { InlineKeyboard } from "grammy";
import type { BotContext } from "../types.js";
import { listChats, listWorkers, setChatWhitelist, type MonitoredChat } from "../grpc/client.js";

const CHATS_PER_PAGE = 15;

export function sortChats(chats: MonitoredChat[]): MonitoredChat[] {
  return [...chats].sort((a, b) => {
    if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
    const ta = (a.title || String(a.chat_id)).toLowerCase();
    const tb = (b.title || String(b.chat_id)).toLowerCase();
    return ta.localeCompare(tb, "ru");
  });
}

function clampPage(page: number, totalPages: number): number {
  return Math.min(Math.max(0, page), Math.max(0, totalPages - 1));
}

function buildChatKeyboard(workerId: number, chats: MonitoredChat[], page: number): InlineKeyboard {
  const sorted = sortChats(chats);
  const totalPages = Math.max(1, Math.ceil(sorted.length / CHATS_PER_PAGE));
  const safePage = clampPage(page, totalPages);
  const slice = sorted.slice(safePage * CHATS_PER_PAGE, (safePage + 1) * CHATS_PER_PAGE);

  const kb = new InlineKeyboard();
  for (const ch of slice) {
    const mark = ch.is_active ? "✅" : "⬜";
    const title = (ch.title || ch.chat_id).slice(0, 30);
    kb.text(`${mark} ${title}`, `chat:toggle:${workerId}:${ch.chat_id}:${safePage}`).row();
  }

  if (totalPages > 1) {
    if (safePage > 0) {
      kb.text("◀️", `worker:chats:${workerId}:${safePage - 1}`);
    }
    if (safePage < totalPages - 1) {
      kb.text("▶️", `worker:chats:${workerId}:${safePage + 1}`);
    }
    kb.row();
  }

  kb.text("⬅️ К воркерам", "workers:list");
  return kb;
}

function chatListText(workerId: number, chats: MonitoredChat[], page: number): string {
  const sorted = sortChats(chats);
  const totalPages = Math.max(1, Math.ceil(sorted.length / CHATS_PER_PAGE));
  const safePage = clampPage(page, totalPages);
  let extra = "";
  if (totalPages > 1) {
    const from = safePage * CHATS_PER_PAGE + 1;
    const to = Math.min((safePage + 1) * CHATS_PER_PAGE, sorted.length);
    extra = `\nПоказано ${from}–${to} из ${sorted.length}. Страница ${safePage + 1} из ${totalPages}.`;
  }
  return `Чаты воркера #${workerId} (нажмите для вкл/выкл):${extra}`;
}

async function replyOrEdit(
  ctx: BotContext,
  text: string,
  replyMarkup: InlineKeyboard,
): Promise<void> {
  const opts = { reply_markup: replyMarkup };
  if (ctx.callbackQuery?.message) {
    await ctx.editMessageText(text, opts);
    return;
  }
  await ctx.reply(text, opts);
}

export async function handleWorkersList(ctx: BotContext, workersClient: any) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    return;
  }

  const workers = await listWorkers(workersClient, sellerId);
  if (workers.length === 0) {
    const text = ["Воркеров нет.", "", "Добавить: /add_worker"].join("\n");
    if (ctx.callbackQuery?.message) {
      await ctx.editMessageText(text);
    } else {
      await ctx.reply(text);
    }
    return;
  }

  const kb = new InlineKeyboard();
  kb.text("➕ Добавить воркера", "worker:add").row();
  for (const w of workers) {
    kb.text(`${w.status} #${w.id} ${w.phone || "—"}`, `worker:chats:${w.id}`).row();
  }

  await replyOrEdit(ctx, "Ваши воркеры (нажмите для настройки чатов):", kb);
}

export async function handleWorkerChats(
  ctx: BotContext,
  workersClient: any,
  workerId: number,
  page = 0,
) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) return;

  const chats = await listChats(workersClient, workerId, sellerId);
  if (chats.length === 0) {
    const text = "Чаты не синхронизированы. Запустите worker-engine с сессией.";
    if (ctx.callbackQuery?.message) {
      await ctx.editMessageText(text);
    } else {
      await ctx.reply(text);
    }
    return;
  }

  const kb = buildChatKeyboard(workerId, chats, page);
  await replyOrEdit(ctx, chatListText(workerId, chats, page), kb);
}

export async function handleChatToggle(
  ctx: BotContext,
  workersClient: any,
  workerId: number,
  chatId: number,
  page = 0,
) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) return;

  const chats = await listChats(workersClient, workerId, sellerId);
  const chat = chats.find((c) => Number(c.chat_id) === chatId);
  const newActive = !(chat?.is_active ?? false);

  await setChatWhitelist(workersClient, workerId, sellerId, [
    { chat_id: chatId, is_active: newActive },
  ]);

  await ctx.answerCallbackQuery({ text: newActive ? "Мониторинг включён" : "Выключено" });
  await handleWorkerChats(ctx, workersClient, workerId, page);
}
