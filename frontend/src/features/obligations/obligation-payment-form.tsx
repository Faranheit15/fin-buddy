"use client";

import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { rupeesToPaise } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import { addObligationPayment, type ObligationPayment } from "@/lib/api/obligations";
import { formatInrFromPaise } from "@/lib/format";

type ObligationPaymentFormProps = {
  accessToken: string;
  obligationId: string;
  currentBalancePaise?: number;
  onCreated: (payment: ObligationPayment) => void;
  onCancel?: () => void;
};

function todayLocalInput(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function ObligationPaymentForm({
  accessToken,
  obligationId,
  currentBalancePaise = 0,
  onCreated,
  onCancel,
}: ObligationPaymentFormProps) {
  const [amountRupees, setAmountRupees] = useState("");
  const [date, setDate] = useState(todayLocalInput);
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
      const paidAt = new Date(date);
      if (Number.isNaN(paidAt.getTime())) throw new Error("Invalid date/time");

      const payment = await addObligationPayment(
        accessToken,
        obligationId,
        {
          amount_paise: amountPaise,
          date: paidAt.toISOString(),
          notes: notes.trim() || null,
        },
        { idempotencyKey: idempotencyKeyRef.current },
      );
      idempotencyKeyRef.current = crypto.randomUUID();
      onCreated(payment);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not record payment",
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
          <Label htmlFor="pay-amount">Amount (₹)</Label>
          <Input
            id="pay-amount"
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
          <Label htmlFor="pay-at">Date</Label>
          <Input
            id="pay-at"
            type="datetime-local"
            required
            value={date}
            onChange={(e) => setDate(e.target.value)}
          />
        </div>
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="pay-notes">Notes</Label>
          <Input
            id="pay-notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Optional"
          />
        </div>
      </div>

      {currentBalancePaise > 0 && (
        <p className="text-xs text-muted-foreground">
          Remaining balance: {formatInrFromPaise(currentBalancePaise)}
        </p>
      )}

      {warnOverpay && (
        <p className="rounded-lg bg-amber-500/10 px-3 py-2 text-sm text-amber-800 dark:text-amber-200">
          Amount exceeds remaining balance. Submit again to confirm overpayment.
        </p>
      )}

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="flex flex-wrap gap-2">
        <Button type="submit" disabled={loading}>
          {loading ? "Saving…" : warnOverpay ? "Confirm overpayment" : "Record payment"}
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
