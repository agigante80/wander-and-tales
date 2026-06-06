"""Generate a machine-readable site content manifest from the repo content.

Walks every world and story, reads the YAML metadata, the narration beat headings,
the on-disk artwork, and the current versioned PDFs in kits/, and emits one JSON the
website builder can ingest directly. Re-run any time the content changes.
"""
import json
import glob
import pathlib
import re
import sys

import yaml

from build.locales import REQUIRED_LOCALES, CANONICAL_LOCALE
from build.render import strings
from build.render.library import _LANG_NAME, _LEVEL_LABELS

ROOT = pathlib.Path(".")
GENERATED_AT = "2026-06-06"
REPO = "https://github.com/agigante80/wander-and-tales"
RAW_BASE = "https://raw.githubusercontent.com/agigante80/wander-and-tales/main/"


def load_yaml(p):
    return yaml.safe_load(pathlib.Path(p).read_text(encoding="utf-8"))


def rel(p):
    """Repo-relative posix path, or None if the file is absent."""
    p = pathlib.Path(p)
    return p.as_posix() if p.is_file() else None


def beats(world, story, locale):
    """The ## headings of the simple narration, in order (the story's beats)."""
    f = ROOT / "worlds" / world / "stories" / story / "content" / locale / "narration.simple.md"
    if not f.is_file():
        return []
    out = []
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            out.append(line[3:].strip())
    return out


def first_pdf(pattern):
    hits = sorted(glob.glob(pattern))
    return pathlib.Path(hits[0]).as_posix() if hits else None


def image_entry(base_dir, img):
    """Normalise a YAML image entry into the manifest shape (path if the PNG exists)."""
    iid = img["id"]
    return {
        "id": iid,
        "role": img.get("role"),
        "orientation": img.get("orientation"),
        "canon_ref": img.get("canon_ref"),
        "path": rel(base_dir / "assets" / f"{iid}.png"),
        "alt": img.get("alt", {}),
    }


def world_pdfs(world):
    out = {}
    for loc in REQUIRED_LOCALES:
        d = f"kits/{loc}/{world}"
        out[loc] = {
            "world_book": first_pdf(f"{d}/*-world-book-{loc}-*.pdf"),
            "example_heroes": first_pdf(f"{d}/*-example-heroes-{loc}-*.pdf"),
        }
    return out


def story_pdfs(world, story):
    out = {}
    for loc in REQUIRED_LOCALES:
        d = f"kits/{loc}/{world}/{story}"
        out[loc] = {
            "tale_simple": first_pdf(f"{d}/*-tale-book-simple-{loc}-*.pdf"),
            "tale_rich": first_pdf(f"{d}/*-tale-book-rich-{loc}-*.pdf"),
            "atlas": first_pdf(f"{d}/*-atlas-{loc}-*.pdf"),
        }
    return out


def build_world(world_dir):
    wid = world_dir.name
    wy = load_yaml(world_dir / "world.yaml")

    # canon: id -> entry, with a world-level portrait path if one points at it
    portrait = {}
    world_images = []
    for img in wy.get("images", []):
        e = image_entry(world_dir, img)
        world_images.append(e)
        if e["canon_ref"]:
            portrait[e["canon_ref"]] = e["path"]

    canon = []
    for cf in sorted((world_dir / "canon").glob("*.yaml")):
        for row in load_yaml(cf) or []:
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
        for h in load_yaml(hf) or []:
            heroes.append({
                "id": h["id"],
                "tier": h.get("tier"),
                "name": h.get("name"),
                "hero_of": h.get("hero_of", {}),
                "magics": h.get("magics", []),
                "energy": h.get("energy"),
                "carry": h.get("carry", []),
                "image_path": rel(world_dir / "assets" / f"{h['image']['id']}.png") if h.get("image") else None,
            })

    stories = []
    for sy_path in sorted(world_dir.glob("stories/*/story.yaml")):
        sdir = sy_path.parent
        sid = sdir.name
        sy = load_yaml(sy_path)
        images = [image_entry(sdir, img) for img in sy.get("images", [])]
        content_paths = {}
        for loc in REQUIRED_LOCALES:
            cdir = sdir / "content" / loc
            content_paths[loc] = {
                kind: rel(cdir / f"{fname}")
                for kind, fname in (
                    ("simple", "narration.simple.md"),
                    ("rich", "narration.rich.md"),
                    ("rules", "rules.md"),
                    ("puzzles", "puzzles.md"),
                )
            }
        svg = sdir / "assets" / "map.svg"
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
            "beats": {loc: beats(wid, sid, loc) for loc in REQUIRED_LOCALES},
            "content_paths": content_paths,
            "images": images,
            "map": {"type": "svg", "path": rel(svg)} if svg.is_file() else {"type": "generated"},
            "pdfs": story_pdfs(wid, sid),
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
        "pdfs": world_pdfs(wid),
        "stories": stories,
    }


def main():
    worlds = [build_world(w.parent) for w in sorted(ROOT.glob("worlds/*/world.yaml"))]

    shared_pdfs = {}
    for loc in REQUIRED_LOCALES:
        shared_pdfs[loc] = {
            "guide": first_pdf(f"kits/guides/Guide_for_the_Grown-Up_{loc}-*.pdf"),
            "how_to_play": first_pdf(f"kits/guides/How_to_Play_{loc}-*.pdf"),
        }

    manifest = {
        "site": {
            "name": "Wander and Tales",
            "tagline": {loc: strings.UI[loc]["tagline"] for loc in REQUIRED_LOCALES},
            "domain": "wanderandtales.com",
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
            "analytics": {"provider": "google", "measurement_id": "G-XXXXXXXXXX", "note": "placeholder; the owner will supply the real Measurement ID later"},
            "cookie_consent": {"required": True, "reason": "EU and UK visitors; analytics consent"},
            "contact": {"type": "github_issues", "url": f"{REPO}/issues", "note": "no email; use GitHub issues for contact and takedown requests"},
            "community": None,
            "disclaimers": [
                "Not affiliated with, or endorsed by, Anthropic. 'Claude' is referenced only as the tool used to author stories.",
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
            "generated_at": GENERATED_AT,
            "note": "Story text lives in the content_paths markdown files (kid-facing narration.simple and narration.rich); render those for the online reader. rules.md and puzzles.md are grown-up-only.",
        },
        "worlds": worlds,
    }

    out = ROOT / "site" / "manifest.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    # quick integrity report to stderr
    missing_img = sum(1 for w in worlds for s in w["stories"] for i in s["images"] if not i["path"])
    missing_pdf = sum(
        1 for w in worlds for s in w["stories"] for loc in REQUIRED_LOCALES
        for v in s["pdfs"][loc].values() if not v
    )
    print(f"wrote {out}  worlds={len(worlds)} stories={manifest['site']['counts']['stories']} "
          f"missing_story_images={missing_img} missing_story_pdfs={missing_pdf}", file=sys.stderr)


if __name__ == "__main__":
    main()
