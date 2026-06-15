import crypto from "node:crypto";
import { describe, expect, test } from "bun:test";
import { validateInitData, validateLoginWidget } from "../src/auth/telegram.ts";
import { LoginRouting } from "../src/redis.ts";

const botToken = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11";

function buildInitData(userId: number): string {
  const user = JSON.stringify({ id: userId, first_name: "Test" });
  const authDate = Math.floor(Date.now() / 1000).toString();
  const params = new URLSearchParams({ auth_date: authDate, user });
  const dataCheckString = [...params.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");
  const secretKey = crypto.createHmac("sha256", "WebAppData").update(botToken).digest();
  const hash = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");
  params.set("hash", hash);
  return params.toString();
}

function buildWidgetParams(userId: number) {
  const authDate = Math.floor(Date.now() / 1000);
  const params: Record<string, string | number> = {
    id: userId,
    first_name: "Test",
    auth_date: authDate,
  };
  const dataCheckString = Object.entries(params)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([k, v]) => `${k}=${v}`)
    .join("\n");
  const secretKey = crypto.createHash("sha256").update(botToken).digest();
  const hash = crypto.createHmac("sha256", secretKey).update(dataCheckString).digest("hex");
  return { ...params, hash };
}

describe("validateInitData", () => {
  test("accepts valid init data", () => {
    const user = validateInitData(buildInitData(42), botToken);
    expect(user?.id).toBe(42);
  });

  test("rejects tampered hash", () => {
    expect(validateInitData(`${buildInitData(42)}x`, botToken)).toBeNull();
  });
});

describe("validateLoginWidget", () => {
  test("accepts valid login widget payload", () => {
    const user = validateLoginWidget(buildWidgetParams(99), botToken);
    expect(user?.id).toBe(99);
  });
});

describe("LoginRouting.pickEngineAddress", () => {
  test("round-robin pick uses all engines", () => {
    const addrs = ["a", "b", "c"];
    const picked = Array.from({ length: 10 }, (_, i) =>
      LoginRouting.pickEngineAddress(addrs, 0, i),
    );
    expect([...new Set(picked)].sort()).toEqual(addrs.sort());
  });
});
