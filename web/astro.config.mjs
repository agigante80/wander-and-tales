// @ts-check
import { defineConfig } from "astro/config";
import tailwindcss from "@tailwindcss/vite";

// Static site (SSG). Deployed to Cloudflare Workers static assets via wrangler.
export default defineConfig({
  site: "https://wanderandtales.com",
  trailingSlash: "ignore",
  build: { format: "directory" },
  vite: { plugins: [tailwindcss()] },
});
