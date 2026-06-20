import { createApiClient } from "@sellbot/api-client";

export type Seller = {
  id: number;
  tg_user_id: number;
  username: string;
  full_name: string;
  sensitivity: string;
  plan: string;
  is_owner: boolean;
};

export type Product = {
  id: number;
  seller_id: number;
  title: string;
  price: string;
  currency: string;
  keywords: string[];
  is_active: boolean;
};

export type Lead = {
  id: number;
  raw_text: string;
  level: string;
  status: string;
  product_id: number;
  author_id: number;
  author_username: string;
  score: number;
};

export type ProductLeadStat = {
  product_id: number;
  product_title: string;
  count: number;
};

export type TeamMember = {
  id: number;
  username: string;
  full_name: string;
  status: string;
  tg_user_id: number | null;
  joined_at: string | null;
};

export type Worker = {
  id: number;
  phone: string;
  status: string;
};

export type MonitoredChat = {
  id: number;
  worker_id: number;
  chat_id: number;
  title: string;
  type: string;
  is_active: boolean;
};

export type Stats = {
  total: number;
  new_count: number;
  contacted: number;
  closed: number;
  spam: number;
  by_product: ProductLeadStat[];
};

const { api } = createApiClient({ credentials: "include" });

export const authApi = {
  me: () => api<Seller>("/api/v1/auth/me"),
  logout: () => api<void>("/api/v1/auth/logout", { method: "POST" }),
  telegram: (payload: Record<string, string | number>) =>
    api<Seller>("/api/v1/auth/telegram", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};

export const sellerApi = {
  stats: (days = 30) => api<Stats>(`/api/v1/seller/stats?days=${days}`),
  products: () => api<{ products: Product[] }>("/api/v1/seller/products"),
  createProduct: (product: Omit<Product, "id" | "seller_id">) =>
    api<Product>("/api/v1/seller/products", {
      method: "POST",
      body: JSON.stringify({ product }),
    }),
  updateProduct: (id: number, product: Partial<Product>) =>
    api<Product>(`/api/v1/seller/products/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ product }),
    }),
  deleteProduct: (id: number) =>
    api<{ success: boolean }>(`/api/v1/seller/products/${id}`, { method: "DELETE" }),
  leads: (status = "") =>
    api<{ leads: Lead[]; total: number }>(
      `/api/v1/seller/leads${status ? `?status=${encodeURIComponent(status)}` : ""}`,
    ),
  updateLead: (id: number, status: string) =>
    api<Lead>(`/api/v1/seller/leads/${id}`, {
      method: "PATCH",
      body: JSON.stringify({ lead: { status } }),
    }),
  workers: () => api<{ workers: Worker[] }>("/api/v1/seller/workers"),
  updateWorkerStatus: (id: number, status: string) =>
    api<Worker>(`/api/v1/seller/workers/${id}/status`, {
      method: "PATCH",
      body: JSON.stringify({ worker: { status } }),
    }),
  workerChats: (workerId: number) =>
    api<{ chats: MonitoredChat[] }>(`/api/v1/seller/workers/${workerId}/chats`),
  setChatWhitelist: (workerId: number, entries: { chat_id: number; is_active: boolean }[]) =>
    api<{ updated: number }>(`/api/v1/seller/workers/${workerId}/chats/whitelist`, {
      method: "PATCH",
      body: JSON.stringify({ entries }),
    }),
  syncWorkerChats: (workerId: number) =>
    api<{ ok: boolean }>(`/api/v1/seller/workers/${workerId}/chats/sync`, { method: "POST" }),
  updateSettings: (sensitivity: string) =>
    api<{ id: number; sensitivity: string }>("/api/v1/seller/settings", {
      method: "PATCH",
      body: JSON.stringify({ settings: { sensitivity } }),
    }),
  createLoginHandoff: () =>
    api<{ token: string; url: string }>("/api/v1/login/handoff", { method: "POST" }),
  team: () => api<{ members: TeamMember[]; is_owner: boolean }>("/api/v1/seller/team"),
  inviteTeamMember: (username: string) =>
    api<TeamMember>("/api/v1/seller/team", {
      method: "POST",
      body: JSON.stringify({ username }),
    }),
  removeTeamMember: (id: number) =>
    api<{ success: boolean }>(`/api/v1/seller/team/${id}`, { method: "DELETE" }),
};
