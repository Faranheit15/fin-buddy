import { describe, expect, it } from "bun:test";

import {
  consumeOAuthFlow,
  generateOAuthState,
  generatePKCEPair,
  sanitizeAppPath,
  storeOAuthFlow,
} from "./oauth";

describe("sanitizeAppPath", () => {
  it("allows valid app paths and subpaths", () => {
    expect(sanitizeAppPath("/app")).toBe("/app");
    expect(sanitizeAppPath("/app/cards")).toBe("/app/cards");
    expect(sanitizeAppPath("/app/accounts/abc-123")).toBe("/app/accounts/abc-123");
    expect(sanitizeAppPath("/app/debts?filter=active")).toBe("/app/debts?filter=active");
  });

  it("defaults to /app for empty or invalid inputs", () => {
    expect(sanitizeAppPath(null)).toBe("/app");
    expect(sanitizeAppPath(undefined)).toBe("/app");
    expect(sanitizeAppPath("")).toBe("/app");
    expect(sanitizeAppPath("   ")).toBe("/app");
  });

  it("rejects external schemes and origins", () => {
    expect(sanitizeAppPath("https://evil.example")).toBe("/app");
    expect(sanitizeAppPath("https://evil.example/app")).toBe("/app");
    expect(sanitizeAppPath("http://localhost:3000/app")).toBe("/app");
    expect(sanitizeAppPath("javascript:alert(1)")).toBe("/app");
    expect(sanitizeAppPath("data:text/html,<script>alert(1)</script>")).toBe("/app");
  });

  it("rejects protocol-relative URLs and backslashes", () => {
    expect(sanitizeAppPath("//evil.example/app")).toBe("/app");
    expect(sanitizeAppPath("/\\evil.example")).toBe("/app");
    expect(sanitizeAppPath("\\\\evil.example")).toBe("/app");
    expect(sanitizeAppPath("/app\\cards")).toBe("/app");
  });

  it("rejects URL fragments", () => {
    expect(sanitizeAppPath("/app#token=secret")).toBe("/app");
    expect(sanitizeAppPath("/app/cards#section")).toBe("/app");
  });

  it("rejects path traversal and encoded traversal", () => {
    expect(sanitizeAppPath("/app/../../evil")).toBe("/app");
    expect(sanitizeAppPath("/app/%2e%2e/evil")).toBe("/app");
    expect(sanitizeAppPath("/app/../accounts")).toBe("/app");
    expect(sanitizeAppPath("/app/./cards")).toBe("/app");
  });

  it("rejects non-app paths", () => {
    expect(sanitizeAppPath("/settings")).toBe("/app");
    expect(sanitizeAppPath("/login")).toBe("/app");
    expect(sanitizeAppPath("/auth/callback")).toBe("/app");
    expect(sanitizeAppPath("/api/v1/auth/me")).toBe("/app");
  });

  it("rejects control characters and CRLF injection", () => {
    expect(sanitizeAppPath("/app\r\nSet-Cookie:bad=1")).toBe("/app");
    expect(sanitizeAppPath("/app\x00evil")).toBe("/app");
  });
});

describe("generatePKCEPair", () => {
  it("generates a valid code_verifier and code_challenge pair", async () => {
    const { codeVerifier, codeChallenge } = await generatePKCEPair();

    // Verifier should be base64url 43 chars (32 bytes)
    expect(codeVerifier).toHaveLength(43);
    expect(codeVerifier).toMatch(/^[A-Za-z0-9_-]+$/);

    // Challenge should be base64url 43 chars (32 bytes SHA-256)
    expect(codeChallenge).toHaveLength(43);
    expect(codeChallenge).toMatch(/^[A-Za-z0-9_-]+$/);

    // Verifier and challenge must not be identical
    expect(codeVerifier).not.toBe(codeChallenge);
  });

  it("generates unique PKCE pairs on successive calls", async () => {
    const pair1 = await generatePKCEPair();
    const pair2 = await generatePKCEPair();

    expect(pair1.codeVerifier).not.toBe(pair2.codeVerifier);
    expect(pair1.codeChallenge).not.toBe(pair2.codeChallenge);
  });
});

