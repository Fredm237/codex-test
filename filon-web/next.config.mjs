/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export → a plain out/ folder of HTML/CSS/JS to upload to Hostinger
  // (shared hosting has no Node server). Set NEXT_PUBLIC_BASE_PATH if the site
  // lives in a sub-folder rather than the domain root.
  output: "export",
  reactStrictMode: true,
  poweredByHeader: false,
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || undefined,
};

export default nextConfig;
