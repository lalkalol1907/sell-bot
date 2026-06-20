<script setup lang="ts">
import { useAuth } from "../composables/useAuth";

const { seller, logout } = useAuth();
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <h1>Sellbot</h1>
        <p class="sidebar-user">{{ seller?.full_name || seller?.username }}</p>
      </div>
      <nav>
        <RouterLink to="/" active-class="active">Статистика</RouterLink>
        <RouterLink to="/catalog" active-class="active">Каталог</RouterLink>
        <RouterLink to="/leads" active-class="active">Лиды</RouterLink>
        <RouterLink to="/team" active-class="active">Команда</RouterLink>
        <RouterLink to="/workers" active-class="active">Воркеры</RouterLink>
      </nav>
      <div class="sidebar-footer">
        <button class="secondary sidebar-logout" @click="logout()">Выйти</button>
      </div>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 240px 1fr;
}

.sidebar {
  background: var(--color-sidebar);
  color: #fff;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
  height: 100vh;
}

.sidebar-brand {
  margin-bottom: 24px;
}

.sidebar-brand h1 {
  font-size: 1.15rem;
  font-weight: 700;
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}

.sidebar-user {
  font-size: 0.85rem;
  color: #9ca3af;
  margin: 0;
}

.sidebar nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.sidebar nav :deep(a) {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-size: 0.95rem;
  font-weight: 500;
  color: #d1d5db;
  transition: background 0.15s, color 0.15s;
}

.sidebar nav :deep(a.active) {
  background: var(--color-sidebar-hover);
  color: #fff;
}

.sidebar nav :deep(a:hover:not(.active)) {
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
}

.sidebar-footer {
  margin-top: auto;
  padding-top: 16px;
}

.sidebar-logout {
  width: 100%;
}

.content {
  padding: 28px 32px;
  max-width: 1200px;
}

@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .sidebar {
    position: static;
    height: auto;
    padding: 16px;
  }

  .sidebar nav {
    flex-direction: row;
    flex-wrap: wrap;
    gap: 6px;
  }

  .sidebar nav :deep(a) {
    padding: 8px 12px;
    font-size: 0.85rem;
  }

  .sidebar-footer {
    margin-top: 12px;
    padding-top: 0;
  }

  .content {
    padding: 20px 16px;
  }
}
</style>

<style>
.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 4px;
  letter-spacing: -0.02em;
}

.page-header p {
  margin: 0;
  color: var(--color-muted);
  font-size: 0.95rem;
}

@media (max-width: 768px) {
  .page-header h2 {
    font-size: 1.25rem;
  }
}

.card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  margin-bottom: 16px;
  border: 1px solid var(--color-border);
}

.card h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 16px;
}

.table-wrap {
  overflow-x: auto;
  margin: -4px;
  padding: 4px;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.95rem;
}

th,
td {
  text-align: left;
  padding: 12px 10px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: middle;
}

th {
  font-size: 0.8rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--color-muted);
}

tbody tr:last-child td {
  border-bottom: none;
}

tbody tr:hover {
  background: #f9fafb;
}

input,
select,
textarea,
button {
  font: inherit;
}

input,
select,
textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: var(--radius-sm);
  background: var(--color-surface);
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
}

input:focus,
select:focus,
textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.12);
}

select {
  max-width: 220px;
  margin-bottom: 16px;
}

button {
  padding: 9px 14px;
  border: none;
  border-radius: var(--radius-sm);
  background: var(--color-primary);
  color: #fff;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s, opacity 0.15s;
  white-space: nowrap;
}

button:hover:not(:disabled) {
  background: var(--color-primary-hover);
}

button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

button.secondary {
  background: #6b7280;
}

button.secondary:hover:not(:disabled) {
  background: #4b5563;
}

button.danger {
  background: var(--color-danger);
}

button.danger:hover:not(:disabled) {
  background: #b91c1c;
}

button.ghost,
.btn-link.ghost {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-border);
}

button.ghost:hover:not(:disabled),
.btn-link.ghost:hover {
  background: #eff6ff;
}

.btn-link {
  display: inline-block;
  padding: 9px 14px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  font-size: 0.9rem;
  white-space: nowrap;
}

.row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
  line-height: 1.4;
}

.badge-new {
  background: #dbeafe;
  color: #1d4ed8;
}

.badge-contacted {
  background: #fef3c7;
  color: #b45309;
}

.badge-closed {
  background: #d1fae5;
  color: #047857;
}

.badge-spam {
  background: #fee2e2;
  color: #b91c1c;
}

.badge-active {
  background: #d1fae5;
  color: #047857;
}

.badge-paused {
  background: #f3f4f6;
  color: #4b5563;
}

.badge-on {
  background: #d1fae5;
  color: #047857;
}

.badge-off {
  background: #f3f4f6;
  color: #6b7280;
}

.empty-state {
  text-align: center;
  padding: 32px 16px;
  color: var(--color-muted);
}

.toolbar {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar input[type="search"] {
  flex: 1;
  min-width: 200px;
  margin-bottom: 0;
}

.toolbar label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.9rem;
  color: var(--color-muted);
  white-space: nowrap;
}

.toolbar input[type="checkbox"] {
  width: auto;
}

.form-grid {
  display: grid;
  gap: 12px;
}
</style>
