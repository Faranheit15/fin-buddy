"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { SettlementForm } from "@/features/contacts/settlement-form";
import { getContact, updateContact, type Contact } from "@/lib/api/contacts";
import { ApiError } from "@/lib/api/client";
import { listSettlements, type Settlement } from "@/lib/api/settlements";
import { listTransactions, type Transaction } from "@/lib/api/transactions";
import { listObligations, type Obligation } from "@/lib/api/obligations";
import { formatDateIst, formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

type Snapshot = {
  contact: Contact | null;
  transactions: Transaction[];
  settlements: Settlement[];
  obligations: Obligation[];
  error: string | null;
  gen: number;
};

export default function ContactDetailPage() {
  const params = useParams<{ id: string }>();
  const { accessToken, ready } = useAuth();
  const [showSettle, setShowSettle] = useState(false);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<Snapshot>({
    contact: null,
    transactions: [],
    settlements: [],
    obligations: [],
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken || !params.id) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const [contact, txs, settles, obligations] = await Promise.all([
          getContact(accessToken, params.id),
          listTransactions(accessToken, { contactId: params.id, pageSize: 50 }),
          listSettlements(accessToken, { contactId: params.id, pageSize: 50 }),
          listObligations(accessToken, { contactId: params.id, pageSize: 50 }),
        ]);
        if (cancelled) return;
        setSnapshot({
          contact,
          transactions: txs.items,
          settlements: settles.items,
          obligations: obligations.items,
          error: null,
          gen,
        });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          contact: null,
          transactions: [],
          settlements: [],
          obligations: [],
          error: err instanceof ApiError ? err.message : "Failed to load contact",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, params.id, reloadKey]);

  async function toggleArchive() {
    if (!accessToken || !snapshot.contact) return;
    const archived = Boolean(snapshot.contact.archived_at);
    setBusy(true);
    setActionError(null);
    try {
      const contact = await updateContact(accessToken, snapshot.contact.id, {
        archived: !archived,
      });
      setSnapshot((s) => ({ ...s, contact }));
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

  if (snapshot.error && !snapshot.contact) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{snapshot.error}</p>
        <Link href="/app/contacts" className={cn(buttonVariants({ size: "sm" }))}>
          Back to contacts
        </Link>
      </div>
    );
  }

  const contact = snapshot.contact;
  if (!contact) return null;

  const bal = contact.outstanding_paise ?? 0;
  const error = actionError ?? snapshot.error;

  type LedgerRow =
    | { kind: "tx"; at: string; id: string; label: string; amountPaise: number; signed: number }
    | {
        kind: "settlement";
        at: string;
        id: string;
        label: string;
        amountPaise: number;
        signed: number;
      };

  const ledger: LedgerRow[] = [
    ...snapshot.transactions.map((t) => {
      const sign =
        t.type === "refund" ? -1 : t.type === "payment_to_issuer" ? 0 : 1;
      // payment_to_issuer shouldn't appear on contact ledger typically; still show if present
      return {
        kind: "tx" as const,
        at: t.occurred_at,
        id: t.id,
        label: `${t.type.replaceAll("_", " ")} · ${t.merchant}`,
        amountPaise: t.amount_paise,
        signed: sign * t.amount_paise,
      };
    }),
    ...snapshot.settlements.map((s) => ({
      kind: "settlement" as const,
      at: s.settled_at,
      id: s.id,
      label: `Settlement · ${s.method.replaceAll("_", " ")}`,
      amountPaise: s.amount_paise,
      signed: -s.amount_paise,
    })),
  ].sort((a, b) => new Date(b.at).getTime() - new Date(a.at).getTime());

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/app/contacts"
            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Contacts
          </Link>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">{contact.name}</h2>
          <p className="text-sm text-muted-foreground">
            {[contact.phone, contact.email].filter(Boolean).join(" · ") || "No phone/email"}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {contact.archived_at && <Badge variant="outline">Archived</Badge>}
          <Badge variant={bal > 0 ? "secondary" : "outline"}>
            {bal > 0 ? "Owes you" : bal < 0 ? "Credit" : "Settled"}
          </Badge>
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardContent className="flex flex-wrap items-end justify-between gap-3 py-5">
          <div>
            <p className="text-xs text-muted-foreground">Outstanding balance</p>
            <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">
              {formatInrFromPaise(bal)}
            </p>
          </div>
          <Button size="sm" onClick={() => setShowSettle((v) => !v)}>
            {showSettle ? "Hide settlement" : "Record settlement"}
          </Button>
        </CardContent>
      </Card>

      {showSettle && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Record settlement</CardTitle>
          </CardHeader>
          <CardContent>
            <SettlementForm
              accessToken={accessToken!}
              contactId={contact.id}
              currentBalancePaise={bal}
              onCancel={() => setShowSettle(false)}
              onCreated={() => {
                setShowSettle(false);
                setReloadKey((k) => k + 1);
              }}
            />
          </CardContent>
        </Card>
      )}

      {(contact.notes || (contact.tags && contact.tags.length > 0)) && (
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="space-y-2 pt-1">
            {contact.notes && (
              <div>
                <p className="text-xs text-muted-foreground">Notes</p>
                <p className="text-sm">{contact.notes}</p>
              </div>
            )}
            {contact.tags && contact.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {contact.tags.map((tag) => (
                  <Badge key={tag} variant="outline">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <CardTitle>Ledger</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {ledger.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              No attributed spends or settlements yet.
            </p>
          ) : (
            <ul className="divide-y">
              {ledger.map((row) => (
                <li
                  key={`${row.kind}-${row.id}`}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium capitalize">{row.label}</p>
                    <p className="font-mono text-[11px] text-muted-foreground">
                      {formatDateIst(row.at)}
                    </p>
                  </div>
                  <p
                    className={cn(
                      "shrink-0 font-mono text-sm tabular-nums",
                      row.signed < 0 && "text-emerald-700 dark:text-emerald-400",
                      row.signed > 0 && "text-foreground",
                    )}
                  >
                    {row.signed > 0 ? "+" : row.signed < 0 ? "−" : ""}
                    {formatInrFromPaise(Math.abs(row.amountPaise))}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {snapshot.obligations.length > 0 && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Debts & Loans</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <ul className="divide-y">
              {snapshot.obligations.map((obl) => (
                <li key={obl.id} className="flex items-center justify-between gap-3 px-4 py-3 hover:bg-muted/30">
                  <div className="min-w-0">
                    <Link href={`/app/debts/${obl.id}`} className="truncate text-sm font-medium hover:underline">
                      {obl.type === "receivable" ? "Receivable" : "Payable"}
                    </Link>
                    <p className="font-mono text-[11px] text-muted-foreground">
                      {formatDateIst(obl.created_at)}
                    </p>
                  </div>
                  <div className="shrink-0 text-right">
                    <p className="font-mono text-sm tabular-nums text-foreground">
                      {formatInrFromPaise(obl.remaining_paise ?? 0)}
                    </p>
                    <Badge variant={obl.status === "active" ? "secondary" : "outline"} className="mt-1 text-[9px] uppercase">
                      {obl.status}
                    </Badge>
                  </div>
                </li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      <div className="flex flex-wrap gap-2">
        <Link
          href={`/app/transactions?contact=${contact.id}`}
          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
        >
          View in transactions
        </Link>
        <Button variant="ghost" size="sm" disabled={busy} onClick={() => void toggleArchive()}>
          {contact.archived_at ? "Unarchive" : "Archive"}
        </Button>
        <Button variant="ghost" size="sm" onClick={() => setReloadKey((k) => k + 1)}>
          Refresh
        </Button>
      </div>
    </div>
  );
}
