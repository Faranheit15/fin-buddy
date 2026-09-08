import { afterEach, describe, expect, mock, test } from "bun:test";

import { uploadStatement } from "@/lib/api/statements";

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  mock.restore();
});

describe("durable statement upload", () => {
  test("keeps a large file out of the backend request body", async () => {
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    globalThis.fetch = mock(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      calls.push({ url, init });
      if (calls.length === 1) {
        return new Response(
          JSON.stringify({
            mode: "signed",
            statement_id: "statement-1",
            object_path: "org-1/user-1/statement-1.txt",
            upload_url: "https://storage.example/upload?token=one-time",
            expires_at: "2026-09-09T00:15:00Z",
            max_upload_bytes: 15 * 1024 * 1024,
            allowed_mime_types: ["text/plain"],
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      }
      if (calls.length === 2) return new Response(null, { status: 409 });
      return new Response(
        JSON.stringify({ id: "statement-1", status: "needs_review", lines: [] }),
        { status: 200, headers: { "content-type": "application/json" } },
      );
    }) as unknown as typeof fetch;

    const file = new Blob([new Uint8Array(5 * 1024 * 1024)], { type: "text/plain" });
    await uploadStatement("access-token", {
      file,
      filename: "statement.txt",
      creditCardId: "card-1",
      idempotencyKey: "statement-upload-test-1",
    });

    expect(calls).toHaveLength(3);
    expect(calls[0]?.init?.method).toBe("POST");
    const prepareHeaders = new Headers(calls[0]?.init?.headers);
    expect(prepareHeaders.get("Content-Type")).toBe("application/json");
    expect(prepareHeaders.get("Idempotency-Key")).toBe("statement-upload-test-1");
    expect((calls[0]?.init?.body as string).length).toBeLessThan(2_000);
    expect(calls[1]?.url).toContain("storage.example/upload");
    expect(calls[1]?.init?.method).toBe("PUT");
    expect(calls[1]?.init?.body).toBeInstanceOf(ArrayBuffer);
    expect((calls[1]?.init?.body as ArrayBuffer).byteLength).toBe(file.size);
    const uploadHeaders = new Headers(calls[1]?.init?.headers);
    expect(uploadHeaders.get("Content-Type")).toBe("text/plain;charset=utf-8");
    expect(uploadHeaders.get("Cache-Control")).toBe("max-age=3600");
    expect(uploadHeaders.get("x-upsert")).toBe("false");
    expect(new Headers(calls[1]?.init?.headers).get("x-upsert")).toBe("false");
    expect(calls[2]?.init?.body as string).toContain('"statement_id":"statement-1"');
  });
});
