import { Keyboard } from "grammy";
import { createProduct, createSeller } from "../grpc/client.js";
import type { BotContext } from "../types.js";
import { isValidPrice, normalizePrice } from "../utils/validation.js";

export function mainMenu() {
  return new Keyboard()
    .text("Каталог")
    .text("Воркеры")
    .row()
    .text("Лиды")
    .text("Статистика")
    .resized();
}

export async function handleStart(ctx: BotContext, catalogClient: any) {
  const from = ctx.from;
  if (!from) return;

  const seller = await createSeller(
    catalogClient,
    from.id,
    from.username ?? "",
    [from.first_name, from.last_name].filter(Boolean).join(" "),
  );

  ctx.session.sellerId = Number(seller.id);

  await ctx.reply(
    `Привет, ${from.first_name}! Вы зарегистрированы как продавец.\n\nВыберите раздел:`,
    { reply_markup: mainMenu() },
  );
}

export async function handleCatalogAdd(ctx: BotContext) {
  ctx.session.flow = "add_product_title";
  await ctx.reply("Введите название товара (например: iPhone 16):");
}

export async function handleCatalogFlow(ctx: BotContext, catalogClient: any) {
  const flow = ctx.session.flow;
  const text = ctx.message?.text?.trim();
  if (!flow || !text) return;

  if (flow === "add_product_title") {
    ctx.session.productTitle = text;
    ctx.session.flow = "add_product_price";
    await ctx.reply("Введите цену (число):");
    return;
  }

  if (flow === "add_product_price") {
    if (!isValidPrice(text)) {
      await ctx.reply("Некорректная цена. Пример: 79990");
      return;
    }
    ctx.session.productPrice = normalizePrice(text);
    ctx.session.flow = "add_product_currency";
    await ctx.reply("Введите валюту (RUB / USD):");
    return;
  }

  if (flow === "add_product_currency") {
    const sellerId = ctx.session.sellerId;
    if (!sellerId || !ctx.session.productTitle || !ctx.session.productPrice) {
      await ctx.reply("Сессия сброшена. Нажмите /start");
      ctx.session.flow = undefined;
      return;
    }

    const title = ctx.session.productTitle;
    await createProduct(
      catalogClient,
      sellerId,
      title,
      ctx.session.productPrice,
      text.toUpperCase() || "RUB",
      [],
    );

    ctx.session.flow = undefined;
    ctx.session.productTitle = undefined;
    ctx.session.productPrice = undefined;

    await ctx.reply(`Товар «${title}» добавлен. Мониторинг включён.`, {
      reply_markup: mainMenu(),
    });
  }
}
