import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

type PagePlaceholderProps = {
  title: string;
  description: string;
};

export function PagePlaceholder({ title, description }: PagePlaceholderProps) {
  return (
    <Card className="mx-auto max-w-lg shadow-sm ring-1 ring-foreground/10">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap gap-2">
        <Link href="/app" className={cn(buttonVariants({ size: "sm" }))}>
          Back to dashboard
        </Link>
        <Link href="/" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
          Marketing home
        </Link>
      </CardContent>
    </Card>
  );
}
