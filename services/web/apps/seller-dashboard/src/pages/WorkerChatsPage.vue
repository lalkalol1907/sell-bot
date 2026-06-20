<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRoute, RouterLink } from "vue-router";
import { sellerApi, type MonitoredChat } from "../api";

const route = useRoute();
const workerId = Number(route.params.id);

const chats = ref<MonitoredChat[]>([]);
const error = ref("");
const loading = ref(true);
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
  load()
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
    <RouterLink to="/workers" class="back-link">← Воркеры</RouterLink>
    <header class="page-header">
      <h2>Чаты воркера #{{ workerId }}</h2>
      <p>Выберите группы и каналы для мониторинга</p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="card toolbar">
      <input v-model="search" type="search" placeholder="Поиск по названию или ID" />
      <label>
        <input v-model="activeOnly" type="checkbox" />
        Только включённые
      </label>
      <button type="button" :disabled="syncing" @click="syncChats">
        {{ syncing ? "Обновляем…" : "Обновить из Telegram" }}
      </button>
    </div>

    <div class="card">
      <div v-if="loading" class="empty-state">Загрузка…</div>
      <p v-else-if="chats.length === 0 && !error" class="empty-state">
        Чаты не синхронизированы. Убедитесь, что worker-engine запущен, и нажмите «Обновить из
        Telegram».
      </p>
      <template v-else>
        <div class="table-wrap">
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
                    :class="chat.is_active ? 'secondary' : 'ghost'"
                    :disabled="toggling === chat.chat_id"
                    @click="toggle(chat)"
                  >
                    {{ chat.is_active ? "Включён" : "Выключен" }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <p v-if="filteredChats.length === 0" class="muted table-meta">
          Ничего не найдено.
        </p>
        <p v-else class="muted table-meta">
          Показано {{ filteredChats.length }} из {{ chats.length }}.
        </p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--color-muted);
  font-size: 0.9rem;
  margin-bottom: 12px;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--color-primary);
}

.table-meta {
  margin-top: 12px;
}
</style>
