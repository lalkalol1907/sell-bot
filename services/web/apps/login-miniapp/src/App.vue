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
    <h1>Подключение воркера</h1>
    <p class="subtitle">Аккаунт-слушатель для мониторинга чатов</p>

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

    <p v-if="error" class="error">{{ error }}</p>
    <p v-if="success" class="success">{{ success }}</p>
    <p v-if="showSessionLoading" class="hint">Загрузка…</p>

    <div v-show="tab === 'qr'" class="panel">
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
        Сгенерировать QR
      </button>
      <div v-if="showQrBox" class="qr-box">
        <img :src="qrDataUrl" alt="QR login" width="220" height="220" />
        <p v-if="qrHint" class="hint">{{ qrHint }}</p>
      </div>
    </div>

    <div v-show="tab === 'phone'" class="panel">
      <div v-if="showPhoneStart">
        <input v-model="phone" placeholder="+79991234567" inputmode="tel" autocomplete="tel" />
        <button
          type="button"
          class="primary"
          :disabled="loading || !phone.trim()"
          @click="onStartPhone"
        >
          Отправить код
        </button>
      </div>

      <div v-if="showCode">
        <p class="hint">{{ codeHint }}</p>
        <input
          v-model="code"
          placeholder="Код из Telegram"
          inputmode="numeric"
          autocomplete="one-time-code"
        />
        <button
          type="button"
          class="primary"
          :disabled="loading || !code.trim()"
          @click="onSubmitCode"
        >
          Подтвердить код
        </button>
      </div>

      <div v-if="showPassword">
        <p class="hint">{{ passwordHint }}</p>
        <input
          v-model="password"
          type="password"
          placeholder="Пароль 2FA"
          autocomplete="current-password"
        />
        <button
          type="button"
          class="primary"
          :disabled="loading || !password"
          @click="onSubmitPassword"
        >
          Подтвердить пароль
        </button>
      </div>
    </div>
  </div>
</template>
