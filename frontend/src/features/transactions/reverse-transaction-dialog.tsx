"use client";

import { useId, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { ApiError } from "@/lib/api/client";
import { reverseTransaction, type Transaction } from "@/lib/api/transactions";
import { formatInrFromPaise } from "@/lib/format";

type ReverseTransactionDialogProps = {
  accessToken: string;
  transaction: Transaction | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onReversed: (tx: Transaction) => void;
};

export function ReverseTransactionDialog({
  accessToken,
  transaction,
  open,
  onOpenChange,
  onReversed,
}: ReverseTransactionDialogProps) {
  const reasonId = useId();
  const errorId = useId();
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isSubmittingRef = useRef(false);
  const idempotencyKeyRef = useRef<string>(crypto.randomUUID());

  function resetLocal() {
    setReason("");
    setError(null);
    setLoading(false);
  }

  async function onConfirm() {
    if (!transaction) return;
    if (isSubmittingRef.current) return;
    const trimmed = reason.trim();
    if (!trimmed) {
      setError("Add a short reason so the ledger stays auditable.");
      return;
    }
    isSubmittingRef.current = true;
    setLoading(true);
    setError(null);
    try {
      const tx = await reverseTransaction(
        accessToken,
        transaction.id,
        { reason: trimmed },
        { idempotencyKey: idempotencyKeyRef.current },
      );
      idempotencyKeyRef.current = crypto.randomUUID();
      resetLocal();
      onReversed(tx);
      onOpenChange(false);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === "already_reversed") {
          setError("This entry is already reversed. Refresh the list if it still shows Reverse.");
        } else if (err.code === "cannot_reverse") {
          setError(err.message || "This entry can’t be reversed.");
        } else if (err.code === "posted_immutable") {
          setError("Posted entries can’t be edited or deleted. Reverse instead.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Could not reverse. Check your connection and try again.");
      }
    } finally {
      isSubmittingRef.current = false;
      setLoading(false);
    }
  }

  const canSubmit = Boolean(transaction) && reason.trim().length > 0 && !loading;

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (loading) return;
        if (!next) resetLocal();
        onOpenChange(next);
      }}
    >
      <DialogContent showCloseButton={!loading}>
        <DialogHeader>
          <DialogTitle>Reverse transaction</DialogTitle>
          <DialogDescription>
            Posts a linked reversing entry for the same amount. The original line stays on the
            ledger.
          </DialogDescription>
        </DialogHeader>

        {transaction ? (
          <p className="min-w-0 rounded-lg border border-border bg-muted/40 px-3 py-2 font-mono text-xs tabular-nums text-muted-foreground">
            <span className="block truncate" title={transaction.merchant}>
              {transaction.merchant}
            </span>
            <span>{formatInrFromPaise(transaction.amount_paise)}</span>
          </p>
        ) : null}

        <div className="space-y-1.5">
          <Label htmlFor={reasonId}>Reason</Label>
          <textarea
            id={reasonId}
            className="flex min-h-20 w-full rounded-lg border border-input bg-background px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 disabled:opacity-50"
            value={reason}
            onChange={(e) => {
              setReason(e.target.value);
              if (error) setError(null);
            }}
            placeholder="Wrong amount, duplicate, …"
            disabled={loading}
            required
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? errorId : undefined}
            maxLength={500}
          />
        </div>

        {error ? (
          <p
            id={errorId}
            role="alert"
            className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive"
          >
            {error}
          </p>
        ) : null}

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            disabled={loading}
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button
            type="button"
            disabled={!canSubmit}
            aria-busy={loading}
            onClick={() => void onConfirm()}
          >
            {loading ? "Reversing…" : "Reverse entry"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
