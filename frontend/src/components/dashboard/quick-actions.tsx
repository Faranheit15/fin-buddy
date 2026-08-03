import Link from "next/link";
import { CreditCard, FileUp, IndianRupee, UserPlus } from "lucide-react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const actions = [
  {
    href: "/app/transactions",
    label: "Log spend",
    description: "Attribute a purchase",
    icon: IndianRupee,
  },
  {
    href: "/app/contacts",
    label: "Record settlement",
    description: "Friend paid you back",
    icon: UserPlus,
  },
  {
    href: "/app/statements",
    label: "Upload statement",
    description: "PDF review import",
    icon: FileUp,
  },
  {
    href: "/app/cards",
    label: "Add card",
    description: "Limit & cycle setup",
    icon: CreditCard,
  },
] as const;

export function QuickActions() {
  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="border-b pb-3!">
        <CardTitle>Quick actions</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 p-3 sm:grid-cols-2">
        {actions.map((action) => {
          const Icon = action.icon;
          return (
            <Link
              key={action.href + action.label}
              href={action.href}
              className={cn(
                "flex items-start gap-3 rounded-lg border border-transparent p-2.5 transition-colors",
                "hover:border-border hover:bg-muted/50",
              )}
            >
              <span className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                <Icon className="size-4" aria-hidden />
              </span>
              <span>
                <span className="block text-sm font-medium">{action.label}</span>
                <span className="block text-xs text-muted-foreground">{action.description}</span>
              </span>
            </Link>
          );
        })}
      </CardContent>
    </Card>
  );
}
