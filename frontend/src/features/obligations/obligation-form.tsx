"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { rupeesToPaise } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import { createObligation, type Obligation, type ObligationType } from "@/lib/api/obligations";
import { type Contact } from "@/lib/api/contacts";

type ObligationFormProps = {
  accessToken: string;
  type: ObligationType;
  contacts?: Contact[];
  onCreated: (obligation: Obligation) => void;
  onCancel?: () => void;
};

export function ObligationForm({
  accessToken,
  type,
  contacts = [],
  onCreated,
  onCancel,
}: ObligationFormProps) {
  const [amountRupees, setAmountRupees] = useState("");
  const [contactId, setContactId] = useState<string>("");
  const [counterpartyName, setCounterpartyName] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const amountPaise = rupeesToPaise(amountRupees);
      if (amountPaise <= 0) throw new Error("Amount must be greater than 0");
      if (!contactId && !counterpartyName.trim()) {
        throw new Error("Must select a contact or provide a name");
      }

      const obligation = await createObligation(accessToken, {
        type,
        amount_paise: amountPaise,
        contact_id: contactId || null,
        counterparty_name: contactId ? null : counterpartyName.trim(),
        notes: notes.trim() || null,
      });
      onCreated(obligation);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not record obligation",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="obl-amount">Amount (₹)</Label>
          <Input
            id="obl-amount"
            required
            inputMode="decimal"
            value={amountRupees}
            onChange={(e) => setAmountRupees(e.target.value)}
            placeholder="5000"
          />
        </div>

        {contacts.length > 0 ? (
          <div className="space-y-1.5">
            <Label htmlFor="obl-contact">Contact</Label>
            <select
              id="obl-contact"
              className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
              value={contactId}
              onChange={(e) => {
                setContactId(e.target.value);
                if (e.target.value) setCounterpartyName("");
              }}
            >
              <option value="">-- Or enter name below --</option>
              {contacts.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <div className="space-y-1.5">
          <Label htmlFor="obl-name">Counterparty Name</Label>
          <Input
            id="obl-name"
            value={counterpartyName}
            disabled={Boolean(contactId)}
            onChange={(e) => setCounterpartyName(e.target.value)}
            placeholder={contactId ? "Using selected contact" : "e.g. Bank Loan"}
            required={!contactId}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="obl-notes">Notes</Label>
          <Input
            id="obl-notes"
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
          {loading ? "Saving…" : "Save obligation"}
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
