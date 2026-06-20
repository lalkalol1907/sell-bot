<script setup lang="ts">
import { useLogin } from "./composables/useLogin";

const {
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
  showQrSkeleton,
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
} = useLogin();
</script>

<template>
  <div class="app" :class="{ initializing }">
    <div v-if="initializing" class="loader-screen">
      <div class="spinner" />
      <span>Подготовка…</span>
    </div>

    <div class="content">
      <header class="header">
        <h1>Подключение воркера</h1>
        <p class="subtitle">Аккаунт-слушатель для мониторинга чатов</p>
      </header>

      <div class="tabs">
        <button type="button" class="tab" :class="{ active: tab === 'qr' }" @click="setTab('qr')">
          QR-код
        </button>
        <button
          type="button"
          class="tab"
          :class="{ active: tab === 'phone' }"
          @click="setTab('phone')"
        >
          Телефон
        </button>
      </div>

      <p v-if="error" class="alert alert-error">{{ error }}</p>
      <p v-if="success" class="alert alert-success">{{ success }}</p>
      <p v-if="showSessionLoading" class="alert alert-info">Загрузка…</p>

      <div v-show="tab === 'qr'" class="panel">
        <div class="card">
          <p class="hint">
            На телефоне с аккаунтом-воркером: Настройки → Устройства → Подключить устройство →
            Сканировать QR.
          </p>
          <button v-if="showQrButton" type="button" class="primary" @click="onStartQR">
            Сгенерировать QR
          </button>
          <div v-if="showQrSkeleton" class="qr-box">
            <div class="qr-skeleton" aria-hidden="true" />
            <div class="qr-skeleton-hint" aria-hidden="true" />
          </div>
          <div v-if="showQrBox" class="qr-box">
            <img :src="qrDataUrl" alt="QR login" width="220" height="220" />
            <p v-if="qrHint" class="hint">{{ qrHint }}</p>
          </div>
        </div>
      </div>

      <div v-show="tab === 'phone'" class="panel">
        <div v-if="showPhoneStart" class="card step-block">
          <div class="field">
            <label for="phone">Номер телефона</label>
            <input
              id="phone"
              v-model="phone"
              placeholder="+79991234567"
              inputmode="tel"
              autocomplete="tel"
            />
          </div>
          <button
            type="button"
            class="primary"
            :disabled="loading || !phone.trim()"
            @click="onStartPhone"
          >
            {{ loading ? "Отправляем…" : "Отправить код" }}
          </button>
        </div>

        <div v-if="showCode" class="card step-block">
          <p class="hint">{{ codeHint }}</p>
          <div class="field">
            <label for="code">Код из Telegram</label>
            <input
              id="code"
              v-model="code"
              placeholder="12345"
              inputmode="numeric"
              autocomplete="one-time-code"
            />
          </div>
          <button
            type="button"
            class="primary"
            :disabled="loading || !code.trim()"
            @click="onSubmitCode"
          >
            {{ loading ? "Проверяем…" : "Подтвердить код" }}
          </button>
        </div>

        <div v-if="showPassword" class="card step-block">
          <p class="hint">{{ passwordHint }}</p>
          <div class="field">
            <label for="password">Пароль 2FA</label>
            <input
              id="password"
              v-model="password"
              type="password"
              placeholder="Пароль"
              autocomplete="current-password"
            />
          </div>
          <button
            type="button"
            class="primary"
            :disabled="loading || !password"
            @click="onSubmitPassword"
          >
            {{ loading ? "Проверяем…" : "Подтвердить пароль" }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style>
*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--tg-theme-bg-color, #f4f6f8);
  color: var(--tg-theme-text-color, #111827);
  line-height: 1.5;
}
</style>

<style scoped>
.app {
  min-height: 100vh;
  padding: 20px 16px 32px;
  max-width: 420px;
  margin: 0 auto;
}

.app.initializing .content {
  display: none;
}

.header {
  margin-bottom: 20px;
}

.header h1 {
  font-size: 1.35rem;
  font-weight: 700;
  margin: 0 0 6px;
  letter-spacing: -0.02em;
}

.subtitle {
  color: var(--tg-theme-hint-color, #6b7280);
  font-size: 0.9rem;
  margin: 0;
}

.loader-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  min-height: 50vh;
  color: var(--tg-theme-hint-color, #6b7280);
  font-size: 0.9rem;
}

.spinner {
  width: 28px;
  height: 28px;
  border: 3px solid var(--tg-theme-secondary-bg-color, #e5e7eb);
  border-top-color: var(--tg-theme-button-color, #2481cc);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.tabs {
  display: flex;
  gap: 6px;
  padding: 4px;
  margin-bottom: 16px;
  border-radius: 12px;
  background: var(--tg-theme-secondary-bg-color, #eef2f7);
}

.tab {
  flex: 1;
  padding: 10px 12px;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: var(--tg-theme-hint-color, #6b7280);
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.tab.active {
  background: var(--tg-theme-bg-color, #fff);
  color: var(--tg-theme-text-color, #111827);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.alert {
  padding: 12px 14px;
  border-radius: 10px;
  font-size: 0.9rem;
  margin-bottom: 14px;
  line-height: 1.45;
}

.alert-error {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.alert-success {
  background: #ecfdf5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.alert-info {
  background: var(--tg-theme-secondary-bg-color, #f3f4f6);
  color: var(--tg-theme-hint-color, #6b7280);
}

.card {
  background: var(--tg-theme-secondary-bg-color, #fff);
  border-radius: 14px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field label {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--tg-theme-hint-color, #6b7280);
}

input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid var(--tg-theme-hint-color, #d1d5db);
  font-size: 1rem;
  background: var(--tg-theme-bg-color, #fff);
  color: inherit;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

input:focus {
  border-color: var(--tg-theme-button-color, #2481cc);
  box-shadow: 0 0 0 3px rgba(36, 129, 204, 0.15);
}

button.primary {
  width: 100%;
  padding: 13px 16px;
  border: none;
  border-radius: 10px;
  background: var(--tg-theme-button-color, #2481cc);
  color: var(--tg-theme-button-text-color, #fff);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s;
}

button.primary:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.qr-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

.qr-box img {
  width: 220px;
  height: 220px;
  border-radius: 12px;
  background: #fff;
  padding: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

.qr-skeleton {
  width: 220px;
  height: 220px;
  border-radius: 12px;
  background: linear-gradient(
    90deg,
    var(--tg-theme-secondary-bg-color, #e5e7eb) 0%,
    var(--tg-theme-bg-color, #f3f4f6) 50%,
    var(--tg-theme-secondary-bg-color, #e5e7eb) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.2s ease-in-out infinite;
}

.qr-skeleton-hint {
  width: 180px;
  height: 14px;
  border-radius: 7px;
  background: linear-gradient(
    90deg,
    var(--tg-theme-secondary-bg-color, #e5e7eb) 0%,
    var(--tg-theme-bg-color, #f3f4f6) 50%,
    var(--tg-theme-secondary-bg-color, #e5e7eb) 100%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.2s ease-in-out infinite;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: 200% 0;
  }

  100% {
    background-position: -200% 0;
  }
}

.hint {
  font-size: 0.85rem;
  color: var(--tg-theme-hint-color, #6b7280);
  line-height: 1.5;
  margin: 0;
}

.step-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
