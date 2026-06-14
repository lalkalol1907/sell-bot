const STATUS_EMOJI: Record<string, string> = {
  new: "🆕",
  contacted: "📞",
  closed: "✅",
  spam: "🚫",
};

export function formatLeadLine(lead: { id: string; status: string; level: string; raw_text: string }): string {
  const emoji = STATUS_EMOJI[lead.status] ?? "•";
  const level = lead.level === "confirmed" ? "точная" : "вероятная";
  return `${emoji} #${lead.id} [${level}] «${lead.raw_text.slice(0, 60)}»`;
}
