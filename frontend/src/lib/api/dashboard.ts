import { apiFetch } from "@/lib/api/client";
import type { CardNetwork, CardStatus } from "@/lib/api/cards";

export type AttentionItem = {
  id: string;
  severity: "critical" | "warning" | "info" | string;
  title: string;
  detail: string;
  href: string | null;
};

export type UpcomingItem = {
  id: string;
  type: "card_due" | "emi_due" | string;
  title: string;
  amount_paise: number;
  due_date: string;
  href: string | null;
};

export type DashboardCardSummary = {
  id: string;
  nickname: string;
  issuer: string;
  last_four: string;
  network: CardNetwork;
  credit_limit_paise: number;
  outstanding_paise: number;
  available_credit_paise: number;
  utilization_percent: number;
  next_due_date: string | null;
  next_statement_date: string | null;
  status: CardStatus;
};

export type DashboardContactSummary = {
  id: string;
  name: string;
  outstanding_paise: number;
  updated_at: string;
};

export type DashboardData = {
  total_credit_limit_paise: number;
  total_outstanding_paise: number;
  total_available_credit_paise: number;
  total_friend_dues_paise: number;
  net_worth_paise: number;
  assets_paise: number;
  liabilities_paise: number;
  period_income_paise: number;
  period_expense_paise: number;
  cards_count: number;
  contacts_count: number;
  transactions_count: number;
  attention: AttentionItem[];
  upcoming_items: UpcomingItem[];
  cards: DashboardCardSummary[];
  top_contacts: DashboardContactSummary[];
};

export function fetchDashboard(accessToken: string) {
  return apiFetch<DashboardData>("/api/v1/dashboard", { method: "GET" }, { accessToken });
}
