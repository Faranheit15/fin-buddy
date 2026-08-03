import Link from "next/link";
import { AlertTriangle, Info, Siren } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DemoAttentionItem } from "@/lib/demo-data";
import { cn } from "@/lib/utils";

const severityStyles: Record<
  DemoAttentionItem["severity"],
  { icon: typeof Siren; badge: "destructive" | "outline" | "secondary"; bar: string }
> = {
  critical: {
    icon: Siren,
    badge: "destructive",
    bar: "border-l-destructive",
  },
  warning: {
    icon: AlertTriangle,
    badge: "outline",
    bar: "border-l-amber-500",
  },
  info: {
    icon: Info,
    badge: "secondary",
    bar: "border-l-muted-foreground/40",
  },
};

type AttentionStripProps = {
  items: DemoAttentionItem[];
};

export function AttentionStrip({ items }: AttentionStripProps) {
  if (items.length === 0) {
    return (
      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardContent className="py-4 text-sm text-muted-foreground">
          Nothing needs attention in the next 7 days. All cards look clear.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="border-b pb-3!">
        <div className="flex items-center justify-between gap-2">
          <CardTitle>Needs attention</CardTitle>
          <Badge variant="outline" className="font-mono text-[10px] tracking-wide uppercase">
            {items.length} items
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="divide-y p-0">
        {items.map((item) => {
          const meta = severityStyles[item.severity];
          const Icon = meta.icon;
          return (
            <Link
              key={item.id}
              href={item.href}
              className={cn(
                "flex items-start gap-3 border-l-2 px-4 py-3 transition-colors hover:bg-muted/50",
                meta.bar,
              )}
            >
              <Icon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-medium">{item.title}</p>
                  <Badge variant={meta.badge} className="capitalize">
                    {item.severity}
                  </Badge>
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground sm:text-sm">{item.detail}</p>
              </div>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}
