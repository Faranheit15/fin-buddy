import { Suspense } from "react";
import Link from "next/link";

import { BrandMark } from "@/components/brand/mark";
import { LoginForm } from "@/features/auth/login-form";

export const metadata = {
  title: "Sign in",
};

export default function LoginPage() {
  return (
    <main className="flex flex-1 items-center justify-center px-6 py-16">
      <div className="w-full max-w-md rounded-2xl border bg-card p-8 shadow-sm">
        <div className="mb-8 space-y-2 text-center">
          <BrandMark size="md" className="mx-auto" />
          <h1 className="text-2xl font-semibold tracking-tight">Sign in to Fin Buddy</h1>
          <p className="text-sm text-muted-foreground">
            Sign-in is handled by the Fin Buddy API (server-side Supabase).
          </p>
        </div>

        <Suspense fallback={<p className="text-sm text-muted-foreground">Loading…</p>}>
          <LoginForm />
        </Suspense>

        <p className="mt-8 text-center text-sm text-muted-foreground">
          <Link href="/" className="underline-offset-4 hover:underline">
            Back to home
          </Link>
        </p>
      </div>
    </main>
  );
}
