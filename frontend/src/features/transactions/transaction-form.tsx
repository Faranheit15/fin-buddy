"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { rupeesToPaise, type CreditCard } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import type { Contact } from "@/lib/api/contacts";
import {
  createTransaction,
  TRANSACTION_TYPES,
  type Transaction,
  type TransactionType,
} from "@/lib/api/transactions";

type TransactionFormProps = {
  accessToken: string;
  cards: CreditCard[];
  contacts: Contact[];
  defaultCardId?: string;
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
  cards,
  contacts,
  defaultCardId,
  defaultContactId,
  onCreated,
  onCancel,
}: TransactionFormProps) {
  const [cardId, setCardId] = useState(defaultCardId ?? cards[0]?.id ?? "");
  const [contactId, setContactId] = useState(defaultContactId ?? "");
  const [type, setType] = useState<TransactionType>("purchase");
  const [amountRupees, setAmountRupees] = useState("");
  const [merchant, setMerchant] = useState("");
  const [category, setCategory] = useState("");
  const [notes, setNotes] = useState("");
  const [occurredAt, setOccurredAt] = useState(todayLocalInput);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!cardId) throw new Error("Select a card");
      const amountPaise = rupeesToPaise(amountRupees);
      if (amountPaise <= 0) throw new Error("Amount must be greater than 0");
      const merch = merchant.trim();
      if (!merch) throw new Error("Merchant / description is required");
      const occurred = new Date(occurredAt);
      if (Number.isNaN(occurred.getTime())) throw new Error("Invalid date/time");

      const tx = await createTransaction(accessToken, {
        credit_card_id: cardId,
        type,
        amount_paise: amountPaise,
        occurred_at: occurred.toISOString(),
        merchant: merch,
        contact_id: contactId || null,
        category: category.trim() || null,
        notes: notes.trim() || null,
      });
      onCreated(tx);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not create transaction",
      );
    } finally {
      setLoading(false);
    }
  }

  if (cards.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Add a credit card first before recording transactions.
      </p>
    );
  }

  return (
    <form className="space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="tx-card">Card</Label>
          <select
            id="tx-card"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
            value={cardId}
            onChange={(e) => setCardId(e.target.value)}
            required
          >
            {cards.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nickname} · •••• {c.last_four}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-type">Type</Label>
          <select
            id="tx-type"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
            value={type}
            onChange={(e) => setType(e.target.value as TransactionType)}
          >
            {TRANSACTION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-amount">Amount (₹)</Label>
          <Input
            id="tx-amount"
            required
            inputMode="decimal"
            value={amountRupees}
            onChange={(e) => setAmountRupees(e.target.value)}
            placeholder="2450"
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
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-contact">Attributed to</Label>
          <select
            id="tx-contact"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
            value={contactId}
            onChange={(e) => setContactId(e.target.value)}
          >
            <option value="">Self (you)</option>
            {contacts.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="tx-category">Category</Label>
          <Input
            id="tx-category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="Food, Travel…"
          />
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="tx-notes">Notes</Label>
          <Input
            id="tx-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional"
          />
        </div>
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Saving…" : "Add transaction"}
        </Button>
        {onCancel ? (
          <Button type="button" variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
        ) : null}
      </div>
    </form>
  );
}
