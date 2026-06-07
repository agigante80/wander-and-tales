// @ts-check
import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";
import tailwindcss from "@tailwindcss/vite";

// Static site (SSG). Deployed to Cloudflare Workers static assets via wrangler.
export default defineConfig({
  site: "https://www.wanderandtales.com",
  trailingSlash: "ignore",
  build: { format: "directory" },
  integrations: [
    sitemap({
      // hreflang alternates: URL prefix -> hreflang code. defaultLocale feeds x-default.
      i18n: {
        defaultLocale: "en",
        locales: { en: "en-GB", es: "es-ES", it: "it-IT", pt: "pt-PT" },
      },
      // drop the root redirect ("/") and the soft-private styleguide.
      filter: (page) => {
        const p = new URL(page).pathname;
        return p !== "/" && !p.startsWith("/styleguide");
      },
      // the integration emits per-locale hreflang but not x-default; add it,
      // pointing at the en (en-GB) version, to match the <head> tags. The links
      // array is shared across a locale group, so guard against adding it twice.
      serialize: (item) => {
        if (item.links && !item.links.some((l) => l.lang === "x-default")) {
          const en = item.links.find((l) => l.lang === "en-GB");
          if (en) item.links.push({ lang: "x-default", url: en.url });
        }
        return item;
      },
    }),
  ],
  vite: { plugins: [tailwindcss()] },
});
