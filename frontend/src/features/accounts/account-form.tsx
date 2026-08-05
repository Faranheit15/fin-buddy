"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { createAccount } from "@/lib/api/accounts";
import { rupeesToPaise } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";

type AccountFormProps = {
  accessToken: string;
  onCreated: () => void;
  onCancel: () => void;
};

export function AccountForm({ accessToken, onCreated, onCancel }: AccountFormProps) {
  const [kind, setKind] = useState<"bank" | "cash" | "wallet">("bank");
  const [name, setName] = useState("");
  const [institution, setInstitution] = useState("");
  const [openingBalance, setOpeningBalance] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const nm = name.trim();
      if (!nm) throw new Error("Account name is required");
      
      const balancePaise = openingBalance.trim() ? rupeesToPaise(openingBalance) : null;
      
      await createAccount(accessToken, {
        kind,
        name: nm,
        institution: institution.trim() || null,
        opening_balance_paise: balancePaise,
      });
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create account");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="space-y-4" onSubmit={submit}>
      <div className="space-y-1.5">
        <Label htmlFor="acc-kind">Type</Label>
        <select
          id="acc-kind"
          className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm disabled:opacity-50"
          value={kind}
          onChange={(e) => setKind(e.target.value as "bank" | "cash" | "wallet")}
          disabled={busy}
        >
          <option value="bank">Bank Account</option>
          <option value="cash">Cash</option>
          <option value="wallet">Wallet</option>
        </select>
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="acc-name">Name</Label>
        <Input
          id="acc-name"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Daily Expenses, HDFC Savings"
          disabled={busy}
          maxLength={120}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="acc-inst">Institution (optional)</Label>
        <Input
          id="acc-inst"
          value={institution}
          onChange={(e) => setInstitution(e.target.value)}
          placeholder="e.g. HDFC, Paytm"
          disabled={busy}
          maxLength={120}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="acc-open">Opening balance (₹, optional)</Label>
        <Input
          id="acc-open"
          inputMode="decimal"
          value={openingBalance}
          onChange={(e) => setOpeningBalance(e.target.value)}
          placeholder="0"
          disabled={busy}
        />
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="flex gap-2 pt-2">
        <Button type="submit" disabled={busy} aria-busy={busy}>
          {busy ? "Saving…" : "Add account"}
        </Button>
        <Button type="button" variant="outline" onClick={onCancel} disabled={busy}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
