"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  createCard,
  rupeesToPaise,
  type CardNetwork,
  type CreditCard,
  type DueRuleType,
} from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";

const NETWORKS: { value: CardNetwork; label: string }[] = [
  { value: "visa", label: "Visa" },
  { value: "mastercard", label: "Mastercard" },
  { value: "rupay", label: "RuPay" },
  { value: "amex", label: "Amex" },
  { value: "other", label: "Other" },
];

type CardFormProps = {
  accessToken: string;
  onCreated: (card: CreditCard) => void;
  onCancel?: () => void;
};

export function CardForm({ accessToken, onCreated, onCancel }: CardFormProps) {
  const [nickname, setNickname] = useState("");
  const [issuer, setIssuer] = useState("");
  const [network, setNetwork] = useState<CardNetwork>("visa");
  const [lastFour, setLastFour] = useState("");
  const [limitRupees, setLimitRupees] = useState("");
  const [openingRupees, setOpeningRupees] = useState("");
  const [statementDay, setStatementDay] = useState("15");
  const [dueRuleType, setDueRuleType] = useState<DueRuleType>("days_after_statement");
  const [dueRuleValue, setDueRuleValue] = useState("20");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      if (!/^\d{4}$/.test(lastFour)) {
        throw new Error("Last four must be exactly 4 digits");
      }
      const limitPaise = rupeesToPaise(limitRupees);
      if (limitPaise <= 0) throw new Error("Credit limit must be greater than 0");

      const card = await createCard(accessToken, {
        nickname: nickname.trim(),
        issuer: issuer.trim(),
        network,
        last_four: lastFour,
        credit_limit_paise: limitPaise,
        statement_day: Number(statementDay),
        due_rule_type: dueRuleType,
        due_rule_value: Number(dueRuleValue),
        notes: notes.trim() || null,
        opening_balance_paise: openingRupees
          ? rupeesToPaise(openingRupees) || null
          : null,
      });
      onCreated(card);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not create card",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <form className="space-y-3" onSubmit={(e) => void onSubmit(e)}>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="nickname">Nickname</Label>
          <Input
            id="nickname"
            required
            value={nickname}
            onChange={(e) => setNickname(e.target.value)}
            placeholder="HDFC Regalia"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="issuer">Issuer / bank</Label>
          <Input
            id="issuer"
            required
            value={issuer}
            onChange={(e) => setIssuer(e.target.value)}
            placeholder="HDFC Bank"
          />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="network">Network</Label>
          <select
            id="network"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
            value={network}
            onChange={(e) => setNetwork(e.target.value as CardNetwork)}
          >
            {NETWORKS.map((n) => (
              <option key={n.value} value={n.value}>
                {n.label}
              </option>
            ))}
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="lastFour">Last 4 digits</Label>
          <Input
            id="lastFour"
            required
            inputMode="numeric"
            maxLength={4}
            value={lastFour}
            onChange={(e) => setLastFour(e.target.value.replace(/\D/g, "").slice(0, 4))}
            placeholder="4821"
            className="font-mono"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="limit">Credit limit (₹)</Label>
          <Input
            id="limit"
            required
            inputMode="decimal"
            value={limitRupees}
            onChange={(e) => setLimitRupees(e.target.value)}
            placeholder="500000"
          />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="statementDay">Statement day</Label>
          <Input
            id="statementDay"
            type="number"
            min={1}
            max={31}
            required
            value={statementDay}
            onChange={(e) => setStatementDay(e.target.value)}
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="dueRuleType">Due rule</Label>
          <select
            id="dueRuleType"
            className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
            value={dueRuleType}
            onChange={(e) => setDueRuleType(e.target.value as DueRuleType)}
          >
            <option value="days_after_statement">Days after statement</option>
            <option value="fixed_day">Fixed day of month</option>
          </select>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="dueRuleValue">
            {dueRuleType === "fixed_day" ? "Due day (1–31)" : "Days after statement"}
          </Label>
          <Input
            id="dueRuleValue"
            type="number"
            min={1}
            max={31}
            required
            value={dueRuleValue}
            onChange={(e) => setDueRuleValue(e.target.value)}
          />
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="space-y-1.5">
          <Label htmlFor="opening">Opening outstanding (₹, optional)</Label>
          <Input
            id="opening"
            inputMode="decimal"
            value={openingRupees}
            onChange={(e) => setOpeningRupees(e.target.value)}
            placeholder="0"
          />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="notes">Notes</Label>
          <Input
            id="notes"
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
          {loading ? "Saving…" : "Add card"}
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
