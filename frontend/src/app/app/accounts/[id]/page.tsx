"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { CorrectBalanceDialog } from "@/features/accounts/correct-balance-dialog";
import { getAccount, archiveAccount, type AccountResponse } from "@/lib/api/accounts";
import { ApiError } from "@/lib/api/client";
import { formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

type AccountSnapshot = {
  account: AccountResponse | null;
  error: string | null;
  gen: number;
};

export default function AccountDetailPage() {
  const params = useParams<{ id: string }>();
  const { accessToken, ready } = useAuth();
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [showCorrectDialog, setShowCorrectDialog] = useState(false);
  const [snapshot, setSnapshot] = useState<AccountSnapshot>({
    account: null,
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken || !params.id) return;

    const gen = reloadKey;
    let cancelled = false;

    void (async () => {
      try {
        const account = await getAccount(accessToken, params.id);
        if (cancelled) return;
        setSnapshot({ account, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          account: null,
          error: err instanceof ApiError ? err.message : "Failed to load account",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, params.id, reloadKey]);

  async function archive() {
    if (!accessToken || !snapshot.account) return;
    if (
      !confirm(`Archive ${snapshot.account.name}? History stays; it hides from the default list.`)
    )
      return;
    setBusy(true);
    setActionError(null);
    try {
      const account = await archiveAccount(accessToken, snapshot.account.id);
      setSnapshot((s) => ({ ...s, account, error: null }));
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Archive failed");
    } finally {
      setBusy(false);
    }
  }

  const loading = !ready || (Boolean(accessToken) && snapshot.gen !== reloadKey);

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (snapshot.error && !snapshot.account) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-destructive">{snapshot.error}</p>
        <Link href="/app/accounts" className={cn(buttonVariants({ size: "sm" }))}>
          Back to accounts
        </Link>
      </div>
    );
  }

  const account = snapshot.account;
  if (!account) return null;

  const error = actionError ?? snapshot.error;
  const isCard = account.kind === "credit_card";
  const label = isCard ? "Outstanding" : "Balance";

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <Link
            href="/app/accounts"
            className="text-xs font-medium text-muted-foreground underline-offset-4 hover:underline"
          >
            ← Accounts
          </Link>
          <h2 className="mt-1 text-lg font-semibold tracking-tight">{account.name}</h2>
          <p className="font-mono text-sm text-muted-foreground capitalize">
            {account.kind.replace("_", " ")}
            {account.institution ? ` · ${account.institution}` : ""}
          </p>
        </div>
        {account.archived_at && (
          <Badge variant="outline" className="font-normal text-muted-foreground">
            Archived
          </Badge>
        )}
      </div>

      {error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">{error}</p>
      )}

      <div className="grid gap-3 sm:grid-cols-2">
        <Card className="shadow-sm ring-1 ring-foreground/10" size="sm">
          <CardContent className="pt-1 pb-4">
            <p className="text-xs text-muted-foreground">{label}</p>
            <p className="mt-1 font-mono text-2xl font-semibold tabular-nums">
              {formatInrFromPaise(account.balance_paise)}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="flex flex-wrap gap-2 pt-2 border-t">
        {!account.archived_at && (
          <Button size="sm" onClick={() => setShowCorrectDialog(true)}>
            Correct balance
          </Button>
        )}

        {isCard && account.credit_card_id && (
          <Link
            href={`/app/cards/${account.credit_card_id}`}
            className={cn(buttonVariants({ variant: "secondary", size: "sm" }))}
          >
            View card
          </Link>
        )}

        {!account.archived_at && (
          <Button size="sm" variant="outline" onClick={archive} disabled={busy}>
            Archive account
          </Button>
        )}
      </div>

      {showCorrectDialog && accessToken && (
        <CorrectBalanceDialog
          accessToken={accessToken}
          accountId={account.id}
          currentBalancePaise={account.balance_paise}
          kind={account.kind}
          open={showCorrectDialog}
          onOpenChange={setShowCorrectDialog}
          onCorrected={() => setReloadKey((k) => k + 1)}
        />
      )}
    </div>
  );
}
