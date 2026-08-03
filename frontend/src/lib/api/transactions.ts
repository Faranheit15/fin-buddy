import { apiFetch } from "@/lib/api/client";

export type TransactionType =
  | "purchase"
  | "refund"
  | "fee"
  | "interest"
  | "payment_to_issuer"
  | "opening_balance";

export type Transaction = {
  id: string;
  organization_id: string;
  credit_card_id: string;
  contact_id: string | null;
  statement_id: string | null;
  type: TransactionType;
  amount_paise: number;
  currency: string;
  occurred_at: string;
  merchant: string;
  category: string | null;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type TransactionCreate = {
  credit_card_id: string;
  type: TransactionType;
  amount_paise: number;
  occurred_at: string;
  merchant: string;
  contact_id?: string | null;
  category?: string | null;
  notes?: string | null;
  currency?: string;
};

export type TransactionUpdate = Partial<{
  type: TransactionType;
  amount_paise: number;
  occurred_at: string;
  merchant: string;
  contact_id: string | null;
  category: string | null;
  notes: string | null;
}>;

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type ListTransactionsOpts = {
  page?: number;
  pageSize?: number;
  cardId?: string;
  contactId?: string;
  type?: TransactionType;
  q?: string;
  dateFrom?: string;
  dateTo?: string;
};

export function listTransactions(accessToken: string, opts: ListTransactionsOpts = {}) {
  const q = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.pageSize ?? 50),
  });
  if (opts.cardId) q.set("card_id", opts.cardId);
  if (opts.contactId) q.set("contact_id", opts.contactId);
  if (opts.type) q.set("type", opts.type);
  if (opts.q) q.set("q", opts.q);
  if (opts.dateFrom) q.set("date_from", opts.dateFrom);
  if (opts.dateTo) q.set("date_to", opts.dateTo);
  return apiFetch<Paginated<Transaction>>(
    `/api/v1/transactions?${q}`,
    { method: "GET" },
    { accessToken },
  );
}

export function createTransaction(accessToken: string, body: TransactionCreate) {
  return apiFetch<Transaction>(
    "/api/v1/transactions",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateTransaction(
  accessToken: string,
  id: string,
  body: TransactionUpdate,
) {
  return apiFetch<Transaction>(
    `/api/v1/transactions/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function deleteTransaction(accessToken: string, id: string) {
  return apiFetch<void>(`/api/v1/transactions/${id}`, { method: "DELETE" }, { accessToken });
}

export const TRANSACTION_TYPES: { value: TransactionType; label: string }[] = [
  { value: "purchase", label: "Purchase" },
  { value: "refund", label: "Refund" },
  { value: "fee", label: "Fee" },
  { value: "interest", label: "Interest" },
  { value: "payment_to_issuer", label: "Payment to issuer" },
];
