"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, useSyncExternalStore } from "react";
import { Bell, LogOut, Menu, Moon, Plus, Sun, User } from "lucide-react";

import { BrandMark } from "@/components/brand/mark";
import { AppSidebar } from "@/components/layout/app-sidebar";
import { appNavItems } from "@/components/layout/nav-items";
import { buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { useAuth } from "@/features/auth/auth-provider";
import { getUnreadNotificationCount } from "@/lib/api/notifications";
import { cn } from "@/lib/utils";

function titleFromPath(pathname: string): string {
  const match = appNavItems.find((item) =>
    item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href),
  );
  if (match) return match.label;
  if (pathname.startsWith("/app/cards/")) return "Card detail";
  if (pathname.startsWith("/app/contacts/")) return "Contact detail";
  if (pathname.startsWith("/app/notifications")) return "Notifications";
  if (pathname.startsWith("/app/statements/")) return "Statement review";
  return "Fin Buddy";
}

function initials(name: string | null | undefined, email: string | null | undefined): string {
  if (name?.trim()) {
    return name
      .split(/\s+/)
      .slice(0, 2)
      .map((p) => p[0]?.toUpperCase() ?? "")
      .join("");
  }
  if (email) return email.slice(0, 2).toUpperCase();
  return "You";
}

type Theme = "light" | "dark";

function currentTheme(): Theme {
  if (typeof window === "undefined") return "light";
  const stored = window.localStorage.getItem("fb-theme");
  if (stored === "dark" || stored === "light") return stored;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function subscribeTheme(onStoreChange: () => void) {
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  window.addEventListener("storage", onStoreChange);
  window.addEventListener("fb-theme-change", onStoreChange);
  media.addEventListener("change", onStoreChange);
  return () => {
    window.removeEventListener("storage", onStoreChange);
    window.removeEventListener("fb-theme-change", onStoreChange);
    media.removeEventListener("change", onStoreChange);
  };
}

export function AppHeader() {
  const pathname = usePathname();
  const router = useRouter();
  const title = titleFromPath(pathname);
  const [open, setOpen] = useState(false);
  const theme = useSyncExternalStore(subscribeTheme, currentTheme, () => "light");
  const [unreadSnap, setUnreadSnap] = useState<{ token: string | null; count: number }>({
    token: null,
    count: 0,
  });
  const { profile, signOut, ready, accessToken } = useAuth();

  function toggleTheme() {
    const nextTheme = theme === "dark" ? "light" : "dark";
    window.localStorage.setItem("fb-theme", nextTheme);
    document.documentElement.classList.toggle("dark", nextTheme === "dark");
    window.dispatchEvent(new Event("fb-theme-change"));
  }

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  const label = profile?.display_name || profile?.email || "Account";
  const unread = ready && accessToken && unreadSnap.token === accessToken ? unreadSnap.count : 0;

  useEffect(() => {
    if (!accessToken) return;

    const token = accessToken;
    let cancelled = false;
    void (async () => {
      try {
        const res = await getUnreadNotificationCount(token, { sync: false });
        if (cancelled) return;
        setUnreadSnap({ token, count: res.unread });
      } catch {
        if (cancelled) return;
        setUnreadSnap({ token, count: 0 });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [accessToken]);

  async function handleSignOut() {
    await signOut();
    router.replace("/login");
    router.refresh();
  }

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-background/95 px-4 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <Sheet open={open} onOpenChange={setOpen}>
        <SheetTrigger
          className={cn(
            buttonVariants({ variant: "ghost", size: "icon" }),
            "md:hidden min-h-11 min-w-11",
          )}
          aria-label="Open menu"
        >
          <Menu className="size-4" />
        </SheetTrigger>
        <SheetContent side="left" className="flex h-full w-60 flex-col p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <AppSidebar onNavigate={() => setOpen(false)} className="h-full w-full border-0" />
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 items-center gap-2">
        <BrandMark className="md:hidden" />
        <div className="min-w-0">
          <h1 className="truncate text-base font-semibold tracking-tight">{title}</h1>
          <p className="hidden text-xs text-muted-foreground sm:block">
            Scan dues, utilization, and friend balances
          </p>
        </div>
      </div>

      <DropdownMenu>
        <DropdownMenuTrigger
          className={cn(
            buttonVariants({ variant: "outline", size: "sm" }),
            "hidden sm:inline-flex",
          )}
        >
          <Plus className="size-3.5" />
          Quick add
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-48">
          <DropdownMenuGroup>
            <DropdownMenuLabel>Create</DropdownMenuLabel>
            <DropdownMenuItem onClick={() => router.push("/app/transactions")}>
              Log spend
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/app/contacts")}>
              Record settlement
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/app/statements")}>
              Upload statement
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => router.push("/app/cards")}>Add card</DropdownMenuItem>
          </DropdownMenuGroup>
        </DropdownMenuContent>
      </DropdownMenu>

      <Link
        href="/app/transactions"
        className={cn(buttonVariants({ variant: "default", size: "icon" }), "size-11 sm:hidden")}
        aria-label="Log a spend"
      >
        <Plus className="size-4" />
      </Link>

      <Link
        href="/app/notifications"
        className={cn(
          buttonVariants({ variant: "ghost", size: "icon" }),
          "relative min-h-11 min-w-11",
        )}
        aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
      >
        <Bell className="size-4" />
        {unread > 0 ? (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        ) : null}
      </Link>

      <DropdownMenu>
        <DropdownMenuTrigger
          className="flex size-11 items-center justify-center rounded-lg bg-muted text-[11px] font-semibold"
          aria-label="Account menu"
        >
          {ready ? initials(profile?.display_name, profile?.email) : "…"}
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-52">
          <DropdownMenuGroup>
            <DropdownMenuLabel className="space-y-0.5 font-normal">
              <span className="block text-sm font-medium">{label}</span>
              {profile?.email ? (
                <span className="block truncate text-xs text-muted-foreground">
                  {profile.email}
                </span>
              ) : null}
              {profile?.platform_role && profile.platform_role !== "user" ? (
                <span className="mt-1 inline-block font-mono text-[10px] uppercase tracking-wide text-muted-foreground">
                  {profile.platform_role}
                </span>
              ) : null}
            </DropdownMenuLabel>
          </DropdownMenuGroup>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => router.push("/app/settings")}>
            <User className="size-3.5" />
            Settings
          </DropdownMenuItem>
          <DropdownMenuItem onClick={toggleTheme}>
            {theme === "dark" ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
            Use {theme === "dark" ? "light" : "dark"} theme
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => void handleSignOut()}>
            <LogOut className="size-3.5" />
            Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
