# Fin Buddy Frontend

Next.js App Router frontend for Fin Buddy.

## Stack

- Next.js 16 + React 19 + TypeScript
- Tailwind CSS v4
- shadcn/ui primitives
- Aceternity UI (copy-in components as needed — see below)
- Zod + `@t3-oss/env-nextjs` for env validation
- Package manager: **[bun](https://bun.sh)**

## Layout

```text
src/
  app/              # routes (App Router)
  components/ui/    # shadcn primitives
  features/         # feature modules (cards, contacts, …)
  hooks/
  lib/              # env, api client, formatters, utils
  types/
```

## Setup

```bash
cd frontend
bun install
cp .env.example .env.local
bun run dev
```

App: http://localhost:3000

## Scripts

```bash
bun run dev          # development server
bun run build        # production build
bun run start        # start production server
bun run lint         # ESLint
bun run typecheck    # tsc --noEmit
bun run format       # Prettier write
```

## Aceternity UI

Aceternity components are **copy-paste** (not a bulk UI kit install). When adding one:

1. Install any peer deps it needs with bun (often `framer-motion`, `clsx`, `tailwind-merge` — already partly covered by shadcn utils).
2. Drop the component under `src/components/aceternity/` or a feature folder.
3. Align colors with CSS variables in `globals.css` so it matches shadcn tokens.
4. Prefer using Aceternity for high-impact moments (hero, dashboard flair); keep dense tables/forms on shadcn.

## Deploy

Target: **Vercel**. Project root: `frontend`.

| Env | Example |
|-----|---------|
| `NEXT_PUBLIC_APP_URL` | `https://your-app.vercel.app` |
| `NEXT_PUBLIC_API_URL` | `https://your-api.example.com` |
| `BACKEND_URL` | Same as API (server-side `/backend` rewrite) |

With `bun.lock` present, Vercel should use Bun for installs. If needed, set install to `bun install` and build to `bun run build`.

Supabase Auth redirect URLs must include `https://your-app.vercel.app/auth/callback`.
