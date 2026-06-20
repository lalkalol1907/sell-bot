import { createRouter, createWebHistory } from "vue-router";
import { useAuth, waitForAuth } from "../composables/useAuth";
import Layout from "../components/Layout.vue";
import CatalogPage from "../pages/CatalogPage.vue";
import LeadsPage from "../pages/LeadsPage.vue";
import LoginPage from "../pages/LoginPage.vue";
import StatsPage from "../pages/StatsPage.vue";
import TeamPage from "../pages/TeamPage.vue";
import WorkersPage from "../pages/WorkersPage.vue";
import WorkerChatsPage from "../pages/WorkerChatsPage.vue";

export const router = createRouter({
  history: createWebHistory("/dashboard/"),
  routes: [
    {
      path: "/login",
      name: "login",
      component: LoginPage,
      meta: { guest: true },
    },
    {
      path: "/",
      component: Layout,
      meta: { requiresAuth: true },
      children: [
        { path: "", name: "stats", component: StatsPage },
        { path: "catalog", name: "catalog", component: CatalogPage },
        { path: "leads", name: "leads", component: LeadsPage },
        { path: "team", name: "team", component: TeamPage },
        { path: "workers", name: "workers", component: WorkersPage },
        { path: "workers/:id/chats", name: "worker-chats", component: WorkerChatsPage },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  await waitForAuth();
  const { seller } = useAuth();

  if (to.meta.requiresAuth && !seller.value) {
    return { name: "login" };
  }

  if (to.meta.guest && seller.value) {
    return { name: "stats" };
  }

  return true;
});
