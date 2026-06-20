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
          <button
            v-if="showQrButton"
            type="button"
            class="primary"
            :disabled="loading"
            @click="onStartQR"
          >
            {{ loading ? "Генерируем…" : "Сгенерировать QR" }}
          </button>
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
