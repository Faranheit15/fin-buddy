"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type AccountResponse } from "@/lib/api/accounts";
import { rupeesToPaise } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import type { Contact } from "@/lib/api/contacts";
import {
  createTransaction,
  TRANSACTION_TYPES,
  type PostingStatus,
  type Transaction,
  type TransactionType,
} from "@/lib/api/transactions";
import { type Category } from "@/lib/api/categories";
import { createTransfer } from "@/lib/api/transfers";

type TransactionFormProps = {
  accessToken: string;
  accounts: AccountResponse[];
  contacts: Contact[];
  categories: Category[];
  defaultAccountId?: string;
  defaultContactId?: string;
  onCreated: (tx: Transaction) => void;
  onCancel?: () => void;
};

function todayLocalInput(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function TransactionForm({
  accessToken,
  accounts,
  contacts,
  categories,
  defaultAccountId,
  defaultContactId,
  onCreated,
  onCancel,
}: TransactionFormProps) {
  const [accountId, setAccountId] = useState(defaultAccountId ?? accounts[0]?.id ?? "");
  const [toAccountId, setToAccountId] = useState(accounts[1]?.id ?? accounts[0]?.id ?? "");
  const [contactId, setContactId] = useState(defaultContactId ?? "");
  const [type, setType] = useState<TransactionType | "transfer">("purchase");
  const [amountRupees, setAmountRupees] = useState("");
  const [merchant, setMerchant] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [notes, setNotes] = useState("");
  const [occurredAt, setOccurredAt] = useState(todayLocalInput);
  const [loading, setLoading] = useState<"posted" | "draft" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function submit(postingStatus: PostingStatus) {
    setLoading(postingStatus);
    setError(null);
    try {
      if (!accountId) throw new Error("Select an account");
      const amountPaise = rupeesToPaise(amountRupees);
      if (amountPaise <= 0) throw new Error("Amount must be greater than 0");
      const merch = merchant.trim();
      if (!merch) throw new Error("Merchant / description is required");
      const occurred = new Date(occurredAt);
      if (Number.isNaN(occurred.getTime())) throw new Error("Invalid date/time");

      const acc = accounts.find((a) => a.id === accountId);
      const isCard = acc?.kind === "credit_card";

      if (type === "transfer") {
        if (!toAccountId) throw new Error("Select destination account");
        if (accountId === toAccountId) throw new Error("Source and destination accounts must be different");
        const [outTx] = await createTransfer(accessToken, {
          from_account_id: accountId,
          to_account_id: toAccountId,
          amount_paise: amountPaise,
          occurred_at: occurred.toISOString(),
          merchant: merch,
          notes: notes.trim() || null,
          posting_status: postingStatus,
        });
        onCreated(outTx);
        return;
      }

      const tx = await createTransaction(accessToken, {
        account_id: accountId,
        credit_card_id: isCard ? acc.credit_card_id : null,
        type,
        amount_paise: amountPaise,
        occurred_at: occurred.toISOString(),
        merchant: merch,
        contact_id: contactId || null,
        category_id: categoryId || null,
        notes: notes.trim() || null,
        posting_status: postingStatus,
      });
      onCreated(tx);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.code === "invalid_posting_type"
            ? "Use Reverse or Correct Balance for corrections — not the create form."
            : err.message
          : err instanceof Error
            ? err.message
            : "Could not create transaction",
      );
    } finally {
      setLoading(null);
    }
  }

  if (accounts.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Add an account first before recording transactions.
      </p>
    );
  }

  const busy = loading !== null;

  return (
    <form
      className="space-y-3"
      onSubmit={(e) => {
        e.preventDefault();
        void submit("posted");
      }}
    >
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="tx-account">Account</Label>
          <select
            id="tx-account"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            required
            disabled={busy}
          >
            {accounts.map((a) => (
              <option key={a.id} value={a.id}>
                {a.name} {a.institution ? `(${a.institution})` : ""}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-type">Type</Label>
          <select
            id="tx-type"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
            value={type}
            onChange={(e) => setType(e.target.value as TransactionType | "transfer")}
            disabled={busy}
          >
            {TRANSACTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
            <option value="transfer">Transfer (between accounts)</option>
          </select>
        </div>
        
        {type === "transfer" && (
          <div className="space-y-1.5">
            <Label htmlFor="tx-to-account">To Account</Label>
            <select
              id="tx-to-account"
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
              value={toAccountId}
              onChange={(e) => setToAccountId(e.target.value)}
              required
              disabled={busy}
            >
              {accounts.map((a) => (
                <option key={a.id} value={a.id}>
                  {a.name} {a.institution ? `(${a.institution})` : ""}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="space-y-1.5">
          <Label htmlFor="tx-amount">Amount (₹)</Label>
          <Input
            id="tx-amount"
            required
            inputMode="decimal"
            value={amountRupees}
            onChange={(e) => setAmountRupees(e.target.value)}
            placeholder="2450"
            disabled={busy}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-when">When</Label>
          <Input
            id="tx-when"
            type="datetime-local"
            required
            value={occurredAt}
            onChange={(e) => setOccurredAt(e.target.value)}
            disabled={busy}
          />
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="tx-merchant">Merchant / description</Label>
          <Input
            id="tx-merchant"
            required
            value={merchant}
            onChange={(e) => setMerchant(e.target.value)}
            placeholder="Swiggy"
            disabled={busy}
            maxLength={255}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-contact">Attributed to</Label>
          <select
            id="tx-contact"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
            value={contactId}
            onChange={(e) => setContactId(e.target.value)}
            disabled={busy}
          >
            <option value="">Self (you)</option>
            {contacts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        {type !== "transfer" && (
          <div className="space-y-1.5">
            <Label htmlFor="tx-category">Category</Label>
            <select
              id="tx-category"
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
              value={categoryId}
              onChange={(e) => setCategoryId(e.target.value)}
              disabled={busy}
            >
              <option value="">Uncategorized</option>
              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="tx-notes">Notes</Label>
          <Input
            id="tx-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional"
            disabled={busy}
            maxLength={500}
          />
        </div>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={busy} aria-busy={loading === "posted"}>
          {loading === "posted" ? "Posting…" : "Add transaction"}
        </Button>
        <Button
          type="button"
          variant="outline"
          disabled={busy}
          aria-busy={loading === "draft"}
          onClick={() => void submit("draft")}
        >
          {loading === "draft" ? "Saving…" : "Save draft"}
        </Button>
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
        ) : null}
      </div>
    </form>
  );
}
