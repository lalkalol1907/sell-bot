<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type Product } from "../api";

const products = ref<Product[]>([]);
const error = ref("");
const loading = ref(true);
const title = ref("");
const price = ref("");
const keywords = ref("");

async function load() {
  const data = await sellerApi.products();
  products.value = data.products;
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

async function onCreate() {
  error.value = "";
  try {
    await sellerApi.createProduct({
      title: title.value,
      price: price.value,
      currency: "RUB",
      keywords: keywords.value
        .split(",")
        .map((k) => k.trim())
        .filter(Boolean),
      is_active: true,
    });
    title.value = "";
    price.value = "";
    keywords.value = "";
    await load();
  } catch (err) {
    error.value = err instanceof Error ? err.message : "Ошибка";
  }
}

async function toggle(product: Product) {
  await sellerApi.updateProduct(product.id, {
    title: product.title,
    price: product.price,
    currency: product.currency,
    keywords: product.keywords,
    is_active: !product.is_active,
  });
  await load();
}

async function remove(id: number) {
  await sellerApi.deleteProduct(id);
  await load();
}
</script>

<template>
  <div>
    <header class="page-header">
      <h2>Каталог</h2>
      <p>Товары для сопоставления с сообщениями в чатах</p>
    </header>

    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h3>Добавить товар</h3>
      <form class="form-grid" @submit.prevent="onCreate">
        <input v-model="title" placeholder="Название" required />
        <input v-model="price" placeholder="Цена" required />
        <input v-model="keywords" placeholder="Ключевые слова через запятую" />
        <div>
          <button type="submit">Добавить</button>
        </div>
      </form>
    </div>

    <div class="card">
      <div v-if="loading" class="empty-state">Загрузка…</div>
      <div v-else-if="products.length === 0" class="empty-state">Товаров пока нет</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Товар</th>
              <th>Цена</th>
              <th>Ключевые слова</th>
              <th>Статус</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in products" :key="p.id">
              <td>{{ p.title }}</td>
              <td>{{ p.price }} {{ p.currency }}</td>
              <td>{{ p.keywords.join(", ") || "—" }}</td>
              <td>
                <span :class="p.is_active ? 'badge badge-on' : 'badge badge-off'">
                  {{ p.is_active ? "Активен" : "Выключен" }}
                </span>
              </td>
              <td class="row">
                <button class="secondary" @click="toggle(p)">
                  {{ p.is_active ? "Выключить" : "Включить" }}
                </button>
                <button class="danger" @click="remove(p.id)">Удалить</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
