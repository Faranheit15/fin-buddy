import { CreditCard, IndianRupee, Users, Wallet } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { formatInrFromPaise } from "@/lib/format";
import { cn } from "@/lib/utils";

type Kpi = {
  label: string;
  valuePaise: number;
  hint: string;
  icon: typeof Wallet;
  emphasize?: boolean;
};

type KpiRowProps = {
  totalLimitPaise: number;
  totalOutstandingPaise: number;
  totalAvailablePaise: number;
  friendDuesPaise: number;
};

export function KpiRow({
  totalLimitPaise,
  totalOutstandingPaise,
  totalAvailablePaise,
  friendDuesPaise,
}: KpiRowProps) {
  const items: Kpi[] = [
    {
      label: "Total limit",
      valuePaise: totalLimitPaise,
      hint: "Across active cards",
      icon: CreditCard,
    },
    {
      label: "Outstanding",
      valuePaise: totalOutstandingPaise,
      hint: "Owed to issuers",
      icon: IndianRupee,
    },
    {
      label: "Available",
      valuePaise: totalAvailablePaise,
      hint: "Spend room left",
      icon: Wallet,
      emphasize: true,
    },
    {
      label: "Friend dues",
      valuePaise: friendDuesPaise,
      hint: "Still owed to you",
      icon: Users,
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {items.map((item) => {
        const Icon = item.icon;
        return (
          <Card
            key={item.label}
            size="sm"
            className={cn(
              "shadow-sm ring-1 ring-foreground/10",
              item.emphasize && "bg-primary text-primary-foreground ring-primary",
            )}
          >
            <CardContent className="flex items-start justify-between gap-3 pt-1">
              <div className="min-w-0">
                <p
                  className={cn(
                    "text-xs font-medium",
                    item.emphasize ? "text-primary-foreground/80" : "text-muted-foreground",
                  )}
                >
                  {item.label}
                </p>
                <p className="mt-1 font-mono text-lg font-semibold tracking-tight tabular-nums sm:text-xl">
                  {formatInrFromPaise(item.valuePaise)}
                </p>
                <p
                  className={cn(
                    "mt-1 text-[11px]",
                    item.emphasize ? "text-primary-foreground/70" : "text-muted-foreground",
                  )}
                >
                  {item.hint}
                </p>
              </div>
              <span
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-lg",
                  item.emphasize ? "bg-primary-foreground/15" : "bg-muted",
                )}
              >
                <Icon className="size-4 opacity-80" aria-hidden />
              </span>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
