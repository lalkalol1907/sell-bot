<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type Worker } from "../api";

const miniAppUrl = import.meta.env.VITE_MINIAPP_URL ?? "/miniapp/";

const workers = ref<Worker[]>([]);
const error = ref("");

async function load() {
  const data = await sellerApi.workers();
  workers.value = data.workers;
}

onMounted(() => {
  load().catch((e) => {
    error.value = e instanceof Error ? e.message : "Ошибка загрузки";
  });
});

async function setStatus(id: number, status: string) {
  await sellerApi.updateWorkerStatus(id, status);
  await load();
}
</script>

<template>
  <div>
    <h2>Воркеры</h2>
    <p v-if="error" class="error">{{ error }}</p>

    <p>
      <a :href="miniAppUrl" target="_blank" rel="noreferrer">
        <button>Добавить воркера (Mini App)</button>
      </a>
    </p>

    <div class="card">
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
            <td>{{ w.id }}</td>
            <td>{{ w.phone || "—" }}</td>
            <td>{{ w.status }}</td>
            <td class="row">
              <button
                v-if="w.status === 'active'"
                class="secondary"
                @click="setStatus(w.id, 'paused')"
              >
                Pause
              </button>
              <button v-else @click="setStatus(w.id, 'active')">Resume</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
