# Documentation context

Documentation is part of the product's operating contract. Before changing a
document, read [`README.md`](README.md), [`ROUTING.md`](ROUTING.md),
[`CONTEXT.md`](CONTEXT.md), and [`GOTCHAS.md`](GOTCHAS.md) as relevant.

- Keep the active productionization plan in `prd/productionization/`.
- Keep human decisions and missing credentials in
  [`user-input-needed.md`](user-input-needed.md), but never record secret
  values there.
- Treat dated reviews as historical evidence. Update the active tracker when
  a decision or implementation status changes.
- Preserve working links and validate Markdown structure, whitespace, and
  cross-document references before closing a documentation task.
- A document-only change must not invent live deployment, database, quota, or
  OAuth verification evidence. Record an explicit blocker instead.
