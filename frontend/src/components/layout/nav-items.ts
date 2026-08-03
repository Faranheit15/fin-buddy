import type { LucideIcon } from "lucide-react";
import {
  CreditCard,
  FileText,
  LayoutDashboard,
  Settings,
  Users,
  ArrowLeftRight,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

export const appNavItems: NavItem[] = [
  { href: "/app", label: "Dashboard", icon: LayoutDashboard },
  { href: "/app/cards", label: "Cards", icon: CreditCard },
  { href: "/app/contacts", label: "Contacts", icon: Users },
  { href: "/app/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/app/statements", label: "Statements", icon: FileText },
  { href: "/app/settings", label: "Settings", icon: Settings },
];
