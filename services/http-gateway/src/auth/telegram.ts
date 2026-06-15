import crypto from "node:crypto";

export type TelegramUser = {
  id: number;
  first_name?: string;
  username?: string;
};

const MAX_AGE_SEC = 86_400;

function secureEqual(a: string, b: string): boolean {
  const bufA = Buffer.from(a);
  const bufB = Buffer.from(b);
  if (bufA.length !== bufB.length) return false;
  return crypto.timingSafeEqual(bufA, bufB);
}

/** Telegram Mini App initData validation. */
export function validateInitData(initData: string, botToken: string): TelegramUser | null {
  if (!initData || !botToken) return null;

  const params = new URLSearchParams(initData);
  const hash = params.get("hash");
  if (!hash) return null;

  params.delete("hash");
  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");

  const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const computed = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");
  if (!secureEqual(computed, hash)) return null;

  const authDate = Number(params.get("auth_date") ?? "0");
  if (authDate > 0 && Math.floor(Date.now() / 1000) - authDate > MAX_AGE_SEC) return null;

  const userRaw = params.get("user");
  if (!userRaw) return null;

  try {
    const user = JSON.parse(userRaw) as { id?: number; first_name?: string; username?: string };
    if (!user?.id) return null;
    return { id: user.id, first_name: user.first_name, username: user.username };
  } catch {
    return null;
  }
}

/** Telegram Login Widget callback validation. */
export function validateLoginWidget(
  payload: Record<string, string | number | undefined>,
  botToken: string,
): TelegramUser | null {
  if (!botToken) return null;

  const data: Record<string, string> = {};
  for (const [k, v] of Object.entries(payload)) {
    if (k === "hash" || v === undefined) continue;
    data[k] = String(v);
  }

  const hash = payload.hash != null ? String(payload.hash) : "";
  if (!hash) return null;

  const dataCheckString = Object.entries(data)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");

  const secretKey = crypto.createHash("sha256").update(botToken).digest();
  const computed = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");
  if (!secureEqual(computed, hash)) return null;

  const authDate = Number(data.auth_date ?? "0");
  if (authDate > 0 && Math.floor(Date.now() / 1000) - authDate > MAX_AGE_SEC) return null;

  const id = Number(data.id ?? "0");
  if (!id) return null;

  return { id, first_name: data.first_name, username: data.username };
}
