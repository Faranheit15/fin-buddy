"use client";

import { useEffect, useState } from "react";
import { Plus, Trash2 } from "lucide-react";

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
import { type Category } from "@/lib/api/categories";
import { ApiError } from "@/lib/api/client";
import { replaceTransactionSplits, type Transaction } from "@/lib/api/transactions";
import { formatInrFromPaise } from "@/lib/format";

type SplitEditorDialogProps = {
  accessToken: string;
  transaction: Transaction | null;
  categories: Category[];
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSaved: () => void;
};

type DraftSplit = {
  id: string; // temp id for React key
  categoryId: string;
  amountRupees: string;
};

export function SplitEditorDialog({
  accessToken,
  transaction,
  categories,
  open,
  onOpenChange,
  onSaved,
}: SplitEditorDialogProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [splits, setSplits] = useState<DraftSplit[]>([]);

  useEffect(() => {
    if (open && transaction) {
      if (transaction.splits && transaction.splits.length > 0) {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSplits(
          transaction.splits.map((s, i) => ({
            id: `init-${i}`,
            categoryId: s.category_id,
            amountRupees: (s.amount_paise / 100).toFixed(2),
          }))
        );
      } else {
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setSplits([
          {
            id: "init-0",
            categoryId: transaction.category_id ?? "",
            amountRupees: (transaction.amount_paise / 100).toFixed(2),
          },
        ]);
      }
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setError(null);
    }
  }, [open, transaction]);

  if (!transaction) return null;

  const totalPaise = transaction.amount_paise;
  const currentPaise = splits.reduce((sum, s) => {
    const p = Math.round(parseFloat(s.amountRupees || "0") * 100);
    return sum + (isNaN(p) ? 0 : p);
  }, 0);
  const remainingPaise = totalPaise - currentPaise;

  const isComplete = currentPaise === totalPaise && splits.every((s) => s.categoryId && parseFloat(s.amountRupees) > 0);

  function addSplit() {
    setSplits((prev) => [
      ...prev,
      {
        id: `new-${Date.now()}`,
        categoryId: "",
        amountRupees: remainingPaise > 0 ? (remainingPaise / 100).toFixed(2) : "",
      },
    ]);
  }

  function removeSplit(id: string) {
    setSplits((prev) => prev.filter((s) => s.id !== id));
  }

  function updateSplit(id: string, field: keyof DraftSplit, value: string) {
    setSplits((prev) => prev.map((s) => (s.id === id ? { ...s, [field]: value } : s)));
  }

  async function onSave() {
    if (!isComplete) {
      setError("Splits must sum exactly to the transaction total.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const payload = splits.map((s) => ({
        category_id: s.categoryId,
        amount_paise: Math.round(parseFloat(s.amountRupees) * 100),
      }));
      await replaceTransactionSplits(accessToken, transaction!.id, payload);
      onSaved();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save splits");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Split transaction</DialogTitle>
          <DialogDescription>
            Divide this {formatInrFromPaise(totalPaise)} transaction across multiple categories.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {splits.map((split) => (
            <div key={split.id} className="flex items-center gap-2">
              <div className="flex-1">
                <select
                  aria-label="Category"
                  className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
                  value={split.categoryId}
                  onChange={(e) => updateSplit(split.id, "categoryId", e.target.value)}
                  disabled={busy}
                >
                  <option value="" disabled>Select category</option>
                  {categories.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="w-28 shrink-0 relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-muted-foreground">
                  ₹
                </span>
                <Input
                  aria-label="Amount"
                  type="number"
                  step="0.01"
                  min="0"
                  className="pl-6 h-9"
                  value={split.amountRupees}
                  onChange={(e) => updateSplit(split.id, "amountRupees", e.target.value)}
                  disabled={busy}
                />
              </div>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 shrink-0 text-muted-foreground hover:text-destructive"
                disabled={busy || splits.length === 1}
                onClick={() => removeSplit(split.id)}
                aria-label="Remove split"
              >
                <Trash2 className="size-4" />
              </Button>
            </div>
          ))}

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addSplit}
            disabled={busy || remainingPaise <= 0}
            className="text-xs"
          >
            <Plus className="mr-1.5 size-3.5" />
            Add split
          </Button>
        </div>

        <div className="flex items-center justify-between border-t pt-4 text-sm">
          <div className="flex gap-4">
            <div>
              <span className="text-muted-foreground">Total:</span>{" "}
              <span className="font-mono">{formatInrFromPaise(totalPaise)}</span>
            </div>
            <div>
              <span className="text-muted-foreground">Remaining:</span>{" "}
              <span
                className={`font-mono font-medium ${
                  remainingPaise === 0
                    ? "text-emerald-600 dark:text-emerald-400"
                    : remainingPaise < 0
                      ? "text-destructive"
                      : ""
                }`}
              >
                {remainingPaise > 0 ? "+" : ""}
                {formatInrFromPaise(remainingPaise)}
              </span>
            </div>
          </div>
        </div>

        {error && (
          <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={busy}>
            Cancel
          </Button>
          <Button onClick={onSave} disabled={busy || !isComplete} aria-busy={busy}>
            {busy ? "Saving…" : "Save splits"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
