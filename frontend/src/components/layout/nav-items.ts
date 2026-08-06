import type { LucideIcon } from "lucide-react";
import {
  Bell,
  CreditCard,
  FileText,
  LayoutDashboard,
  Settings,
  Users,
  ArrowLeftRight,
  Wallet,
  Tags,
  Landmark,
} from "lucide-react";

export type NavItem = {
  href: string;
  label: string;
  icon: LucideIcon;
};

export const appNavItems: NavItem[] = [
  { href: "/app", label: "Dashboard", icon: LayoutDashboard },
  { href: "/app/accounts", label: "Accounts", icon: Wallet },
  { href: "/app/cards", label: "Cards", icon: CreditCard },
  { href: "/app/contacts", label: "Contacts", icon: Users },
  { href: "/app/debts", label: "Debts", icon: Landmark },
  { href: "/app/transactions", label: "Transactions", icon: ArrowLeftRight },
  { href: "/app/statements", label: "Statements", icon: FileText },
  { href: "/app/categories", label: "Categories", icon: Tags },
  { href: "/app/notifications", label: "Notifications", icon: Bell },
  { href: "/app/settings", label: "Settings", icon: Settings },
];
