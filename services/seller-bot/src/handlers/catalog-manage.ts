import { InlineKeyboard } from "grammy";
import type { BotContext } from "../types.js";
import { getSeller, updateSeller, type Product } from "../grpc/client.js";

const SENSITIVITY_LABELS: Record<string, string> = {
  precise: "🎯 Точный — меньше ложных лидов",
  balanced: "⚖️ Сбалансированный",
  aggressive: "🔥 Агрессивный — больше лидов",
};

export function catalogMenu() {
  return new InlineKeyboard()
    .text("Добавить товар", "catalog:add")
    .row()
    .text("Чувствительность", "catalog:sensitivity")
    .row()
    .text("« Назад", "catalog:back");
}

export function productActionsKeyboard(productId: number, isActive: boolean) {
  const kb = new InlineKeyboard()
    .text("Изменить", `catalog:edit:${productId}`)
    .text(isActive ? "Пауза" : "Включить", `catalog:toggle:${productId}`)
    .row()
    .text("Удалить", `catalog:delete:${productId}`);
  return kb;
}

export async function handleCatalogMenu(ctx: BotContext, catalogClient: any, products: Product[]) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    return;
  }

  const seller = await getSeller(catalogClient, sellerId);
  const lines = [
    "📦 Каталог",
    `Чувствительность: ${SENSITIVITY_LABELS[seller.sensitivity] ?? seller.sensitivity}`,
    "",
  ];

  if (products.length === 0) {
    lines.push("Каталог пуст.");
  } else {
    for (const p of products) {
      lines.push(`${p.is_active ? "✅" : "⏸"} ${p.title} — ${p.price} (id: ${p.id})`);
    }
  }

  await ctx.reply(lines.join("\n"), { reply_markup: catalogMenu() });

  for (const p of products) {
    await ctx.reply(`Товар: ${p.title}`, {
      reply_markup: productActionsKeyboard(Number(p.id), p.is_active),
    });
  }
}

export async function handleSensitivityMenu(ctx: BotContext, catalogClient: any) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) return;

  const seller = await getSeller(catalogClient, sellerId);
  const kb = new InlineKeyboard()
    .text(seller.sensitivity === "precise" ? "✓ Точный" : "Точный", "sensitivity:precise")
    .row()
    .text(seller.sensitivity === "balanced" ? "✓ Сбалансированный" : "Сбалансированный", "sensitivity:balanced")
    .row()
    .text(seller.sensitivity === "aggressive" ? "✓ Агрессивный" : "Агрессивный", "sensitivity:aggressive");

  await ctx.reply("Выберите чувствительность matching:", { reply_markup: kb });
}

export async function handleSensitivitySet(ctx: BotContext, catalogClient: any, value: string) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) return;

  await updateSeller(catalogClient, sellerId, value);
  await ctx.answerCallbackQuery({ text: `Чувствительность: ${value}` });
  await ctx.editMessageText(`Чувствительность обновлена: ${SENSITIVITY_LABELS[value] ?? value}`);
}

export async function handleProductEditStart(ctx: BotContext, productId: number) {
  ctx.session.flow = "edit_product_title";
  ctx.session.editProductId = productId;
  await ctx.answerCallbackQuery();
  await ctx.reply(`Редактирование товара #${productId}. Введите новое название:`);
}

export async function handleProductEditFlow(ctx: BotContext, catalogClient: any) {
  const flow = ctx.session.flow;
  const text = ctx.message?.text?.trim();
  if (!flow?.startsWith("edit_product") || !text) return;

  const sellerId = ctx.session.sellerId;
  const productId = ctx.session.editProductId;
  if (!sellerId || !productId) {
    await ctx.reply("Сессия сброшена. /start");
    ctx.session.flow = undefined;
    return;
  }

  if (flow === "edit_product_title") {
    ctx.session.productTitle = text;
    ctx.session.flow = "edit_product_price";
    await ctx.reply("Введите новую цену:");
    return;
  }

  if (flow === "edit_product_price") {
    const { isValidPrice, normalizePrice } = await import("../utils/validation.js");
    if (!isValidPrice(text)) {
      await ctx.reply("Некорректная цена. Пример: 79990");
      return;
    }

    const { updateProduct, listProducts } = await import("../grpc/client.js");
    const products = await listProducts(catalogClient, sellerId);
    const existing = products.find((p) => Number(p.id) === productId);
    if (!existing) {
      await ctx.reply("Товар не найден");
      ctx.session.flow = undefined;
      return;
    }

    await updateProduct(catalogClient, {
      id: productId,
      seller_id: sellerId,
      title: ctx.session.productTitle!,
      price: normalizePrice(text),
      currency: existing.currency || "RUB",
      keywords: existing.keywords ?? [],
      is_active: existing.is_active,
    });

    ctx.session.flow = undefined;
    ctx.session.editProductId = undefined;
    ctx.session.productTitle = undefined;
    ctx.session.productPrice = undefined;

    await ctx.reply(`Товар #${productId} обновлён.`, { reply_markup: catalogMenu() });
  }
}
