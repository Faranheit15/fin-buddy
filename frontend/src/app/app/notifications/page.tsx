"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Bell, CheckCheck } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { Badge } from "@/components/ui/badge";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { ApiError } from "@/lib/api/client";
import {
  listNotifications,
  markAllNotificationsRead,
  markNotificationRead,
  type Notification,
} from "@/lib/api/notifications";
import { formatDateIst } from "@/lib/format";
import { cn } from "@/lib/utils";

type Snapshot = {
  items: Notification[];
  error: string | null;
  gen: number;
};

function typeLabel(type: string): string {
  switch (type) {
    case "overdue":
      return "Overdue";
    case "due_soon":
      return "Due soon";
    case "high_utilization":
      return "Utilization";
    case "statement_ready":
    case "statement_review":
      return "Statement";
    case "friend_dues":
      return "Friends";
    default:
      return type.replace(/_/g, " ");
  }
}

export default function NotificationsPage() {
  const { accessToken, ready } = useAuth();
  const [reloadKey, setReloadKey] = useState(0);
  const [busy, setBusy] = useState(false);
  const [snapshot, setSnapshot] = useState<Snapshot>({
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
        const res = await listNotifications(accessToken, { pageSize: 50, sync: true });
        if (cancelled) return;
        setSnapshot({ items: res.items, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          items: [],
          error: err instanceof ApiError ? err.message : "Failed to load notifications",
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
        Sign in to view in-app notifications.
      </p>
    );
  }

  const loading = snapshot.gen !== reloadKey;
  const items = snapshot.items;
  const unread = items.filter((n) => !n.read_at).length;

  async function handleMarkAll() {
    if (!accessToken || unread === 0) return;
    setBusy(true);
    try {
      await markAllNotificationsRead(accessToken);
      setReloadKey((k) => k + 1);
    } catch {
      // keep list
    } finally {
      setBusy(false);
    }
  }

  async function handleOpen(n: Notification) {
    if (!accessToken) return;
    if (!n.read_at) {
      try {
        await markNotificationRead(accessToken, n.id);
      } catch {
        // navigation still ok
      }
    }
    setReloadKey((k) => k + 1);
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Notifications</h2>
          <p className="text-sm text-muted-foreground">
            Due dates, utilization, and statement import alerts
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unread > 0 ? (
            <Badge variant="secondary" className="font-mono text-[10px]">
              {unread} unread
            </Badge>
          ) : null}
          <Button
            size="sm"
            variant="outline"
            disabled={busy || unread === 0}
            onClick={() => void handleMarkAll()}
          >
            <CheckCheck className="size-3.5" />
            Mark all read
          </Button>
        </div>
      </div>

      {snapshot.error ? (
        <p className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
          {snapshot.error}
        </p>
      ) : null}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading notifications…</p>
      ) : items.length === 0 ? (
        <EmptyState
          icon={Bell}
          title="All quiet"
          description="No notifications yet. Due-soon, high utilization, and statement-ready alerts will appear here."
          action={
            <Link href="/app/settings" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
              Adjust thresholds
            </Link>
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="divide-y p-0">
            {items.map((n) => {
              const unreadRow = !n.read_at;
              const inner = (
                <div
                  className={cn(
                    "flex gap-3 px-4 py-3 transition-colors",
                    unreadRow ? "bg-primary/5" : "hover:bg-muted/40",
                  )}
                >
                  <span
                    className={cn(
                      "mt-1.5 size-2 shrink-0 rounded-full",
                      unreadRow ? "bg-primary" : "bg-transparent",
                    )}
                    aria-hidden
                  />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <p className={cn("text-sm", unreadRow ? "font-semibold" : "font-medium")}>
                        {n.title}
                      </p>
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">
                        {typeLabel(n.type)}
                      </Badge>
                    </div>
                    <p className="mt-0.5 text-sm text-muted-foreground">{n.body}</p>
                    <p className="mt-1 font-mono text-[11px] text-muted-foreground">
                      {formatDateIst(n.created_at)}
                    </p>
                  </div>
                </div>
              );

              if (n.href) {
                return (
                  <Link
                    key={n.id}
                    href={n.href}
                    onClick={() => void handleOpen(n)}
                    className="block"
                  >
                    {inner}
                  </Link>
                );
              }

              return (
                <button
                  key={n.id}
                  type="button"
                  className="block w-full text-left"
                  onClick={() => void handleOpen(n)}
                >
                  {inner}
                </button>
              );
            })}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
