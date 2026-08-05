"use client";

import { useState } from "react";

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
import {
  reverseTransaction,
  type Transaction,
} from "@/lib/api/transactions";
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
  const [reason, setReason] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onConfirm() {
    if (!transaction) return;
    const trimmed = reason.trim();
    if (!trimmed) {
      setError("Reason is required");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const tx = await reverseTransaction(accessToken, transaction.id, {
        reason: trimmed,
      });
      setReason("");
      onReversed(tx);
      onOpenChange(false);
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.code === "already_reversed") {
          setError("This entry is already reversed.");
        } else if (err.code === "cannot_reverse") {
          setError(err.message);
        } else if (err.code === "posted_immutable") {
          setError("Posted entries can’t be edited or deleted. Reverse instead.");
        } else {
          setError(err.message);
        }
      } else {
        setError("Could not reverse transaction");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          setReason("");
          setError(null);
        }
        onOpenChange(next);
      }}
    >
      <DialogContent showCloseButton={!loading}>
        <DialogHeader>
          <DialogTitle>Reverse transaction</DialogTitle>
          <DialogDescription>
            Posts a linked reversing entry for the same amount. The original line stays on
            the ledger.
          </DialogDescription>
        </DialogHeader>

        {transaction ? (
          <p className="rounded-lg border border-border bg-muted/40 px-3 py-2 font-mono text-xs tabular-nums text-muted-foreground">
            {transaction.merchant} · {formatInrFromPaise(transaction.amount_paise)}
          </p>
        ) : null}

        <div className="space-y-1.5">
          <Label htmlFor="reverse-reason">Reason</Label>
          <textarea
            id="reverse-reason"
            className="flex min-h-20 w-full rounded-lg border border-input bg-background px-2.5 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Wrong amount, duplicate, …"
            disabled={loading}
            required
          />
        </div>

        {error ? (
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
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
          <Button type="button" disabled={loading || !transaction} onClick={() => void onConfirm()}>
            {loading ? "Reversing…" : "Reverse entry"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
