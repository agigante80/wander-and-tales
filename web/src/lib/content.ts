import fs from "node:fs";
import path from "node:path";
import { marked } from "marked";

// npm scripts (dev/build) always run from web/, so the repo root is one level up.
export const ROOT = path.resolve(process.cwd(), "..");

const manifest = JSON.parse(
  fs.readFileSync(path.join(ROOT, "site/manifest.json"), "utf-8"),
);

export const site = manifest.site as any;
export const worlds = manifest.worlds as any[];

export const worldById = (id: string) => worlds.find((w) => w.id === id);
export const storyById = (worldId: string, storyId: string) =>
  worldById(worldId)?.stories.find((s: any) => s.id === storyId);

export function readText(relPath: string): string {
  try {
    return fs.readFileSync(path.join(ROOT, relPath), "utf-8");
  } catch {
    return "";
  }
}

// public URL for a manifest image path ("worlds/.../assets/x.png"). prepare-assets
// resizes the source PNG to a WebP at the same path, so the served file is .webp.
export const mediaUrl = (relPath?: string | null) =>
  relPath ? "/media/" + relPath.replace(/\.png$/, ".webp") : null;

// the rendered trail map for a story+locale. The PNG lives in <root>/maps (committed);
// prepare-assets resizes it to a WebP under /maps, which is what we serve.
export const storyMapUrl = (worldId: string, storyId: string, locale: string) => {
  const png = `maps/${worldId}/${storyId}/map-${locale}.png`;
  return fs.existsSync(path.join(ROOT, png))
    ? `/maps/${worldId}/${storyId}/map-${locale}.webp`
    : null;
};

// Responsive srcset. prepare-assets writes <base>-<W>.webp for each width <= native,
// under web/public; build the srcset from the variants that exist so the browser
// picks the right size for the display. urlBase is the public path without extension.
const PUB = path.resolve(process.cwd(), "public");
const SRCSET_WIDTHS = [320, 640, 960, 1280];
function srcsetFrom(urlBase: string, pubBase: string): string {
  return SRCSET_WIDTHS.filter((w) => fs.existsSync(`${pubBase}-${w}.webp`))
    .map((w) => `${urlBase}-${w}.webp ${w}w`)
    .join(", ");
}
// srcset for a manifest image path ("worlds/.../assets/x.png")
export const mediaSrcset = (relPath?: string | null) => {
  if (!relPath) return undefined;
  const base = relPath.replace(/\.png$/, "");
  const set = srcsetFrom("/media/" + base, path.join(PUB, "media", base));
  return set || undefined;
};
// srcset for a story trail map
export const mapSrcset = (worldId: string, storyId: string, locale: string) => {
  const base = `${worldId}/${storyId}/map-${locale}`;
  const set = srcsetFrom("/maps/" + base, path.join(PUB, "maps", base));
  return set || undefined;
};

// A manifest PDF entry is { path, version, updated } (or null). The PDFs are
// self-hosted under /kits/... (copied into public by scripts/prepare-assets.mjs).
export const pdfUrl = (entry?: any) => {
  const p = typeof entry === "string" ? entry : entry?.path;
  return p ? "/" + p : null;
};
export const pdfVer = (entry?: any) =>
  entry && typeof entry === "object" ? entry.version : null;

