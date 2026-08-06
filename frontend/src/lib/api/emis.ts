import { apiFetch } from "@/lib/api/client";

export type EmiPlanStatus = "active" | "completed";
export type EmiInstallmentStatus = "pending" | "paid";

export type EmiInstallment = {
  id: string;
  plan_id: string;
  sequence_number: number;
  due_date: string;
  principal_paise: number;
  interest_paise: number;
  fees_paise: number;
  gst_paise: number;
  total_paise: number;
  status: EmiInstallmentStatus;
};

export type EmiPlan = {
  id: string;
  organization_id: string;
  credit_card_id: string;
  reference_transaction_id: string | null;
  principal_paise: number;
  interest_rate_bps: number;
  tenure_months: number;
  status: EmiPlanStatus;
  created_at: string;
  installments: EmiInstallment[];
};

export type EmiPlanCreate = {
  credit_card_id: string;
  reference_transaction_id?: string | null;
  principal_paise: number;
  interest_rate_bps: number;
  tenure_months: number;
  start_date: string;
};

export function createEmiPlan(accessToken: string, body: EmiPlanCreate) {
  return apiFetch<EmiPlan>(
    "/api/v1/emis",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function listCardEmiPlans(accessToken: string, cardId: string) {
  return apiFetch<EmiPlan[]>(
    `/api/v1/emis/card/${cardId}`,
    { method: "GET" },
    { accessToken },
  );
}
