import crypto from "node:crypto";

export type TelegramWebAppUser = {
  id: number;
  first_name?: string;
  username?: string;
};

export function validateInitData(
  initData: string,
  botToken: string,
): TelegramWebAppUser | null {
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
  if (computed !== hash) return null;

  const authDate = Number(params.get("auth_date") ?? "0");
  if (authDate > 0 && Date.now() / 1000 - authDate > 86400) {
    return null;
  }

  const userRaw = params.get("user");
  if (!userRaw) return null;

  try {
    const user = JSON.parse(userRaw) as TelegramWebAppUser;
    if (!user?.id) return null;
    return user;
  } catch {
    return null;
  }
}
