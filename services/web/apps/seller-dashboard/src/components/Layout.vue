<script setup lang="ts">
import { useAuth } from "../composables/useAuth";

const { seller, logout } = useAuth();
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <h1>Sellbot</h1>
      <p style="opacity: 0.8; margin-bottom: 16px">{{ seller?.full_name || seller?.username }}</p>
      <nav>
        <RouterLink to="/" active-class="active">Статистика</RouterLink>
        <RouterLink to="/catalog" active-class="active">Каталог</RouterLink>
        <RouterLink to="/leads" active-class="active">Лиды</RouterLink>
        <RouterLink to="/workers" active-class="active">Воркеры</RouterLink>
      </nav>
      <button class="secondary" style="margin-top: 24px" @click="logout()">Выйти</button>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>
