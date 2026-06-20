<script setup lang="ts">
import { ref, watch } from "vue";
import { sellerApi, type Lead } from "../api";

const statusLabels: Record<string, string> = {
  "": "Все",
  new: "Новые",
  contacted: "В работе",
  closed: "Закрытые",
  spam: "Спам",
};

const statusBadges: Record<string, string> = {
  new: "badge-new",
  contacted: "badge-contacted",
  closed: "badge-closed",
  spam: "badge-spam",
};

const statuses = ["", "new", "contacted", "closed", "spam"];

function authorUrl(authorId: number): string | null {
  if (!authorId || authorId <= 0) return null;
  return `tg://user?id=${authorId}`;
}

const leads = ref<Lead[]>([]);
const filter = ref("");
const error = ref("");
const loading = ref(true);

async function load(status = filter.value) {
  loading.value = true;
  try {
    const data = await sellerApi.leads(status);
    leads.value = data.leads;
  } finally {
    loading.value = false;
  }
}

watch(
  filter,
  () => {
    load().catch((e) => {
      error.value = e instanceof Error ? e.message : "Ошибка загрузки";
    });
  },
  { immediate: true },
);

async function setStatus(id: number, status: string) {
  await sellerApi.updateLead(id, status);
  await load();
}
</script>

<template>
  <div>
    <header class="page-header">
      <h2>Лиды</h2>
      <p>Входящие сообщения из мониторинга чатов</p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <select v-model="filter">
      <option v-for="s in statuses" :key="s || 'all'" :value="s">
        {{ statusLabels[s] ?? s }}
      </option>
    </select>

    <div class="card">
      <div v-if="loading" class="empty-state">Загрузка…</div>
      <div v-else-if="leads.length === 0" class="empty-state">Лидов не найдено</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Текст</th>
              <th>Уровень</th>
              <th>Статус</th>
              <th>Автор</th>
              <th>Контакт</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="lead in leads" :key="lead.id">
              <td class="lead-text">{{ lead.raw_text }}</td>
              <td>{{ lead.level }}</td>
              <td>
                <span :class="['badge', statusBadges[lead.status] ?? 'badge-off']">
                  {{ statusLabels[lead.status] ?? lead.status }}
                </span>
              </td>
              <td>{{ lead.author_username ? `@${lead.author_username}` : "—" }}</td>
              <td>
                <a
                  v-if="authorUrl(lead.author_id)"
                  class="author-link"
                  :href="authorUrl(lead.author_id)!"
                >
                  Написать
                </a>
                <span v-else>—</span>
              </td>
              <td class="row">
                <button @click="setStatus(lead.id, 'contacted')">В работе</button>
                <button class="secondary" @click="setStatus(lead.id, 'closed')">Закрыть</button>
                <button class="danger" @click="setStatus(lead.id, 'spam')">Спам</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lead-text {
  max-width: 320px;
}

.author-link {
  color: var(--color-primary, #2563eb);
  font-weight: 500;
  text-decoration: none;
}

.author-link:hover {
  text-decoration: underline;
}
</style>
