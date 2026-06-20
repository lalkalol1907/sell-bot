import { describe, expect, test } from "bun:test";
import { authorContactUrl, formatLeadNotification } from "./lead-notification.js";

describe("authorContactUrl", () => {
  test("builds tg user link", () => {
    expect(authorContactUrl(123456)).toBe("tg://user?id=123456");
  });

  test("returns null for invalid id", () => {
    expect(authorContactUrl(0)).toBeNull();
  });
});

describe("formatLeadNotification", () => {
  test("includes product and chat", () => {
    const text = formatLeadNotification({
      lead_id: 1,
      seller_id: 1,
      tg_user_id: 99,
      product_title: "iPhone 16",
      raw_text: "куплю айфон",
      chat_title: "Opt Chat",
      author_username: "buyer",
      author_id: 555,
      level: "confirmed",
      chat_id: 1,
      message_id: 2,
    });
    expect(text).toContain("iPhone 16");
    expect(text).toContain("Opt Chat");
    expect(text).toContain("@buyer");
  });
});
