# Reviews and release evidence

This folder contains dated reviews and the repeatable remediation queue. These
documents record evidence at a point in time; the current release status lives
in the release trackers and [`../CONTEXT.md`](../CONTEXT.md).

## Review timeline

| Date | Document | Purpose | Current reading |
| --- | --- | --- | --- |
| 2026-08-10 | [`2026-08-10-production-readiness-audit.md`](2026-08-10-production-readiness-audit.md) | Source/configuration/static-UI audit, fixed findings, remaining risks, and required evidence. | Historical baseline for the remediation work. |
| 2026-08-11 | [`2026-08-11-release-readiness.md`](2026-08-11-release-readiness.md) | Release-owner decision, remediated findings, deployment checklist, and validation gates. | Latest release-readiness record. |
| Ongoing queue | [`production-remediation-loop.md`](production-remediation-loop.md) | One-subtask-at-a-time queue for deferred production hardening. | Follow-up tracker; `todo` rows remain open until evidence is added. |

## How to read these records

- Use the 2026-08-11 review for the current deployment sequence and its prerequisites.
- Use the 2026-08-10 audit for the original finding IDs and acceptance evidence.
- Use the remediation loop only for follow-up hardening; it is not a replacement for the product PRD or Release 2 tracker.
