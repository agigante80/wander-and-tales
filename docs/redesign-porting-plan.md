# Wander & Tales website redesign: porting plan

Plan for porting the Claude Design handoff (a mobile-first, light/dark redesign)
into the existing Astro + Tailwind site under `web/`.

The handoff bundle (`design_handoff_wander_and_tales/`: five HTML prototypes plus
`tokens.css`, `components.css`, `app.js`, `brand-icon.svg`) lives under `temp/`,
which is gitignored. It is a high-fidelity reference, not code to ship verbatim:
recreate each screen as Astro components using our own patterns, and port the
tokens into Tailwind v4 `@theme`.

## Decisions baked into this plan

- **Style guide: soft-private route.** Build it as a real Astro route from the
  live tokens (so it never drifts), but keep it out of search and the audience's
  way: `noindex`, `robots` disallow, and not in the nav, the sitemap, or the
  hreflang set. Reachable only by direct URL. It is one non-localized route (design,
  not content), which sidesteps the four-locale model.
- **Theme toggle: responsive placement.** Header top-right (next to the language
  switcher) on desktop where there is room; on mobile (under 860px) it moves into
  the nav sheet alongside the language switcher, so the 60px bar at 390px stays
  uncluttered. Behaviour (persist, no-flash, OS sync) is identical either way.

## 1. Screen and file mapping

| Prototype | Target Astro file | Notes |
|---|---|---|
| `index.html` | `web/src/pages/[lang]/index.astro` | Hero (How to play + Explore the worlds), the stat row, worlds grid via `WorldCard.astro`, the "Create your own" panel and feature card. |
| `story.html` (flagship) | `web/src/pages/[lang]/worlds/[world]/[story].astro` | Sticky reading-level segmented toggle, drop-cap, Caveat beat labels, the "tricky bit" callout, the `<details>` spoiler, pictures grid, trail map, `.btn-dl` downloads. Highest effort; do it carefully. |
| `world.html` | `web/src/pages/[lang]/worlds/[world]/index.astro` | World hero, story cards (featured plus rest), Example heroes (the energy meter is new), the who-is-who glossary, world downloads. |
| `how-to-play.html` | `web/src/pages/[lang]/how-to-play.astro` | Three numbered step cards, the promise callout, the one-page PDF `.btn-dl`, the onward link card to the Guide. Exists already; restyle it. |
| `styleguide.html` | `web/src/pages/styleguide.astro` (new, soft-private) | Not under `[lang]`. Living token and component reference built from the real tokens. See section 5. |
| (no prototype) | `help.astro` (Guide), `why.astro`, `create.astro`, `privacy.astro`, `legal.astro`, `terms.astro`, `404.astro` | Not designed, but they inherit the new chrome and tokens. Map each to the nearest prototype pattern: Guide and Why use the reader prose (`.prose-tale` with `--measure`); Create reuses the home "Create your own" panel; the legal trio and 404 use simple `.wrap-read` prose. |

## 2. Tokens, styles, assets

| Prototype | Target | Action |
|---|---|---|
| `assets/tokens.css` | `web/src/styles/global.css` | Replace the current `@theme` block. Keep the brand hexes as fixed `@theme`; put the light and dark semantic vars in `:root` and `:root[data-theme="dark"]`. Drop the Google Fonts `@import` and keep our self-hosted TTF `@font-face` rules (Quicksand, Nunito, Caveat already vendored under `/fonts`). |
| `assets/components.css` | `web/src/styles/global.css` plus component-scoped styles | Lift the component classes (`.btn`, `.card`, `.chip`, `.seg`, `.spoiler`, `.btn-dl`, the reader type rules, the callouts). Use Tailwind utilities for the trivial ones; keep the complex ones as classes. |
| `assets/app.js` | inline `is:inline` scripts | Split by concern (section 3). Do not ship it as one file. |
| `assets/brand-icon.svg` | `web/public/` | Header lockup and favicon source. We already have a brand asset set; reconcile. |
| `--bg-grad`, shadows, radii, easing | `global.css` | Carry across verbatim; they are theme-aware. |

## 3. Behaviours (from `app.js`)

