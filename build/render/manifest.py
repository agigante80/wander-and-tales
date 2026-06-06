"""Generate the machine-readable site content manifest (site/manifest.json).

A snapshot of the whole library for a website to ingest: every world and story with
titles, tags, lore, beat headings, image paths, and PDF links, in every required
locale. PDF filenames carry no version (stable URLs); each PDF entry instead records
its git-derived version and date, so the site can show it. Derived data, regenerated
on every `build rebuild` (and via `python -m build manifest`), so it never drifts from
the content. Not a render source, so writing it does not bump any PDF version.
"""
from __future__ import annotations

import datetime
import glob
import json
from pathlib import Path

import yaml

from build.locales import CANONICAL_LOCALE, REQUIRED_LOCALES
from build.render import strings
from build.render import version as ver
from build.render.library import _LANG_NAME, _LEVEL_LABELS

REPO = "https://github.com/agigante80/wander-and-tales"
RAW_BASE = "https://raw.githubusercontent.com/agigante80/wander-and-tales/main/"


def _load(p: Path):
    return yaml.safe_load(p.read_text(encoding="utf-8"))


def _rel(root: Path, p: Path) -> str | None:
    """Root-relative posix path, or None when the file is absent."""
    return p.relative_to(root).as_posix() if p.is_file() else None


def _beats(content_dir: Path) -> list[str]:
    """The ## headings of the simple narration, in order (the story's beats)."""
    f = content_dir / "narration.simple.md"
    if not f.is_file():
        return []
    return [line[3:].strip() for line in f.read_text(encoding="utf-8").splitlines()
            if line.startswith("## ")]


def _first_pdf(root: Path, pattern: str) -> str | None:
    hits = sorted(glob.glob(pattern))
    return Path(hits[0]).relative_to(root).as_posix() if hits else None


def _pdf(root: Path, path: str | None, content_inputs: list) -> dict | None:
    """A PDF entry: its root-relative path plus the git-derived version and date.

    Filenames carry no version (stable URLs), so the version travels here instead and
    in the PDF colophon. Recomputed from git, deterministically matching the build.
    """
    if not path:
        return None
    vi = ver.version_info(root, content_inputs, ver.render_sources(root))
    return {"path": path, "version": vi.label, "updated": vi.updated}


def _image(root: Path, base: Path, img: dict) -> dict:
    iid = img["id"]
    return {
        "id": iid,
        "role": img.get("role"),
        "orientation": img.get("orientation"),
        "canon_ref": img.get("canon_ref"),
        "path": _rel(root, base / "assets" / f"{iid}.png"),
        "alt": img.get("alt", {}),
    }


def _world(root: Path, out_dir: Path, world_dir: Path) -> dict:
    wid = world_dir.name
    wy = _load(world_dir / "world.yaml")

    portrait: dict[str, str | None] = {}
    world_images = []
    for img in wy.get("images", []):
        e = _image(root, world_dir, img)
        world_images.append(e)
        if e["canon_ref"]:
            portrait[e["canon_ref"]] = e["path"]

    canon = []
    for cf in sorted((world_dir / "canon").glob("*.yaml")):
        for row in _load(cf) or []:
            canon.append({
                "id": row["id"],
                "kind": row.get("kind"),
                "disposition": row.get("disposition"),
                "names": row.get("names", {}),
                "description": row.get("description", {}),
                "image_path": portrait.get(row["id"]),
            })

    heroes = []
    hf = world_dir / "heroes.yaml"
    if hf.is_file():
        for h in _load(hf) or []:
            img = h.get("image")
            heroes.append({
                "id": h["id"],
                "tier": h.get("tier"),
                "name": h.get("name"),
                "hero_of": h.get("hero_of", {}),
                "magics": h.get("magics", []),
                "energy": h.get("energy"),
                "carry": h.get("carry", []),
                "image_path": _rel(root, world_dir / "assets" / f"{img['id']}.png") if img else None,
            })

    def world_pdfs() -> dict:
        out = {}
        for loc in REQUIRED_LOCALES:
            d = str(out_dir / loc / wid)
            out[loc] = {
                "world_book": _pdf(
                    root, _first_pdf(root, f"{d}/*-world-book-{loc}.pdf"),
                    ver.world_book_inputs(root, wid, loc),
                ),
                "example_heroes": _pdf(
                    root, _first_pdf(root, f"{d}/*-example-heroes-{loc}.pdf"),
                    ver.example_heroes_inputs(root, wid, loc),
                ),
            }
        return out

    stories = []
    for sy_path in sorted(world_dir.glob("stories/*/story.yaml")):
        sdir = sy_path.parent
        sid = sdir.name
        sy = _load(sy_path)
        content_paths = {}
        beats = {}
        for loc in REQUIRED_LOCALES:
            cdir = sdir / "content" / loc
            content_paths[loc] = {
                "simple": _rel(root, cdir / "narration.simple.md"),
                "rich": _rel(root, cdir / "narration.rich.md"),
                "rules": _rel(root, cdir / "rules.md"),
                "puzzles": _rel(root, cdir / "puzzles.md"),
            }
            beats[loc] = _beats(cdir)
        svg = sdir / "assets" / "map.svg"
        story_pdfs = {}
        for loc in REQUIRED_LOCALES:
            d = str(out_dir / loc / wid / sid)
            story_pdfs[loc] = {
                "tale_simple": _pdf(
                    root, _first_pdf(root, f"{d}/*-tale-book-simple-{loc}.pdf"),
                    ver.tale_book_inputs(root, wid, sid, loc, "simple"),
                ),
                "tale_rich": _pdf(
                    root, _first_pdf(root, f"{d}/*-tale-book-rich-{loc}.pdf"),
                    ver.tale_book_inputs(root, wid, sid, loc, "rich"),
                ),
                "atlas": _pdf(
                    root, _first_pdf(root, f"{d}/*-atlas-{loc}.pdf"),
                    ver.atlas_inputs(root, wid, sid, loc),
                ),
            }
        stories.append({
            "id": sid,
            "slug": sid,
            "title": sy.get("title", {}),
            "tags": {
                "age_recommended": sy.get("age", {}).get("recommended"),
                "age_also_works_for": sy.get("age", {}).get("also_works_for", []),
                "skills": sy.get("skills", []),
                "peril": sy.get("peril"),
                "players": sy.get("players", {}),
                "play_time_minutes": sy.get("play_time_minutes"),
                "adult_gm": sy.get("adult_gm"),
                "dice": sy.get("dice", {}),
            },
            "beats": beats,
            "content_paths": content_paths,
            "images": [_image(root, sdir, img) for img in sy.get("images", [])],
            "map": {"type": "svg", "path": _rel(root, svg)} if svg.is_file() else {"type": "generated"},
            "pdfs": story_pdfs,
        })

    return {
        "id": wid,
        "slug": wid,
        "name": wy.get("name", {}),
        "tone": wy.get("tone"),
        "hero_powers": wy.get("hero_powers", "magic"),
        "palette": wy.get("palette", []),
        "font_default": (wy.get("fonts") or {}).get("default"),
        "lore": wy.get("lore_summary", {}),
        "visual_style": wy.get("visual_style"),
        "images": world_images,
        "canon": canon,
        "heroes": heroes,
        "pdfs": world_pdfs(),
        "stories": stories,
    }


