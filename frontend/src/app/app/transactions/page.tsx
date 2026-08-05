"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { ArrowLeftRight, Plus } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/features/auth/auth-provider";
import { ReverseTransactionDialog } from "@/features/transactions/reverse-transaction-dialog";
import { TransactionForm } from "@/features/transactions/transaction-form";
import { listCards, type CreditCard } from "@/lib/api/cards";
import { listContacts, type Contact } from "@/lib/api/contacts";
import { ApiError } from "@/lib/api/client";
import {
  deleteTransaction,
  listTransactions,
  postTransaction,
  TRANSACTION_TYPES,
  type PostingStatus,
  type Transaction,
  type TransactionType,
} from "@/lib/api/transactions";
import { formatDateIst, formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

type Snapshot = {
  items: Transaction[];
  total: number;
  error: string | null;
  gen: number;
};

function friendlyLedgerError(err: unknown, fallback: string): string {
  if (err instanceof ApiError) {
    if (err.code === "posted_immutable") {
      return "Posted entries can’t be edited or deleted. Reverse instead.";
    }
    return err.message;
  }
  return fallback;
}

function TransactionsInner() {
  const searchParams = useSearchParams();
  const { accessToken, ready } = useAuth();
  const initialCard = searchParams.get("card") ?? "";
  const initialContact = searchParams.get("contact") ?? "";

  const [showForm, setShowForm] = useState(false);
  const [cardFilter, setCardFilter] = useState(initialCard);
  const [contactFilter, setContactFilter] = useState(initialContact);
  const [typeFilter, setTypeFilter] = useState<TransactionType | "">("");
  const [statusFilter, setStatusFilter] = useState<PostingStatus | "">("");
  const [q, setQ] = useState("");
  const [qDebounced, setQDebounced] = useState("");
  const [cards, setCards] = useState<CreditCard[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reverseTarget, setReverseTarget] = useState<Transaction | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot>({
    items: [],
    total: 0,
    error: null,
    gen: -1,
  });

  useEffect(() => {
    const t = setTimeout(() => setQDebounced(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

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
        // meta load is best-effort; list still works
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ready, accessToken]);

  useEffect(() => {
    if (!ready || !accessToken) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const res = await listTransactions(accessToken, {
          pageSize: 50,
          cardId: cardFilter || undefined,
          contactId: contactFilter || undefined,
          type: typeFilter || undefined,
          postingStatus: statusFilter || undefined,
          q: qDebounced || undefined,
        });
        if (cancelled) return;
        setSnapshot({ items: res.items, total: res.total, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          items: [],
          total: 0,
          error: err instanceof ApiError ? err.message : "Failed to load transactions",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [
    ready,
    accessToken,
    reloadKey,
    cardFilter,
    contactFilter,
    typeFilter,
    statusFilter,
    qDebounced,
  ]);

  const cardMap = useMemo(
    () => Object.fromEntries(cards.map((c) => [c.id, c])),
    [cards],
  );
  const contactMap = useMemo(
    () => Object.fromEntries(contacts.map((c) => [c.id, c])),
    [contacts],
  );

  async function onDelete(id: string) {
    if (!accessToken) return;
    if (!confirm("Delete this draft? This cannot be undone.")) return;
    setBusyId(id);
    setActionError(null);
    try {
      await deleteTransaction(accessToken, id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setActionError(friendlyLedgerError(err, "Delete failed"));
    } finally {
      setBusyId(null);
    }
  }

  async function onPost(id: string) {
    if (!accessToken) return;
    setBusyId(id);
    setActionError(null);
    try {
      await postTransaction(accessToken, id);
      setReloadKey((k) => k + 1);
    } catch (err) {
      setActionError(friendlyLedgerError(err, "Could not post draft"));
    } finally {
      setBusyId(null);
    }
  }

  if (!ready) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (!accessToken) {
    return (
      <p className="text-sm text-muted-foreground">
        Sign in (or use demo login) to manage transactions.
      </p>
    );
  }

  const loading = snapshot.gen !== reloadKey;
  const txs = snapshot.items;
  const error = snapshot.error;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Transactions</h2>
          <p className="text-sm text-muted-foreground">
            Spend ledger with card and contact attribution
            {snapshot.total > 0 ? ` · ${snapshot.total} total` : ""}
          </p>
        </div>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="size-3.5" />
          {showForm ? "Hide form" : "Add transaction"}
        </Button>
      </div>

      {showForm && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Add transaction</CardTitle>
          </CardHeader>
          <CardContent>
            <TransactionForm
              accessToken={accessToken}
              cards={cards}
              contacts={contacts}
              defaultCardId={cardFilter || undefined}
              defaultContactId={contactFilter || undefined}
              onCancel={() => setShowForm(false)}
              onCreated={() => {
                setShowForm(false);
                setReloadKey((k) => k + 1);
              }}
            />
          </CardContent>
        </Card>
      )}

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardContent className="grid gap-3 py-4 sm:grid-cols-2 lg:grid-cols-5">
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-muted-foreground">Card</p>
            <select
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
              value={cardFilter}
              onChange={(e) => setCardFilter(e.target.value)}
            >
              <option value="">All cards</option>
              {cards.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.nickname}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-muted-foreground">Contact</p>
            <select
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
              value={contactFilter}
              onChange={(e) => setContactFilter(e.target.value)}
            >
              <option value="">Anyone</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-muted-foreground">Type</p>
            <select
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value as TransactionType | "")}
            >
              <option value="">All types</option>
              {TRANSACTION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-muted-foreground">Status</p>
            <select
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as PostingStatus | "")}
            >
              <option value="">All</option>
              <option value="posted">Posted</option>
              <option value="draft">Draft</option>
            </select>
          </div>
          <div className="space-y-1">
            <p className="text-[11px] font-medium text-muted-foreground">Search merchant</p>
            <Input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Swiggy, Netflix…"
              className="h-8"
            />
          </div>
        </CardContent>
      </Card>

      {(error || actionError) && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {actionError ?? error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading transactions…</p>
      ) : txs.length === 0 ? (
        <EmptyState
          icon={ArrowLeftRight}
          title="No transactions yet"
          description="Post a purchase or save a draft. Drafts stay off balances until you post them."
          action={
            !showForm ? (
              <Button size="sm" onClick={() => setShowForm(true)}>
                <Plus className="size-3.5" />
                Add transaction
              </Button>
            ) : null
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[820px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">When</th>
                  <th className="px-4 py-2.5 font-medium">Merchant</th>
                  <th className="px-4 py-2.5 font-medium">Card</th>
                  <th className="px-4 py-2.5 font-medium">Who</th>
                  <th className="px-4 py-2.5 font-medium">Type</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium">Amount</th>
                  <th className="px-4 py-2.5 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y">
                {txs.map((tx) => {
                  const card = cardMap[tx.credit_card_id];
                  const contact = tx.contact_id ? contactMap[tx.contact_id] : null;
                  const reduce =
                    tx.type === "refund" ||
                    tx.type === "payment_to_issuer" ||
                    tx.type === "reversal" ||
                    (tx.type === "adjustment" && (tx.delta_sign ?? 1) < 0);
                  const isDraft = tx.posting_status === "draft";
                  const alreadyReversed = Boolean(tx.reversed_by_id);
                  return (
                    <tr key={tx.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {formatDateIst(tx.occurred_at)}
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-medium">{tx.merchant}</p>
                        {tx.category && (
                          <p className="text-[11px] text-muted-foreground">{tx.category}</p>
                        )}
                        {alreadyReversed ? (
                          <p className="text-[11px] text-muted-foreground">Reversed</p>
                        ) : null}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {card ? (
                          <Link
                            href={`/app/cards/${card.id}`}
                            className="hover:underline"
                          >
                            {card.nickname}
                          </Link>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-xs">
                        {contact ? (
                          <Link
                            href={`/app/contacts/${contact.id}`}
                            className="hover:underline"
                          >
                            {contact.name}
                          </Link>
                        ) : (
                          <span className="text-muted-foreground">Self</span>
                        )}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="text-[10px] capitalize">
                          {tx.type.replaceAll("_", " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={isDraft ? "secondary" : "outline"}
                          className="font-mono text-[10px] uppercase tracking-wide"
                        >
                          {isDraft ? "Draft" : "Posted"}
                        </Badge>
                      </td>
                      <td
                        className={cn(
                          "px-4 py-3 font-mono text-sm tabular-nums",
                          reduce && "text-emerald-700 dark:text-emerald-400",
                        )}
                      >
                        {reduce ? "−" : ""}
                        {formatInrFromPaise(tx.amount_paise)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex flex-wrap justify-end gap-1">
                          {isDraft ? (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                className="h-7 text-xs"
                                disabled={busyId === tx.id}
                                onClick={() => void onPost(tx.id)}
                              >
                                Post
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 text-xs text-muted-foreground"
                                disabled={busyId === tx.id}
                                onClick={() => void onDelete(tx.id)}
                              >
                                Delete
                              </Button>
                            </>
                          ) : tx.type !== "reversal" ? (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              disabled={busyId === tx.id || alreadyReversed}
                              onClick={() => setReverseTarget(tx)}
                            >
                              {alreadyReversed ? "Reversed" : "Reverse"}
                            </Button>
                          ) : null}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      <ReverseTransactionDialog
        accessToken={accessToken}
        transaction={reverseTarget}
        open={reverseTarget !== null}
        onOpenChange={(open) => {
          if (!open) setReverseTarget(null);
        }}
        onReversed={() => {
          setActionError(null);
          setReloadKey((k) => k + 1);
        }}
      />
    </div>
  );
}

export default function TransactionsPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
      <TransactionsInner />
    </Suspense>
  );
}
