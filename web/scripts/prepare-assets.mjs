// Prepare the assets the site serves, from the content repo (one level up), into
// web/public. Run as the prebuild step. Outputs are gitignored.
//
//  - world and story illustrations: ../worlds/**/assets/*.png
//      -> public/media/worlds/.../x.webp        (default, ~1200px longest side; og/fallback)
//      -> public/media/worlds/.../x-<W>.webp    (responsive widths for srcset)
//  - trail maps: ../maps/**/map-<locale>.png    -> public/maps/.../map-<locale>{,-<W>}.webp
//  - brand fonts: ../build/assets/fonts/*.ttf   -> public/fonts/*.ttf
//  - published kits (PDFs): ../kits/**          -> public/kits/**
//
// The source art is full-resolution PNG (covers 1024x1536, scenes 1536x1024, up to
// ~4 MB each) but is shown at 116 to 700 px. We resize to a default plus a few widths
// and convert to WebP; content.ts emits a srcset from the variants so the browser
// downloads only the size it needs.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import sharp from "sharp";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, "../.."); // repo root
const PUB = path.resolve(HERE, "../public");

const WIDTHS = [320, 640, 960, 1280]; // responsive variants (only those <= native are made)

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

// Write a default WebP (fit inside 1200) plus exact-width variants for srcset.
// destBase is the output path without extension.
async function responsiveWebp(src, destBase, quality) {
  fs.mkdirSync(path.dirname(destBase), { recursive: true });
  const nativeWidth = (await sharp(src).metadata()).width ?? 0;
  await sharp(src)
    .resize({ width: 1200, height: 1200, fit: "inside", withoutEnlargement: true })
    .webp({ quality, effort: 4 })
    .toFile(`${destBase}.webp`);
  for (const w of WIDTHS) {
    if (w > nativeWidth) continue; // never upscale; keep srcset width descriptors honest
    await sharp(src).resize({ width: w }).webp({ quality, effort: 4 }).toFile(`${destBase}-${w}.webp`);
  }
}

async function runPool(tasks, limit = 8) {
  const queue = [...tasks];
  const workers = Array.from({ length: limit }, async () => {
    while (queue.length) await queue.shift()();
  });
  await Promise.all(workers);
}

// 1) world + story images
let imageCount = 0;
const worldsDir = path.join(ROOT, "worlds");
const imageTasks = [];
walk(worldsDir, (file) => {
  if (file.endsWith(".png") && path.basename(path.dirname(file)) === "assets") {
    const relNoExt = path.relative(ROOT, file).replace(/\.png$/, ""); // worlds/.../assets/x
    imageTasks.push(() => responsiveWebp(file, path.join(PUB, "media", relNoExt), 72));
    imageCount++;
  }
});

// 2) trail maps (text on them, so a touch more quality)
let mapCount = 0;
const mapsDir = path.join(ROOT, "maps");
const mapTasks = [];
if (fs.existsSync(mapsDir)) {
  walk(mapsDir, (file) => {
    if (file.endsWith(".png")) {
      const relNoExt = path.relative(mapsDir, file).replace(/\.png$/, "");
      mapTasks.push(() => responsiveWebp(file, path.join(PUB, "maps", relNoExt), 82));
      mapCount++;
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

// 4) the published kits (PDFs)
let pdfs = 0;
const kitsDir = path.join(ROOT, "kits");
if (fs.existsSync(kitsDir)) {
  fs.cpSync(kitsDir, path.join(PUB, "kits"), { recursive: true });
  walk(path.join(PUB, "kits"), (f) => {
    if (f.endsWith(".pdf")) pdfs++;
  });
}

console.log(`prepare-assets: ${imageCount} images and ${mapCount} maps to responsive WebP, ${fonts} fonts, ${pdfs} PDFs into web/public`);
