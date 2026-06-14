import { InlineKeyboard } from "grammy";
import type { BotContext } from "../types.js";
import { listChats, listWorkers, setChatWhitelist } from "../grpc/client.js";

export async function handleWorkersList(ctx: BotContext, workersClient: any) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    return;
  }

  const workers = await listWorkers(workersClient, sellerId);
  if (workers.length === 0) {
    await ctx.reply(
      [
        "Воркеров нет.",
        "",
        "Добавить: /add_worker",
      ].join("\n"),
    );
    return;
  }

  const kb = new InlineKeyboard();
  kb.text("➕ Добавить воркера", "worker:add").row();
  for (const w of workers) {
    kb.text(`${w.status} #${w.id} ${w.phone || "—"}`, `worker:chats:${w.id}`).row();
  }

  await ctx.reply("Ваши воркеры (нажмите для настройки чатов):", { reply_markup: kb });
}

export async function handleWorkerChats(
  ctx: BotContext,
  workersClient: any,
  workerId: number,
) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) return;

  const chats = await listChats(workersClient, workerId, sellerId);
  if (chats.length === 0) {
    await ctx.reply("Чаты не синхронизированы. Запустите worker-engine с сессией.");
    return;
  }

  const kb = new InlineKeyboard();
  for (const ch of chats.slice(0, 20)) {
    const mark = ch.is_active ? "✅" : "⬜";
    const title = (ch.title || ch.chat_id).slice(0, 30);
    kb.text(`${mark} ${title}`, `chat:toggle:${workerId}:${ch.chat_id}`).row();
  }

  await ctx.reply(`Чаты воркера #${workerId} (нажмите для вкл/выкл):`, { reply_markup: kb });
}

export async function handleChatToggle(
  ctx: BotContext,
  workersClient: any,
  workerId: number,
  chatId: number,
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
  await handleWorkerChats(ctx, workersClient, workerId);
}
