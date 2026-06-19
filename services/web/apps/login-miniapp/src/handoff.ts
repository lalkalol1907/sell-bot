const HANDOFF_STORAGE_KEY = "login_handoff";

export function initHandoffToken(): string {
  const params = new URLSearchParams(window.location.search);
  const fromUrl = params.get("handoff");
  if (fromUrl) {
    sessionStorage.setItem(HANDOFF_STORAGE_KEY, fromUrl);
    params.delete("handoff");
    const query = params.toString();
    const next = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
    window.history.replaceState({}, "", next);
  }
  return sessionStorage.getItem(HANDOFF_STORAGE_KEY) ?? "";
}

export function getHandoffToken(): string {
  return sessionStorage.getItem(HANDOFF_STORAGE_KEY) ?? "";
}
