import { apiFetch } from "@/lib/api/client";
import { type Transaction } from "@/lib/api/transactions";

export type TransferCreate = {
  from_account_id: string;
  to_account_id: string;
  amount_paise: number;
  occurred_at: string;
  merchant?: string | null;
  notes?: string | null;
  posting_status?: "draft" | "posted";
};

export function createTransfer(
  accessToken: string,
  body: TransferCreate,
  options?: { idempotencyKey?: string },
) {
  return apiFetch<[Transaction, Transaction]>(
    "/api/v1/transfers",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken, idempotencyKey: options?.idempotencyKey },
  );
}
