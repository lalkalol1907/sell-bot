export type BotTransport = "polling" | "webhook";

export type AppConfig = {
  token: string;
  transport: BotTransport;
  httpPort: number;
  coreAddr: string;
  natsUrl: string;
  redisUrl: string;
  loginWebUrl: string;
  webhookUrl?: string;
  webhookPath: string;
  webhookSecret?: string;
  webhookRegisterOnStartup: boolean;
};

function parseBool(value: string | undefined, defaultValue: boolean): boolean {
  if (value === undefined || value === "") return defaultValue;
  const normalized = value.trim().toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off"].includes(normalized)) return false;
  throw new Error(`invalid boolean env value: ${value}`);
}

export function loadConfig(env: Record<string, string | undefined> = process.env): AppConfig {
  const token = env.BOT_TOKEN?.trim();
  if (!token) {
    throw new Error("BOT_TOKEN is required");
  }

  const transportRaw = (env.BOT_TRANSPORT ?? "polling").trim().toLowerCase();
  if (transportRaw !== "polling" && transportRaw !== "webhook") {
    throw new Error(`invalid BOT_TRANSPORT: ${transportRaw} (expected polling or webhook)`);
  }
  const transport = transportRaw as BotTransport;

  const webhookPath = normalizeWebhookPath(env.WEBHOOK_PATH ?? "/telegram/webhook");
  const webhookSecret = env.WEBHOOK_SECRET?.trim() || undefined;
  const webhookUrl = env.WEBHOOK_URL?.trim() || undefined;

  if (transport === "webhook") {
    if (!webhookUrl) {
      throw new Error("WEBHOOK_URL is required when BOT_TRANSPORT=webhook");
    }
    if (!webhookSecret) {
      throw new Error("WEBHOOK_SECRET is required when BOT_TRANSPORT=webhook");
    }
    assertWebhookUrlMatchesPath(webhookUrl, webhookPath);
  }

  return {
    token,
    transport,
    httpPort: Number(env.HTTP_PORT ?? env.METRICS_PORT ?? "8080"),
    coreAddr: env.CORE_GRPC_ADDR ?? "core:50051",
    natsUrl: env.NATS_URL ?? "nats://nats:4222",
    redisUrl: env.REDIS_URL ?? "redis://redis:6379/0",
    loginWebUrl: env.LOGIN_WEB_URL ?? "",
    webhookUrl,
    webhookPath,
    webhookSecret,
    webhookRegisterOnStartup: parseBool(env.WEBHOOK_REGISTER_ON_STARTUP, transport === "webhook"),
  };
}

export function normalizeWebhookPath(path: string): string {
  const trimmed = path.trim();
  if (!trimmed.startsWith("/")) {
    return `/${trimmed}`;
  }
  return trimmed.replace(/\/+$/, "") || "/";
}

export function assertWebhookUrlMatchesPath(webhookUrl: string, webhookPath: string): void {
  let pathname: string;
  try {
    pathname = new URL(webhookUrl).pathname.replace(/\/+$/, "") || "/";
  } catch {
    throw new Error(`invalid WEBHOOK_URL: ${webhookUrl}`);
  }

  const expected = webhookPath.replace(/\/+$/, "") || "/";
  if (pathname !== expected) {
    throw new Error(
      `WEBHOOK_URL path (${pathname}) must match WEBHOOK_PATH (${expected})`,
    );
  }
}
