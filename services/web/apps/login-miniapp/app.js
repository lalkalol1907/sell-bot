import {
  initSession,
  notifyBotAndClose,
  pollStatus,
  startPhone,
  startQR,
  submitCode,
  submitPassword,
} from "./api.js";

const $ = (id) => document.getElementById(id);

const els = {
  error: $("error"),
  success: $("success"),
  loading: $("loading"),
  panelQr: $("panel-qr"),
  panelPhone: $("panel-phone"),
  btnStartQr: $("btn-start-qr"),
  qrBox: $("qr-box"),
  qrImage: $("qr-image"),
  qrHint: $("qr-hint"),
  phoneInput: $("phone-input"),
  btnStartPhone: $("btn-start-phone"),
  phoneStart: $("phone-start"),
  phoneCode: $("phone-code"),
  codeHint: $("code-hint"),
  codeInput: $("code-input"),
  btnSubmitCode: $("btn-submit-code"),
  phonePassword: $("phone-password"),
  passwordHint: $("password-hint"),
  passwordInput: $("password-input"),
  btnSubmitPassword: $("btn-submit-password"),
};

const state = {
  tab: "qr",
  loading: true,
  loginId: "",
  step: null,
  pollTimer: null,
};

function setError(message) {
  if (message) {
    els.error.textContent = message;
    els.error.classList.remove("hidden");
  } else {
    els.error.textContent = "";
    els.error.classList.add("hidden");
  }
}

function setLoading(loading) {
  state.loading = loading;
  els.loading.classList.toggle("hidden", !loading || state.step);
  for (const btn of [
    els.btnStartQr,
    els.btnStartPhone,
    els.btnSubmitCode,
    els.btnSubmitPassword,
  ]) {
    btn.disabled = loading;
  }
  els.btnStartPhone.disabled = loading || !els.phoneInput.value.trim();
  els.btnSubmitCode.disabled = loading || !els.codeInput.value.trim();
  els.btnSubmitPassword.disabled = loading || !els.passwordInput.value.trim();
}

function setTab(tab) {
  state.tab = tab;
  for (const btn of document.querySelectorAll(".tab")) {
    btn.classList.toggle("active", btn.dataset.tab === tab);
  }
  els.panelQr.classList.toggle("hidden", tab !== "qr");
  els.panelPhone.classList.toggle("hidden", tab !== "phone");
}

function handleSuccess(step) {
  if (step.status === "success" && step.worker_id) {
    notifyBotAndClose(step.worker_id, step.message);
  }
}

function stopPolling() {
  if (state.pollTimer) {
    clearInterval(state.pollTimer);
    state.pollTimer = null;
  }
}

function startPolling() {
  stopPolling();
  if (!state.loginId) return;
  if (state.step?.status === "success" || state.step?.status === "error") return;

  state.pollTimer = setInterval(async () => {
    try {
      const step = await pollStatus(state.loginId);
      applyStep(step);
      handleSuccess(step);
    } catch {
      /* ignore transient poll errors */
    }
  }, 2000);
}

async function renderQr(step) {
  if (!step?.qr_url) {
    els.qrBox.classList.add("hidden");
    els.qrImage.removeAttribute("src");
    return;
  }

  try {
    const dataUrl = await QRCode.toDataURL(step.qr_url, { width: 220, margin: 1 });
    els.qrImage.src = dataUrl;
    els.qrHint.textContent = step.message ?? "";
    els.qrBox.classList.remove("hidden");
  } catch {
    els.qrBox.classList.add("hidden");
  }
}

function applyStep(step) {
  state.step = step;
  if (step?.login_id) {
    state.loginId = step.login_id;
  }

  const isSuccess = step?.status === "success";
  const isError = step?.status === "error";

  if (isSuccess) {
    els.success.textContent = step.message || `Воркер #${step.worker_id} подключён`;
    els.success.classList.remove("hidden");
  } else {
    els.success.classList.add("hidden");
  }

  els.btnStartQr.classList.toggle("hidden", Boolean(state.loginId));
  void renderQr(step);

  const showPhoneStart = !state.loginId;
  els.phoneStart.classList.toggle("hidden", !showPhoneStart);

  const showCode =
    state.loginId && (step?.status === "code_sent" || step?.status === "" || !step?.status);
  els.phoneCode.classList.toggle("hidden", !showCode);
  if (showCode) {
    els.codeHint.textContent = step?.message || "Введите код из Telegram";
  }

  const showPassword = state.loginId && step?.status === "password_required";
  els.phonePassword.classList.toggle("hidden", !showPassword);
  if (showPassword) {
    els.passwordHint.textContent = step.message ?? "";
  }

  els.loading.classList.add("hidden");

  if (isSuccess || isError) {
    stopPolling();
  } else if (state.loginId) {
    startPolling();
  }
}

async function onStartQR() {
  setError("");
  setLoading(true);
  try {
    const step = await startQR();
    applyStep(step);
    handleSuccess(step);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Ошибка QR");
  } finally {
    setLoading(false);
  }
}

async function onStartPhone() {
  setError("");
  setLoading(true);
  try {
    const step = await startPhone(els.phoneInput.value.trim());
    applyStep(step);
    handleSuccess(step);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Ошибка");
  } finally {
    setLoading(false);
  }
}

async function onSubmitCode() {
  if (!state.loginId) return;
  setError("");
  setLoading(true);
  try {
    const step = await submitCode(state.loginId, els.codeInput.value.trim());
    applyStep(step);
    handleSuccess(step);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Ошибка кода");
  } finally {
    setLoading(false);
  }
}

async function onSubmitPassword() {
  if (!state.loginId) return;
  setError("");
  setLoading(true);
  try {
    const step = await submitPassword(state.loginId, els.passwordInput.value);
    applyStep(step);
    handleSuccess(step);
  } catch (err) {
    setError(err instanceof Error ? err.message : "Ошибка пароля");
  } finally {
    setLoading(false);
  }
}

document.querySelectorAll(".tab").forEach((btn) => {
  btn.addEventListener("click", () => setTab(btn.dataset.tab));
});

els.btnStartQr.addEventListener("click", () => void onStartQR());
els.btnStartPhone.addEventListener("click", () => void onStartPhone());
els.btnSubmitCode.addEventListener("click", () => void onSubmitCode());
els.btnSubmitPassword.addEventListener("click", () => void onSubmitPassword());

els.phoneInput.addEventListener("input", () => {
  els.btnStartPhone.disabled = state.loading || !els.phoneInput.value.trim();
});

els.codeInput.addEventListener("input", () => {
  els.btnSubmitCode.disabled = state.loading || !els.codeInput.value.trim();
});

els.passwordInput.addEventListener("input", () => {
  els.btnSubmitPassword.disabled = state.loading || !els.passwordInput.value.trim();
});

window.Telegram?.WebApp?.ready();
window.Telegram?.WebApp?.expand();

setTab("qr");
setLoading(true);

initSession()
  .catch((err) => setError(err instanceof Error ? err.message : "Ошибка сессии"))
  .finally(() => {
    document.querySelector(".app")?.classList.remove("initializing");
    setLoading(false);
    els.loading.classList.add("hidden");
    els.panelQr.classList.remove("hidden");
  });
