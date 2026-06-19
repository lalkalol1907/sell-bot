<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { sellerApi, type MonitoredChat } from "../api";

const route = useRoute();
const workerId = Number(route.params.id);

const chats = ref<MonitoredChat[]>([]);
const error = ref("");
const search = ref("");
const activeOnly = ref(false);
const syncing = ref(false);
const toggling = ref<number | null>(null);

function sortChats(items: MonitoredChat[]): MonitoredChat[] {
  return [...items].sort((a, b) => {
    if (a.is_active !== b.is_active) return a.is_active ? -1 : 1;
    const ta = (a.title || String(a.chat_id)).toLowerCase();
    const tb = (b.title || String(b.chat_id)).toLowerCase();
    return ta.localeCompare(tb, "ru");
  });
}

const filteredChats = computed(() => {
  const q = search.value.trim().toLowerCase();
  return sortChats(chats.value).filter((chat) => {
    if (activeOnly.value && !chat.is_active) return false;
    if (!q) return true;
    const title = (chat.title || String(chat.chat_id)).toLowerCase();
    return title.includes(q) || String(chat.chat_id).includes(q);
  });
});

async function load() {
  const data = await sellerApi.workerChats(workerId);
  chats.value = data.chats;
}

async function syncChats() {
  syncing.value = true;
  error.value = "";
  try {
    await sellerApi.syncWorkerChats(workerId);
    await new Promise((resolve) => setTimeout(resolve, 2000));
    await load();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Не удалось обновить чаты";
  } finally {
    syncing.value = false;
  }
}

async function toggle(chat: MonitoredChat) {
  toggling.value = chat.chat_id;
  error.value = "";
  try {
    await sellerApi.setChatWhitelist(workerId, [
      { chat_id: chat.chat_id, is_active: !chat.is_active },
    ]);
    await load();
  } catch (e) {
    error.value = e instanceof Error ? e.message : "Не удалось изменить статус";
  } finally {
    toggling.value = null;
  }
}

onMounted(() => {
  load().catch((e) => {
    error.value = e instanceof Error ? e.message : "Ошибка загрузки";
  });
});
</script>

<template>
  <div>
    <p><RouterLink to="/workers">← Воркеры</RouterLink></p>
    <h2>Чаты воркера #{{ workerId }}</h2>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card row controls">
      <input v-model="search" type="search" placeholder="Поиск по названию или ID" />
      <label>
        <input v-model="activeOnly" type="checkbox" />
        Только включённые
      </label>
      <button type="button" :disabled="syncing" @click="syncChats">
        {{ syncing ? "Обновляем…" : "Обновить из Telegram" }}
      </button>
    </div>

    <p v-if="chats.length === 0 && !error" class="muted">
      Чаты не синхронизированы. Убедитесь, что worker-engine запущен, и нажмите «Обновить из Telegram».
    </p>

    <div v-else class="card">
      <table>
        <thead>
          <tr>
            <th>Название</th>
            <th>Тип</th>
            <th>Мониторинг</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="chat in filteredChats" :key="chat.id">
            <td>{{ chat.title || chat.chat_id }}</td>
            <td>{{ chat.type || "—" }}</td>
            <td>
              <button
                type="button"
                class="secondary"
                :disabled="toggling === chat.chat_id"
                @click="toggle(chat)"
              >
                {{ chat.is_active ? "Включён" : "Выключен" }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="filteredChats.length === 0" class="muted">Ничего не найдено.</p>
      <p v-else class="muted">Показано {{ filteredChats.length }} из {{ chats.length }}.</p>
    </div>
  </div>
</template>

<style scoped>
.controls {
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.controls input[type="search"] {
  min-width: 220px;
}

.muted {
  opacity: 0.75;
}
</style>
