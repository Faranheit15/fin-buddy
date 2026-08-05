"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Wallet } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { AccountForm } from "@/features/accounts/account-form";
import { listAccounts, type AccountResponse } from "@/lib/api/accounts";
import { ApiError } from "@/lib/api/client";
import { formatInrFromPaise } from "@/lib/format";

type AccountsSnapshot = {
  items: AccountResponse[];
  error: string | null;
  gen: number;
};

export default function AccountsPage() {
  const { accessToken, ready } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<AccountsSnapshot>({
    items: [],
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const res = await listAccounts(accessToken);
        if (cancelled) return;
        setSnapshot({ items: res.items, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          items: [],
          error: err instanceof ApiError ? err.message : "Failed to load accounts",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, reloadKey]);

  if (!ready) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (!accessToken) {
    return (
      <p className="text-sm text-muted-foreground">
        Sign in (or use demo login) to manage accounts.
      </p>
    );
  }

  const loading = snapshot.gen !== reloadKey;
  const accounts = snapshot.items;
  const error = snapshot.error;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Accounts</h2>
          <p className="text-sm text-muted-foreground">
            Balances from posted ledger entries
          </p>
        </div>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="size-3.5" />
          {showForm ? "Hide form" : "Add account"}
        </Button>
      </div>

      {showForm && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Add account</CardTitle>
          </CardHeader>
          <CardContent className="pt-4">
            <AccountForm
              accessToken={accessToken}
              onCancel={() => setShowForm(false)}
              onCreated={() => {
                setShowForm(false);
                setReloadKey((k) => k + 1);
              }}
            />
          </CardContent>
        </Card>
      )}

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading accounts…</p>
      ) : accounts.length === 0 ? (
        <EmptyState
          icon={Wallet}
          title="No accounts yet"
          description="Start with Cash if you track pocket money. Card balances stay under Cards."
          action={
            !showForm ? (
              <Button size="sm" onClick={() => setShowForm(true)}>
                <Plus className="size-3.5" />
                Add account
              </Button>
            ) : null
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[500px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Name</th>
                  <th className="px-4 py-2.5 font-medium">Kind</th>
                  <th className="px-4 py-2.5 font-medium text-right">Balance</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {accounts.map((acc) => {
                  const href = acc.kind === "credit_card" && acc.credit_card_id
                    ? `/app/cards/${acc.credit_card_id}`
                    : `/app/accounts/${acc.id}`;
                  return (
                    <tr key={acc.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <Link href={href} className="group block min-w-0">
                          <p className="font-medium group-hover:underline">{acc.name}</p>
                          {acc.institution && (
                            <p className="text-xs text-muted-foreground">{acc.institution}</p>
                          )}
                        </Link>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline" className="capitalize font-normal text-xs text-muted-foreground">
                          {acc.kind.replace("_", " ")}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-right font-mono tabular-nums text-sm">
                        {formatInrFromPaise(acc.balance_paise)}
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