describe("generateOAuthState", () => {
  it("generates a high-entropy random urlsafe state", () => {
    const state1 = generateOAuthState();
    const state2 = generateOAuthState();

    expect(state1.length).toBeGreaterThanOrEqual(32);
    expect(state1).toMatch(/^[A-Za-z0-9_-]+$/);
    expect(state1).not.toBe(state2);
  });
});

describe("storeOAuthFlow and consumeOAuthFlow", () => {
  it("stores and consumes a flow record successfully", () => {
    const state = generateOAuthState();
    storeOAuthFlow({
      state,
      codeVerifier: "test-code-verifier-43-chars-long-1234567890",
      next: "/app/cards",
      createdAt: Date.now(),
    });

    const flow = consumeOAuthFlow(state);
    expect(flow).not.toBeNull();
    expect(flow?.state).toBe(state);
    expect(flow?.codeVerifier).toBe("test-code-verifier-43-chars-long-1234567890");
    expect(flow?.next).toBe("/app/cards");
  });

  it("enforces single-use: repeated consume returns null", () => {
    const state = generateOAuthState();
    storeOAuthFlow({
      state,
      codeVerifier: "test-code-verifier-43-chars-long-1234567890",
      next: "/app/debts",
      createdAt: Date.now(),
    });

    const firstConsume = consumeOAuthFlow(state);
    expect(firstConsume).not.toBeNull();

    // Replay attempt must return null
    const secondConsume = consumeOAuthFlow(state);
    expect(secondConsume).toBeNull();
  });

  it("stores and consumes pending flow without state parameter", () => {
    storeOAuthFlow({
      codeVerifier: "test-code-verifier-without-state-43-chars-xx",
      next: "/app/cards",
      createdAt: Date.now(),
    });

    const flow = consumeOAuthFlow();
    expect(flow).not.toBeNull();
    expect(flow?.codeVerifier).toBe("test-code-verifier-without-state-43-chars-xx");
    expect(flow?.next).toBe("/app/cards");

    // Single use
    expect(consumeOAuthFlow()).toBeNull();
  });

  it("rejects empty store or expired pending flow", () => {
    expect(consumeOAuthFlow()).toBeNull();

    const elevenMinutesAgo = Date.now() - 11 * 60 * 1000;
    storeOAuthFlow({
      codeVerifier: "expired-verifier-43-chars-long-1234567890123",
      next: "/app",
      createdAt: elevenMinutesAgo,
    });
    expect(consumeOAuthFlow()).toBeNull();
  });

  it("rejects unknown or invalid state when store is empty", () => {
    expect(consumeOAuthFlow("non-existent-state")).toBeNull();
    expect(consumeOAuthFlow(null)).toBeNull();
    expect(consumeOAuthFlow(undefined)).toBeNull();
  });

  it("rejects expired state records (>10 minutes old)", () => {
    const state = generateOAuthState();
    const elevenMinutesAgo = Date.now() - 11 * 60 * 1000;
    storeOAuthFlow({
      state,
      codeVerifier: "test-code-verifier-43-chars-long-1234567890",
      next: "/app",
      createdAt: elevenMinutesAgo,
    });

    expect(consumeOAuthFlow(state)).toBeNull();
  });

  it("handles multiple concurrent tabs without interference", () => {
    const stateTab1 = generateOAuthState();
    const stateTab2 = generateOAuthState();

    storeOAuthFlow({
      state: stateTab1,
      codeVerifier: "verifier-for-tab-1-123456789012345678901234",
      next: "/app/cards",
      createdAt: Date.now(),
    });

    storeOAuthFlow({
      state: stateTab2,
      codeVerifier: "verifier-for-tab-2-123456789012345678901234",
      next: "/app/accounts",
      createdAt: Date.now(),
    });

    // Consuming tab 1 succeeds and returns tab 1's destination
    const flow1 = consumeOAuthFlow(stateTab1);
    expect(flow1?.next).toBe("/app/cards");
    expect(flow1?.codeVerifier).toBe("verifier-for-tab-1-123456789012345678901234");

    // Tab 2 remains untouched and can be consumed independently
    const flow2 = consumeOAuthFlow(stateTab2);
    expect(flow2?.next).toBe("/app/accounts");
    expect(flow2?.codeVerifier).toBe("verifier-for-tab-2-123456789012345678901234");
  });
});
