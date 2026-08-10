import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type EmptyStateProps = {
  icon?: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
  /** compact = less padding for inline panels */
  size?: "default" | "compact";
};

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
  size = "default",
}: EmptyStateProps) {
  return (
    <Card className={cn("shadow-sm ring-1 ring-foreground/10", className)}>
      <CardContent
        className={cn(
          "flex flex-col items-center text-center",
          size === "compact" ? "gap-2 py-8" : "gap-3 py-12",
        )}
      >
        {Icon ? (
          <div className="flex size-11 items-center justify-center rounded-xl bg-muted text-muted-foreground">
            <Icon className="size-5" aria-hidden />
          </div>
        ) : null}
        <div className="max-w-sm space-y-1">
          <p className="font-medium tracking-tight">{title}</p>
          <p className="text-sm text-muted-foreground">{description}</p>
        </div>
        {action ? (
          <div className="mt-1 flex flex-wrap items-center justify-center gap-2">{action}</div>
        ) : null}
      </CardContent>
    </Card>
  );
}
