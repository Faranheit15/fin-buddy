"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Trash } from "lucide-react";
import { useRouter } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DetailPageSkeleton } from "@/components/shared/page-skeleton";
import { useAuth } from "@/features/auth/auth-provider";
import { ObligationPaymentForm } from "@/features/obligations/obligation-payment-form";
import {
  getObligation,
  listObligationPayments,
  deleteObligation,
  type Obligation,
  type ObligationPayment,
} from "@/lib/api/obligations";
import { getContact, type Contact } from "@/lib/api/contacts";
import { ApiError } from "@/lib/api/client";
import { formatDateIst, formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

type Snapshot = {
  obligation: Obligation | null;
  payments: ObligationPayment[];
  contact: Contact | null;
  error: string | null;
  gen: number;
};

export default function DebtDetailPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken, ready } = useAuth();
  const [showPayment, setShowPayment] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<Snapshot>({
    obligation: null,
    payments: [],
    contact: null,
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken || !params.id) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const [obl, payments] = await Promise.all([
          getObligation(accessToken, params.id),
          listObligationPayments(accessToken, params.id),
        ]);
        let contact: Contact | null = null;
        if (obl.contact_id) {
          contact = await getContact(accessToken, obl.contact_id);
        }
        if (cancelled) return;
        setSnapshot({
          obligation: obl,
          payments,
          contact,
          error: null,
          gen,
        });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          obligation: null,
          payments: [],
          contact: null,
          error: err instanceof ApiError ? err.message : "Failed to load obligation",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, params.id, reloadKey]);

  async function doDelete() {
    if (!confirm("Are you sure you want to delete this obligation and all its payments?")) return;
    setBusy(true);
    try {
      await deleteObligation(accessToken!, params.id);
      router.push("/app/debts");
    } catch (err) {
      setSnapshot((s) => ({
        ...s,
        error: err instanceof ApiError ? err.message : "Failed to delete",
      }));
      setBusy(false);
    }
  }

  const loading = !ready || (Boolean(accessToken) && snapshot.gen !== reloadKey);

  if (loading) {
    return <DetailPageSkeleton />;
  }

  if (snapshot.error && !snapshot.obligation) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{snapshot.error}</p>
        <Link href="/app/debts" className={cn(buttonVariants({ size: "sm" }))}>
          Back to debts
        </Link>
      </div>
    );
  }

  const obl = snapshot.obligation;
  if (!obl) return null;

  const remaining = obl.remaining_paise ?? 0;
  const name = snapshot.contact ? snapshot.contact.name : obl.counterparty_name || "Unknown";

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/app/debts"
            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Debts
          </Link>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">{name}</h2>
          <p className="text-sm text-muted-foreground capitalize">
            {obl.type} · {formatDateIst(obl.created_at)}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {snapshot.contact && (
            <Link
              href={`/app/contacts/${snapshot.contact.id}`}
              className={cn(buttonVariants({ variant: "outline", size: "sm" }), "h-6 px-2 text-xs")}
            >
              View contact
            </Link>
          )}
          <Badge variant={obl.status === "active" ? "secondary" : "outline"} className="uppercase">
            {obl.status}
          </Badge>
        </div>
      </div>

      {snapshot.error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {snapshot.error}
        </p>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="py-5">
            <p className="text-xs text-muted-foreground">Original amount</p>
            <p className="mt-1 font-mono text-2xl font-semibold tabular-nums text-muted-foreground">
              {formatInrFromPaise(obl.amount_paise)}
            </p>
          </CardContent>
        </Card>
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="flex flex-wrap items-end justify-between gap-3 py-5">
            <div>
              <p className="text-xs text-muted-foreground">Remaining balance</p>
              <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">
                {formatInrFromPaise(remaining)}
              </p>
            </div>
            {remaining > 0 && (
              <Button size="sm" onClick={() => setShowPayment((v) => !v)}>
                {showPayment ? "Cancel" : "Record payment"}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {showPayment && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Record payment</CardTitle>
          </CardHeader>
          <CardContent>
            <ObligationPaymentForm
              accessToken={accessToken!}
              obligationId={obl.id}
              currentBalancePaise={remaining}
              onCancel={() => setShowPayment(false)}
              onCreated={() => {
                setShowPayment(false);
                setReloadKey((k) => k + 1);
              }}
            />
          </CardContent>
        </Card>
      )}

      {obl.notes && (
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="space-y-2 pt-1">
            <p className="text-xs text-muted-foreground">Notes</p>
            <p className="text-sm">{obl.notes}</p>
          </CardContent>
        </Card>
      )}

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <CardTitle>Payments</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {snapshot.payments.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              No payments recorded yet.
            </p>
          ) : (
            <ul className="divide-y">
              {snapshot.payments.map((p) => (
                <li key={p.id} className="flex items-center justify-between gap-3 px-4 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">Repayment</p>
                    <p className="font-mono text-[11px] text-muted-foreground">
                      {formatDateIst(p.date)} {p.notes ? `· ${p.notes}` : ""}
                    </p>
                  </div>
                  <p className="shrink-0 font-mono text-sm tabular-nums text-foreground">
                    {formatInrFromPaise(p.amount_paise)}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      <div className="flex justify-end gap-2">
        <Button variant="ghost" size="sm" onClick={() => setReloadKey((k) => k + 1)}>
          Refresh
        </Button>
        <Button
          variant="ghost"
          size="sm"
          disabled={busy}
          onClick={() => void doDelete()}
          className="text-destructive hover:bg-destructive/10 hover:text-destructive"
        >
          <Trash className="mr-1.5 size-3.5" />
          Delete
        </Button>
      </div>
    </div>
  );
}
