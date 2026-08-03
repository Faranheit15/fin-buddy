import { Badge } from "@/components/ui/badge";

export function DemoBanner() {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2 rounded-xl border border-dashed bg-muted/40 px-3 py-2 text-xs text-muted-foreground shadow-sm">
      <Badge variant="outline" className="font-mono text-[10px] tracking-wide uppercase">
        Synthetic
      </Badge>
      <span>
        Demo data for UI development — not real balances. Wire Supabase + API to replace this.
      </span>
    </div>
  );
}
