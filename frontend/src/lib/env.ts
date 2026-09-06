import { createEnv } from "@t3-oss/env-nextjs";
import { z } from "zod";

/**
 * Typed environment variables.
 * Server secrets never go in NEXT_PUBLIC_*.
 */
export const env = createEnv({
  server: {
    BACKEND_URL: z.string().url().default("http://127.0.0.1:8001"),
  },
  client: {
    NEXT_PUBLIC_APP_URL: z.string().url().default("http://localhost:3000"),
    NEXT_PUBLIC_SUPABASE_URL: z.string().url().optional(),
    /**
     * Supabase Publishable Key (sb_publishable_... or legacy anon JWT).
     * Primary variable is NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY with legacy
     * NEXT_PUBLIC_SUPABASE_ANON_KEY supported as a compatibility alias.
     */
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY: z.string().min(1).optional(),
    NEXT_PUBLIC_SUPABASE_ANON_KEY: z.string().min(1).optional(),
  },
  runtimeEnv: {
    BACKEND_URL: process.env.BACKEND_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
    NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
    NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY:
      process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  },
  emptyStringAsUndefined: true,
  skipValidation: process.env.SKIP_ENV_VALIDATION === "1",
});

export function isSupabaseConfigured(): boolean {
  return Boolean(
    env.NEXT_PUBLIC_SUPABASE_URL &&
      (env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY || env.NEXT_PUBLIC_SUPABASE_ANON_KEY),
  );
}

export function requireSupabaseConfig(): {
  url: string;
  publishableKey: string;
  /** @deprecated use publishableKey */
  anonKey: string;
} {
  const key =
    env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!env.NEXT_PUBLIC_SUPABASE_URL || !key) {
    throw new Error(
      "Supabase is not configured. Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY in frontend/.env.local",
    );
  }
  return {
    url: env.NEXT_PUBLIC_SUPABASE_URL,
    publishableKey: key,
    anonKey: key,
  };
}
