"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Plus, Users } from "lucide-react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageTableSkeleton, TableSkeleton } from "@/components/shared/page-skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/features/auth/auth-provider";
import { ContactForm } from "@/features/contacts/contact-form";
import { listContacts, type Contact } from "@/lib/api/contacts";
import { ApiError } from "@/lib/api/client";
import { formatInrFromPaise } from "@/lib/format";

type Snapshot = {
  items: Contact[];
  error: string | null;
  gen: number;
};

export default function ContactsPage() {
  const { accessToken, ready } = useAuth();
  const [showForm, setShowForm] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
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
        const res = await listContacts(accessToken, { pageSize: 100 });
        if (cancelled) return;
        setSnapshot({ items: res.items, error: null, gen });
      } catch (err) {
        if (cancelled) return;
        setSnapshot({
          items: [],
          error: err instanceof ApiError ? err.message : "Failed to load contacts",
          gen,
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [ready, accessToken, reloadKey]);

  if (!ready) {
    return <PageTableSkeleton columns={4} titleWidth="w-24" />;
  }

  if (!accessToken) {
    return (
      <p className="text-sm text-muted-foreground">
        Sign in (or use demo login) to manage contacts.
      </p>
    );
  }

  const loading = snapshot.gen !== reloadKey;
  const contacts = snapshot.items;
  const error = snapshot.error;
  const openDues = contacts.filter((c) => (c.outstanding_paise ?? 0) > 0).length;

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Contacts</h2>
          <p className="text-sm text-muted-foreground">
            Friends who use your cards — balances and settlements
            {openDues > 0 ? ` · ${openDues} with open dues` : ""}
          </p>
        </div>
        <Button size="sm" onClick={() => setShowForm((v) => !v)}>
          <Plus className="size-3.5" />
          {showForm ? "Hide form" : "Add contact"}
        </Button>
      </div>

      {showForm && (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardHeader className="border-b pb-3!">
            <CardTitle>Add contact</CardTitle>
          </CardHeader>
          <CardContent>
            <ContactForm
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
        <TableSkeleton columns={4} label="Loading contacts" />
      ) : contacts.length === 0 ? (
        <EmptyState
          icon={Users}
          title="No contacts yet"
          description="Add friends you lend cards to. Contacts are not app users — just people on your ledger for balances and settlements."
          action={
            !showForm ? (
              <Button size="sm" onClick={() => setShowForm(true)}>
                <Plus className="size-3.5" />
                Add contact
              </Button>
            ) : null
          }
        />
      ) : (
        <Card className="shadow-sm ring-1 ring-foreground/10">
          <CardContent className="overflow-x-auto p-0">
            <table className="w-full min-w-[560px] text-left text-sm">
              <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
                <tr>
                  <th className="px-4 py-2.5 font-medium">Name</th>
                  <th className="px-4 py-2.5 font-medium">Contact</th>
                  <th className="px-4 py-2.5 font-medium">Outstanding</th>
                  <th className="px-4 py-2.5 font-medium">Tags</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {[...contacts]
                  .sort((a, b) => (b.outstanding_paise ?? 0) - (a.outstanding_paise ?? 0))
                  .map((contact) => {
                    const bal = contact.outstanding_paise ?? 0;
                    return (
                      <tr key={contact.id} className="hover:bg-muted/30">
                        <td className="px-4 py-3">
                          <Link
                            href={`/app/contacts/${contact.id}`}
                            className="font-medium hover:underline"
                          >
                            {contact.name}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-xs text-muted-foreground">
                          {[contact.phone, contact.email].filter(Boolean).join(" · ") || "—"}
                        </td>
                        <td className="px-4 py-3 font-mono text-sm tabular-nums">
                          <span className={bal > 0 ? "font-medium" : "text-muted-foreground"}>
                            {formatInrFromPaise(bal)}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {(contact.tags ?? []).slice(0, 3).map((tag) => (
                              <Badge key={tag} variant="outline" className="text-[10px]">
                                {tag}
                              </Badge>
                            ))}
                            {(contact.tags ?? []).length === 0 && (
                              <span className="text-xs text-muted-foreground">—</span>
                            )}
                          </div>
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
