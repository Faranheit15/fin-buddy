<!-- BEGIN:nextjs-agent-rules -->
# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` before writing any code. Heed deprecation notices.
<!-- END:nextjs-agent-rules -->

# Frontend Service Context

## Architecture
Next.js, TypeScript, Tailwind, and shadcn/ui web app.
- `src/app`: Route files (Next.js App Router conventions).
- `src/components`: Reusable UI components.
- `src/features`: Feature modules.
- `src/lib`: API clients and shared utilities.

## Coding Style & Naming Conventions
TypeScript should stay type-safe and component-focused:
- React components use `PascalCase`.
- Hooks use `use*`.
- Route directories follow Next.js conventions.
- Shared helpers stay in `src/lib`.
- Format code using Prettier before committing.

## Build, Test, and Development Commands
```bash
bun install
bun run dev
```

## Definition of Done (DoD)
Before any frontend change is considered complete, you MUST pass linting and typechecking:
```bash
bun run lint
bun run typecheck
bun run build
bun run format
```
