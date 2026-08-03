import { ArrowDownLeft, ArrowUpRight, CreditCard, Receipt } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DemoActivity } from "@/lib/demo-data";
import { formatDateIst } from "@/lib/format";

const icons = {
  spend: ArrowUpRight,
  settlement: ArrowDownLeft,
  payment: Receipt,
  card: CreditCard,
} as const;

type ActivityFeedProps = {
  items: DemoActivity[];
};

export function ActivityFeed({ items }: ActivityFeedProps) {
  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="border-b pb-3!">
        <CardTitle>Recent activity</CardTitle>
      </CardHeader>
      <CardContent className="divide-y p-0">
        {items.map((item) => {
          const Icon = icons[item.kind];
          return (
            <div key={item.id} className="flex items-start gap-3 px-4 py-3">
              <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Icon className="size-3.5 text-muted-foreground" aria-hidden />
              </span>
              <div className="min-w-0">
                <p className="text-sm leading-snug">{item.summary}</p>
                <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                  {formatDateIst(item.at)}
                </p>
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
