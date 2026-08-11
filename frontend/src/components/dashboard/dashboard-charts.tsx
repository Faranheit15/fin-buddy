"use client";

import { useMemo } from "react";

import AreaChart, { Area } from "@/components/charts/area-chart";
import Bar from "@/components/charts/bar";
import BarChart from "@/components/charts/bar-chart";
import BarXAxis from "@/components/charts/bar-x-axis";
import Grid from "@/components/charts/grid";
import PieCenter from "@/components/charts/pie-center";
import PieChart from "@/components/charts/pie-chart";
import PieSlice from "@/components/charts/pie-slice";
import XAxis from "@/components/charts/x-axis";
import ChartTooltip from "@/components/charts/tooltip/chart-tooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardCashFlowMonth, DashboardSpendCategory } from "@/lib/api/dashboard";
import type { DemoCard } from "@/lib/demo-data";

const money = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

const compactMoney = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  notation: "compact",
  maximumFractionDigits: 1,
});

const categoryColors = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

type DashboardChartsProps = {
  cashFlow: DashboardCashFlowMonth[];
  spendingCategories: DashboardSpendCategory[];
  cards: DemoCard[];
};

function toRupees(paise: number) {
  return paise / 100;
}

export function DashboardCharts({ cashFlow, spendingCategories, cards }: DashboardChartsProps) {
  const flowData = useMemo(
    () =>
      cashFlow.map((point) => ({
        date: new Date(`${point.month}T00:00:00`),
        income: toRupees(point.income_paise),
        expense: toRupees(point.expense_paise),
      })),
    [cashFlow],
  );
  const utilizationData = useMemo(
    () =>
      cards
        .filter((card) => card.creditLimitPaise > 0)
        .sort(
          (a, b) =>
            b.outstandingPaise / b.creditLimitPaise - a.outstandingPaise / a.creditLimitPaise,
        )
        .slice(0, 5)
        .map((card) => ({
          card: card.nickname.length > 12 ? `${card.nickname.slice(0, 12)}…` : card.nickname,
          utilization: Math.round((card.outstandingPaise / card.creditLimitPaise) * 100),
        })),
    [cards],
  );
  const categoryData = useMemo(
    () =>
      spendingCategories.map((category, index) => ({
        label: category.name,
        value: toRupees(category.amount_paise),
        color: categoryColors[index % categoryColors.length],
      })),
    [spendingCategories],
  );
  const totalSpend = categoryData.reduce((sum, category) => sum + category.value, 0);

  return (
    <section className="space-y-4" aria-labelledby="dashboard-insights-title">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <div>
          <p className="text-xs font-medium text-muted-foreground">Patterns, not just totals</p>
          <h2 id="dashboard-insights-title" className="text-lg font-semibold tracking-tight">
            Money in focus
          </h2>
        </div>
        <p className="text-xs text-muted-foreground">
          All amounts in INR · current and previous five months
        </p>
      </div>

      <div className="grid gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex-row items-start justify-between gap-4 space-y-0 pb-2">
            <div>
              <CardTitle className="text-base">Cash flow</CardTitle>
              <p className="mt-1 text-sm text-muted-foreground">
                Income and spending by month. Hover to inspect a period.
              </p>
            </div>
            <div className="flex gap-3 pt-1 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <i className="size-2 rounded-full bg-[var(--chart-line-primary)]" /> Income
              </span>
              <span className="flex items-center gap-1.5">
                <i className="size-2 rounded-full bg-[var(--chart-line-secondary)]" /> Spending
              </span>
            </div>
          </CardHeader>
          <CardContent>
            {flowData.some((point) => point.income > 0 || point.expense > 0) ? (
              <figure>
                <AreaChart
                  data={flowData}
                  className="[--chart-line-primary:var(--chart-1)] [--chart-line-secondary:var(--chart-3)]"
                  margin={{ top: 18, right: 20, bottom: 26, left: 20 }}
                >
                  <Grid horizontal numTicksRows={4} />
                  <Area dataKey="income" fill="var(--chart-line-primary)" fillOpacity={0.24} />
                  <Area dataKey="expense" fill="var(--chart-line-secondary)" fillOpacity={0.18} />
                  <XAxis numTicks={6} />
                  <ChartTooltip />
                </AreaChart>
                <figcaption className="sr-only">
                  Six-month cash-flow trend. Income and spending are displayed in Indian rupees.
                </figcaption>
              </figure>
            ) : (
              <EmptyChart copy="Log categorized income or spending to see your cash-flow trend." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Spending mix</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">This month’s categorized spend.</p>
          </CardHeader>
          <CardContent>
            {categoryData.length > 0 ? (
              <div className="flex items-center gap-4 xl:block">
                <figure className="min-w-0 flex-1">
                  <PieChart data={categoryData} innerRadius={54} padAngle={0.035} size={190}>
                    {categoryData.map((category, index) => (
                      <PieSlice key={category.label} color={category.color} index={index} />
                    ))}
                    <PieCenter defaultLabel="Spent" prefix="₹" />
                  </PieChart>
                  <figcaption className="sr-only">
                    Current-month spending by category, totaling {money.format(totalSpend)}.
                  </figcaption>
                </figure>
                <ul className="min-w-0 flex-1 space-y-2" aria-label="Spending category totals">
                  {categoryData.map((category) => (
                    <li
                      key={category.label}
                      className="flex items-center justify-between gap-2 text-sm"
                    >
                      <span className="flex min-w-0 items-center gap-2">
                        <i
                          className="size-2 shrink-0 rounded-full"
                          style={{ backgroundColor: category.color }}
                        />
                        <span className="truncate">{category.label}</span>
                      </span>
                      <span className="shrink-0 text-muted-foreground">
                        {compactMoney.format(category.value)}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <EmptyChart copy="Add categories to transactions to reveal where this month’s money went." />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex-row items-start justify-between gap-4 space-y-0 pb-2">
          <div>
            <CardTitle className="text-base">Credit utilization</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Keep each card comfortably below the utilization threshold you set in Notifications.
            </p>
          </div>
          <span className="text-xs text-muted-foreground">Top five active cards</span>
        </CardHeader>
        <CardContent>
          {utilizationData.length > 0 ? (
            <figure>
              <BarChart
                data={utilizationData}
                xDataKey="card"
                className="[--chart-line-primary:var(--chart-2)]"
                margin={{ top: 14, right: 16, bottom: 34, left: 16 }}
              >
                <Grid horizontal numTicksRows={4} />
                <Bar dataKey="utilization" fill="var(--chart-line-primary)" minBarHeight={2} />
                <BarXAxis />
                <ChartTooltip />
              </BarChart>
              <figcaption className="sr-only">
                Credit-card utilization percentage by card, ordered from highest to lowest.
              </figcaption>
            </figure>
          ) : (
            <EmptyChart copy="Add a card with a credit limit to monitor utilization." />
          )}
        </CardContent>
      </Card>
    </section>
  );
}

function EmptyChart({ copy }: { copy: string }) {
  return (
    <div className="flex min-h-48 items-center justify-center rounded-lg border border-dashed bg-muted/20 p-6 text-center text-sm text-muted-foreground">
      <p className="max-w-sm">{copy}</p>
    </div>
  );
}
