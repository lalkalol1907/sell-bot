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
      <div v-if="botUsername" ref="loginContainer" />
      <p v-else class="error">VITE_BOT_USERNAME не настроен</p>
      <p v-if="error" class="error">{{ error }}</p>
    </div>
  </div>
</template>
