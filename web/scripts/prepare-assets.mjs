// Copy the assets the site serves from the content repo (one level up) into web/public.
// Run as the prebuild step. Outputs are gitignored (public/media, public/fonts).
//
//  - world and story illustrations: ../worlds/**/assets/*.png  ->  public/media/worlds/.../*.png
//    (the manifest image "path" is "worlds/.../assets/x.png", so the public URL is "/media/" + path)
//  - brand fonts: ../build/assets/fonts/*.ttf  ->  public/fonts/*.ttf  (self-hosted, no Google Fonts)
//
// PDFs are NOT copied; the site links them from GitHub raw (manifest repo_raw_base) for now.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

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

// 1) world + story images
let images = 0;
const worldsDir = path.join(ROOT, "worlds");
walk(worldsDir, (file) => {
  if (file.endsWith(".png") && path.basename(path.dirname(file)) === "assets") {
    const rel = path.relative(ROOT, file); // worlds/.../assets/x.png
    copy(file, path.join(PUB, "media", rel));
    images++;
  }
});

// 2) brand fonts
let fonts = 0;
const fontDir = path.join(ROOT, "build", "assets", "fonts");
for (const f of ["Quicksand-SemiBold.ttf", "Nunito-Regular.ttf", "Nunito-Bold.ttf", "Caveat-SemiBold.ttf"]) {
  const src = path.join(fontDir, f);
  if (fs.existsSync(src)) {
    copy(src, path.join(PUB, "fonts", f));
    fonts++;
  }
}

console.log(`prepare-assets: copied ${images} images and ${fonts} fonts into web/public`);
