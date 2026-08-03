import { cn } from "@/lib/utils";

type BrandMarkProps = {
  className?: string;
  size?: "sm" | "md";
};

export function BrandMark({ className, size = "sm" }: BrandMarkProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center justify-center rounded-lg bg-primary font-semibold text-primary-foreground",
        size === "sm" ? "size-8 text-sm" : "size-10 text-sm",
        className,
      )}
      aria-hidden
    >
      FB
    </span>
  );
}
