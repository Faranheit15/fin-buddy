import { apiFetch } from "@/lib/api/client";

export type CardNetwork = "visa" | "mastercard" | "rupay" | "amex" | "other";
export type DueRuleType = "fixed_day" | "days_after_statement";
export type CardStatus = "active" | "closed";

export type CreditCard = {
  id: string;
  organization_id: string;
  nickname: string;
  issuer: string;
  network: CardNetwork;
  last_four: string;
  credit_limit_paise: number;
  currency: string;
  statement_day: number;
  due_rule_type: DueRuleType;
  due_rule_value: number;
  status: CardStatus;
  held_by_contact_id: string | null;
  notes: string | null;
  outstanding_paise: number | null;
  spend_outstanding_paise: number | null;
  emi_principal_blocked_paise: number | null;
  available_credit_paise: number | null;
  utilization_percent: number | null;
  next_statement_date: string | null;
  next_due_date: string | null;
  created_at: string;
  updated_at: string;
};

export type CreditCardCreate = {
  nickname: string;
  issuer: string;
  network: CardNetwork;
  last_four: string;
  credit_limit_paise: number;
  currency?: string;
  statement_day: number;
  due_rule_type: DueRuleType;
  due_rule_value: number;
  notes?: string | null;
  opening_balance_paise?: number | null;
};

export type CreditCardUpdate = Partial<{
  nickname: string;
  issuer: string;
  network: CardNetwork;
  credit_limit_paise: number;
  statement_day: number;
  due_rule_type: DueRuleType;
  due_rule_value: number;
  status: CardStatus;
  notes: string | null;
}>;

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function listCards(accessToken: string, page = 1, pageSize = 50) {
  const q = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  return apiFetch<Paginated<CreditCard>>(`/api/v1/cards?${q}`, { method: "GET" }, { accessToken });
}

export function getCard(accessToken: string, id: string) {
  return apiFetch<CreditCard>(`/api/v1/cards/${id}`, { method: "GET" }, { accessToken });
}

export function createCard(
  accessToken: string,
  body: CreditCardCreate,
  options?: { idempotencyKey?: string },
) {
  return apiFetch<CreditCard>(
    "/api/v1/cards",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken, idempotencyKey: options?.idempotencyKey },
  );
}

export function updateCard(accessToken: string, id: string, body: CreditCardUpdate) {
  return apiFetch<CreditCard>(
    `/api/v1/cards/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

/** Convert rupees string/number to paise integer. */
export function rupeesToPaise(rupees: string | number): number {
  const n = typeof rupees === "number" ? rupees : Number(rupees.replace(/,/g, ""));
  if (!Number.isFinite(n) || n < 0) return 0;
  return Math.round(n * 100);
}
