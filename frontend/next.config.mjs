/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export: `next build` writes a plain HTML/JS site to out/,
  // which is served by Cloudflare Workers static assets.
  output: "export"
};

export default nextConfig;
