import type { BotContext } from "../types.js";
import { listProducts } from "../grpc/client.js";
import { handleCatalogMenu } from "./catalog-manage.js";

export async function handleCatalogList(ctx: BotContext, catalogClient: any) {
  const sellerId = ctx.session.sellerId;
  if (!sellerId) {
    await ctx.reply("Сначала /start");
    return;
  }

  const products = await listProducts(catalogClient, sellerId);
  await handleCatalogMenu(ctx, catalogClient, products);
}
