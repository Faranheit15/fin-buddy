# Architecture references

This folder holds focused architecture and UI-integration notes. The complete
product architecture is described across the root [`DESIGN.md`](../../DESIGN.md),
[`PRODUCT.md`](../../PRODUCT.md), and the service READMEs.

## References

| Document | Use it for |
| --- | --- |
| [`aceternity.md`](aceternity.md) | When to use Aceternity UI, where to place copied components, and how to keep them aligned with shadcn tokens. |
| [`../../DESIGN.md`](../../DESIGN.md) | Design tokens, typography, layout density, components, motion, and visual guardrails. |
| [`../../PRODUCT.md`](../../PRODUCT.md) | Product positioning, operating context, capabilities, constraints, and product principles. |
| [`../GOTCHAS.md`](../GOTCHAS.md) | Non-negotiable frontend/backend boundaries and repository-specific implementation traps. |

## Repository boundary

Fin Buddy is two sibling applications rather than a monorepo: the Next.js
frontend communicates with the FastAPI backend through the API layer. Keep that
boundary intact when documenting or implementing new features.
