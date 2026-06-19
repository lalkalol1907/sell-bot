<script setup lang="ts">
import { ref, watch } from "vue";
import { sellerApi, type Lead } from "../api";

const statuses = ["", "new", "contacted", "closed", "spam"];

const leads = ref<Lead[]>([]);
const filter = ref("");
const error = ref("");

async function load(status = filter.value) {
  const data = await sellerApi.leads(status);
  leads.value = data.leads;
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
    <h2>Лиды</h2>
    <p v-if="error" class="error">{{ error }}</p>

    <select v-model="filter">
      <option v-for="s in statuses" :key="s || 'all'" :value="s">
        {{ s || "Все" }}
      </option>
    </select>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Текст</th>
            <th>Уровень</th>
            <th>Статус</th>
            <th>Автор</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="lead in leads" :key="lead.id">
            <td>{{ lead.raw_text }}</td>
            <td>{{ lead.level }}</td>
            <td>{{ lead.status }}</td>
            <td>{{ lead.author_username || "—" }}</td>
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
</template>
