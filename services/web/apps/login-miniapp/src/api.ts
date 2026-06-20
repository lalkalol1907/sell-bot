export interface LoginStep {
  login_id?: string;
  status?: string;
  qr_url?: string;
  worker_id?: number;
  message?: string;
}

import { createApiClient } from "@sellbot/api-client";
import { getHandoffToken, initHandoffToken } from "./handoff";

initHandoffToken();

function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? "";
}

const { api } = createApiClient({
  getHeaders: () => {
    const headers = new Headers();
    const initData = getInitData();
    if (initData) {
      headers.set("X-Telegram-Init-Data", initData);
      return headers;
    }

    const handoff = getHandoffToken();
    if (handoff) {
      headers.set("X-Login-Handoff", handoff);
    }
    return headers;
  },
});

export function initSession() {
  return api<LoginStep>("/api/v1/login/session", { method: "POST" });
}

export function startQR() {
  return api<LoginStep>("/api/v1/login/qr/start", { method: "POST" });
}

export function startPhone(phone: string) {
  return api<LoginStep>("/api/v1/login/phone/start", {
    method: "POST",
    body: JSON.stringify({ phone }),
  });
}

export function submitCode(loginId: string, code: string) {
  return api<LoginStep>(`/api/v1/login/${loginId}/code`, {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function submitPassword(loginId: string, password: string) {
  return api<LoginStep>(`/api/v1/login/${loginId}/password`, {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export function pollStatus(loginId: string) {
  return api<LoginStep>(`/api/v1/login/${loginId}/status`);
}

export function notifyBotAndClose(workerId: number, message?: string) {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.sendData(JSON.stringify({ status: "success", worker_id: workerId, message }));
    tg.close();
  }
}
