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
        <RouterLink to="/workers" active-class="active">Воркеры</RouterLink>
      </nav>
      <div class="sidebar-footer">
        <button class="secondary" style="width: 100%" @click="logout()">Выйти</button>
      </div>
    </aside>
    <main class="content">
      <RouterView />
    </main>
  </div>
</template>
