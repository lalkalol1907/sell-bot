import { InlineKeyboard } from "grammy";
import type { BotContext } from "../types.js";

export async function handleWorkerAddStart(ctx: BotContext, loginWebUrl: string) {
  if (!ctx.session.sellerId) {
    await ctx.reply("Сначала нажмите /start");
    return;
  }

  if (!loginWebUrl) {
    await ctx.reply("LOGIN_WEB_URL не настроен. Обратитесь к администратору.");
    return;
  }

  const keyboard = new InlineKeyboard().webApp("Открыть подключение воркера", loginWebUrl);

  await ctx.reply(
    [
      "Добавление воркера (аккаунт-слушатель).",
      "",
      "Нажмите кнопку ниже — откроется форма в Telegram.",
      "Подключите аккаунт по QR или по номеру телефона.",
      "Код и пароль 2FA вводятся только в форме, не в чате.",
    ].join("\n"),
    { reply_markup: keyboard },
  );
}

export async function handleWorkerAddResult(ctx: BotContext, rawData: string) {
  try {
    const data = JSON.parse(rawData) as {
      status?: string;
      worker_id?: number;
      message?: string;
    };

    if (data.status === "success" && data.worker_id) {
      await ctx.reply(
        [
          data.message || `Воркер #${data.worker_id} подключён.`,
          "",
          `Откройте «Воркеры» → чаты воркера #${data.worker_id} и включите нужные группы.`,
          "Воркер подключится автоматически в течение ~30 секунд.",
        ].join("\n"),
      );
      return;
    }

    await ctx.reply(data.message || "Не удалось подключить воркера. Попробуйте снова.");
  } catch {
    await ctx.reply("Некорректный ответ от формы. Попробуйте снова.");
  }
}
