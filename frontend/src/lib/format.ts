/**
 * India-first display helpers.
 * Ledger math must never use these — only presentation.
 */

const inrFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 2,
});

const inrCompact = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1,
});

const dateFormatter = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata",
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const dateShortFormatter = new Intl.DateTimeFormat("en-IN", {
  timeZone: "Asia/Kolkata",
  day: "2-digit",
  month: "short",
});

/** Format integer paise as INR for display. */
export function formatInrFromPaise(paise: number): string {
  return inrFormatter.format(paise / 100);
}

export function formatInrCompactFromPaise(paise: number): string {
  return inrCompact.format(paise / 100);
}

export function formatInr(rupees: number): string {
  return inrFormatter.format(rupees);
}

export function formatDateIst(value: Date | string): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return dateFormatter.format(date);
}

export function formatDateShortIst(value: Date | string): string {
  const date = typeof value === "string" ? new Date(value) : value;
  return dateShortFormatter.format(date);
}

export function formatPercent(value: number, digits = 0): string {
  return `${value.toFixed(digits)}%`;
}

/** Days until date in IST calendar sense (approx using local offset-safe UTC noon). */
export function daysUntil(value: Date | string, now = new Date()): number {
  const target = typeof value === "string" ? new Date(value) : value;
  const msPerDay = 24 * 60 * 60 * 1000;
  const start = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
  const end = Date.UTC(target.getFullYear(), target.getMonth(), target.getDate());
  return Math.round((end - start) / msPerDay);
}

export function formatRelativeDue(value: Date | string, now = new Date()): string {
  const d = daysUntil(value, now);
  if (d < 0) return `${Math.abs(d)}d overdue`;
  if (d === 0) return "Due today";
  if (d === 1) return "Due tomorrow";
  return `Due in ${d}d`;
}