// render narration markdown to HTML, dropping the leading "# Title" (we render our own)
export function narrationHtml(relPath?: string | null): string {
  if (!relPath) return "";
  const md = readText(relPath);
  if (!md) return "";
  const body = md.replace(/^#\s+.*$/m, "").trim();
  return marked.parse(body, { gfm: true, async: false }) as string;
}

// shift every heading down by `by` levels (h1 -> h2 ...), capped at h6
function shiftHeadings(html: string, by: number): string {
  if (!by) return html;
  for (let n = 6; n >= 1; n--) {
    const m = Math.min(6, n + by);
    html = html.replace(new RegExp(`<(/?)h${n}(?=[ >])`, "g"), `<$1h${m}`);
  }
  return html;
}

// render a markdown file to HTML as-is (keeps its heading); used for the grown-up
// rules and puzzles sections. `shift` demotes headings so a page keeps a single
// <h1> and the heading order does not skip a level.
export function mdHtml(relPath?: string | null, shift = 0): string {
  if (!relPath) return "";
  const md = readText(relPath);
  if (!md) return "";
  return shiftHeadings(marked.parse(md, { gfm: true, async: false }) as string, shift);
}

// trim text to a meta-description-friendly length at a word boundary
export function snippet(text?: string | null, max = 158): string {
  const t = (text ?? "").replace(/\s+/g, " ").trim();
  if (t.length <= max) return t;
  const cut = t.slice(0, max);
  return cut.slice(0, Math.max(cut.lastIndexOf(" "), max - 20)).trimEnd() + "...";
}

// ---- per-stop story reader ---------------------------------------------------
// Narration and puzzles share the same "## Stop N: Name" headings, so we can
// interleave each stop's scene image and its grown-up solution inline.

const stripH1 = (md: string) => md.replace(/^#\s+.*$/m, "").trim();

// split markdown into sections by "## " headings; text before the first ## has heading=null
function splitSections(md: string): { heading: string | null; body: string }[] {
  const out: { heading: string | null; body: string[] }[] = [{ heading: null, body: [] }];
  for (const ln of md.split("\n")) {
    const m = ln.match(/^##\s+(.*\S)\s*$/);
    if (m) out.push({ heading: m[1].trim(), body: [] });
    else out[out.length - 1].body.push(ln);
  }
  return out
    .map((s) => ({ heading: s.heading, body: s.body.join("\n").trim() }))
    .filter((s) => s.heading !== null || s.body);
}

// normalize a stop heading for matching across files (drops a trailing "(Easy)" band)
const normHeading = (h: string) => h.toLowerCase().replace(/\s*\([^)]*\)\s*$/, "").trim();

export interface ReaderSection {
  heading: string | null;
  simpleHtml: string;
  richHtml: string;
  sceneUrl: string | null;
  sceneSrcset?: string;
  sceneAlt: string;
  solutionHtml: string | null;
}

export function storyReader(
  simplePath?: string | null,
  richPath?: string | null,
  puzzlesPath?: string | null,
  scenes: any[] = [],
  locale = "en-GB",
): ReaderSection[] {
  const md2 = (b: string) => (b ? (marked.parse(b, { gfm: true, async: false }) as string) : "");
  const simple = simplePath ? splitSections(stripH1(readText(simplePath))) : [];
  const rich = richPath ? splitSections(stripH1(readText(richPath))) : [];
  const puzz = puzzlesPath ? splitSections(stripH1(readText(puzzlesPath))) : [];

  const puzzMap = new Map<string, string>();
  for (const p of puzz) if (p.heading) puzzMap.set(normHeading(p.heading), p.body);

  // scenes correspond to the trailing headed sections (the stops and the ending);
  // the opening "before you begin" section has no scene. Match by order so it works
  // in every locale (scene ids are English slugs, headings are translated).
  const headedIdx = simple.map((s, i) => (s.heading ? i : -1)).filter((i) => i >= 0);
  const target = headedIdx.slice(Math.max(0, headedIdx.length - scenes.length));
  const sceneFor = new Map<number, any>();
  target.forEach((idx, k) => { if (scenes[k]) sceneFor.set(idx, scenes[k]); });

  return simple.map((s, i) => {
    const r = rich[i] ?? s;
    const sc = sceneFor.get(i);
    const sol = s.heading ? puzzMap.get(normHeading(s.heading)) : null;
    return {
      heading: s.heading,
      simpleHtml: md2(s.body),
      richHtml: md2(r.body),
      sceneUrl: sc ? mediaUrl(sc.path) : null,
      sceneSrcset: sc ? mediaSrcset(sc.path) : undefined,
      sceneAlt: sc?.alt?.[locale] ?? "",
      solutionHtml: sol ? md2(sol) : null,
    };
  });
}

// the first body paragraph of a markdown file (skips headings and *italic* lines):
// used as a localized, unique meta description for a story
export function firstParagraph(relPath?: string | null): string {
  const md = readText(relPath);
  if (!md) return "";
  for (const para of md.split(/\n\s*\n/)) {
    const line = para.trim();
    if (!line || line.startsWith("#") || line.startsWith("*") || line.startsWith("|")) continue;
    return line.replace(/\n/g, " ");
  }
  return "";
}
