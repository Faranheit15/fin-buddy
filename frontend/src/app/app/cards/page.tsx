"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CreditCard as CreditCardIcon, Plus } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageTableSkeleton, TableSkeleton } from "@/components/shared/page-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { CardForm } from "@/features/cards/card-form";
import { listCards, type CreditCard } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import {
  formatDateShortIst,
  formatInrFromPaise,
  formatPercent,
  formatRelativeDue,
} from "@/lib/format";
import { cn } from "@/lib/utils";

type CardsSnapshot = {
  items: CreditCard[];
  error: string | null;
  gen: number;
};

export default function CardsPage() {
  const { accessToken, ready } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<CardsSnapshot>({
    items: [],
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const res = await listCards(accessToken);
        if (cancelled) return;
        setSnapshot({ items: res.items, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          items: [],
          error: err instanceof ApiError ? err.message : "Failed to load cards",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, reloadKey]);

  if (!ready) {
    return <PageTableSkeleton columns={6} titleWidth="w-16" />;
  }

  if (!accessToken) {
    return (
      <p className="text-sm text-muted-foreground">Sign in (or use demo login) to manage cards.</p>
    );
  }

  const loading = snapshot.gen !== reloadKey;
  const cards = snapshot.items;
  const error = snapshot.error;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Cards</h2>
          <p className="text-sm text-muted-foreground">
            Limits, utilization, statement day, and due dates
          </p>
        </div>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="size-3.5" />
          {showForm ? "Hide form" : "Add card"}
        </Button>
      </div>

      {showForm && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Add credit card</CardTitle>
          </CardHeader>
          <CardContent>
            <CardForm
              accessToken={accessToken}
              onCancel={() => setShowForm(false)}
              onCreated={() => {
                setShowForm(false);
                setReloadKey((k) => k + 1);
              }}
            />
          </CardContent>
        </Card>
      )}

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      {loading ? (
        <TableSkeleton columns={6} label="Loading cards" />
      ) : cards.length === 0 ? (
        <EmptyState
          icon={CreditCardIcon}
          title="No cards yet"
          description="Add your first credit card to track limits, utilization, and billing cycles. Last 4 digits only — never full PAN or CVV."
          action={
            !showForm ? (
              <Button size="sm" onClick={() => setShowForm(true)}>
                <Plus className="size-3.5" />
                Add card
              </Button>
            ) : null
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Card</th>
                  <th className="px-4 py-2.5 font-medium">Utilization</th>
                  <th className="px-4 py-2.5 font-medium">Outstanding</th>
                  <th className="px-4 py-2.5 font-medium">Available</th>
                  <th className="px-4 py-2.5 font-medium">Next due</th>
                  <th className="px-4 py-2.5 font-medium">Statement</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {cards.map((card) => {
                  const util = card.utilization_percent ?? 0;
                  const critical = util >= 90;
                  const warn = util >= 80;
                  return (
                    <tr key={card.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <Link href={`/app/cards/${card.id}`} className="group block min-w-0">
                          <p className="font-medium group-hover:underline">{card.nickname}</p>
                          <p className="font-mono text-xs text-muted-foreground">
                            {card.issuer} · •••• {card.last_four}
                          </p>
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <div className="flex min-w-28 flex-col gap-1">
                          <span
                            className={cn(
                              "font-mono text-xs tabular-nums",
                              critical && "text-destructive",
                              warn && !critical && "text-amber-700 dark:text-amber-400",
                            )}
                          >
                            {formatPercent(util)}
                          </span>
                          <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                critical ? "bg-destructive" : warn ? "bg-amber-500" : "bg-primary",
                              )}
                              style={{ width: `${Math.min(util, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs tabular-nums sm:text-sm">
                        {formatInrFromPaise(card.outstanding_paise ?? 0)}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs tabular-nums sm:text-sm">
                        {formatInrFromPaise(card.available_credit_paise ?? 0)}
                      </td>
                      <td className="px-4 py-3">
                        {card.next_due_date ? (
                          <div className="flex flex-col gap-1">
                            <Badge variant="outline" className="w-fit">
                              {formatRelativeDue(card.next_due_date)}
                            </Badge>
                            <span className="font-mono text-[11px] text-muted-foreground">
                              {formatDateShortIst(card.next_due_date)}
                            </span>
                          </div>
                        ) : (
                          "—"
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        Day {card.statement_day}
                        {card.next_statement_date
                          ? ` · ${formatDateShortIst(card.next_statement_date)}`
                          : ""}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
