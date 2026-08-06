import { apiFetch } from "@/lib/api/client";

export type ObligationType = "receivable" | "payable";
export type ObligationStatus = "active" | "paid" | "defaulted";

export type Obligation = {
  id: string;
  organization_id: string;
  contact_id: string | null;
  counterparty_name: string | null;
  type: ObligationType;
  amount_paise: number;
  currency: string;
  due_date: string | null;
  status: ObligationStatus;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  remaining_paise: number | null;
};

export type ObligationCreate = {
  contact_id?: string | null;
  counterparty_name?: string | null;
  type: ObligationType;
  amount_paise: number;
  currency?: string;
  due_date?: string | null;
  notes?: string | null;
};

export type ObligationUpdate = Partial<{
  status: ObligationStatus;
  due_date: string | null;
  notes: string | null;
}>;

export type ObligationPayment = {
  id: string;
  organization_id: string;
  obligation_id: string;
  account_id: string | null;
  amount_paise: number;
  date: string;
  notes: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
};

export type ObligationPaymentCreate = {
  amount_paise: number;
  date: string;
  account_id?: string | null;
  notes?: string | null;
};

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function listObligations(
  accessToken: string,
  opts: { page?: number; pageSize?: number; status?: ObligationStatus; type?: ObligationType; contactId?: string } = {},
) {
  const q = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.pageSize ?? 50),
  });
  if (opts.status) q.set("status", opts.status);
  if (opts.type) q.set("type", opts.type);
  if (opts.contactId) q.set("contact_id", opts.contactId);
  return apiFetch<Paginated<Obligation>>(`/api/v1/obligations?${q}`, { method: "GET" }, { accessToken });
}

export function getObligation(accessToken: string, id: string) {
  return apiFetch<Obligation>(`/api/v1/obligations/${id}`, { method: "GET" }, { accessToken });
}

export function createObligation(accessToken: string, body: ObligationCreate) {
  return apiFetch<Obligation>(
    "/api/v1/obligations",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateObligation(accessToken: string, id: string, body: ObligationUpdate) {
  return apiFetch<Obligation>(
    `/api/v1/obligations/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function deleteObligation(accessToken: string, id: string) {
  return apiFetch<void>(
    `/api/v1/obligations/${id}`,
    { method: "DELETE" },
    { accessToken },
  );
}

export function listObligationPayments(accessToken: string, obligationId: string) {
  return apiFetch<ObligationPayment[]>(
    `/api/v1/obligations/${obligationId}/payments`,
    { method: "GET" },
    { accessToken },
  );
}

export function addObligationPayment(accessToken: string, obligationId: string, body: ObligationPaymentCreate) {
  return apiFetch<ObligationPayment>(
    `/api/v1/obligations/${obligationId}/payments`,
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}
