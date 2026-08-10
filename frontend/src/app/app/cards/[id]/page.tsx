"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { getCard, updateCard, type CreditCard } from "@/lib/api/cards";
import { listCardEmiPlans, type EmiPlan } from "@/lib/api/emis";
import { ApiError } from "@/lib/api/client";
import { CreateEmiDialog } from "@/features/cards/create-emi-dialog";
import { formatDateIst, formatInrFromPaise, formatPercent, formatRelativeDue } from "@/lib/format";
import { cn } from "@/lib/utils";

type CardSnapshot = {
  card: CreditCard | null;
  emis: EmiPlan[];
  error: string | null;
  gen: number;
};

export default function CardDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken, ready } = useAuth();
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<CardSnapshot>({
    card: null,
    emis: [],
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken || !params.id) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const [card, emis] = await Promise.all([
          getCard(accessToken, params.id as string),
          listCardEmiPlans(accessToken, params.id as string),
        ]);
        if (cancelled) return;
        setSnapshot({ card, emis, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          card: null,
          emis: [],
          error: err instanceof ApiError ? err.message : "Failed to load card",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, params.id, reloadKey]);

  async function closeCard() {
    if (!accessToken || !snapshot.card) return;
    if (!confirm(`Close ${snapshot.card.nickname}? History is kept.`)) return;
    setBusy(true);
    setActionError(null);
    try {
      const card = await updateCard(accessToken, snapshot.card.id, { status: "closed" });
      setSnapshot((s) => ({ ...s, card, error: null }));
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  async function reopenCard() {
    if (!accessToken || !snapshot.card) return;
    setBusy(true);
    setActionError(null);
    try {
      const card = await updateCard(accessToken, snapshot.card.id, { status: "active" });
      setSnapshot((s) => ({ ...s, card, error: null }));
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Update failed");
    } finally {
      setBusy(false);
    }
  }

  const loading = !ready || (Boolean(accessToken) && snapshot.gen !== reloadKey);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (snapshot.error && !snapshot.card) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{snapshot.error}</p>
        <Link href="/app/cards" className={cn(buttonVariants({ size: "sm" }))}>
          Back to cards
        </Link>
      </div>
    );
  }

  const card = snapshot.card;
  if (!card) return null;

  const util = card.utilization_percent ?? 0;
  const error = actionError ?? snapshot.error;

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/app/cards"
            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Cards
          </Link>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">{card.nickname}</h2>
          <p className="font-mono text-sm text-muted-foreground">
            {card.issuer} · {card.network.toUpperCase()} · •••• {card.last_four}
          </p>
        </div>
        <Badge variant={card.status === "active" ? "secondary" : "outline"}>{card.status}</Badge>
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="grid gap-3 sm:grid-cols-3">
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Outstanding</p>
            <p className="mt-1 font-mono text-lg font-semibold tabular-nums">
              {formatInrFromPaise(card.outstanding_paise ?? 0)}
            </p>
          </CardContent>
        </Card>
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Available</p>
            <p className="mt-1 font-mono text-lg font-semibold tabular-nums">
              {formatInrFromPaise(card.available_credit_paise ?? 0)}
            </p>
          </CardContent>
        </Card>
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Limit</p>
            <p className="mt-1 font-mono text-lg font-semibold tabular-nums">
              {formatInrFromPaise(card.credit_limit_paise)}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <CardTitle>Utilization</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Used</span>
            <span className="font-mono tabular-nums">{formatPercent(util, 1)}</span>
          </div>
          <div className="flex h-2 overflow-hidden rounded-full bg-muted">
            <div
              className={cn(
                "h-full",
                util >= 90 ? "bg-destructive" : util >= 80 ? "bg-amber-500" : "bg-primary",
              )}
              style={{
                width: `${Math.min(((card.spend_outstanding_paise ?? 0) / card.credit_limit_paise) * 100, 100)}%`,
              }}
            />
            <div
              className="h-full bg-indigo-400"
              style={{
                width: `${Math.min(((card.emi_principal_blocked_paise ?? 0) / card.credit_limit_paise) * 100, 100)}%`,
              }}
            />
          </div>
          <div className="flex flex-wrap gap-4 pt-1 text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5">
              <div className="size-2 rounded-full bg-primary" /> Spend (
              <span className="font-mono">
                {formatInrFromPaise(card.spend_outstanding_paise ?? 0)}
              </span>
              )
            </div>
            <div className="flex items-center gap-1.5">
              <div className="size-2 rounded-full bg-indigo-400" /> EMI Block (
              <span className="font-mono">
                {formatInrFromPaise(card.emi_principal_blocked_paise ?? 0)}
              </span>
              )
            </div>
            <div className="flex items-center gap-1.5">
              <div className="size-2 rounded-full bg-muted" /> Available (
              <span className="font-mono">
                {formatInrFromPaise(card.available_credit_paise ?? 0)}
              </span>
              )
            </div>
          </div>
          <p className="pt-2 text-xs text-muted-foreground">
            Available credit is your limit minus spend outstanding and EMI principal blocked.
          </p>
        </CardContent>
      </Card>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="flex flex-row items-center justify-between border-b pb-3!">
          <CardTitle>Active EMI Plans</CardTitle>
          <CreateEmiDialog cardId={card.id} onCreated={() => setReloadKey((k) => k + 1)} />
        </CardHeader>
        <CardContent className="p-0">
          {snapshot.emis.length === 0 ? (
            <p className="p-4 text-sm text-muted-foreground">No active EMI plans on this card.</p>
          ) : (
            <div className="divide-y">
              {snapshot.emis.map((plan) => {
                const paidCount = plan.installments.filter((i) => i.status === "paid").length;
                const total = plan.installments.length;
                const nextPending = plan.installments.find((i) => i.status === "pending");
                return (
                  <div key={plan.id} className="flex items-center justify-between p-4 text-sm">
                    <div>
                      <div className="flex justify-between font-medium">
                        <span>
                          EMI Plan •{" "}
                          <span className="font-mono">
                            {formatInrFromPaise(plan.principal_paise)}
                          </span>
                        </span>
                      </div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        Started{" "}
                        <span className="font-mono tabular-nums">
                          {formatDateIst(plan.created_at)}
                        </span>{" "}
                        •{" "}
                        <span className="font-mono tabular-nums">
                          {(plan.interest_rate_bps / 100).toFixed(2)}%
                        </span>{" "}
                        p.a.
                      </div>
                      <div className="mt-1 text-xs font-mono tabular-nums text-muted-foreground">
                        {paidCount} / {total} Months Paid
                      </div>
                    </div>
                    {nextPending && (
                      <Button
                        variant="secondary"
                        size="sm"
                        disabled={busy}
                        onClick={async () => {
                          if (!accessToken) return;
                          setBusy(true);
                          try {
                            const { payInstallment } = await import("@/lib/api/emis");
                            await payInstallment(accessToken, nextPending.id);
                            setReloadKey((k) => k + 1);
                          } catch (err) {
                            setActionError(
                              err instanceof ApiError ? err.message : "Failed to pay installment",
                            );
                          } finally {
                            setBusy(false);
                          }
                        }}
                      >
                        Pay Next
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <CardTitle>Billing cycle</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-3 text-sm sm:grid-cols-2">
          <div>
            <p className="text-xs text-muted-foreground">Statement day</p>
            <p className="font-medium">Day {card.statement_day} of month</p>
            {card.next_statement_date && (
              <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                Next: {formatDateIst(card.next_statement_date)}
              </p>
            )}
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Due rule</p>
            <p className="font-medium">
              {card.due_rule_type === "fixed_day"
                ? `Fixed day ${card.due_rule_value}`
                : `${card.due_rule_value} days after statement`}
            </p>
            {card.next_due_date && (
              <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                Next due: {formatRelativeDue(card.next_due_date)} (
                {formatDateIst(card.next_due_date)})
              </p>
            )}
          </div>
          {card.notes && (
            <div className="sm:col-span-2">
              <p className="text-xs text-muted-foreground">Notes</p>
              <p>{card.notes}</p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-wrap gap-2">
        {card.status === "active" ? (
          <Button variant="outline" disabled={busy} onClick={() => void closeCard()}>
            Close card
          </Button>
        ) : (
          <Button variant="outline" disabled={busy} onClick={() => void reopenCard()}>
            Reopen card
          </Button>
        )}
        <Button variant="ghost" onClick={() => router.push(`/app/transactions?card=${card.id}`)}>
          View transactions
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setReloadKey((k) => k + 1)}>
          Refresh
        </Button>
      </div>
    </div>
  );
}
