import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // BACKEND_URL is read server-side only (not exposed to browser)
  serverRuntimeConfig: {
    backendUrl: process.env.BACKEND_URL || "http://localhost:8000",
  },
};

export default nextConfig;
