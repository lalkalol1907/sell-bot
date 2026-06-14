import { describe, expect, test } from "bun:test";
import { handleWorkerAddResult } from "./worker-add.js";

describe("handleWorkerAddResult", () => {
  test("parses success payload", async () => {
    const replies: string[] = [];
    const ctx = {
      reply: async (text: string) => {
        replies.push(text);
      },
    } as any;

    await handleWorkerAddResult(
      ctx,
      JSON.stringify({ status: "success", worker_id: 7, message: "OK" }),
    );

    expect(replies.length).toBe(1);
    expect(replies[0]).toContain("#7");
  });

  test("handles invalid json", async () => {
    const replies: string[] = [];
    const ctx = {
      reply: async (text: string) => {
        replies.push(text);
      },
    } as any;

    await handleWorkerAddResult(ctx, "not-json");
    expect(replies[0]).toContain("Некорректный");
  });
});
