// Prepare the assets the site serves, from the content repo (one level up), into
// web/public. Run as the prebuild step. Outputs are gitignored.
//
//  - world and story illustrations: ../worlds/**/assets/*.png  ->  resized WebP at
//    public/media/worlds/.../*.webp  (the manifest image "path" is "worlds/.../x.png",
//    so the public URL is "/media/" + path with the extension swapped to .webp)
//  - trail maps: ../maps/**/map-<locale>.png  ->  resized WebP at public/maps/.../*.webp
//  - brand fonts: ../build/assets/fonts/*.ttf  ->  public/fonts/*.ttf (self-hosted)
//  - published kits (PDFs): ../kits/**  ->  public/kits/**
//
// The source art is full-resolution PNG (covers 1024x1536, scenes 1536x1024, up to
// ~4 MB each). Serving that for 116-700px displays is wasteful, so we resize to a
// sensible max and convert to WebP, which cuts each image by roughly 20x.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../.."); // repo root
const PUB = path.resolve(HERE, "../public");

function copy(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function walk(dir, onFile) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, entry.name);
    if (entry.isDirectory()) walk(p, onFile);
    else onFile(p);
  }
}

async function toWebp(src, dest, { maxSide = 1200, quality = 72 } = {}) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  await sharp(src)
    .resize({ width: maxSide, height: maxSide, fit: "inside", withoutEnlargement: true })
    .webp({ quality, effort: 4 })
    .toFile(dest);
}

// run async tasks with a small concurrency cap (sharp is heavy)
async function runPool(tasks, limit = 8) {
  const queue = [...tasks];
  const workers = Array.from({ length: limit }, async () => {
    while (queue.length) await queue.shift()();
  });
  await Promise.all(workers);
}

// 1) world + story images -> resized WebP
const imageTasks = [];
const worldsDir = path.join(ROOT, "worlds");
walk(worldsDir, (file) => {
  if (file.endsWith(".png") && path.basename(path.dirname(file)) === "assets") {
    const rel = path.relative(ROOT, file).replace(/\.png$/, ".webp"); // worlds/.../assets/x.webp
    imageTasks.push(() => toWebp(file, path.join(PUB, "media", rel), { maxSide: 1200, quality: 72 }));
  }
});

// 2) trail maps -> resized WebP (text on the map, so a touch more quality)
const mapTasks = [];
const mapsDir = path.join(ROOT, "maps");
if (fs.existsSync(mapsDir)) {
  walk(mapsDir, (file) => {
    if (file.endsWith(".png")) {
      const rel = path.relative(mapsDir, file).replace(/\.png$/, ".webp");
      mapTasks.push(() => toWebp(file, path.join(PUB, "maps", rel), { maxSide: 1200, quality: 82 }));
    }
  });
}

await runPool([...imageTasks, ...mapTasks]);

// 3) brand fonts
let fonts = 0;
const fontDir = path.join(ROOT, "build", "assets", "fonts");
for (const f of ["Quicksand-SemiBold.ttf", "Nunito-Regular.ttf", "Nunito-Bold.ttf", "Caveat-SemiBold.ttf"]) {
  const src = path.join(fontDir, f);
  if (fs.existsSync(src)) {
    copy(src, path.join(PUB, "fonts", f));
    fonts++;
  }
}

// 4) the published kits (PDFs), self-hosted at /kits/...
let pdfs = 0;
const kitsDir = path.join(ROOT, "kits");
if (fs.existsSync(kitsDir)) {
  fs.cpSync(kitsDir, path.join(PUB, "kits"), { recursive: true });
  walk(path.join(PUB, "kits"), (f) => {
    if (f.endsWith(".pdf")) pdfs++;
  });
}

console.log(`prepare-assets: ${imageTasks.length} images and ${mapTasks.length} maps to WebP, ${fonts} fonts, ${pdfs} PDFs into web/public`);
