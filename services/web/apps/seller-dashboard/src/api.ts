export type Seller = {
  id: number;
  tg_user_id: number;
  username: string;
  full_name: string;
  sensitivity: string;
  plan: string;
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
  author_username: string;
  score: number;
};

export type Worker = {
  id: number;
  phone: string;
  status: string;
};

export type Stats = {
  total: number;
  new_count: number;
  contacted: number;
  closed: number;
  spam: number;
};

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(path, {
    ...options,
    headers,
    credentials: "include",
  });

  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.error ?? `HTTP ${res.status}`);
  }
  return data as T;
}

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
  updateSettings: (sensitivity: string) =>
    api<{ id: number; sensitivity: string }>("/api/v1/seller/settings", {
      method: "PATCH",
      body: JSON.stringify({ settings: { sensitivity } }),
    }),
  createLoginHandoff: () =>
    api<{ token: string; url: string }>("/api/v1/login/handoff", { method: "POST" }),
};
