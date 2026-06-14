export function normalizePhone(raw: string): string {
  const digits = raw.replace(/\s/g, "");
  if (digits.startsWith("+")) return digits;
  if (digits.startsWith("8") && digits.length === 11) return `+7${digits.slice(1)}`;
  return `+${digits}`;
}
