"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { type Category, createCategory } from "@/lib/api/categories";
import { ApiError } from "@/lib/api/client";

type CategoryFormProps = {
  accessToken: string;
  onCreated: (cat: Category) => void;
  onCancel?: () => void;
};

export function CategoryForm({ accessToken, onCreated, onCancel }: CategoryFormProps) {
  const [name, setName] = useState("");
  const [kind, setKind] = useState<"income" | "expense">("expense");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;

    setBusy(true);
    setError(null);
    try {
      const cat = await createCategory(accessToken, { name: name.trim(), kind });
      onCreated(cat);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add category");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={submit}>
      <div className="space-y-1.5">
        <Label htmlFor="cat-name">Category name</Label>
        <Input
          id="cat-name"
          required
          autoFocus
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Travel"
          disabled={busy}
          maxLength={64}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="cat-kind">Kind</Label>
        <select
          id="cat-kind"
          className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
          value={kind}
          onChange={(e) => setKind(e.target.value as "income" | "expense")}
          disabled={busy}
        >
          <option value="expense">Expense</option>
          <option value="income">Income</option>
        </select>
      </div>

      {error && (
        <p role="alert" className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {error}
        </p>
      )}

      <div className="flex flex-wrap gap-2 pt-2">
        <Button type="submit" disabled={busy || !name.trim()} aria-busy={busy}>
          {busy ? "Saving…" : "Save"}
        </Button>
        {onCancel && (
          <Button type="button" variant="outline" onClick={onCancel} disabled={busy}>
            Cancel
          </Button>
        )}
      </div>
    </form>
  );
}
