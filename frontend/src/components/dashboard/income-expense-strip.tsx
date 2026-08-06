import { ArrowDown, ArrowUp } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { formatInrFromPaise } from "@/lib/format";

type IncomeExpenseStripProps = {
  incomePaise: number;
  expensePaise: number;
};

export function IncomeExpenseStrip({
  incomePaise,
  expensePaise,
}: IncomeExpenseStripProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardContent className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">
              Period income
            </p>
            <p className="mt-1 font-mono text-lg font-semibold tracking-tight text-foreground tabular-nums">
              {formatInrFromPaise(incomePaise)}
            </p>
          </div>
          <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-emerald-500/10 text-emerald-600">
            <ArrowDown className="size-5" aria-hidden />
          </div>
        </CardContent>
      </Card>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardContent className="flex items-center justify-between p-4">
          <div>
            <p className="text-xs font-medium text-muted-foreground">
              Period expenses
            </p>
            <p className="mt-1 font-mono text-lg font-semibold tracking-tight text-foreground tabular-nums">
              {formatInrFromPaise(expensePaise)}
            </p>
          </div>
          <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-coral-500/10 text-coral-600">
            <ArrowUp className="size-5" aria-hidden />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
