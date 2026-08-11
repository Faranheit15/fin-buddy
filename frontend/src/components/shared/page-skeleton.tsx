import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type PageSkeletonProps = {
  className?: string;
  columns?: number;
  rows?: number;
  titleWidth?: string;
  showAction?: boolean;
};

function LoadingAnnouncement({ label }: { label: string }) {
  return (
    <span className="sr-only" role="status">
      {label}
    </span>
  );
}

export function PageHeaderSkeleton({
  titleWidth = "w-28",
  showAction = true,
}: Pick<PageSkeletonProps, "titleWidth" | "showAction">) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3" aria-hidden="true">
      <div className="space-y-2">
        <Skeleton className={cn("h-5", titleWidth)} />
        <Skeleton className="h-4 w-64 max-w-[70vw]" />
      </div>
      {showAction ? <Skeleton className="h-8 w-24 rounded-lg" /> : null}
    </div>
  );
}

export function TableSkeleton({
  columns = 4,
  rows = 5,
  className,
  label = "Loading table",
}: PageSkeletonProps & { label?: string }) {
  return (
    <Card className={cn("overflow-hidden shadow-sm ring-1 ring-foreground/10", className)}>
      <LoadingAnnouncement label={label} />
      <CardContent className="overflow-x-auto p-0" aria-busy="true">
        <div className="min-w-[420px] divide-y">
          <div
            className="grid gap-4 bg-muted/40 px-4 py-3"
            style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
            aria-hidden="true"
          >
            {Array.from({ length: columns }).map((_, index) => (
              <Skeleton key={index} className="h-3 w-3/5" />
            ))}
          </div>
          {Array.from({ length: rows }).map((_, row) => (
            <div
              key={row}
              className="grid items-center gap-4 px-4 py-3.5"
              style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}
              aria-hidden="true"
            >
              {Array.from({ length: columns }).map((_, column) => (
                <Skeleton
                  key={column}
                  className={cn(
                    "h-4",
                    column === 0 ? "w-4/5" : column === columns - 1 ? "ml-auto w-3/5" : "w-2/3",
                  )}
                />
              ))}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function ListSkeleton({
  rows = 5,
  label = "Loading list",
}: Pick<PageSkeletonProps, "rows"> & { label?: string }) {
  return (
    <Card className="overflow-hidden shadow-sm ring-1 ring-foreground/10">
      <LoadingAnnouncement label={label} />
      <CardContent className="divide-y p-0" aria-busy="true">
        {Array.from({ length: rows }).map((_, index) => (
          <div key={index} className="flex gap-3 px-4 py-4" aria-hidden="true">
            <Skeleton className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" />
            <div className="min-w-0 flex-1 space-y-2">
              <Skeleton className="h-4 w-2/5" />
              <Skeleton className="h-3.5 w-full max-w-xl" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function PageTableSkeleton({
  className,
  columns = 4,
  rows = 5,
  titleWidth,
  showAction,
}: PageSkeletonProps) {
  return (
    <div className={cn("mx-auto flex w-full max-w-5xl flex-col gap-4", className)}>
      <LoadingAnnouncement label="Loading page" />
      <PageHeaderSkeleton titleWidth={titleWidth} showAction={showAction} />
      <TableSkeleton columns={columns} rows={rows} />
    </div>
  );
}

export function DetailPageSkeleton({ className }: Pick<PageSkeletonProps, "className">) {
  return (
    <div className={cn("mx-auto flex w-full max-w-3xl flex-col gap-4", className)}>
      <LoadingAnnouncement label="Loading details" />
      <div className="space-y-2" aria-hidden="true">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-6 w-44" />
        <Skeleton className="h-4 w-52" />
      </div>
      <div className="grid gap-3 sm:grid-cols-3" aria-hidden="true">
        {Array.from({ length: 3 }).map((_, index) => (
          <Card key={index} className="shadow-sm ring-1 ring-foreground/10" size="sm">
            <CardContent className="space-y-2 py-4">
              <Skeleton className="h-3 w-2/5" />
              <Skeleton className="h-6 w-4/5" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="shadow-sm ring-1 ring-foreground/10" aria-hidden="true">
        <CardContent className="space-y-4 p-5">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-3.5 w-full" />
          <Skeleton className="h-3.5 w-4/5" />
          <Skeleton className="h-2 w-full rounded-full" />
        </CardContent>
      </Card>
      <TableSkeleton columns={3} rows={3} label="Loading related records" />
    </div>
  );
}

export function SettingsPageSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      <LoadingAnnouncement label="Loading settings" />
      <PageHeaderSkeleton titleWidth="w-20" showAction={false} />
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index} className="shadow-sm ring-1 ring-foreground/10" aria-hidden="true">
          <CardContent className="space-y-4 p-5">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-3.5 w-full max-w-lg" />
            <div className="grid gap-3 sm:grid-cols-2">
              <Skeleton className="h-9 w-full" />
              <Skeleton className="h-9 w-full" />
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function AuthFormSkeleton() {
  return (
    <div className="space-y-5" aria-busy="true">
      <LoadingAnnouncement label="Loading sign-in form" />
      <div className="space-y-2" aria-hidden="true">
        <Skeleton className="h-3 w-16" />
        <Skeleton className="h-10 w-full" />
      </div>
      <div className="space-y-2" aria-hidden="true">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-10 w-full" />
      </div>
      <Skeleton className="h-10 w-full" aria-hidden="true" />
    </div>
  );
}
