import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { availablePaise, DEMO_AS_OF, type DemoCard, utilization } from "@/lib/demo-data";
import {
  formatDateShortIst,
  formatInrFromPaise,
  formatPercent,
  formatRelativeDue,
} from "@/lib/format";
import { cn } from "@/lib/utils";

type CardsTableProps = {
  cards: DemoCard[];
};

export function CardsTable({ cards }: CardsTableProps) {
  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="flex flex-row items-center justify-between border-b pb-3!">
        <CardTitle>Cards & utilization</CardTitle>
        <Link
          href="/app/cards"
          className="text-xs font-medium text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <CardContent className="overflow-x-auto p-0">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead className="border-b bg-muted/40 text-xs text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5 font-medium">Card</th>
              <th className="px-4 py-2.5 font-medium">Utilization</th>
              <th className="px-4 py-2.5 font-medium">Outstanding</th>
              <th className="px-4 py-2.5 font-medium">Available</th>
              <th className="px-4 py-2.5 font-medium">Next due</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {cards.map((card) => {
              const util = utilization(card);
              const dueLabel = formatRelativeDue(card.nextDueDate, DEMO_AS_OF);
              const critical = util >= 90;
              const warn = util >= 80 || dueLabel.includes("overdue") || dueLabel.includes("today");
              return (
                <tr key={card.id} className="hover:bg-muted/30">
                  <td className="px-4 py-3">
                    <Link href={`/app/cards/${card.id}`} className="group block min-w-0">
                      <p className="font-medium group-hover:underline">{card.nickname}</p>
                      <p className="font-mono text-xs text-muted-foreground">
                        {card.issuer} · •••• {card.lastFour}
                      </p>
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex min-w-28 flex-col gap-1">
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={cn(
                            "font-mono text-xs tabular-nums",
                            critical && "text-destructive",
                            warn && !critical && "text-amber-700 dark:text-amber-400",
                          )}
                        >
                          {formatPercent(util)}
                        </span>
                      </div>
                      <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all",
                            critical ? "bg-destructive" : warn ? "bg-amber-500" : "bg-primary",
                          )}
                          style={{ width: `${Math.min(util, 100)}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs tabular-nums sm:text-sm">
                    {formatInrFromPaise(card.outstandingPaise)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs tabular-nums sm:text-sm">
                    {formatInrFromPaise(availablePaise(card))}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-col gap-1">
                      <Badge
                        variant={
                          dueLabel.includes("overdue") || dueLabel.includes("today")
                            ? "destructive"
                            : dueLabel.includes("tomorrow") ||
                                dueLabel.includes("in 1") ||
                                dueLabel.includes("in 2")
                              ? "outline"
                              : "secondary"
                        }
                        className="w-fit"
                      >
                        {dueLabel}
                      </Badge>
                      <span className="font-mono text-[11px] text-muted-foreground">
                        {formatDateShortIst(card.nextDueDate)}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </CardContent>
    </Card>
  );
}
