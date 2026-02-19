import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // Allow Railway's internal URLs
  images: {
    domains: [],
  },
};

export default nextConfig;
