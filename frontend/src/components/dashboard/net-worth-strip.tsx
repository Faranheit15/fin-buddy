import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { formatInrFromPaise } from "@/lib/format";

type NetWorthStripProps = {
  netWorthPaise: number;
  assetsPaise: number;
  liabilitiesPaise: number;
};

export function NetWorthStrip({
  netWorthPaise,
  assetsPaise,
  liabilitiesPaise,
}: NetWorthStripProps) {
  return (
    <Card className="shadow-sm ring-1 ring-foreground/10 overflow-hidden">
      <div className="grid divide-y sm:grid-cols-3 sm:divide-x sm:divide-y-0">
        <CardContent className="flex flex-col gap-1 p-5 bg-muted/20">
          <p className="text-sm font-medium text-muted-foreground">Net Worth</p>
          <p className="font-mono text-3xl font-semibold tracking-tight text-foreground tabular-nums">
            {formatInrFromPaise(netWorthPaise)}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            Assets minus liabilities
          </p>
        </CardContent>
        <CardContent className="flex flex-col gap-1 p-5">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <ArrowUpRight className="size-4 text-emerald-600" />
            Assets
          </div>
          <p className="font-mono text-xl font-medium tracking-tight text-foreground tabular-nums">
            {formatInrFromPaise(assetsPaise)}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            Bank, cash, receivables
          </p>
        </CardContent>
        <CardContent className="flex flex-col gap-1 p-5">
          <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
            <ArrowDownRight className="size-4 text-coral-600" />
            Liabilities
          </div>
          <p className="font-mono text-xl font-medium tracking-tight text-foreground tabular-nums">
            {formatInrFromPaise(liabilitiesPaise)}
          </p>
          <p className="text-[11px] text-muted-foreground mt-1">
            Cards, payables
          </p>
        </CardContent>
      </div>
    </Card>
  );
}
