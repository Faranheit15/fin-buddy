"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { rupeesToPaise } from "@/lib/api/cards";
import { createEmiPlan } from "@/lib/api/emis";
import { ApiError } from "@/lib/api/client";

function todayLocalInput(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function CreateEmiDialog({ cardId, onCreated }: { cardId: string; onCreated: () => void }) {
  const [open, setOpen] = useState(false);
  const { accessToken } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [principalRupees, setPrincipalRupees] = useState("");
  const [interestPercent, setInterestPercent] = useState("");
  const [tenureMonths, setTenureMonths] = useState("");
  const [startDate, setStartDate] = useState(todayLocalInput);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken) return;

    setBusy(true);
    setError(null);
    try {
      const principalPaise = rupeesToPaise(principalRupees);
      const interestRateBps = Math.round(parseFloat(interestPercent || "0") * 100);
      const tenure = parseInt(tenureMonths, 10);

      if (principalPaise <= 0) throw new Error("Principal must be > 0");
      if (tenure <= 0) throw new Error("Tenure must be > 0");
      if (interestRateBps < 0) throw new Error("Interest rate must be >= 0");

      await createEmiPlan(accessToken, {
        credit_card_id: cardId,
        principal_paise: principalPaise,
        interest_rate_bps: interestRateBps,
        tenure_months: tenure,
        start_date: startDate,
      });

      setOpen(false);
      onCreated();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : err instanceof Error ? err.message : "Failed to create EMI");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <Button variant="outline" size="sm" onClick={() => setOpen(true)}>Convert to EMI</Button>
      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
        <DialogHeader>
          <DialogTitle>Create EMI Plan</DialogTitle>
          <DialogDescription>Block limit for a new EMI plan.</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="emi-principal">Principal (₹)</Label>
              <Input
                id="emi-principal"
                required
                inputMode="decimal"
                value={principalRupees}
                onChange={(e) => setPrincipalRupees(e.target.value)}
                disabled={busy}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="emi-tenure">Tenure (months)</Label>
              <Input
                id="emi-tenure"
                required
                inputMode="numeric"
                value={tenureMonths}
                onChange={(e) => setTenureMonths(e.target.value)}
                disabled={busy}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="emi-interest">Interest Rate (%)</Label>
              <Input
                id="emi-interest"
                required
                inputMode="decimal"
                value={interestPercent}
                onChange={(e) => setInterestPercent(e.target.value)}
                placeholder="15.0"
                disabled={busy}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="emi-start">Start Date</Label>
              <Input
                id="emi-start"
                required
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                disabled={busy}
              />
            </div>
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setOpen(false)} disabled={busy}>
              Cancel
            </Button>
            <Button type="submit" disabled={busy}>
              Create EMI
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
    </>
  );
}
