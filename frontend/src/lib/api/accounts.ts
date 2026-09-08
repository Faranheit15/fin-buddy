import { apiFetch } from "@/lib/api/client";
import type { Paginated } from "@/lib/api/cards";
import type { Transaction } from "@/lib/api/transactions";

export type AccountKind = "bank" | "cash" | "wallet" | "credit_card";

export type AccountResponse = {
  id: string;
  organization_id: string;
  kind: AccountKind;
  name: string;
  institution: string | null;
  currency: string;
  credit_card_id: string | null;
  archived_at: string | null;
  balance_paise: number;
  created_at: string;
  updated_at: string;
};

export type AccountCreate = {
  kind: "bank" | "cash" | "wallet";
  name: string;
  institution?: string | null;
  currency?: string;
  opening_balance_paise?: number | null;
};

export type AccountUpdate = {
  name?: string | null;
  institution?: string | null;
};

export type CorrectBalanceRequest = {
  target_balance_paise: number;
  reason: string;
  occurred_at?: string | null;
};

export function listAccounts(
  accessToken: string,
  page = 1,
  pageSize = 50,
  kind?: AccountKind,
  includeArchived = false,
) {
  const q = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
    include_archived: String(includeArchived),
  });
  if (kind) q.set("kind", kind);
  return apiFetch<Paginated<AccountResponse>>(
    `/api/v1/accounts?${q}`,
    { method: "GET" },
    { accessToken },
  );
}

export function getAccount(accessToken: string, id: string) {
  return apiFetch<AccountResponse>(`/api/v1/accounts/${id}`, { method: "GET" }, { accessToken });
}

export function createAccount(
  accessToken: string,
  body: AccountCreate,
  options?: { idempotencyKey?: string },
) {
  return apiFetch<AccountResponse>(
    "/api/v1/accounts",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken, idempotencyKey: options?.idempotencyKey },
  );
}

export function updateAccount(accessToken: string, id: string, body: AccountUpdate) {
  return apiFetch<AccountResponse>(
    `/api/v1/accounts/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function archiveAccount(accessToken: string, id: string) {
  return apiFetch<AccountResponse>(
    `/api/v1/accounts/${id}/archive`,
    { method: "POST" },
    { accessToken },
  );
}

export function correctBalance(
  accessToken: string,
  id: string,
  body: CorrectBalanceRequest,
  options?: { idempotencyKey?: string },
) {
  return apiFetch<Transaction>(
    `/api/v1/accounts/${id}/correct-balance`,
    { method: "POST", body: JSON.stringify(body) },
    { accessToken, idempotencyKey: options?.idempotencyKey },
  );
}
