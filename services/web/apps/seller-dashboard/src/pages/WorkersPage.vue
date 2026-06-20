<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import { sellerApi, type Worker } from "../api";

const workers = ref<Worker[]>([]);
const error = ref("");
const loading = ref(true);
const openingMiniApp = ref(false);

const statusLabels: Record<string, string> = {
  active: "Активен",
  paused: "На паузе",
};

async function load() {
  const data = await sellerApi.workers();
  workers.value = data.workers;
}

async function openMiniApp() {
  openingMiniApp.value = true;
  try {
    const { url } = await sellerApi.createLoginHandoff();
    window.open(url, "_blank", "noopener,noreferrer");
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Не удалось открыть Mini App";
  } finally {
    openingMiniApp.value = false;
  }
}

onMounted(() => {
  load()
    .catch((e) => {
      error.value = e instanceof Error ? e.message : "Ошибка загрузки";
    })
    .finally(() => {
      loading.value = false;
    });
});

async function setStatus(id: number, status: string) {
  await sellerApi.updateWorkerStatus(id, status);
  await load();
}
</script>

<template>
  <div>
    <header class="page-header">
      <h2>Воркеры</h2>
      <p>Telegram-аккаунты для мониторинга чатов</p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="toolbar">
      <button type="button" :disabled="openingMiniApp" @click="openMiniApp">
        {{ openingMiniApp ? "Открываем…" : "+ Добавить воркера" }}
      </button>
    </div>

    <div class="card">
      <div v-if="loading" class="empty-state">Загрузка…</div>
      <div v-else-if="workers.length === 0" class="empty-state">
        Воркеров пока нет. Нажмите «Добавить воркера», чтобы подключить аккаунт.
      </div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Телефон</th>
              <th>Статус</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="w in workers" :key="w.id">
              <td>#{{ w.id }}</td>
              <td>{{ w.phone || "—" }}</td>
              <td>
                <span :class="w.status === 'active' ? 'badge badge-active' : 'badge badge-paused'">
                  {{ statusLabels[w.status] ?? w.status }}
                </span>
              </td>
              <td class="row">
                <RouterLink class="btn-link ghost" :to="`/workers/${w.id}/chats`">Чаты</RouterLink>
                <button
                  v-if="w.status === 'active'"
                  class="secondary"
                  @click="setStatus(w.id, 'paused')"
                >
                  Пауза
                </button>
                <button v-else @click="setStatus(w.id, 'active')">Возобновить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
