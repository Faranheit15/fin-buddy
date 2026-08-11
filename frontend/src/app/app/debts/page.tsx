"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Landmark } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageTableSkeleton, TableSkeleton } from "@/components/shared/page-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { ObligationForm } from "@/features/obligations/obligation-form";
import { listObligations, type Obligation } from "@/lib/api/obligations";
import { listContacts, type Contact } from "@/lib/api/contacts";
import { ApiError } from "@/lib/api/client";
import { formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

type Snapshot = {
  receivables: Obligation[];
  payables: Obligation[];
  contacts: Contact[];
  error: string | null;
  gen: number;
};

export default function DebtsPage() {
  const { accessToken, ready } = useAuth();
  const [showForm, setShowForm] = useState<"receivable" | "payable" | null>(null);
  const [activeTab, setActiveTab] = useState<"receivable" | "payable">("receivable");
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<Snapshot>({
    receivables: [],
    payables: [],
    contacts: [],
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const [recRes, payRes, contactRes] = await Promise.all([
          listObligations(accessToken, { type: "receivable", pageSize: 100 }),
          listObligations(accessToken, { type: "payable", pageSize: 100 }),
          listContacts(accessToken, { pageSize: 100 }),
        ]);
        if (cancelled) return;
        setSnapshot({
          receivables: recRes.items,
          payables: payRes.items,
          contacts: contactRes.items,
          error: null,
          gen,
        });
      } catch (err) {
        if (cancelled) return;
        setSnapshot((s) => ({
          ...s,
          error: err instanceof ApiError ? err.message : "Failed to load debts",
          gen,
        }));
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, reloadKey]);

  if (!ready) {
    return <PageTableSkeleton columns={4} titleWidth="w-32" />;
  }
  if (!accessToken) {
    return <p className="text-sm text-muted-foreground">Sign in to manage debts.</p>;
  }

  const loading = snapshot.gen !== reloadKey;
  const items = activeTab === "receivable" ? snapshot.receivables : snapshot.payables;
  const error = snapshot.error;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Debts & Loans</h2>
          <p className="text-sm text-muted-foreground">
            Track money owed outside of shared card spends
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowForm(showForm === "receivable" ? null : "receivable")}
          >
            <Plus className="mr-1.5 size-3.5" />
            Add Receivable
          </Button>
          <Button size="sm" onClick={() => setShowForm(showForm === "payable" ? null : "payable")}>
            <Plus className="mr-1.5 size-3.5" />
            Add Payable
          </Button>
        </div>
      </div>

      {showForm && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Add {showForm}</CardTitle>
          </CardHeader>
          <CardContent>
            <ObligationForm
              accessToken={accessToken}
              type={showForm}
              contacts={snapshot.contacts}
              onCancel={() => setShowForm(null)}
              onCreated={() => {
                setShowForm(null);
                setActiveTab(showForm);
                setReloadKey((k) => k + 1);
              }}
            />
          </CardContent>
        </Card>
      )}

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="flex gap-4 border-b">
        <button
          onClick={() => {
            setActiveTab("receivable");
            setShowForm(null);
          }}
          className={cn(
            "border-b-2 px-1 pb-2 text-sm font-medium transition-colors",
            activeTab === "receivable"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          Receivables ({snapshot.receivables.length})
        </button>
        <button
          onClick={() => {
            setActiveTab("payable");
            setShowForm(null);
          }}
          className={cn(
            "border-b-2 px-1 pb-2 text-sm font-medium transition-colors",
            activeTab === "payable"
              ? "border-primary text-foreground"
              : "border-transparent text-muted-foreground hover:text-foreground",
          )}
        >
          Payables ({snapshot.payables.length})
        </button>
      </div>

      {loading ? (
        <TableSkeleton columns={4} label="Loading debts" />
      ) : items.length === 0 ? (
        <EmptyState
          icon={Landmark}
          title={`No ${activeTab}s`}
          description={`Track loans or debts you ${activeTab === "receivable" ? "are owed" : "owe"} outside card spends.`}
          action={
            <Button size="sm" onClick={() => setShowForm(activeTab)}>
              <Plus className="mr-1.5 size-3.5" />
              Add {activeTab}
            </Button>
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[600px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Counterparty</th>
                  <th className="px-4 py-2.5 font-medium">Original Amount</th>
                  <th className="px-4 py-2.5 font-medium">Remaining</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {items.map((obl) => {
                  const remaining = obl.remaining_paise ?? 0;
                  const contact = snapshot.contacts.find((c) => c.id === obl.contact_id);
                  const name = contact ? contact.name : obl.counterparty_name || "Unknown";
                  return (
                    <tr key={obl.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <Link href={`/app/debts/${obl.id}`} className="font-medium hover:underline">
                          {name}
                        </Link>
                        {obl.contact_id && (
                          <span className="ml-2 rounded border px-1.5 py-0.5 text-[10px] text-muted-foreground">
                            Contact
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm tabular-nums text-muted-foreground">
                        {formatInrFromPaise(obl.amount_paise)}
                      </td>
                      <td className="px-4 py-3 font-mono text-sm tabular-nums">
                        <span
                          className={
                            remaining > 0 ? "font-medium text-foreground" : "text-muted-foreground"
                          }
                        >
                          {formatInrFromPaise(remaining)}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={obl.status === "active" ? "secondary" : "outline"}
                          className="text-[10px] uppercase"
                        >
                          {obl.status}
                        </Badge>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
