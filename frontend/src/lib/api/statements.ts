import { apiFetch } from "@/lib/api/client";
import { env } from "@/lib/env";

export type StatementStatus = "uploaded" | "parsing" | "needs_review" | "imported" | "failed";

export type LineReviewStatus = "pending" | "accepted" | "rejected" | "edited";

export type TransactionType =
  "purchase" | "refund" | "fee" | "interest" | "payment_to_issuer" | "opening_balance";

export type Statement = {
  id: string;
  organization_id: string;
  credit_card_id: string;
  period_start: string | null;
  period_end: string | null;
  statement_date: string | null;
  due_date: string | null;
  pdf_storage_path: string | null;
  status: StatementStatus;
  parse_error: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  lines_count?: number | null;
  pending_count?: number | null;
  accepted_count?: number | null;
  imported_count?: number | null;
};

export type StatementLine = {
  id: string;
  statement_id: string;
  organization_id: string;
  raw_payload: Record<string, unknown> | null;
  occurred_at: string | null;
  merchant: string | null;
  amount_paise: number | null;
  proposed_type: TransactionType | null;
  proposed_contact_id: string | null;
  review_status: LineReviewStatus;
  committed_transaction_id: string | null;
  created_at: string;
  updated_at: string;
};

export type StatementDetail = Statement & {
  lines: StatementLine[];
};

export type StatementImportResult = {
  created: number;
  skipped: number;
  status: StatementStatus;
  statement: Statement;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type StatementLineUpdate = {
  review_status?: LineReviewStatus;
  merchant?: string;
  amount_paise?: number;
  occurred_at?: string;
  proposed_type?: TransactionType;
  proposed_contact_id?: string | null;
  clear_contact?: boolean;
};

function apiBase(): string {
  if (typeof window !== "undefined") return "/api/backend";
  return env.BACKEND_URL.replace(/\/$/, "");
}

export function listStatements(
  accessToken: string,
  opts: { page?: number; pageSize?: number; cardId?: string; status?: StatementStatus } = {},
) {
  const q = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.pageSize ?? 50),
  });
  if (opts.cardId) q.set("card_id", opts.cardId);
  if (opts.status) q.set("status", opts.status);
  return apiFetch<Paginated<Statement>>(
    `/api/v1/statements?${q}`,
    { method: "GET" },
    { accessToken },
  );
}

export function getStatement(accessToken: string, id: string) {
  return apiFetch<StatementDetail>(`/api/v1/statements/${id}`, { method: "GET" }, { accessToken });
}

export async function uploadStatement(
  accessToken: string,
  body: {
    file: File | Blob;
    filename?: string;
    creditCardId: string;
    periodStart?: string;
    periodEnd?: string;
    statementDate?: string;
    dueDate?: string;
    autoParse?: boolean;
  },
): Promise<StatementDetail> {
  const form = new FormData();
  form.append(
    "file",
    body.file,
    body.filename ?? (body.file instanceof File ? body.file.name : "statement.txt"),
  );
  form.append("credit_card_id", body.creditCardId);
  if (body.periodStart) form.append("period_start", body.periodStart);
  if (body.periodEnd) form.append("period_end", body.periodEnd);
  if (body.statementDate) form.append("statement_date", body.statementDate);
  if (body.dueDate) form.append("due_date", body.dueDate);
  form.append("auto_parse", body.autoParse === false ? "false" : "true");

  const url = `${apiBase()}/api/v1/statements/upload`;
  const response = await fetch(url, {
    method: "POST",
    headers:
      typeof window === "undefined" && accessToken
        ? { Authorization: `Bearer ${accessToken}` }
        : undefined,
    body: form,
  });

  if (!response.ok) {
    let message = response.statusText || "Upload failed";
    try {
      const err = (await response.json()) as { error?: { message?: string } };
      message = err.error?.message ?? message;
    } catch {
      // ignore
    }
    const { ApiError } = await import("@/lib/api/client");
    throw new ApiError(message, response.status);
  }
  return (await response.json()) as StatementDetail;
}

export function parseStatement(accessToken: string, id: string) {
  return apiFetch<StatementDetail>(
    `/api/v1/statements/${id}/parse`,
    { method: "POST" },
    { accessToken },
  );
}

export function updateStatementLine(
  accessToken: string,
  statementId: string,
  lineId: string,
  body: StatementLineUpdate,
) {
  return apiFetch<StatementLine>(
    `/api/v1/statements/${statementId}/lines/${lineId}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function bulkReviewLines(
  accessToken: string,
  statementId: string,
  reviewStatus: LineReviewStatus,
  onlyPending = true,
) {
  return apiFetch<{ updated: number }>(
    `/api/v1/statements/${statementId}/lines/bulk-review`,
    {
      method: "POST",
      body: JSON.stringify({ review_status: reviewStatus, only_pending: onlyPending }),
    },
    { accessToken },
  );
}

export function importStatement(accessToken: string, id: string) {
  return apiFetch<StatementImportResult>(
    `/api/v1/statements/${id}/import`,
    { method: "POST" },
    { accessToken },
  );
}

/** Demo sample matching FinBuddySampleParser. */
export function finBuddySampleText(lastFour = "4821"): string {
  return `FINBUDDY_STATEMENT
CARD:${lastFour}
PERIOD:2026-06-15..2026-07-14
STATEMENT_DATE:2026-07-15
DUE_DATE:2026-08-04
---
2026-07-01|purchase|SWIGGY BANGALORE|2450.00
2026-07-05|purchase|AMAZON PAY|1299.00
2026-07-08|purchase|UBER TRIP|680.50
2026-07-10|refund|AMAZON PAY|500.00
2026-07-12|payment_to_issuer|PAYMENT THANK YOU|15000.00
`;
}

export const STATEMENT_STATUS_LABEL: Record<StatementStatus, string> = {
  uploaded: "Uploaded",
  parsing: "Parsing",
  needs_review: "Needs review",
  imported: "Imported",
  failed: "Failed",
};
