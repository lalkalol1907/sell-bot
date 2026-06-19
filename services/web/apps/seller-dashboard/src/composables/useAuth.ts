import { ref } from "vue";
import { authApi, type Seller } from "../api";

const seller = ref<Seller | null>(null);
const loading = ref(true);
let ready: Promise<void> | undefined;

async function refresh() {
  try {
    seller.value = await authApi.me();
  } catch {
    seller.value = null;
  } finally {
    loading.value = false;
  }
}

async function loginWithTelegram(payload: Record<string, string | number>) {
  await authApi.telegram(payload);
  try {
    seller.value = await authApi.me();
  } catch {
    seller.value = null;
    throw new Error(
      "Сессия не создана. Выполните /start в боте и привяжите домен через @BotFather → /setdomain.",
    );
  }
}

async function logout() {
  await authApi.logout();
  seller.value = null;
}

export function initAuth() {
  ready = refresh();
}

export function waitForAuth() {
  return ready ?? refresh();
}

export function useAuth() {
  return { seller, loading, refresh, loginWithTelegram, logout };
}
