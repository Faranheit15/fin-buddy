# Reviews and release evidence

This folder contains dated reviews and the original repeatable remediation
queue. These documents record evidence at a point in time; the active work now
lives in the [Productionization & Product Polish plan](../prd/productionization/README.md)
and its tracker, with [`../CONTEXT.md`](../CONTEXT.md) as the short current
context.

## Review timeline

| Date | Document | Purpose | Current reading |
| --- | --- | --- | --- |
| 2026-08-10 | [`2026-08-10-production-readiness-audit.md`](2026-08-10-production-readiness-audit.md) | Source/configuration/static-UI audit, fixed findings, remaining risks, and required evidence. | Historical baseline for the remediation work. |
| 2026-08-11 | [`2026-08-11-release-readiness.md`](2026-08-11-release-readiness.md) | Release-owner decision, remediated findings, deployment checklist, and validation gates. | Latest release-readiness record. |
| Historical queue | [`production-remediation-loop.md`](production-remediation-loop.md) | Original one-subtask-at-a-time queue for deferred production hardening. | Historical IDs are mapped into the active productionization stories. |

## How to read these records

- Use the 2026-08-11 review for the current deployment sequence and its prerequisites.
- Use the 2026-08-10 audit for the original finding IDs and acceptance evidence.
- Use the [Productionization & Product Polish plan](../prd/productionization/README.md) for new loops. Use the old remediation loop only for historical finding IDs; it is not a competing queue or a replacement for the product PRD.
