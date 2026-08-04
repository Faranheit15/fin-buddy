"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { BrandMark } from "@/components/brand/mark";
import { appNavItems } from "@/components/layout/nav-items";
import { useAuth } from "@/features/auth/auth-provider";
import { cn } from "@/lib/utils";

type AppSidebarProps = {
  className?: string;
  onNavigate?: () => void;
};

export function AppSidebar({ className, onNavigate }: AppSidebarProps) {
  const pathname = usePathname();
  const { organizations, profile, ready, accessToken } = useAuth();
  const workspace = organizations[0]?.name ?? "Personal workspace";

  return (
    <aside
      className={cn(
        "flex h-full w-72 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground",
        className,
      )}
    >
      <div className="flex h-14 shrink-0 items-center gap-2 border-b border-sidebar-border px-4">
        <BrandMark />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold tracking-tight">Fin Buddy</p>
          <p className="truncate font-mono text-[11px] text-muted-foreground">Ledger shelf</p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-0.5 overflow-y-auto p-2" aria-label="Main">
        {appNavItems.map((item) => {
          const active =
            item.href === "/app"
              ? pathname === "/app"
              : pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground"
                  : "text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              )}
            >
              <Icon className="size-4 shrink-0 opacity-80" aria-hidden />
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto shrink-0 border-t border-sidebar-border p-3">
        <p className="truncate text-[11px] leading-snug text-muted-foreground">
          {workspace}
          {!ready ? (
            <span className="mt-1 block font-mono text-[10px] tracking-wide">
              Checking session…
            </span>
          ) : profile ? (
            <span className="mt-1 block truncate font-mono text-[10px] tracking-wide">
              {profile.email}
            </span>
          ) : accessToken ? (
            <span className="mt-1 block font-mono text-[10px] tracking-wide">
              Loading profile…
            </span>
          ) : (
            <span className="mt-1 block font-mono text-[10px] tracking-wide">
              Sign in to sync your workspace
            </span>
          )}
        </p>
      </div>
    </aside>
  );
}
