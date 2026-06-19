import { describe, expect, test } from "bun:test";
import { sortChats } from "./workers.js";
import type { MonitoredChat } from "../grpc/client.js";

function chat(title: string, isActive: boolean, chatId = title): MonitoredChat {
  return { id: chatId, chat_id: chatId, title, is_active: isActive };
}

describe("sortChats", () => {
  test("active chats first, then alphabetical", () => {
    const sorted = sortChats([
      chat("Beta", false),
      chat("Alpha", true),
      chat("Gamma", false),
      chat("Zeta", true),
    ]);

    expect(sorted.map((c) => c.title)).toEqual(["Alpha", "Zeta", "Beta", "Gamma"]);
  });
});
