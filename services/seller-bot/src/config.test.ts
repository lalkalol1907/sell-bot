import { describe, expect, test } from "bun:test";
import {
  assertWebhookUrlMatchesPath,
  loadConfig,
  normalizeWebhookPath,
} from "./config.js";

describe("normalizeWebhookPath", () => {
  test("adds leading slash", () => {
    expect(normalizeWebhookPath("telegram/webhook")).toBe("/telegram/webhook");
  });

  test("strips trailing slash", () => {
    expect(normalizeWebhookPath("/telegram/webhook/")).toBe("/telegram/webhook");
  });
});

describe("assertWebhookUrlMatchesPath", () => {
  test("accepts matching path", () => {
    expect(() =>
      assertWebhookUrlMatchesPath(
        "https://bot.example.com/telegram/webhook",
        "/telegram/webhook",
      ),
    ).not.toThrow();
  });

  test("rejects mismatched path", () => {
    expect(() =>
      assertWebhookUrlMatchesPath("https://bot.example.com/hook", "/telegram/webhook"),
    ).toThrow(/must match/);
  });
});

describe("loadConfig", () => {
  test("defaults to polling", () => {
    const config = loadConfig({
      BOT_TOKEN: "test-token",
    });
    expect(config.transport).toBe("polling");
    expect(config.httpPort).toBe(8080);
    expect(config.webhookRegisterOnStartup).toBe(false);
  });

  test("requires webhook settings in webhook mode", () => {
    expect(() =>
      loadConfig({
        BOT_TOKEN: "test-token",
        BOT_TRANSPORT: "webhook",
      }),
    ).toThrow(/WEBHOOK_URL/);

    expect(() =>
      loadConfig({
        BOT_TOKEN: "test-token",
        BOT_TRANSPORT: "webhook",
        WEBHOOK_URL: "https://bot.example.com/telegram/webhook",
      }),
    ).toThrow(/WEBHOOK_SECRET/);
  });

  test("loads webhook config", () => {
    const config = loadConfig({
      BOT_TOKEN: "test-token",
      BOT_TRANSPORT: "webhook",
      WEBHOOK_URL: "https://bot.example.com/telegram/webhook",
      WEBHOOK_SECRET: "secret",
      HTTP_PORT: "9000",
    });

    expect(config.transport).toBe("webhook");
    expect(config.httpPort).toBe(9000);
    expect(config.webhookPath).toBe("/telegram/webhook");
    expect(config.webhookRegisterOnStartup).toBe(true);
  });

  test("supports legacy METRICS_PORT", () => {
    const config = loadConfig({
      BOT_TOKEN: "test-token",
      METRICS_PORT: "9090",
    });
    expect(config.httpPort).toBe(9090);
  });
});
