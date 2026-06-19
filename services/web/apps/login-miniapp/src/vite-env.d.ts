/// <reference types="vite/client" />

interface TelegramWebApp {
  ready(): void;
  expand(): void;
  close(): void;
  sendData(data: string): void;
  initData: string;
}

interface Window {
  Telegram?: {
    WebApp?: TelegramWebApp;
  };
}
