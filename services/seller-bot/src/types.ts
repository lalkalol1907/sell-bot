import type { Context } from "grammy";

export type SessionData = {
  sellerId?: number;
  flow?: string;
  productTitle?: string;
  productPrice?: string;
  loginId?: string;
  workerPhone?: string;
};

export type BotContext = Context & { session: SessionData };
