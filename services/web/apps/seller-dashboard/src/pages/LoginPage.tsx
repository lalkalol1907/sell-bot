import { useEffect, useState } from "react";
import { useAuth } from "../auth";

declare global {
  interface Window {
    onTelegramAuth?: (user: Record<string, string | number>) => void;
  }
}

const botUsername = import.meta.env.VITE_BOT_USERNAME ?? "";

export function LoginPage() {
  const { loginWithTelegram } = useAuth();
  const [error, setError] = useState("");

  useEffect(() => {
    window.onTelegramAuth = async (user) => {
      setError("");
      try {
        await loginWithTelegram(user);
      } catch (e) {
        setError(e instanceof Error ? e.message : "Ошибка входа");
      }
    };

    const container = document.getElementById("telegram-login");
    if (container && botUsername) {
      container.innerHTML = "";
      const script = document.createElement("script");
      script.src = "https://telegram.org/js/telegram-widget.js?22";
      script.async = true;
      script.setAttribute("data-telegram-login", botUsername);
      script.setAttribute("data-size", "large");
      script.setAttribute("data-onauth", "onTelegramAuth(user)");
      script.setAttribute("data-request-access", "write");
      container.appendChild(script);
    }
  }, [loginWithTelegram]);

  const domain = typeof window !== "undefined" ? window.location.hostname : "";

  return (
    <div className="login-page">
      <div className="login-card">
        <h1>Кабинет продавца</h1>
        <p>Войдите через Telegram. Сначала выполните /start в боте.</p>
        {domain && (
          <p className="hint">
            Домен <code>{domain}</code> должен быть привязан к боту: @BotFather → /setdomain →{" "}
            <code>{domain}</code>
          </p>
        )}
        {botUsername ? (
          <div id="telegram-login" />
        ) : (
          <p className="error">VITE_BOT_USERNAME не настроен</p>
        )}
        {error && <p className="error">{error}</p>}
      </div>
    </div>
  );
}
