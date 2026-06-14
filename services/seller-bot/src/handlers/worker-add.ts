import type { BotContext } from "../types.js";
import { normalizePhone } from "../utils/phone.js";
import {
  startWorkerLogin,
  submitWorkerLoginCode,
  submitWorkerLoginPassword,
  type LoginStep,
} from "../grpc/client.js";

async function replyStep(ctx: BotContext, step: LoginStep) {
  const lines = [step.message || step.status];
  if (step.status === "code_sent") {
    lines.push("", "Введите код из Telegram:");
  }
  if (step.status === "password_required") {
    lines.push("", "Введите пароль 2FA:");
  }
  if (step.status === "success" && step.worker_id) {
    lines.push("", `Откройте «Воркеры» → чаты воркера #${step.worker_id} и включите нужные группы.`);
    lines.push("Воркер подключится автоматически в течение ~30 секунд.");
  }
  await ctx.reply(lines.join("\n"));
}

export async function handleWorkerAddStart(ctx: BotContext) {
  ctx.session.flow = "worker_add_phone";
  ctx.session.loginId = undefined;
  ctx.session.workerPhone = undefined;
  await ctx.reply(
    [
      "Добавление воркера (аккаунт-слушатель).",
      "",
      "Введите номер телефона в формате +79991234567",
    ].join("\n"),
  );
}

export async function handleWorkerAddFlow(
  ctx: BotContext,
  loginClient: ReturnType<typeof import("../grpc/client.js").createWorkerLoginClient>,
  internalGrpcToken = "",
) {
  const text = ctx.message?.text?.trim();
  if (!text || !ctx.session.flow?.startsWith("worker_add")) return;

  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    ctx.session.flow = undefined;
    return;
  }

  if (ctx.session.flow === "worker_add_phone") {
    if (!/^\+?\d{10,15}$/.test(text.replace(/\s/g, ""))) {
      await ctx.reply("Некорректный номер. Пример: +79991234567");
      return;
    }

    const phone = normalizePhone(text);
    await ctx.reply("Отправляем код в Telegram…");

    try {
      const step = await startWorkerLogin(loginClient, sellerId, phone, internalGrpcToken);
      if (step.status === "error") {
        await ctx.reply(`Ошибка: ${step.message}`);
        ctx.session.flow = undefined;
        return;
      }
      ctx.session.loginId = step.login_id;
      ctx.session.workerPhone = phone;
      ctx.session.flow = "worker_add_code";
      await replyStep(ctx, step);
    } catch (err) {
      console.error("StartLogin failed", err);
      await ctx.reply("Не удалось начать авторизацию. Проверьте TG_API_ID/HASH и worker-engine.");
      ctx.session.flow = undefined;
    }
    return;
  }

  if (ctx.session.flow === "worker_add_code") {
    const loginId = ctx.session.loginId;
    if (!loginId) {
      await ctx.reply("Сессия устарела. Начните заново: /add_worker");
      ctx.session.flow = undefined;
      return;
    }

    const code = text.replace(/\s/g, "");
    try {
      const step = await submitWorkerLoginCode(loginClient, loginId, code);
      if (step.status === "error") {
        await ctx.reply(`Ошибка: ${step.message}`);
        return;
      }
      if (step.status === "password_required") {
        ctx.session.flow = "worker_add_password";
        await replyStep(ctx, step);
        return;
      }
      if (step.status === "success") {
        ctx.session.flow = undefined;
        ctx.session.loginId = undefined;
        await replyStep(ctx, step);
        return;
      }
      await replyStep(ctx, step);
    } catch (err) {
      console.error("SubmitCode failed", err);
      await ctx.reply("Ошибка при проверке кода. Попробуйте ещё раз.");
    }
    return;
  }

  if (ctx.session.flow === "worker_add_password") {
    const loginId = ctx.session.loginId;
    if (!loginId) {
      await ctx.reply("Сессия устарела. Начните заново: /add_worker");
      ctx.session.flow = undefined;
      return;
    }

    try {
      const step = await submitWorkerLoginPassword(loginClient, loginId, text);
      if (step.status === "error") {
        await ctx.reply(`Ошибка: ${step.message}`);
        return;
      }
      ctx.session.flow = undefined;
      ctx.session.loginId = undefined;
      await replyStep(ctx, step);
    } catch (err) {
      console.error("SubmitPassword failed", err);
      await ctx.reply("Ошибка при проверке пароля. Попробуйте ещё раз.");
    }
  }
}
