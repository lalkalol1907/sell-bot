import { describe, expect, test } from "bun:test";
import { formatLeadNotification, leadActionCallback } from "./lead-notification.js";
import { formatLeadLine } from "./leads-format.js";
import { normalizePhone } from "./phone.js";
import { chatMessageLink } from "./telegram-link.js";
import { isValidPrice, normalizePrice } from "./validation.js";

describe("chatMessageLink", () => {
  test("builds supergroup link", () => {
    expect(chatMessageLink(-1001234567890, 42)).toBe("https://t.me/c/1234567890/42");
  });

  test("returns null for non-channel ids", () => {
    expect(chatMessageLink(12345, 1)).toBeNull();
  });

  test("returns null for zero ids", () => {
    expect(chatMessageLink(0, 0)).toBeNull();
  });
});

describe("normalizePhone", () => {
  test("converts 8-prefix Russian number", () => {
    expect(normalizePhone("89991234567")).toBe("+79991234567");
  });

  test("keeps international format", () => {
    expect(normalizePhone("+79991234567")).toBe("+79991234567");
  });

  test("adds plus to bare digits", () => {
    expect(normalizePhone("79991234567")).toBe("+79991234567");
  });
});

describe("price validation", () => {
  test("accepts integer price", () => {
    expect(isValidPrice("79990")).toBe(true);
  });

  test("accepts decimal comma", () => {
    expect(isValidPrice("79990,50")).toBe(true);
  });

  test("rejects text", () => {
    expect(isValidPrice("abc")).toBe(false);
  });

  test("normalizes comma to dot", () => {
    expect(normalizePrice(" 79990,5 ")).toBe("79990.5");
  });
});

describe("formatLeadLine", () => {
  test("formats confirmed lead", () => {
    const line = formatLeadLine({
      id: "7",
      status: "new",
      level: "confirmed",
      raw_text: "куплю айфон 16",
    });
    expect(line).toContain("#7");
    expect(line).toContain("[точная]");
    expect(line).toContain("куплю айфон 16");
  });

  test("truncates long text", () => {
    const long = "а".repeat(100);
    const line = formatLeadLine({ id: "1", status: "spam", level: "probable", raw_text: long });
    expect(line).toContain("«" + "а".repeat(60) + "»");
  });
});

describe("formatLeadNotification", () => {
  test("confirmed lead with link", () => {
    const text = formatLeadNotification({
      lead_id: 1,
      seller_id: 1,
      tg_user_id: 100,
      product_title: "iPhone 16",
      raw_text: "куплю айфон",
      chat_title: "Барахолка",
      author_username: "buyer",
      author_id: 555,
      level: "confirmed",
      chat_id: -1001234567890,
      message_id: 55,
    });
    expect(text).toContain("🔥 Новая заявка");
    expect(text).toContain("iPhone 16");
    expect(text).toContain("@buyer");
    expect(text).toContain("https://t.me/c/1234567890/55");
  });

  test("probable lead without username", () => {
    const text = formatLeadNotification({
      lead_id: 2,
      seller_id: 1,
      tg_user_id: 100,
      product_title: "MacBook",
      raw_text: "ищу макбук",
      chat_title: "",
      author_username: "",
      author_id: 0,
      level: "probable",
      chat_id: 0,
      message_id: 0,
    });
    expect(text).toContain("💡 Возможная заявка");
    expect(text).toContain("Автор: —");
    expect(text).not.toContain("https://t.me");
  });
});

describe("leadActionCallback", () => {
  test("builds callback data", () => {
    expect(leadActionCallback("contacted", 42)).toBe("lead:contacted:42");
  });
});
