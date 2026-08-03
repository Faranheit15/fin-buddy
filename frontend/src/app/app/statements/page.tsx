"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { FileText, FileUp, Plus } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import { listCards, type CreditCard } from "@/lib/api/cards";
import { ApiError } from "@/lib/api/client";
import {
  finBuddySampleText,
  listStatements,
  STATEMENT_STATUS_LABEL,
  uploadStatement,
  type Statement,
} from "@/lib/api/statements";
import { formatDateIst } from "@/lib/format";
import { cn } from "@/lib/utils";

type Snapshot = {
  items: Statement[];
  error: string | null;
  gen: number;
};

function statusVariant(
  status: Statement["status"],
): "default" | "secondary" | "outline" | "destructive" {
  if (status === "needs_review") return "secondary";
  if (status === "failed") return "destructive";
  if (status === "imported") return "outline";
  return "outline";
}

export default function StatementsPage() {
  const { accessToken, ready } = useAuth();
  const [showUpload, setShowUpload] = useState(false);
  const [cards, setCards] = useState<CreditCard[]>([]);
  const [cardId, setCardId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [snapshot, setSnapshot] = useState<Snapshot>({
    items: [],
    error: null,
    gen: -1,
  });

  useEffect(() => {
    if (!ready || !accessToken) return;
    let cancelled = false;
    void (async () => {
      try {
        const res = await listCards(accessToken, 1, 100);
        if (cancelled) return;
        setCards(res.items);
        if (!cardId && res.items[0]) setCardId(res.items[0].id);
      } catch {
        // ignore
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, cardId]);

  useEffect(() => {
    if (!ready || !accessToken) return;
    const gen = reloadKey;
    let cancelled = false;
    void (async () => {
      try {
        const res = await listStatements(accessToken, { pageSize: 50 });
        if (cancelled) return;
        setSnapshot({ items: res.items, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          items: [],
          error: err instanceof ApiError ? err.message : "Failed to load statements",
          gen,
        });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, reloadKey]);

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!accessToken || !cardId) return;
    setUploading(true);
    setUploadError(null);
    try {
      let payload: File | Blob;
      let filename: string;
      if (file) {
        payload = file;
        filename = file.name;
      } else {
        const card = cards.find((c) => c.id === cardId);
        payload = new Blob([finBuddySampleText(card?.last_four ?? "4821")], {
          type: "text/plain",
        });
        filename = "finbuddy-sample.txt";
      }
      const detail = await uploadStatement(accessToken, {
        file: payload,
        filename,
        creditCardId: cardId,
      });
      setShowUpload(false);
      setFile(null);
      setReloadKey((k) => k + 1);
      window.location.href = `/app/statements/${detail.id}`;
    } catch (err) {
      setUploadError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Upload failed",
      );
    } finally {
      setUploading(false);
    }
  }

  if (!ready) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (!accessToken) {
    return (
      <p className="text-sm text-muted-foreground">
        Sign in (or use demo login) to manage statements.
      </p>
    );
  }

  const loading = snapshot.gen !== reloadKey;
  const statements = snapshot.items;
  const cardMap = Object.fromEntries(cards.map((c) => [c.id, c]));

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Statements</h2>
          <p className="text-sm text-muted-foreground">
            Upload PDFs or sample text, review proposed lines, then import
          </p>
        </div>
        <Button size="sm" onClick={() => setShowUpload((v) => !v)}>
          <Plus className="size-3.5" />
          {showUpload ? "Hide upload" : "Upload statement"}
        </Button>
      </div>

      {showUpload && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle className="flex items-center gap-2">
              <FileUp className="size-4" />
              Upload
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form className="space-y-3" onSubmit={(e) => void onUpload(e)}>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <Label htmlFor="stmt-card">Card</Label>
                  <select
                    id="stmt-card"
                    className="flex h-8 w-full rounded-lg border border-input bg-background px-2.5 text-sm"
                    value={cardId}
                    onChange={(e) => setCardId(e.target.value)}
                    required
                  >
                    {cards.length === 0 && <option value="">No cards — add one first</option>}
                    {cards.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.nickname} · •••• {c.last_four}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="stmt-file">PDF or .txt (optional)</Label>
                  <Input
                    id="stmt-file"
                    type="file"
                    accept=".pdf,.txt,.csv,application/pdf,text/plain"
                    onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                  />
                  <p className="text-[11px] text-muted-foreground">
                    Leave empty to upload a FinBuddy sample statement for demo review.
                  </p>
                </div>
              </div>

              {uploadError && (
                <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
                  {uploadError}
                </p>
              )}

              <div className="flex flex-wrap gap-2">
                <Button type="submit" disabled={uploading || !cardId || cards.length === 0}>
                  {uploading ? "Uploading…" : file ? "Upload & parse" : "Use sample & parse"}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  disabled={uploading}
                  onClick={() => setShowUpload(false)}
                >
                  Cancel
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {snapshot.error && (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {snapshot.error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading statements…</p>
      ) : statements.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No statements yet"
          description="Upload a bank PDF or try the built-in sample format. Parsed lines always need human review before they hit the ledger."
          action={
            !showUpload ? (
              <Button size="sm" onClick={() => setShowUpload(true)}>
                <FileUp className="size-3.5" />
                Upload statement
              </Button>
            ) : null
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Card</th>
                  <th className="px-4 py-2.5 font-medium">Status</th>
                  <th className="px-4 py-2.5 font-medium">Period / date</th>
                  <th className="px-4 py-2.5 font-medium">Lines</th>
                  <th className="px-4 py-2.5 font-medium">Uploaded</th>
                  <th className="px-4 py-2.5 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y">
                {statements.map((s) => {
                  const card = cardMap[s.credit_card_id];
                  return (
                    <tr key={s.id} className="hover:bg-muted/30">
                      <td className="px-4 py-3">
                        <p className="font-medium">{card?.nickname ?? "Card"}</p>
                        <p className="font-mono text-[11px] text-muted-foreground">
                          {card ? `•••• ${card.last_four}` : s.credit_card_id.slice(0, 8)}
                        </p>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={statusVariant(s.status)}>
                          {STATEMENT_STATUS_LABEL[s.status]}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {s.statement_date
                          ? formatDateIst(s.statement_date)
                          : s.period_start && s.period_end
                            ? `${s.period_start} → ${s.period_end}`
                            : "—"}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs tabular-nums">
                        {s.lines_count ?? 0}
                        {(s.pending_count ?? 0) > 0 && (
                          <span className="text-muted-foreground">
                            {" "}
                            · {s.pending_count} pending
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-muted-foreground">
                        {formatDateIst(s.created_at)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <Link
                          href={`/app/statements/${s.id}`}
                          className={cn(buttonVariants({ variant: "ghost", size: "sm" }), "h-7")}
                        >
                          Open
                        </Link>
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
