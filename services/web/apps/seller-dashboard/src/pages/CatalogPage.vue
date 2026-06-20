<script setup lang="ts">
import { onMounted, ref } from "vue";
import { sellerApi, type Product } from "../api";

const products = ref<Product[]>([]);
const error = ref("");
const title = ref("");
const price = ref("");
const keywords = ref("");

async function load() {
  const data = await sellerApi.products();
  products.value = data.products;
}

onMounted(() => {
  load().catch((e) => {
    error.value = e instanceof Error ? e.message : "Ошибка загрузки";
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
    <h2>Каталог</h2>
    <p v-if="error" class="error">{{ error }}</p>

    <div class="card">
      <h3>Добавить товар</h3>
      <form @submit.prevent="onCreate">
        <input v-model="title" placeholder="Название" required />
        <input v-model="price" placeholder="Цена" required />
        <input v-model="keywords" placeholder="Keywords через запятую" />
        <button type="submit">Добавить</button>
      </form>
    </div>

    <div class="card">
      <table>
        <thead>
          <tr>
            <th>Товар</th>
            <th>Цена</th>
            <th>Keywords</th>
            <th>Статус</th>
            <th />
          </tr>
        </thead>
        <tbody>
          <tr v-for="p in products" :key="p.id">
            <td>{{ p.title }}</td>
            <td>{{ p.price }}</td>
            <td>{{ p.keywords.join(", ") || "—" }}</td>
            <td>{{ p.is_active ? "активен" : "выкл" }}</td>
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
</template>
