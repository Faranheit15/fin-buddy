import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DemoContact } from "@/lib/demo-data";
import { formatDateShortIst, formatInrFromPaise } from "@/lib/format";

type ContactsListProps = {
  contacts: DemoContact[];
};

export function ContactsList({ contacts }: ContactsListProps) {
  const ranked = [...contacts]
    .filter((c) => c.outstandingPaise > 0)
    .sort((a, b) => b.outstandingPaise - a.outstandingPaise);

  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="flex flex-row items-center justify-between border-b pb-3!">
        <CardTitle>Top contacts by dues</CardTitle>
        <Link
          href="/app/contacts"
          className="text-xs font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent className="divide-y p-0">
        {ranked.length === 0 ? (
          <p className="px-4 py-6 text-sm text-muted-foreground">No open friend balances.</p>
        ) : (
          ranked.map((contact) => (
            <Link
              key={contact.id}
              href={`/app/contacts/${contact.id}`}
              className="flex items-center justify-between gap-3 px-4 py-3 transition-colors hover:bg-muted/40"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{contact.name}</p>
                <p className="text-[11px] text-muted-foreground">
                  Last activity {formatDateShortIst(contact.lastActivity)}
                </p>
              </div>
              <p className="shrink-0 font-mono text-sm font-medium tabular-nums">
                {formatInrFromPaise(contact.outstandingPaise)}
              </p>
            </Link>
          ))
        )}
      </CardContent>
    </Card>
  );
}
