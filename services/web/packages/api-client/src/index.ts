export type ApiFetchOptions = RequestInit;

export type ApiErrorBody = {
  error?: string;
  message?: string;
};

export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export type CreateApiClientOptions = {
  getHeaders?: () => HeadersInit;
  credentials?: RequestCredentials;
};

export function createApiClient(options: CreateApiClientOptions = {}) {
  const { getHeaders, credentials } = options;

  async function api<T>(path: string, init: ApiFetchOptions = {}): Promise<T> {
    const headers = new Headers(init.headers);

    if (!(init.body instanceof FormData) && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }

    const extra = getHeaders?.();
    if (extra) {
      new Headers(extra).forEach((value, key) => {
        headers.set(key, value);
      });
    }

    const res = await fetch(path, {
      ...init,
      headers,
      credentials: init.credentials ?? credentials,
    });

    if (res.status === 204) {
      return undefined as T;
    }

    const data = (await res.json().catch(() => ({}))) as ApiErrorBody;
    if (!res.ok) {
      throw new ApiError(data.error ?? data.message ?? `HTTP ${res.status}`, res.status);
    }

    return data as T;
  }

  return { api };
}
