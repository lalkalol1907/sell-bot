<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type TeamMember } from "../api";

const members = ref<TeamMember[]>([]);
const isOwner = ref(false);
const username = ref("");
const error = ref("");
const loading = ref(true);
const inviting = ref(false);

const statusLabels: Record<string, string> = {
  pending: "Ожидает /start в боте",
  active: "Подключён",
};

async function load() {
  const data = await sellerApi.team();
  members.value = data.members;
  isOwner.value = data.is_owner;
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

async function onInvite() {
  error.value = "";
  inviting.value = true;
  try {
    await sellerApi.inviteTeamMember(username.value);
    username.value = "";
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Не удалось пригласить";
  } finally {
    inviting.value = false;
  }
}

async function onRemove(id: number) {
  error.value = "";
  try {
    await sellerApi.removeTeamMember(id);
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Не удалось удалить";
  }
}
</script>

<template>
  <div>
    <header class="page-header">
      <h2>Команда</h2>
      <p>Сотрудники с доступом к боту и дашборду вашего аккаунта</p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="isOwner" class="card">
      <h3>Пригласить сотрудника</h3>
      <p class="muted">
        Укажите Telegram username без @. Сотрудник должен нажать /start в боте — после этого
        получит доступ.
      </p>
      <form class="form-grid" @submit.prevent="onInvite">
        <input v-model="username" placeholder="username" required />
        <div>
          <button type="submit" :disabled="inviting">
            {{ inviting ? "Отправляем…" : "Пригласить" }}
          </button>
        </div>
      </form>
    </div>

    <div class="card">
      <div v-if="loading" class="empty-state">Загрузка…</div>
      <div v-else-if="members.length === 0" class="empty-state">Сотрудников пока нет</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Username</th>
              <th>Имя</th>
              <th>Статус</th>
              <th v-if="isOwner" />
            </tr>
          </thead>
          <tbody>
            <tr v-for="member in members" :key="member.id">
              <td>@{{ member.username }}</td>
              <td>{{ member.full_name || "—" }}</td>
              <td>{{ statusLabels[member.status] ?? member.status }}</td>
              <td v-if="isOwner" class="row">
                <button class="danger" @click="onRemove(member.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
