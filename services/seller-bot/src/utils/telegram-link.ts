/** Build t.me/c/ link for supergroup/channel messages (MTProto chat_id format). */
export function chatMessageLink(chatId: number, messageId: number): string | null {
  if (!chatId || !messageId) return null;
  const raw = String(chatId);
  if (!raw.startsWith("-100")) return null;
  return `https://t.me/c/${raw.slice(4)}/${messageId}`;
}
