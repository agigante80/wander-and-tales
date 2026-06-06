# Brand assets (favicons, app icons, OG)

The "floating archipelago at dusk" mark (designed in claude.design), finalized for
web. No letters or numbers inside the mark, so it works in any language.

## Files

| File | Use |
|---|---|
| `icon.svg` | Master mark, full-bleed square. Source of truth; scale to anything. |
| `icon-rounded.svg` | Same mark, pre-rounded into an iOS-style tile. |
| `favicon.svg` | Simplified one-island mark for browser tabs (the full archipelago turns to mush at 16px). |
| `favicon-16/32/48.png`, `favicon.ico` | Raster favicons / legacy. |
| `apple-touch-icon.png` (180) | iOS home screen. |
| `icon-192/512/1024.png` | Android / PWA / large display (full art). |
| `maskable-512.png`, `maskable.svg` | Android adaptive icon: full art padded into the safe zone so it is not clipped. |
| `icon-rounded-512/1024.png` | Pre-rounded raster tiles. |
| `og-image.png` (1200x630) | Social / Open Graph share card. |
| `site.webmanifest` | PWA manifest (icons + theme colours). |

The favicon is a simplified single island so it stays legible small; the rich
archipelago is used everywhere it has room (app icon, PWA, OG). The maskable is the
full art scaled to roughly 76 percent on the dusk gradient so the adaptive-icon crop
keeps the lower islands.

## Palette

```
Deep green  #25543c    Twilight top   #5b62a8    Gold (moons) #f2a93b
Mid green   #2f6f4f    Twilight base  #9a86c4    Cream        #f6f1e6
Leaf green  #4ea24a    Ampersand teal #2bb3a3
```

Sky is a vertical gradient `#5b62a8` (top) to `#9a86c4` (bottom).
`theme_color` = `#5b62a8`, `background_color` = `#f6f1e6`.

## Drop-in HTML head

```html
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#5b62a8">

<meta property="og:image" content="/og-image.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
```
