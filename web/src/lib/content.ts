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

// public URL for a manifest image path ("worlds/.../assets/x.png")
export const mediaUrl = (relPath?: string | null) =>
  relPath ? "/media/" + relPath : null;

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

// render a markdown file to HTML as-is (keeps its heading); used for the grown-up
// rules and puzzles sections
export function mdHtml(relPath?: string | null): string {
  if (!relPath) return "";
  const md = readText(relPath);
  return md ? (marked.parse(md, { gfm: true, async: false }) as string) : "";
}
