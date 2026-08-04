import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function HomePage() {
  return (
    <main className="relative flex flex-1 flex-col overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top,_oklch(0.95_0.02_250)_0%,_transparent_55%)] dark:bg-[radial-gradient(ellipse_at_top,_oklch(0.25_0.04_250)_0%,_transparent_55%)]" />

      <header className="relative z-10 mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <span className="flex size-8 items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground">
            FB
          </span>
          <span className="text-lg font-semibold tracking-tight">Fin Buddy</span>
        </div>
        <Link
          href="/login"
          className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
        >
          Sign in
        </Link>
      </header>

      <section className="relative z-10 mx-auto flex w-full max-w-6xl flex-1 flex-col justify-center px-6 pb-24 pt-8">
        <p className="mb-4 text-sm font-medium uppercase tracking-[0.2em] text-muted-foreground">
          Credit cards · Lending ledger · India
        </p>
        <h1 className="max-w-3xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl md:text-6xl">
          Track every card, cycle, and friend balance — without the spreadsheet chaos.
        </h1>
        <p className="mt-6 max-w-2xl text-lg text-muted-foreground text-pretty">
          Fin Buddy is a production-grade personal finance tool for multi-card limits,
          statement and due dates, full spend ledgers, and settlements when friends use your
          cards.
        </p>
        <div className="mt-10 flex flex-wrap items-center gap-3">
          <Link href="/app" className={cn(buttonVariants({ size: "lg" }))}>
            Open dashboard
          </Link>
          <Link href="/login" className={cn(buttonVariants({ variant: "outline", size: "lg" }))}>
            Sign in
          </Link>
        </div>

        <dl className="mt-16 grid gap-4 sm:grid-cols-3">
          {[
            {
              title: "Cards & cycles",
              body: "Limits, utilization, statement day, and due dates in one place.",
            },
            {
              title: "Friend ledger",
              body: "Attribute every spend and track who still owes you.",
            },
            {
              title: "Statement import",
              body: "Upload PDFs, review proposed lines, then commit to the ledger.",
            },
          ].map((item) => (
            <div
              key={item.title}
              className="rounded-xl border bg-card/80 p-5 shadow-sm backdrop-blur-sm"
            >
              <dt className="font-medium">{item.title}</dt>
              <dd className="mt-2 text-sm text-muted-foreground">{item.body}</dd>
            </div>
          ))}
        </dl>
      </section>
    </main>
  );
}
