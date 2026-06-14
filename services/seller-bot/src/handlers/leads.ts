import type { BotContext } from "../types.js";
import { listLeads } from "../grpc/client.js";
import { formatLeadLine } from "../utils/leads-format.js";

export async function handleLeadsList(ctx: BotContext, leadsClient: any) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    return;
  }

  const leads = await listLeads(leadsClient, sellerId, 15);
  if (leads.length === 0) {
    await ctx.reply("Лидов пока нет.");
    return;
  }

  const lines = leads.map((l) => formatLeadLine(l));

  await ctx.reply(["Последние лиды:", "", ...lines].join("\n"));
}
