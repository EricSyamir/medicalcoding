/** @type {import('next').NextConfig} */
const nextConfig = {
  // BACKEND_URL is read server-side only (not exposed to browser)
  serverRuntimeConfig: {
    backendUrl: process.env.BACKEND_URL || "http://localhost:8000",
  },
};

module.exports = nextConfig;

