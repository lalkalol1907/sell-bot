import { describe, expect, test } from "bun:test";
import crypto from "node:crypto";
import { validateInitData } from "../src/init-data";

function buildInitData(botToken: string, user: { id: number; first_name: string }) {
  const authDate = Math.floor(Date.now() / 1000).toString();
  const userJson = JSON.stringify(user);
  const params = new URLSearchParams({
    auth_date: authDate,
    user: userJson,
  });
  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");
  const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const hash = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");
  params.set("hash", hash);
  return params.toString();
}

describe("validateInitData", () => {
  test("accepts valid init data", () => {
    const token = "123456:ABC-DEF";
    const initData = buildInitData(token, { id: 42, first_name: "Test" });
    const user = validateInitData(initData, token);
    expect(user?.id).toBe(42);
  });

  test("rejects tampered hash", () => {
    const token = "123456:ABC-DEF";
    const initData = buildInitData(token, { id: 42, first_name: "Test" }) + "x";
    expect(validateInitData(initData, token)).toBeNull();
  });

  test("rejects wrong token", () => {
    const initData = buildInitData("123456:ABC-DEF", { id: 1, first_name: "A" });
    expect(validateInitData(initData, "other-token")).toBeNull();
  });
});
