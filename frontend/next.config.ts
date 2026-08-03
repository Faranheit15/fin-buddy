import type { NextConfig } from "next";

/**
 * Browser calls same-origin `/backend/*` which is rewritten to the FastAPI server.
 * Avoids CORS "Failed to fetch" when the UI and API run on different ports.
 *
 * BACKEND_URL (server-only) wins for the rewrite target; falls back to NEXT_PUBLIC_API_URL.
 */
const backendUrl = (
  process.env.BACKEND_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8001"
).replace(/\/$/, "");

const nextConfig: NextConfig = {
  // Lean production image via `output: "standalone"` (see frontend/Dockerfile).
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/backend/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
