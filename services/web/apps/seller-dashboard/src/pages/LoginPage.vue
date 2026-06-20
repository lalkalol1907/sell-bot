<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useAuth } from "../composables/useAuth";

const botUsername = import.meta.env.VITE_BOT_USERNAME ?? "";
const { loginWithTelegram } = useAuth();

const error = ref("");
const loginContainer = ref<HTMLElement | null>(null);
const domain = typeof window !== "undefined" ? window.location.hostname : "";

onMounted(() => {
  window.onTelegramAuth = async (user) => {
    error.value = "";
    try {
      await loginWithTelegram(user);
    } catch (e) {
      error.value = e instanceof Error ? e.message : "Ошибка входа";
    }
  };

  if (loginContainer.value && botUsername) {
    loginContainer.value.innerHTML = "";
    const script = document.createElement("script");
    script.src = "https://telegram.org/js/telegram-widget.js?22";
    script.async = true;
    script.setAttribute("data-telegram-login", botUsername);
    script.setAttribute("data-size", "large");
    script.setAttribute("data-onauth", "onTelegramAuth(user)");
    script.setAttribute("data-request-access", "write");
    loginContainer.value.appendChild(script);
  }
});
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <h1>Кабинет продавца</h1>
      <p>Войдите через Telegram. Сначала выполните /start в боте.</p>
      <p v-if="domain" class="hint">
        Домен <code>{{ domain }}</code> должен быть привязан к боту: @BotFather → /setdomain →
        <code>{{ domain }}</code>
      </p>
      <div v-if="botUsername" ref="loginContainer" class="login-widget" />
      <p v-else class="error">VITE_BOT_USERNAME не настроен</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: linear-gradient(160deg, #eff6ff 0%, var(--color-bg) 50%);
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: var(--color-surface);
  padding: 36px 32px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border);
}

.login-card h1 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}

.login-card > p {
  margin: 0 0 16px;
  color: var(--color-muted);
}

.login-card code {
  font-size: 0.85em;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.login-widget {
  margin-top: 8px;
}
</style>
