"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus } from "lucide-react";

import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { AttentionStrip } from "@/components/dashboard/attention-strip";
import { CardsTable } from "@/components/dashboard/cards-table";
import { ContactsList } from "@/components/dashboard/contacts-list";
import { KpiRow } from "@/components/dashboard/kpi-row";
import { NetWorthStrip } from "@/components/dashboard/net-worth-strip";
import { IncomeExpenseStrip } from "@/components/dashboard/income-expense-strip";
import { UpcomingList } from "@/components/dashboard/upcoming-list";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BootstrapBanner } from "@/features/auth/bootstrap-banner";
import { useAuth } from "@/features/auth/auth-provider";
import {
  fetchDashboard,
  type DashboardContactSummary,
  type DashboardData,
} from "@/lib/api/dashboard";
import { ApiError } from "@/lib/api/client";
import {
  attentionItems,
  dashboardKpis,
  demoActivity,
  demoCards,
  demoContacts,
  demoUpcomingItems,
} from "@/lib/demo-data";
import type { DemoAttentionItem, DemoCard, DemoContact } from "@/lib/demo-data";
import { cn } from "@/lib/utils";

function DashboardLoading() {
  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-4" aria-busy="true">
      <div className="flex items-center gap-2 rounded-xl border bg-muted/30 px-3 py-2">
        <Badge variant="secondary" className="font-mono text-[10px] uppercase tracking-wide">
          Loading
        </Badge>
        <span className="text-xs text-muted-foreground">Loading your workspace…</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <div className="grid gap-4 xl:grid-cols-3">
        <Skeleton className="h-72 rounded-xl xl:col-span-2" />
        <div className="flex flex-col gap-4">
          <Skeleton className="h-40 rounded-xl" />
          <Skeleton className="h-40 rounded-xl" />
        </div>
      </div>
    </div>
  );
}

function mapLiveCards(data: DashboardData): DemoCard[] {
  return data.cards.map((c) => ({
    id: c.id,
    nickname: c.nickname,
    issuer: c.issuer,
    lastFour: c.last_four,
    network: c.network,
    creditLimitPaise: c.credit_limit_paise,
    outstandingPaise: c.outstanding_paise,
    nextDueDate: c.next_due_date ?? new Date().toISOString().slice(0, 10),
    statementDay: 1,
  }));
}

function mapAttention(data: DashboardData): DemoAttentionItem[] {
  return data.attention.map((a) => ({
    id: a.id,
    severity: (a.severity as DemoAttentionItem["severity"]) || "info",
    title: a.title,
    detail: a.detail,
    href: a.href || "/app",
  }));
}

function mapLiveContacts(items: DashboardContactSummary[]): DemoContact[] {
  return items.map((c) => ({
    id: c.id,
    name: c.name,
    outstandingPaise: c.outstanding_paise,
    lastActivity: c.updated_at,
  }));
}

type DashSnapshot = {
  live: DashboardData | null;
  error: string | null;
  gen: number;
};

