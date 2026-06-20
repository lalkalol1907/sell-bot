<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type Stats } from "../api";

const stats = ref<Stats | null>(null);
const error = ref("");
const loading = ref(true);

onMounted(() => {
  sellerApi
    .stats()
    .then((data) => {
      stats.value = data;
    })
    .catch((e) => {
      error.value = e instanceof Error ? e.message : "Ошибка загрузки";
    })
    .finally(() => {
      loading.value = false;
    });
});
</script>

<template>
  <div>
    <header class="page-header">
      <h2>Статистика</h2>
      <p>Лиды за последние 30 дней</p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>
    <div v-else-if="loading" class="card">
      <p class="muted">Загрузка…</p>
    </div>
    <div v-else-if="stats" class="grid">
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
  </div>
</template>

<style scoped>
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
}

.stat {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  padding: 18px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
}

.stat strong {
  display: block;
  font-size: 1.75rem;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
  letter-spacing: -0.02em;
}

.stat span {
  font-size: 0.85rem;
  color: var(--color-muted);
}
</style>
