import type { NextConfig } from "next";

const offline = process.env.NEXT_PUBLIC_AIR_GAP_MODE === "true";
if (offline) {
  process.env.COPILOTKIT_TELEMETRY_DISABLED = "true";
  process.env.DO_NOT_TRACK = "1";
  process.env.NEXT_TELEMETRY_DISABLED = "1";
}
const nextConfig: NextConfig = {
  async headers() {
    if (!offline) return [];
    return [{ source: "/:path*", headers: [{ key: "Content-Security-Policy", value:
      "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self' blob:; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; form-action 'self'"
    }] }];
  },
  output: "standalone",
  serverExternalPackages: ["@copilotkit/runtime"],
};

export default nextConfig;
