# Using Aceternity UI in Fin Buddy

Aceternity UI is a **copy-paste** component library (similar in spirit to shadcn), not a single install-everything package.

## When to use it

- Landing / marketing hero flair
- Dashboard decorative cards or backgrounds
- Selective motion that improves clarity (not noise)

## When not to use it

- Dense data tables, forms, dialogs, sidebars → use **shadcn/ui**
- Anything that would fight design tokens or accessibility

## How to add a component

1. Pick a component from [ui.aceternity.com](https://ui.aceternity.com/).
2. Install any listed peer dependencies with **bun** (often `bun add framer-motion`).
3. Place source under `frontend/src/components/aceternity/<name>.tsx`.
4. Map colors/spacing to CSS variables from `globals.css` (`--primary`, `--muted`, etc.).
5. Keep bundle impact in mind; prefer dynamic import for heavy motion pieces on non-critical routes.

## Design system rule

One visual language: shadcn tokens are the source of truth. Aceternity components must adapt to those tokens, not introduce a second palette.
