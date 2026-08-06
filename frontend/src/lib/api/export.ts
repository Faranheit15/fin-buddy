import { apiBase, ApiError } from "./client";

export async function exportData(accessToken: string): Promise<Blob> {
  const url = `${apiBase()}/api/v1/export`;
  const res = await fetch(url, {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });

  if (!res.ok) {
    let message = "Failed to download export";
    try {
      const body = await res.json();
      message = body.error?.message || message;
    } catch {
      // Ignore
    }
    throw new ApiError(message, res.status);
  }

  return res.blob();
}
