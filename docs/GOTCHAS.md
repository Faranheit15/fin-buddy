# Project Gotchas & Retired Claims

Agents must review this document to avoid common pitfalls in this specific repository.

## Architecture Boundaries
- Do NOT share types or models directly between the frontend and backend directories. They must remain decoupled. Rely on the API schema contract instead.

## Supabase Quirks
- Service-role keys must NEVER be exposed to the frontend. They are backend-only.
- Always check the allowed redirect URLs in Supabase if authentication flows fail locally.

## Retired Approaches
- *(Add any technical approaches that were tried and failed here, so agents do not attempt them again)*
