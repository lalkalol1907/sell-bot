<script setup lang="ts">
import { useAuth } from "./composables/useAuth";

const { loading } = useAuth();
</script>

<template>
  <div v-if="loading" class="loader-screen">
    <div class="spinner" />
    <span>Загрузка…</span>
  </div>
  <RouterView v-else />
</template>

<style>
:root {
  --color-bg: #f4f6f8;
  --color-surface: #ffffff;
  --color-text: #111827;
  --color-muted: #6b7280;
  --color-border: #e5e7eb;
  --color-primary: #2563eb;
  --color-primary-hover: #1d4ed8;
  --color-sidebar: #111827;
  --color-sidebar-hover: #1f2937;
  --color-danger: #dc2626;
  --color-success: #059669;
  --color-warning: #d97706;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.08);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.08);
}

*,
*::before,
*::after {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.5;
}

a {
  color: inherit;
  text-decoration: none;
}

.error {
  color: var(--color-danger);
  font-size: 0.9rem;
}

.hint,
.muted {
  color: var(--color-muted);
  font-size: 0.9rem;
}
</style>

<style scoped>
.loader-screen {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  min-height: 100vh;
  color: var(--color-muted);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 3px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
