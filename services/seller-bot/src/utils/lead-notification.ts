import { chatMessageLink } from "./telegram-link.js";

export type LeadCreatedEvent = {
  lead_id: number;
  seller_id: number;
  tg_user_id: number;
  product_title: string;
  raw_text: string;
  chat_title: string;
  author_username: string;
  level: string;
  chat_id: number;
  message_id: number;
};

export function formatLeadNotification(event: LeadCreatedEvent): string {
  const prefix = event.level === "confirmed" ? "🔥 Новая заявка" : "💡 Возможная заявка";
  const link = chatMessageLink(event.chat_id, event.message_id);
  return [
    prefix,
    `Товар: ${event.product_title}`,
    `Запрос: «${event.raw_text}»`,
    `Чат: ${event.chat_title || event.chat_id}`,
    `Автор: ${event.author_username ? `@${event.author_username}` : "—"}`,
    link ? `Сообщение: ${link}` : "",
  ]
    .filter(Boolean)
    .join("\n");
}

export function leadActionCallback(status: string, leadId: number): string {
  return `lead:${status}:${leadId}`;
}
