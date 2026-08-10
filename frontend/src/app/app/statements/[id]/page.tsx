"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/features/auth/auth-provider";
import { listCards, type CreditCard } from "@/lib/api/cards";
import { listContacts, type Contact } from "@/lib/api/contacts";
import { ApiError } from "@/lib/api/client";
import {
  bulkReviewLines,
  getStatement,
  importStatement,
  parseStatement,
  STATEMENT_STATUS_LABEL,
  updateStatementLine,
  type LineReviewStatus,
  type StatementDetail,
  type StatementLine,
  type TransactionType,
} from "@/lib/api/statements";
import { formatDateIst, formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

const TYPES: { value: TransactionType; label: string }[] = [
  { value: "purchase", label: "Purchase" },
  { value: "refund", label: "Refund" },
  { value: "fee", label: "Fee" },
  { value: "interest", label: "Interest" },
  { value: "payment_to_issuer", label: "Payment to issuer" },
];

type Snapshot = {
  detail: StatementDetail | null;
  error: string | null;
  gen: number;
};

export default function StatementReviewPage() {
  const params = useParams<{ id: string }>();
  const { accessToken, ready } = useAuth();
  const [reloadKey, setReloadKey] = useState(0);
  const [cards, setCards] = useState<CreditCard[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot>({
    detail: null,
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken) return;
    let cancelled = false;
    void (async () => {
      try {
        const [cardRes, contactRes] = await Promise.all([
          listCards(accessToken, 1, 100),
          listContacts(accessToken, { pageSize: 100 }),
        ]);
        if (cancelled) return;
        setCards(cardRes.items);
        setContacts(contactRes.items);
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ready, accessToken]);

  useEffect(() => {
    if (!ready || !accessToken || !params.id) return;
    const gen = reloadKey;
    let cancelled = false;
    void (async () => {
      try {
        const detail = await getStatement(accessToken, params.id);
        if (cancelled) return;
        setSnapshot({ detail, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          detail: null,
          error: err instanceof ApiError ? err.message : "Failed to load statement",
          gen,
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, params.id, reloadKey]);

  async function withAction(fn: () => Promise<void>) {
    setBusy(true);
    setActionError(null);
    setMessage(null);
    try {
      await fn();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function onLineStatus(line: StatementLine, review_status: LineReviewStatus) {
    if (!accessToken) return;
    await withAction(async () => {
      await updateStatementLine(accessToken, params.id, line.id, { review_status });
      setReloadKey((k) => k + 1);
    });
  }

  async function onLineField(
    line: StatementLine,
    patch: {
      merchant?: string;
      proposed_type?: TransactionType;
      proposed_contact_id?: string | null;
      clear_contact?: boolean;
    },
  ) {
    if (!accessToken) return;
    await withAction(async () => {
      await updateStatementLine(accessToken, params.id, line.id, patch);
      setReloadKey((k) => k + 1);
    });
  }

  const loading = !ready || (Boolean(accessToken) && snapshot.gen !== reloadKey);
  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (snapshot.error && !snapshot.detail) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{snapshot.error}</p>
        <Link href="/app/statements" className={cn(buttonVariants({ size: "sm" }))}>
          Back to statements
        </Link>
      </div>
    );
  }

  const detail = snapshot.detail;
  if (!detail) return null;

  const card = cards.find((c) => c.id === detail.credit_card_id);
  const accepted = detail.lines.filter(
    (l) =>
      (l.review_status === "accepted" || l.review_status === "edited") &&
      !l.committed_transaction_id,
  ).length;
  const pending = detail.lines.filter((l) => l.review_status === "pending").length;
  const imported = detail.lines.filter((l) => l.committed_transaction_id).length;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/app/statements"
            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Statements
          </Link>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">
            {card ? `${card.nickname} statement` : "Statement review"}
          </h2>
          <p className="text-sm text-muted-foreground">
            {detail.statement_date
              ? `Statement date ${formatDateIst(detail.statement_date)}`
              : "Review proposed lines before import"}
            {detail.due_date ? ` · Due ${formatDateIst(detail.due_date)}` : ""}
          </p>
        </div>
        <Badge
          variant={
            detail.status === "needs_review"
              ? "secondary"
              : detail.status === "failed"
                ? "destructive"
                : "outline"
          }
        >
          {STATEMENT_STATUS_LABEL[detail.status]}
        </Badge>
      </div>

      {detail.parse_error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {detail.parse_error}
        </p>
      )}
      {actionError && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {actionError}
        </p>
      )}
      {message && (
        <p className="rounded-lg bg-emerald-500/10 px-3 py-2 text-sm text-emerald-800 dark:text-emerald-200">
          {message}
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-4">
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Lines</p>
            <p className="mt-1 font-mono text-lg font-semibold">{detail.lines.length}</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Pending</p>
            <p className="mt-1 font-mono text-lg font-semibold">{pending}</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Ready to import</p>
            <p className="mt-1 font-mono text-lg font-semibold">{accepted}</p>
          </CardContent>
        </Card>
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1">
            <p className="text-xs text-muted-foreground">Imported</p>
            <p className="mt-1 font-mono text-lg font-semibold">{imported}</p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2">
        {detail.status !== "imported" && (
          <>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() =>
                void withAction(async () => {
                  await bulkReviewLines(accessToken!, detail.id, "accepted");
                  setReloadKey((k) => k + 1);
                  setMessage("All pending lines accepted");
                })
              }
            >
              Accept all pending
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={busy}
              onClick={() =>
                void withAction(async () => {
                  await bulkReviewLines(accessToken!, detail.id, "rejected");
                  setReloadKey((k) => k + 1);
                  setMessage("All pending lines rejected");
                })
              }
            >
              Reject all pending
            </Button>
            <Button
              size="sm"
              disabled={busy || accepted === 0}
              onClick={() =>
                void withAction(async () => {
                  const res = await importStatement(accessToken!, detail.id);
                  setReloadKey((k) => k + 1);
                  setMessage(
                    `Imported ${res.created} transaction(s)` +
                      (res.skipped ? ` · skipped ${res.skipped}` : ""),
                  );
                })
              }
            >
              Import accepted
            </Button>
          </>
        )}
        {detail.status !== "imported" && (
          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            onClick={() =>
              void withAction(async () => {
                await parseStatement(accessToken!, detail.id);
                setReloadKey((k) => k + 1);
                setMessage("Re-parsed statement");
              })
            }
          >
            Re-parse
          </Button>
        )}
        <Button
          size="sm"
          variant="ghost"
          disabled={busy}
          onClick={() => setReloadKey((k) => k + 1)}
        >
          Refresh
        </Button>
        {imported > 0 && (
          <Link
            href={`/app/transactions?card=${detail.credit_card_id}`}
            className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
          >
            View transactions
          </Link>
        )}
      </div>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <CardTitle>Proposed lines</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto p-0">
          {detail.lines.length === 0 ? (
            <p className="px-4 py-8 text-center text-sm text-muted-foreground">
              No lines parsed. Re-parse or upload a FinBuddy sample / text-based PDF.
            </p>
          ) : (
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-3 py-2.5 font-medium">Date</th>
                  <th className="px-3 py-2.5 font-medium">Merchant</th>
                  <th className="px-3 py-2.5 font-medium">Type</th>
                  <th className="px-3 py-2.5 font-medium">Contact</th>
                  <th className="px-3 py-2.5 font-medium">Amount</th>
                  <th className="px-3 py-2.5 font-medium">Status</th>
                  <th className="px-3 py-2.5 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {detail.lines.map((line) => {
                  const locked = Boolean(line.committed_transaction_id);
                  return (
                    <tr
                      key={line.id}
                      className={cn(
                        line.review_status === "rejected" && "opacity-50",
                        locked && "bg-muted/20",
                      )}
                    >
                      <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                        {line.occurred_at ? formatDateIst(line.occurred_at) : "—"}
                      </td>
                      <td className="px-3 py-2">
                        {locked ? (
                          <span className="text-sm">{line.merchant}</span>
                        ) : (
                          <Input
                            className="h-8 min-w-40"
                            defaultValue={line.merchant ?? ""}
                            onBlur={(e) => {
                              const v = e.target.value.trim();
                              if (v && v !== line.merchant) {
                                void onLineField(line, { merchant: v });
                              }
                            }}
                          />
                        )}
                      </td>
                      <td className="px-3 py-2">
                        <select
                          className="flex h-8 w-full min-w-28 rounded-lg border border-input bg-background px-2 text-xs"
                          disabled={locked || busy}
                          value={line.proposed_type ?? "purchase"}
                          onChange={(e) =>
                            void onLineField(line, {
                              proposed_type: e.target.value as TransactionType,
                            })
                          }
                        >
                          {TYPES.map((t) => (
                            <option key={t.value} value={t.value}>
                              {t.label}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2">
                        <select
                          className="flex h-8 w-full min-w-28 rounded-lg border border-input bg-background px-2 text-xs"
                          disabled={locked || busy}
                          value={line.proposed_contact_id ?? ""}
                          onChange={(e) => {
                            const v = e.target.value;
                            void onLineField(
                              line,
                              v ? { proposed_contact_id: v } : { clear_contact: true },
                            );
                          }}
                        >
                          <option value="">Self</option>
                          {contacts.map((c) => (
                            <option key={c.id} value={c.id}>
                              {c.name}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td className="px-3 py-2 font-mono text-xs tabular-nums">
                        {line.amount_paise != null ? formatInrFromPaise(line.amount_paise) : "—"}
                      </td>
                      <td className="px-3 py-2">
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {locked ? "imported" : line.review_status}
                        </Badge>
                      </td>
                      <td className="px-3 py-2">
                        {!locked && (
                          <div className="flex flex-wrap gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 px-2 text-xs"
                              disabled={busy || line.review_status === "accepted"}
                              onClick={() => void onLineStatus(line, "accepted")}
                            >
                              Accept
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="h-7 px-2 text-xs"
                              disabled={busy || line.review_status === "rejected"}
                              onClick={() => void onLineStatus(line, "rejected")}
                            >
                              Reject
                            </Button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
