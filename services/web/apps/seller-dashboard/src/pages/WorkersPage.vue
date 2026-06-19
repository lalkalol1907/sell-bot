<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type Worker } from "../api";

const workers = ref<Worker[]>([]);
const error = ref("");
const openingMiniApp = ref(false);

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
      <button type="button" :disabled="openingMiniApp" @click="openMiniApp">
        {{ openingMiniApp ? "Открываем…" : "Добавить воркера" }}
      </button>
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
