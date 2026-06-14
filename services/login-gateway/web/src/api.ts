export type LoginStep = {
  login_id: string;
  status: string;
  message: string;
  worker_id: number;
  qr_url: string;
  qr_expires_at: number;
};

function getInitData(): string {
  return window.Telegram?.WebApp?.initData ?? "";
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Telegram-Init-Data", getInitData());

  const res = await fetch(path, { ...options, headers });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error ?? data.message ?? `HTTP ${res.status}`);
  }
  return data as T;
}

export async function initSession(): Promise<{ seller_id: number }> {
  return api("/api/login/session", { method: "POST" });
}

export async function startQR(): Promise<LoginStep> {
  return api("/api/login/qr/start", { method: "POST" });
}

export async function startPhone(phone: string): Promise<LoginStep> {
  return api("/api/login/phone/start", {
    method: "POST",
    body: JSON.stringify({ phone }),
  });
}

export async function submitCode(loginId: string, code: string): Promise<LoginStep> {
  return api(`/api/login/${loginId}/code`, {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export async function submitPassword(loginId: string, password: string): Promise<LoginStep> {
  return api(`/api/login/${loginId}/password`, {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export async function pollStatus(loginId: string): Promise<LoginStep> {
  return api(`/api/login/${loginId}/status`);
}

export function notifyBotAndClose(workerId: number, message: string) {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.sendData(JSON.stringify({ status: "success", worker_id: workerId, message }));
    tg.close();
  }
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData: string;
        ready: () => void;
        expand: () => void;
        sendData: (data: string) => void;
        close: () => void;
      };
    };
  }
}