| Behaviour | Where it lands |
|---|---|
| No-flash theme init: read `localStorage['wt-theme']`, else `prefers-color-scheme`, set `data-theme` on `<html>` before paint | `is:inline` script in the `<head>` of `Base.astro`, before the stylesheet link. |
| Theme toggle: flip `data-theme`, persist, update `aria-pressed` and the `theme-color` meta, live-update on OS change until a manual choice is stored | new `ThemeToggle.astro`, placed responsively (section 4). |
| Reading-level toggle: segmented control sets `data-level` on the reader root; CSS swaps `data-when="simple|rich"` blocks and the type metrics; persist `localStorage['wt-level']`, restore on load | `[story].astro` plus a small `is:inline` script. Our content already has both levels; render both into one DOM tagged `data-when`. |
| Spoiler | native `<details>`, no JS (already our pattern). |
| Mobile nav sheet and language popover | `Header.astro`; `LangSwitcher.astro` gains the popover behaviour and keeps routing to real locales. |

## 4. Theme toggle (responsive) detail

- `ThemeToggle.astro`: a 44x44px icon button, sun in light and moon in dark,
  `aria-pressed` reflecting dark, `aria-label` flipping between "Switch to dark
  mode" and "Switch to light mode".
- **Desktop (>= 860px):** render it in the header right-hand tools, next to the
  language switcher.
- **Mobile (< 860px):** hide the header instance; render a labelled row ("Theme")
  inside the mobile nav sheet, above or beside the language options. One component,
  two mount points, CSS shows the right one per breakpoint.
- The no-flash init script and the `theme-color` meta swap are independent of
  placement and live in `Base.astro`.

## 5. Style guide (soft-private) detail

- File: `web/src/pages/styleguide.astro` (single route, not localized, not under
  `[lang]`).
- Built from the live `global.css` tokens so it always reflects what is deployed:
  swatch grids of the light and dark values, the type scale, spacing, radius and
  shadow samples, and live components (buttons, chips, the segmented toggle, the
  promise callout, the spoiler, the download affordance), plus the theme toggle so
  a reviewer can flip and see the retune.
- Keep it out of sight: add `<meta name="robots" content="noindex, nofollow">` on
  this page only, add a `Disallow: /styleguide` line to `public/robots.txt`, and do
  **not** add it to `Header.astro`, `Footer.astro`, `sitemap.xml.ts`, or the
  hreflang alternates. Reachable only by typing the URL.

## 6. Phased order (the site stays shippable at each step)

1. **Foundation:** tokens into `global.css`, fonts self-hosted, `ThemeToggle` plus
   the no-flash script in `Base.astro`, restyle `Header.astro` and `Footer.astro`
   (responsive toggle placement). The whole site re-themes at once.
2. **Story reader:** `[story].astro`, including the reading-level swap.
3. **Home, World, How-to-Play:** `index.astro`, `[world]/index.astro`,
   `how-to-play.astro`, `WorldCard.astro`.
4. **Inherited pages and the style guide:** Guide, Why, Create, legal trio, 404
   adopt the patterns; add the soft-private `styleguide.astro`.

## 7. Hard constraints to preserve while porting

- **Do not touch the SEO head contract** in `Base.astro`: unique title and
  description, hreflang plus x-default, og:locale plus alternates, per-page
  og:image, JSON-LD. Add only the `theme-color` swap and the no-flash script.
- **i18n:** every new string (the hero stat row, the footer groups, the step
  labels, the "Adult-led" badge, the chip labels, the theme and reading-level
  control labels) goes through `i18n.ts` in en, es, it, and pt. No hardcoded
  English.
- **Self-hosted PDFs plus manifest:** keep `.btn-dl` reading the version from the
  manifest; stable unversioned URLs; no GitHub release links.
- **Cookieless:** no cookie or consent banner; the analytics beacon stays as is.
- **No em or en dashes** in any copy or file (a hook blocks writes that contain
  one). Number ranges as "3 to 12".
- **Imagery:** the prototype frames are placeholders; real coloured-pencil art
  drops into the same rounded frames at the same aspect ratios (16/10 default,
  21/9 wide, 4/5 tall, 1/1 square).

## 8. Open or deferred

- Reconcile the prototype's archipelago `brand-icon.svg` with the existing favicon
  and brand asset set (pick one source of truth).
- The Example heroes "energy meter" and the richer footer (three link groups plus
  the Caveat promise line) are new UI; confirm copy in all four locales.
- The prototype uses demo world and story names ("The Mossfern Wood", "The House
  That Went Wandering"); ignore them, our real content stays.
