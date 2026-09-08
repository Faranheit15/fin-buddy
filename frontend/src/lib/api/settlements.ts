import { apiFetch } from "@/lib/api/client";

export type SettlementMethod = "upi" | "cash" | "bank_transfer" | "other";

export type Settlement = {
  id: string;
  organization_id: string;
  contact_id: string;
  amount_paise: number;
  currency: string;
  settled_at: string;
  method: SettlementMethod;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type SettlementCreate = {
  contact_id: string;
  amount_paise: number;
  settled_at: string;
  method: SettlementMethod;
  notes?: string | null;
  currency?: string;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function listSettlements(
  accessToken: string,
  opts: { page?: number; pageSize?: number; contactId?: string } = {},
) {
  const q = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.pageSize ?? 50),
  });
  if (opts.contactId) q.set("contact_id", opts.contactId);
  return apiFetch<Paginated<Settlement>>(
    `/api/v1/settlements?${q}`,
    { method: "GET" },
    { accessToken },
  );
}

export function createSettlement(
  accessToken: string,
  body: SettlementCreate,
  options?: { idempotencyKey?: string },
) {
  return apiFetch<Settlement>(
    "/api/v1/settlements",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken, idempotencyKey: options?.idempotencyKey },
  );
}

export function deleteSettlement(accessToken: string, id: string) {
  return apiFetch<void>(`/api/v1/settlements/${id}`, { method: "DELETE" }, { accessToken });
}

export const SETTLEMENT_METHODS: { value: SettlementMethod; label: string }[] = [
  { value: "upi", label: "UPI" },
  { value: "cash", label: "Cash" },
  { value: "bank_transfer", label: "Bank transfer" },
  { value: "other", label: "Other" },
];