export default function DashboardPage() {
  const { accessToken, ready, profile } = useAuth();
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<DashSnapshot>({
    live: null,
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!accessToken) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const data = await fetchDashboard(accessToken);
        if (cancelled) return;
        setSnapshot({ live: data, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          live: null,
          error: err instanceof ApiError ? err.message : "Failed to load dashboard",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [accessToken, reloadKey]);

  const live = snapshot.live;
  const error = snapshot.error;
  const useLive = Boolean(live && accessToken);
  const showSynthetic = ready && !accessToken;
  const showLoading = !useLive && !error && (!ready || Boolean(accessToken));

  if (showLoading) {
    return (
      <>
        <BootstrapBanner />
        <DashboardLoading />
      </>
    );
  }

  const kpis = useLive
    ? {
        totalLimitPaise: live!.total_credit_limit_paise,
        totalOutstandingPaise: live!.total_outstanding_paise,
        totalAvailablePaise: live!.total_available_credit_paise,
        friendDuesPaise: live!.total_friend_dues_paise,
        netWorthPaise: live!.net_worth_paise,
        assetsPaise: live!.assets_paise,
        liabilitiesPaise: live!.liabilities_paise,
        periodIncomePaise: live!.period_income_paise,
        periodExpensePaise: live!.period_expense_paise,
      }
    : dashboardKpis();

  const attention = useLive ? mapAttention(live!) : attentionItems();
  const cards = useLive ? mapLiveCards(live!) : demoCards;
  const contacts = useLive
    ? mapLiveContacts(live!.top_contacts ?? [])
    : demoContacts;
  const emptyLive = useLive && live!.cards_count === 0;

  return (
    <div className="mx-auto flex w-full max-w-7xl flex-col gap-4">
      <BootstrapBanner />

      {useLive ? (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border bg-muted/30 px-3 py-2 text-xs text-muted-foreground shadow-sm">
          <Badge variant="secondary" className="font-mono text-[10px] uppercase tracking-wide">
            Live
          </Badge>
          <span>
            Data from your workspace
            {profile?.email ? ` · ${profile.email}` : ""}.
            {emptyLive ? " Add a card to populate KPIs." : null}
          </span>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-7"
            onClick={() => setReloadKey((k) => k + 1)}
          >
            Refresh
          </Button>
        </div>
      ) : showSynthetic ? (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-dashed bg-muted/40 px-3 py-2 text-xs text-muted-foreground shadow-sm">
          <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-wide">
            Sample
          </Badge>
          <span>Showing sample layout. Sign in to load your workspace.</span>
        </div>
      ) : error ? (
        <div className="flex flex-wrap items-center gap-2 rounded-xl border border-dashed bg-muted/40 px-3 py-2 text-xs text-muted-foreground shadow-sm">
          <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-wide">
            Error
          </Badge>
          <span>Live dashboard unavailable ({error}).</span>
          <Button
            variant="ghost"
            size="sm"
            className="ml-auto h-7"
            onClick={() => setReloadKey((k) => k + 1)}
          >
            Retry
          </Button>
        </div>
      ) : null}

      {emptyLive ? (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="flex flex-col gap-5 py-8">
            <div className="flex flex-col items-start gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="font-medium">Get your ledger ready</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  A short checklist to make Fin Buddy your daily driver for cards and friend dues.
                </p>
              </div>
              <Link href="/app/cards" className={cn(buttonVariants())}>
                <Plus className="size-3.5" />
                Add card
              </Link>
            </div>
            <ol className="grid gap-2 text-sm sm:grid-cols-3">
              <li className="rounded-xl border bg-muted/30 px-3 py-3">
                <p className="font-medium">1. Add a card</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Limit, statement day, due rule — last 4 only.
                </p>
              </li>
              <li className="rounded-xl border bg-muted/30 px-3 py-3">
                <p className="font-medium">2. Add contacts</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Friends you lend cards to (not app users).
                </p>
              </li>
              <li className="rounded-xl border bg-muted/30 px-3 py-3">
                <p className="font-medium">3. Log spend</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Attribute purchases and record settlements.
                </p>
              </li>
            </ol>
            <div className="flex flex-wrap gap-2">
              <Link
                href="/app/contacts"
                className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
              >
                Add contact
              </Link>
              <Link
                href="/app/transactions"
                className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
              >
                Log transaction
              </Link>
              <Link
                href="/app/settings"
                className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
              >
                Notification thresholds
              </Link>
            </div>
          </CardContent>
        </Card>
      ) : useLive || showSynthetic ? (
        <>
          <AttentionStrip items={attention} />

          <KpiRow
            totalLimitPaise={kpis.totalLimitPaise}
            totalOutstandingPaise={kpis.totalOutstandingPaise}
            totalAvailablePaise={kpis.totalAvailablePaise}
            friendDuesPaise={kpis.friendDuesPaise}
          />
          
          <NetWorthStrip
            netWorthPaise={kpis.netWorthPaise}
            assetsPaise={kpis.assetsPaise}
            liabilitiesPaise={kpis.liabilitiesPaise}
          />
          <IncomeExpenseStrip
            incomePaise={kpis.periodIncomePaise}
            expensePaise={kpis.periodExpensePaise}
          />
          
          <div className="grid gap-4 xl:grid-cols-3">
            <div className="flex flex-col gap-4 xl:col-span-2">
              <UpcomingList items={useLive ? live!.upcoming_items : demoUpcomingItems()} />
              <CardsTable cards={cards} />
            </div>
            <div className="flex flex-col gap-4">
              <ContactsList contacts={contacts} />
              <QuickActions />
            </div>
          </div>
          {showSynthetic && <ActivityFeed items={demoActivity} />}
        </>
      ) : null}
    </div>
  );
}
