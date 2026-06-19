import { computed, onMounted, onUnmounted, ref } from "vue";
import QRCode from "qrcode";
import {
  initSession,
  notifyBotAndClose,
  pollStatus,
  startPhone,
  startQR,
  submitCode,
  submitPassword,
  type LoginStep,
} from "../api";

export function useLogin() {
  const tab = ref<"qr" | "phone">("qr");
  const initializing = ref(true);
  const loading = ref(false);
  const error = ref("");
  const success = ref("");
  const loginId = ref("");
  const step = ref<LoginStep | null>(null);
  const qrDataUrl = ref("");
  const qrHint = ref("");

  const phone = ref("");
  const code = ref("");
  const password = ref("");

  let pollTimer: ReturnType<typeof setInterval> | null = null;

  const showSessionLoading = computed(() => loading.value && !step.value);
  const showQrButton = computed(() => !loginId.value);
  const showQrBox = computed(() => Boolean(qrDataUrl.value));
  const showPhoneStart = computed(() => !loginId.value);
  const showCode = computed(
    () =>
      Boolean(loginId.value) &&
      (step.value?.status === "code_sent" ||
        step.value?.status === "" ||
        !step.value?.status),
  );
  const showPassword = computed(
    () => Boolean(loginId.value) && step.value?.status === "password_required",
  );
  const codeHint = computed(() => step.value?.message || "Введите код из Telegram");
  const passwordHint = computed(() => step.value?.message ?? "");

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  function handleSuccess(current: LoginStep) {
    if (current.status === "success" && current.worker_id) {
      notifyBotAndClose(current.worker_id, current.message);
    }
  }

  async function renderQr(current: LoginStep | null) {
    if (!current?.qr_url) {
      qrDataUrl.value = "";
      qrHint.value = "";
      return;
    }

    try {
      qrDataUrl.value = await QRCode.toDataURL(current.qr_url, { width: 220, margin: 1 });
      qrHint.value = current.message ?? "";
    } catch {
      qrDataUrl.value = "";
      qrHint.value = "";
    }
  }

  function applyStep(current: LoginStep) {
    step.value = current;
    if (current.login_id) {
      loginId.value = current.login_id;
    }

    const isSuccess = current.status === "success";
    const isError = current.status === "error";

    if (isSuccess) {
      success.value = current.message || `Воркер #${current.worker_id} подключён`;
    } else {
      success.value = "";
    }

    void renderQr(current);

    if (isSuccess || isError) {
      stopPolling();
    } else if (loginId.value) {
      startPolling();
    }
  }

  function startPolling() {
    stopPolling();
    if (!loginId.value) return;
    if (step.value?.status === "success" || step.value?.status === "error") return;

    pollTimer = setInterval(async () => {
      try {
        const current = await pollStatus(loginId.value);
        applyStep(current);
        handleSuccess(current);
      } catch {
        /* ignore transient poll errors */
      }
    }, 2000);
  }

  async function runAction(action: () => Promise<LoginStep>, fallbackError: string) {
    error.value = "";
    loading.value = true;
    try {
      const current = await action();
      applyStep(current);
      handleSuccess(current);
    } catch (err) {
      error.value = err instanceof Error ? err.message : fallbackError;
    } finally {
      loading.value = false;
    }
  }

  function setTab(next: "qr" | "phone") {
    tab.value = next;
  }

  async function onStartQR() {
    await runAction(startQR, "Ошибка QR");
  }

  async function onStartPhone() {
    await runAction(() => startPhone(phone.value.trim()), "Ошибка");
  }

  async function onSubmitCode() {
    if (!loginId.value) return;
    await runAction(() => submitCode(loginId.value, code.value.trim()), "Ошибка кода");
  }

  async function onSubmitPassword() {
    if (!loginId.value) return;
    await runAction(() => submitPassword(loginId.value, password.value), "Ошибка пароля");
  }

  onMounted(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();

    initSession()
      .catch((err) => {
        error.value = err instanceof Error ? err.message : "Ошибка сессии";
      })
      .finally(() => {
        initializing.value = false;
        loading.value = false;
      });
  });

  onUnmounted(() => {
    stopPolling();
  });

  return {
    tab,
    initializing,
    loading,
    error,
    success,
    phone,
    code,
    password,
    qrDataUrl,
    qrHint,
    showSessionLoading,
    showQrButton,
    showQrBox,
    showPhoneStart,
    showCode,
    showPassword,
    codeHint,
    passwordHint,
    setTab,
    onStartQR,
    onStartPhone,
    onSubmitCode,
    onSubmitPassword,
  };
}
