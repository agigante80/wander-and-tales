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

// download URL for a kit PDF (served from GitHub raw for now; self-host later)
export const pdfUrl = (relPath?: string | null) =>
  relPath ? site.repo_raw_base + relPath : null;

// render narration markdown to HTML, dropping the leading "# Title" (we render our own)
export function narrationHtml(relPath?: string | null): string {
  if (!relPath) return "";
  const md = readText(relPath);
  if (!md) return "";
  const body = md.replace(/^#\s+.*$/m, "").trim();
  return marked.parse(body, { gfm: true, async: false }) as string;
}
