/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_BOT_USERNAME: string;
  readonly VITE_MINIAPP_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

interface Window {
  onTelegramAuth?: (user: Record<string, string | number>) => void;
}
