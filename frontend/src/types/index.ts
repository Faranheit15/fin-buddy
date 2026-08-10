/**
 * Shared frontend types.
 * Domain DTOs will expand as OpenAPI / API contracts land.
 */

export type OrganizationRole = "owner" | "admin" | "member";

export type TransactionType = "purchase" | "refund" | "fee" | "interest" | "payment_to_issuer";

export type DueRuleType = "fixed_day" | "days_after_statement";
