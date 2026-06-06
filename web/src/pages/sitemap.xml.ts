import { worlds } from "../lib/content";
import { LANGS, SITE_URL } from "../consts";

export const GET = () => {
  const urls: string[] = [];
  for (const l of LANGS) {
    urls.push(`/${l.code}/`, `/${l.code}/how-to-play`, `/${l.code}/help`, `/${l.code}/why`, `/${l.code}/create`, `/${l.code}/privacy`, `/${l.code}/legal`, `/${l.code}/terms`);
    for (const w of worlds) {
      urls.push(`/${l.code}/worlds/${w.id}`);
      for (const s of w.stories) urls.push(`/${l.code}/worlds/${w.id}/${s.id}`);
    }
  }
  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    urls.map((u) => `  <url><loc>${SITE_URL}${u}</loc></url>`).join("\n") +
    `\n</urlset>\n`;
  return new Response(body, { headers: { "Content-Type": "application/xml" } });
};
