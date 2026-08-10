import { apiFetch } from "@/lib/api/client";

export type TransactionType =
  | "purchase"
  | "refund"
  | "fee"
  | "interest"
  | "payment_to_issuer"
  | "opening_balance"
  | "adjustment"
  | "reversal"
  | "transfer_out"
  | "transfer_in"
  | "emi_interest"
  | "emi_gst"
  | "emi_fees";

export type PostingStatus = "draft" | "posted";

export type TransactionSplit = {
  id: string;
  transaction_id: string;
  category_id: string;
  amount_paise: number;
  created_at: string;
  updated_at: string;
};

export type Transaction = {
  id: string;
  organization_id: string;
  account_id: string;
  credit_card_id: string | null;
  contact_id: string | null;
  statement_id: string | null;
  type: TransactionType;
  posting_status: PostingStatus;
  amount_paise: number;
  gst_paise: number | null;
  currency: string;
  occurred_at: string;
  merchant: string;
  category_id: string | null;
  transfer_group_id: string | null;
  category: string | null;
  notes: string | null;
  correction_reason: string | null;
  delta_sign: number | null;
  reverses_id: string | null;
  reversed_by_id: string | null;
  created_by: string | null;
  tags: string[];
  created_at: string;
  updated_at: string;
  splits: TransactionSplit[];
};

export type TransactionCreate = {
  account_id?: string | null;
  credit_card_id?: string | null;
  type: TransactionType;
  amount_paise: number;
  gst_paise?: number | null;
  occurred_at: string;
  merchant: string;
  contact_id?: string | null;
  category_id?: string | null;
  category?: string | null;
  notes?: string | null;
  currency?: string;
  posting_status?: PostingStatus;
  tags?: string[];
  transfer_group_id?: string | null;
};

export type TransactionUpdate = Partial<{
  type: TransactionType;
  amount_paise: number;
  gst_paise: number | null;
  occurred_at: string;
  merchant: string;
  contact_id: string | null;
  category_id: string | null;
  category: string | null;
  notes: string | null;
  tags: string[];
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
  accountId?: string;
  cardId?: string;
  contactId?: string;
  categoryId?: string;
  type?: TransactionType;
  postingStatus?: PostingStatus;
  q?: string;
  dateFrom?: string;
  dateTo?: string;
};

/** Types offered on the create form (corrections use reverse/adjust). */
export const TRANSACTION_TYPES: { value: TransactionType; label: string }[] = [
  { value: "purchase", label: "Purchase" },
  { value: "refund", label: "Refund" },
  { value: "fee", label: "Fee" },
  { value: "interest", label: "Interest" },
  { value: "payment_to_issuer", label: "Payment to issuer" },
];

export function listTransactions(accessToken: string, opts: ListTransactionsOpts = {}) {
  const q = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.pageSize ?? 50),
  });
  if (opts.accountId) q.set("account_id", opts.accountId);
  if (opts.cardId) q.set("card_id", opts.cardId);
  if (opts.contactId) q.set("contact_id", opts.contactId);
  if (opts.categoryId) q.set("category_id", opts.categoryId);
  if (opts.type) q.set("type", opts.type);
  if (opts.postingStatus) q.set("posting_status", opts.postingStatus);
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

export function postTransaction(accessToken: string, id: string) {
  return apiFetch<Transaction>(
    `/api/v1/transactions/${id}/post`,
    { method: "POST" },
    { accessToken },
  );
}

export function reverseTransaction(
  accessToken: string,
  id: string,
  body: { reason: string; occurred_at?: string },
) {
  return apiFetch<Transaction>(
    `/api/v1/transactions/${id}/reverse`,
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateTransaction(accessToken: string, id: string, body: TransactionUpdate) {
  return apiFetch<Transaction>(
    `/api/v1/transactions/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function deleteTransaction(accessToken: string, id: string) {
  return apiFetch<void>(`/api/v1/transactions/${id}`, { method: "DELETE" }, { accessToken });
}

export function replaceTransactionSplits(
  accessToken: string,
  id: string,
  splits: { category_id: string; amount_paise: number }[],
) {
  return apiFetch<Transaction>(
    `/api/v1/transactions/${id}/splits`,
    { method: "PUT", body: JSON.stringify(splits) },
    { accessToken },
  );
}
