<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type Stats } from "../api";

const stats = ref<Stats | null>(null);
const error = ref("");

onMounted(() => {
  sellerApi
    .stats()
    .then((data) => {
      stats.value = data;
    })
    .catch((e) => {
      error.value = e instanceof Error ? e.message : "Ошибка загрузки";
    });
});
</script>

<template>
  <div>
    <p v-if="error" class="error">{{ error }}</p>
    <p v-else-if="!stats">Загрузка…</p>
    <template v-else>
      <h2>Статистика (30 дней)</h2>
      <div class="grid">
        <div class="stat">
          <strong>{{ stats.total }}</strong>
          <span>Всего лидов</span>
        </div>
        <div class="stat">
          <strong>{{ stats.new_count }}</strong>
          <span>Новые</span>
        </div>
        <div class="stat">
          <strong>{{ stats.contacted }}</strong>
          <span>В работе</span>
        </div>
        <div class="stat">
          <strong>{{ stats.closed }}</strong>
          <span>Закрыты</span>
        </div>
        <div class="stat">
          <strong>{{ stats.spam }}</strong>
          <span>Спам</span>
        </div>
      </div>
    </template>
  </div>
</template>
