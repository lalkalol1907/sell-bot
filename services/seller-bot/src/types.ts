import type { Context } from "grammy";

export type SessionData = {
  sellerId?: number;
  flow?: string;
  productTitle?: string;
  productPrice?: string;
};

export type BotContext = Context & { session: SessionData };
