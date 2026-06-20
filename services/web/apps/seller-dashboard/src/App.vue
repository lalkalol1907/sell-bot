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
