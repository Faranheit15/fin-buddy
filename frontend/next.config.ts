import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // `standalone` is for Docker Compose images only — on Vercel it breaks routing
  // (platform 404 NOT_FOUND). Dockerfile sets DOCKER_BUILD=1.
  ...(process.env.DOCKER_BUILD === "1" ? { output: "standalone" as const } : {}),
  async headers() {
    const headers = [
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      {
        key: "Permissions-Policy",
        value: "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
      },
    ];
    if (process.env.NODE_ENV === "production") {
      headers.push({
        key: "Strict-Transport-Security",
        value: "max-age=63072000; includeSubDomains; preload",
      });
    }
    return [{ source: "/:path*", headers }];
  },
};

export default nextConfig;
