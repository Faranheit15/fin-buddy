import Link from "next/link";
import { CalendarDays, CreditCard } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { type UpcomingItem } from "@/lib/api/dashboard";
import { formatDateIst, formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";
import { buttonVariants } from "@/components/ui/button";

type UpcomingListProps = {
  items: UpcomingItem[];
};

export function UpcomingList({ items }: UpcomingListProps) {
  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="border-b pb-3">
        <CardTitle className="flex items-center gap-2">
          <CalendarDays className="size-4 opacity-80" />
          Upcoming
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {items.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 p-8 text-center">
            <p className="text-sm font-medium">All caught up</p>
            <p className="text-xs text-muted-foreground">No upcoming dues right now.</p>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex flex-wrap items-start justify-between gap-4 p-4 hover:bg-muted/30"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <CreditCard className="size-4 opacity-70" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">{item.title}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      Due {formatDateIst(item.due_date)}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <p className="font-mono text-sm font-medium tabular-nums text-foreground">
                    {formatInrFromPaise(item.amount_paise)}
                  </p>
                  {item.href && (
                    <Link
                      href={item.href}
                      className={cn(
                        buttonVariants({ variant: "outline", size: "sm" }),
                        "h-7 px-3 text-[11px]",
                      )}
                    >
                      View
                    </Link>
                  )}
                </div>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
