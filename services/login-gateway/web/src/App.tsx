import { useCallback, useEffect, useState } from "react";
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
} from "./api";

type Tab = "qr" | "phone";

export function App() {
  const [tab, setTab] = useState<Tab>("qr");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [loginId, setLoginId] = useState("");
  const [step, setStep] = useState<LoginStep | null>(null);
  const [qrDataUrl, setQrDataUrl] = useState("");
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");

  const handleSuccess = useCallback((s: LoginStep) => {
    if (s.status === "success" && s.worker_id) {
      notifyBotAndClose(s.worker_id, s.message);
    }
  }, []);

  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
    initSession()
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!step?.qr_url) {
      setQrDataUrl("");
      return;
    }
    QRCode.toDataURL(step.qr_url, { width: 220, margin: 1 })
      .then(setQrDataUrl)
      .catch(() => setQrDataUrl(""));
  }, [step?.qr_url]);

  useEffect(() => {
    if (!loginId) return;
    if (step?.status === "success" || step?.status === "error") return;

    const id = setInterval(async () => {
      try {
        const s = await pollStatus(loginId);
        setStep(s);
        handleSuccess(s);
      } catch {
        /* ignore transient poll errors */
      }
    }, 2000);

    return () => clearInterval(id);
  }, [loginId, step?.status, handleSuccess]);

  async function onStartQR() {
    setError("");
    setLoading(true);
    try {
      const s = await startQR();
      setStep(s);
      setLoginId(s.login_id);
      handleSuccess(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка QR");
    } finally {
      setLoading(false);
    }
  }

  async function onStartPhone() {
    setError("");
    setLoading(true);
    try {
      const s = await startPhone(phone);
      setStep(s);
      setLoginId(s.login_id);
      handleSuccess(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmitCode() {
    if (!loginId) return;
    setError("");
    setLoading(true);
    try {
      const s = await submitCode(loginId, code);
      setStep(s);
      handleSuccess(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка кода");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmitPassword() {
    if (!loginId) return;
    setError("");
    setLoading(true);
    try {
      const s = await submitPassword(loginId, password);
      setStep(s);
      handleSuccess(s);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ошибка пароля");
    } finally {
      setLoading(false);
    }
  }

  if (loading && !step) {
    return (
      <div className="app">
        <p>Загрузка…</p>
      </div>
    );
  }

  return (
    <div className="app">
      <h1>Подключение воркера</h1>
      <p className="subtitle">Аккаунт-слушатель для мониторинга чатов</p>

      <div className="tabs">
        <button className={`tab ${tab === "qr" ? "active" : ""}`} onClick={() => setTab("qr")}>
          QR-код
        </button>
        <button className={`tab ${tab === "phone" ? "active" : ""}`} onClick={() => setTab("phone")}>
          Телефон
        </button>
      </div>

      {error && <p className="error">{error}</p>}
      {step?.status === "success" && (
        <p className="success">{step.message || `Воркер #${step.worker_id} подключён`}</p>
      )}

      {tab === "qr" && (
        <div className="panel">
          <p className="hint">
            На телефоне с аккаунтом-воркером: Настройки → Устройства → Подключить устройство →
            Сканировать QR.
          </p>
          {!loginId && (
            <button className="primary" disabled={loading} onClick={onStartQR}>
              Сгенерировать QR
            </button>
          )}
          {qrDataUrl && (
            <div className="qr-box">
              <img src={qrDataUrl} alt="QR login" />
              <p className="hint">{step?.message}</p>
            </div>
          )}
        </div>
      )}

      {tab === "phone" && (
        <div className="panel">
          {!loginId && (
            <>
              <input
                placeholder="+79991234567"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
              <button className="primary" disabled={loading || !phone} onClick={onStartPhone}>
                Отправить код
              </button>
            </>
          )}
          {loginId && (step?.status === "code_sent" || step?.status === "") && (
            <>
              <p className="hint">{step?.message || "Введите код из Telegram"}</p>
              <input
                placeholder="Код из Telegram"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                inputMode="numeric"
              />
              <button className="primary" disabled={loading || !code} onClick={onSubmitCode}>
                Подтвердить код
              </button>
            </>
          )}
          {loginId && step?.status === "password_required" && (
            <>
              <p className="hint">{step.message}</p>
              <input
                type="password"
                placeholder="Пароль 2FA"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <button className="primary" disabled={loading || !password} onClick={onSubmitPassword}>
                Подтвердить пароль
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
