export function parseApiDate(value) {
  if (!value) return null;
  if (value instanceof Date) return value;

  const text = String(value).trim();
  const normalized = text.includes('T') && !/[zZ]|[+-]\d{2}:\d{2}$/.test(text)
    ? `${text}Z`
    : text;

  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}
