import type { BotContext } from "../types.js";
import { getLeadStats } from "../grpc/client.js";

export async function handleStats(ctx: BotContext, leadsClient: any) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    return;
  }

  const stats = await getLeadStats(leadsClient, sellerId, 30);
  await ctx.reply(
    [
      "Статистика за 30 дней:",
      `Всего: ${stats.total}`,
      `Новые: ${stats.new_count}`,
      `В работе: ${stats.contacted}`,
      `Закрыты: ${stats.closed}`,
      `Спам: ${stats.spam}`,
    ].join("\n"),
  );
}