def build_manifest(root: Path, out_dir: Path, manifest_path: Path | None = None) -> Path:
    """Write site/manifest.json from the content tree and the built kits in out_dir."""
    root = root.resolve()
    out_dir = out_dir if out_dir.is_absolute() else root / out_dir
    worlds = [_world(root, out_dir, w.parent) for w in sorted(root.glob("worlds/*/world.yaml"))]

    shared_pdfs = {}
    for loc in REQUIRED_LOCALES:
        g = str(out_dir / "guides")
        guide_inputs = ver.guide_inputs(root, loc)  # the How to Play shares the guide version
        shared_pdfs[loc] = {
            "guide": _pdf(root, _first_pdf(root, f"{g}/Guide_for_the_Grown-Up_{loc}.pdf"), guide_inputs),
            "how_to_play": _pdf(root, _first_pdf(root, f"{g}/How_to_Play_{loc}.pdf"), guide_inputs),
        }

    manifest = {
        "site": {
            "name": "Wander and Tales",
            "tagline": {loc: strings.UI[loc]["tagline"] for loc in REQUIRED_LOCALES},
            "domain": "www.wanderandtales.com",
            "repo": REPO,
            "repo_raw_base": RAW_BASE,
            "default_language": CANONICAL_LOCALE,
            "languages": [
                {"code": loc, "endonym": _LANG_NAME.get(loc, loc), "default": loc == CANONICAL_LOCALE}
                for loc in REQUIRED_LOCALES
            ],
            "level_labels": {loc: _LEVEL_LABELS.get(loc, _LEVEL_LABELS[CANONICAL_LOCALE]) for loc in REQUIRED_LOCALES},
            "license": {
                "content": {
                    "code": "CC BY-SA 4.0",
                    "url": "https://creativecommons.org/licenses/by-sa/4.0/",
                    "covers": "worlds/, guide/, lexicon/, the kits/ PDFs, translations, and generated maps",
                    "attribution": "Wander and Tales (github.com/agigante80/wander-and-tales)",
                },
                "code": {"code": "MIT", "url": f"{REPO}/blob/main/LICENSE"},
                "ai_illustrations": "Illustrations are AI-generated from text prompts, offered under CC BY-SA 4.0 to the extent protectable; AI images may not be eligible for copyright in some jurisdictions.",
                "fonts": "Bundled fonts keep their own licences (DejaVu Fonts Licence and SIL Open Font Licence 1.1); see build/assets/fonts/OFL-NOTICE.txt.",
            },
            "analytics": {"provider": None, "note": "to be configured; cookieless analytics avoids a consent banner"},
            "cookie_consent": {"required": False, "note": "no banner needed if analytics stays cookieless; revisit if a cookie-setting tool is added"},
            "contact": {"type": "github_issues", "url": f"{REPO}/issues", "note": "general contact; a private channel is needed for GDPR rights and takedown requests"},
            "community": None,
            "disclaimers": [
                "Not affiliated with, or endorsed by, Anthropic.",
                "Cooperative, no-lose games: nobody competes, nobody is eliminated, and there are no wrong answers.",
            ],
            "create_your_own": {
                "headline": "Create your own stories with Claude",
                "summary": "Open the project in Claude Code and ask to create a story: a guided skill interviews you, writes it in every language, and builds your printable PDFs. No coding needed.",
                "cta_url": f"{REPO}#create-your-own-story",
                "requires": ["Claude Code", "Python 3.11+"],
                "optional": "Image generation uses your own OpenAI key.",
            },
            "ui_strings_source": "build/render/strings.py (per-locale UI labels)",
            "shared_pdfs": shared_pdfs,
            "counts": {"worlds": len(worlds), "stories": sum(len(w["stories"]) for w in worlds), "languages": len(REQUIRED_LOCALES)},
            "generated_at": datetime.date.today().isoformat(),
            "note": "Story text lives in the content_paths markdown files (kid-facing narration.simple and narration.rich); render those for the online reader. rules.md and puzzles.md are grown-up-only.",
        },
        "worlds": worlds,
    }

    out = manifest_path or (root / "site" / "manifest.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out
