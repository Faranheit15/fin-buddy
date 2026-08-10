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
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { correctBalance } from "@/lib/api/accounts";
import { rupeesToPaise } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import { formatInrFromPaise } from "@/lib/format";

type CorrectBalanceDialogProps = {
  accessToken: string;
  accountId: string;
  currentBalancePaise: number;
  kind: "bank" | "cash" | "wallet" | "credit_card";
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCorrected: () => void;
};

function todayLocalInput(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export function CorrectBalanceDialog({
  accessToken,
  accountId,
  currentBalancePaise,
  kind,
  open,
  onOpenChange,
  onCorrected,
}: CorrectBalanceDialogProps) {
  const [targetBalance, setTargetBalance] = useState("");
  const [reason, setReason] = useState("");
  const [occurredAt, setOccurredAt] = useState(todayLocalInput);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const targetPaise = targetBalance.trim() ? rupeesToPaise(targetBalance) : null;
  const deltaPaise = targetPaise !== null ? targetPaise - currentBalancePaise : null;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (targetPaise === null) throw new Error("Target balance is required");
      if (targetPaise === currentBalancePaise) throw new Error("Already at that balance");
      const r = reason.trim();
      if (!r) throw new Error("Reason is required");

      const occurred = new Date(occurredAt);
      if (Number.isNaN(occurred.getTime())) throw new Error("Invalid date");

      await correctBalance(accessToken, accountId, {
        target_balance_paise: targetPaise,
        reason: r,
        occurred_at: occurred.toISOString(),
      });
      onOpenChange(false);
      onCorrected();

      // Reset
      setTargetBalance("");
      setReason("");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.code === "already_at_target"
            ? "Already at that balance."
            : err.message
          : "Could not correct balance",
      );
    } finally {
      setBusy(false);
    }
  }

  const label = kind === "credit_card" ? "Outstanding" : "Balance";

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Correct balance</DialogTitle>
          <DialogDescription>
            Post an adjustment transaction to reconcile the account.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4 pt-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Current {label.toLowerCase()}</Label>
              <div className="flex h-8 w-full items-center rounded-lg border border-input bg-muted/50 px-2.5 font-mono text-sm">
                {formatInrFromPaise(currentBalancePaise)}
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cb-target">Target {label.toLowerCase()} (₹)</Label>
              <Input
                id="cb-target"
                required
                inputMode="decimal"
                value={targetBalance}
                onChange={(e) => setTargetBalance(e.target.value)}
                placeholder="0"
                disabled={busy}
              />
            </div>
          </div>

          <div className="space-y-1.5">
            <Label>Adjustment delta</Label>
            <div className="flex h-8 w-full items-center rounded-lg border border-input bg-muted/50 px-2.5 font-mono text-sm">
              {deltaPaise !== null
                ? `${deltaPaise >= 0 ? "+" : ""}${formatInrFromPaise(deltaPaise)}`
                : "—"}
            </div>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="cb-reason">Reason</Label>
            <Input
              id="cb-reason"
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Reconcile with bank statement"
              disabled={busy}
              maxLength={2000}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="cb-when">Effective at</Label>
            <Input
              id="cb-when"
              type="datetime-local"
              required
              value={occurredAt}
              onChange={(e) => setOccurredAt(e.target.value)}
              disabled={busy}
            />
          </div>

          {error && (
            <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </p>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={busy}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={busy || deltaPaise === 0} aria-busy={busy}>
              {busy ? "Posting…" : "Post adjustment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
