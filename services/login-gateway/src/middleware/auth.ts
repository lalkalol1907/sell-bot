import type { TelegramWebAppUser } from "../init-data.js";
import { validateInitData } from "../init-data.js";

export type AuthContext = {
  user: TelegramWebAppUser;
  sellerId: number;
};

const INIT_DATA_HEADER = "x-telegram-init-data";

export function getInitDataFromRequest(req: Request): string | null {
  return req.headers.get(INIT_DATA_HEADER) ?? req.headers.get("X-Telegram-Init-Data");
}

export function parseInitData(initData: string | null, botToken: string): TelegramWebAppUser | null {
  if (!initData) return null;
  return validateInitData(initData, botToken);
}

export { INIT_DATA_HEADER };
