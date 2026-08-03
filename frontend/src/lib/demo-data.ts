/**
 * Synthetic demo data for UI development.
 * Labeled in the UI — never present as real customer data.
 */

export type DemoCard = {
  id: string;
  nickname: string;
  issuer: string;
  lastFour: string;
  network: string;
  creditLimitPaise: number;
  outstandingPaise: number;
  nextDueDate: string;
  statementDay: number;
};

export type DemoContact = {
  id: string;
  name: string;
  outstandingPaise: number;
  lastActivity: string;
};

export type DemoActivity = {
  id: string;
  summary: string;
  at: string;
  kind: "spend" | "settlement" | "payment" | "card";
};

export type DemoAttentionItem = {
  id: string;
  severity: "critical" | "warning" | "info";
  title: string;
  detail: string;
  href: string;
};

/** Fixed "today" reference for stable relative dues in demo (IST-oriented). */
export const DEMO_AS_OF = new Date("2026-07-27T06:30:00+05:30");

export const demoCards: DemoCard[] = [
  {
    id: "c1",
    nickname: "HDFC Regalia",
    issuer: "HDFC Bank",
    lastFour: "4821",
    network: "Visa",
    creditLimitPaise: 500_000_00,
    outstandingPaise: 312_450_00,
    nextDueDate: "2026-08-02",
    statementDay: 15,
  },
  {
    id: "c2",
    nickname: "Axis Ace",
    issuer: "Axis Bank",
    lastFour: "9033",
    network: "Visa",
    creditLimitPaise: 250_000_00,
    outstandingPaise: 228_100_00,
    nextDueDate: "2026-07-28",
    statementDay: 5,
  },
  {
    id: "c3",
    nickname: "SBI Cashback",
    issuer: "SBI Card",
    lastFour: "1140",
    network: "RuPay",
    creditLimitPaise: 150_000_00,
    outstandingPaise: 42_800_00,
    nextDueDate: "2026-08-12",
    statementDay: 20,
  },
  {
    id: "c4",
    nickname: "Amex SmartEarn",
    issuer: "American Express",
    lastFour: "3007",
    network: "Amex",
    creditLimitPaise: 300_000_00,
    outstandingPaise: 0,
    nextDueDate: "2026-08-18",
    statementDay: 25,
  },
  {
    id: "c5",
    nickname: "ICICI Amazon",
    issuer: "ICICI Bank",
    lastFour: "7712",
    network: "Visa",
    creditLimitPaise: 200_000_00,
    outstandingPaise: 89_200_00,
    nextDueDate: "2026-07-25",
    statementDay: 10,
  },
];

export const demoContacts: DemoContact[] = [
  {
    id: "p1",
    name: "Rahul Mehta",
    outstandingPaise: 18_400_00,
    lastActivity: "2026-07-22",
  },
  {
    id: "p2",
    name: "Priya Nair",
    outstandingPaise: 7_250_00,
    lastActivity: "2026-07-20",
  },
  {
    id: "p3",
    name: "Arjun Desai",
    outstandingPaise: 3_100_00,
    lastActivity: "2026-07-18",
  },
  {
    id: "p4",
    name: "Sneha Iyer",
    outstandingPaise: 0,
    lastActivity: "2026-07-10",
  },
];

export const demoActivity: DemoActivity[] = [
  {
    id: "a1",
    summary: "₹2,450 · Swiggy · Axis Ace · Rahul Mehta",
    at: "2026-07-26T19:40:00+05:30",
    kind: "spend",
  },
  {
    id: "a2",
    summary: "Settlement ₹5,000 received · Priya Nair · UPI",
    at: "2026-07-26T11:15:00+05:30",
    kind: "settlement",
  },
  {
    id: "a3",
    summary: "Payment to issuer ₹45,000 · HDFC Regalia",
    at: "2026-07-25T09:00:00+05:30",
    kind: "payment",
  },
  {
    id: "a4",
    summary: "₹1,199 · Netflix · SBI Cashback · You",
    at: "2026-07-24T21:05:00+05:30",
    kind: "spend",
  },
  {
    id: "a5",
    summary: "Card added · Amex SmartEarn · •••• 3007",
    at: "2026-07-20T14:22:00+05:30",
    kind: "card",
  },
];

export function utilization(card: DemoCard): number {
  if (card.creditLimitPaise <= 0) return 0;
  return (card.outstandingPaise / card.creditLimitPaise) * 100;
}

export function availablePaise(card: DemoCard): number {
  return Math.max(card.creditLimitPaise - card.outstandingPaise, 0);
}

export function dashboardKpis() {
  const totalLimit = demoCards.reduce((s, c) => s + c.creditLimitPaise, 0);
  const totalOutstanding = demoCards.reduce((s, c) => s + c.outstandingPaise, 0);
  const friendDues = demoContacts.reduce((s, c) => s + c.outstandingPaise, 0);
  return {
    totalLimitPaise: totalLimit,
    totalOutstandingPaise: totalOutstanding,
    totalAvailablePaise: Math.max(totalLimit - totalOutstanding, 0),
    friendDuesPaise: friendDues,
    cardsCount: demoCards.length,
    contactsWithBalance: demoContacts.filter((c) => c.outstandingPaise > 0).length,
  };
}

export function attentionItems(asOf = DEMO_AS_OF): DemoAttentionItem[] {
  const items: DemoAttentionItem[] = [];

  for (const card of demoCards) {
    const due = new Date(card.nextDueDate);
    const days =
      Math.round(
        (Date.UTC(due.getFullYear(), due.getMonth(), due.getDate()) -
          Date.UTC(asOf.getFullYear(), asOf.getMonth(), asOf.getDate())) /
          (24 * 60 * 60 * 1000),
      );
    const util = utilization(card);

    if (days < 0) {
      items.push({
        id: `due-${card.id}`,
        severity: "critical",
        title: `${card.nickname} overdue`,
        detail: `Payment was due ${formatRelative(days)}. Outstanding ${formatMoney(card.outstandingPaise)}.`,
        href: `/app/cards/${card.id}`,
      });
    } else if (days <= 7) {
      items.push({
        id: `due-${card.id}`,
        severity: days <= 2 ? "critical" : "warning",
        title: `${card.nickname} due soon`,
        detail: `${formatRelative(days)} · ${formatMoney(card.outstandingPaise)} outstanding`,
        href: `/app/cards/${card.id}`,
      });
    }

    if (util >= 80) {
      items.push({
        id: `util-${card.id}`,
        severity: util >= 90 ? "critical" : "warning",
        title: `${card.nickname} high utilization`,
        detail: `${util.toFixed(0)}% of limit used · ${formatMoney(availablePaise(card))} available`,
        href: `/app/cards/${card.id}`,
      });
    }
  }

  const friendTotal = demoContacts.reduce((s, c) => s + c.outstandingPaise, 0);
  if (friendTotal > 0) {
    items.push({
      id: "friends",
      severity: "info",
      title: "Friend balances open",
      detail: `${formatMoney(friendTotal)} across ${demoContacts.filter((c) => c.outstandingPaise > 0).length} contacts`,
      href: "/app/contacts",
    });
  }

  return items;
}

function formatMoney(paise: number): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(paise / 100);
}

function formatRelative(days: number): string {
  if (days < 0) return `${Math.abs(days)}d ago`;
  if (days === 0) return "today";
  if (days === 1) return "tomorrow";
  return `in ${days}d`;
}
