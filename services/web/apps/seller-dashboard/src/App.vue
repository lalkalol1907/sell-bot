<script setup lang="ts">
import { useAuth } from "./composables/useAuth";

const { loading } = useAuth();
</script>

<template>
  <p v-if="loading" style="padding: 24px">Загрузка…</p>
  <RouterView v-else />
</template>
