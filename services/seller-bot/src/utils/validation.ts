export function isValidPrice(text: string): boolean {
  return /^\d+([.,]\d+)?$/.test(text.trim());
}

export function normalizePrice(text: string): string {
  return text.trim().replace(",", ".");
}
