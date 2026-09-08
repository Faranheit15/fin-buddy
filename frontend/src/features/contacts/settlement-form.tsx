"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { rupeesToPaise } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import {
  createSettlement,
  SETTLEMENT_METHODS,
  type Settlement,
  type SettlementMethod,
} from "@/lib/api/settlements";
import { formatInrFromPaise } from "@/lib/format";

type SettlementFormProps = {
  accessToken: string;
  contactId: string;
  currentBalancePaise?: number;
  onCreated: (settlement: Settlement) => void;
  onCancel?: () => void;
};

function todayLocalInput(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function SettlementForm({
  accessToken,
  contactId,
  currentBalancePaise = 0,
  onCreated,
  onCancel,
}: SettlementFormProps) {
  const [amountRupees, setAmountRupees] = useState("");
  const [settledAt, setSettledAt] = useState(todayLocalInput);
  const [method, setMethod] = useState<SettlementMethod>("upi");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [warnOverpay, setWarnOverpay] = useState(false);
  const isSubmittingRef = useRef(false);
  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (isSubmittingRef.current) return;
    isSubmittingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const amountPaise = rupeesToPaise(amountRupees);
      if (amountPaise <= 0) throw new Error("Amount must be greater than 0");
      if (amountPaise > currentBalancePaise && currentBalancePaise > 0 && !warnOverpay) {
        setWarnOverpay(true);
        setLoading(false);
        isSubmittingRef.current = false;
        return;
      }
      const settled = new Date(settledAt);
      if (Number.isNaN(settled.getTime())) throw new Error("Invalid date/time");

      const settlement = await createSettlement(
        accessToken,
        {
          contact_id: contactId,
          amount_paise: amountPaise,
          settled_at: settled.toISOString(),
          method,
          notes: notes.trim() || null,
        },
        { idempotencyKey: idempotencyKeyRef.current },
      );
      idempotencyKeyRef.current = crypto.randomUUID();
      onCreated(settlement);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not record settlement",
      );
    } finally {
      isSubmittingRef.current = false;
      setLoading(false);
    }
  }

  return (
    <form className="space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="settle-amount">Amount (₹)</Label>
          <Input
            id="settle-amount"
            required
            inputMode="decimal"
            value={amountRupees}
            onChange={(e) => {
              setAmountRupees(e.target.value);
              setWarnOverpay(false);
            }}
            placeholder="5000"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="settle-method">Method</Label>
          <select
            id="settle-method"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
            value={method}
            onChange={(e) => setMethod(e.target.value as SettlementMethod)}
          >
            {SETTLEMENT_METHODS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="settle-at">Settled at</Label>
          <Input
            id="settle-at"
            type="datetime-local"
            required
            value={settledAt}
            onChange={(e) => setSettledAt(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="settle-notes">Notes</Label>
          <Input
            id="settle-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional"
          />
        </div>
      </div>

      {currentBalancePaise > 0 && (
        <p className="text-xs text-muted-foreground">
          Current balance: {formatInrFromPaise(currentBalancePaise)}
        </p>
      )}

      {warnOverpay && (
        <p className="rounded-lg bg-amber-500/10 px-3 py-2 text-sm text-amber-800 dark:text-amber-200">
          Amount exceeds current balance. Submit again to confirm overpayment (credit).
        </p>
      )}

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Saving…" : warnOverpay ? "Confirm overpayment" : "Record settlement"}
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
