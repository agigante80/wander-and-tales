"""Command line: python -m build {validate,lint,catalog,render,render-guide,prompts,generate-images}."""

import argparse
import os
import sys
from pathlib import Path

from build import catalog, content, lint


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=Path("."), help="repo root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_root(sub.add_parser("validate", help="load and validate all content"))
    _add_root(sub.add_parser("lint", help="run structural lint"))
    catalog_parser = sub.add_parser("catalog", help="generate catalog.md")
    _add_root(catalog_parser)
    catalog_parser.add_argument("--out", type=Path, default=Path("catalog.md"))

    render_parser = sub.add_parser("render", help="build a kit PDF")
    _add_root(render_parser)
    render_parser.add_argument("--world", required=True)
    render_parser.add_argument("--story", required=True)
    render_parser.add_argument("--locale", required=True)
    render_parser.add_argument("--reading-level", required=True,
                               choices=("simple", "rich"))
    render_parser.add_argument("--out-dir", type=Path, default=None)

    guide_parser = sub.add_parser("render-guide", help="build the Guide PDF")
    _add_root(guide_parser)
    guide_parser.add_argument("--locale", required=True)
    guide_parser.add_argument("--out-dir", type=Path, default=None)

    prompts_parser = sub.add_parser("prompts", help="export image generation prompts")
    _add_root(prompts_parser)
    prompts_parser.add_argument("--world", default=None)
    prompts_parser.add_argument("--story", default=None)
    prompts_parser.add_argument("--out", type=Path, default=None)

    generate_parser = sub.add_parser("generate-images", help="generate image files")
    _add_root(generate_parser)
    generate_parser.add_argument("--world", default=None)
    generate_parser.add_argument("--story", default=None)
    generate_parser.add_argument("--force", action="store_true")

    args = parser.parse_args(argv)

    if args.command == "validate":
        stories = list(content.iter_stories(args.root / "worlds"))
        print(f"OK: validated {len(stories)} story file(s)")
        return 0

    if args.command == "lint":
        issues = lint.lint_repo(args.root)
        for issue in issues:
            print(f"[{issue.level}] {issue.message} ({issue.location})")
        errors = [i for i in issues if i.level == "error"]
        if errors:
            print(f"{len(errors)} error(s)")
            return 1
        print("lint clean")
        return 0

    if args.command == "catalog":
        stories = list(content.iter_stories(args.root / "worlds"))
        catalog.write_catalog(stories, args.out)
        print(f"wrote {args.out}")
        return 0

    if args.command == "render":
        from build.render import kit

        out = kit.build_kit(
            args.root, args.world, args.story, args.locale, args.reading_level,
            out_dir=args.out_dir,
        )
        print(f"built {out}")
        return 0

    if args.command == "render-guide":
        from build.render import pages, version as ver
        from build.render.colophon import PROJECT_URL

        src = args.root / "guide" / args.locale / "guide.md"
        if not src.is_file():
            print(f"no guide markdown at {src}")
            return 1
        out_dir = args.out_dir if args.out_dir is not None else args.root / "dist"
        vi = ver.version_info(args.root, ver.guide_inputs(args.root, args.locale))
        out = out_dir / "guides" / f"Guide_for_the_Grown-Up_{args.locale}-{vi.label}.pdf"
        qr = f"{PROJECT_URL}/tree/main/kits/guides"
        pages.render_guide(src, out, args.locale, version=vi, qr_url=qr)
        print(f"built {out}")
        return 0

    if args.command == "prompts":
        from build import prompts as prompts_mod

        entries = prompts_mod.iter_image_prompts(
            args.root, world=args.world, story=args.story
        )
        if args.out is not None:
            prompts_mod.write_prompts(entries, args.out)
            print(f"wrote {args.out}")
        else:
            print(prompts_mod.build_prompts_markdown(entries))
        return 0

    if args.command == "generate-images":
        try:
            from dotenv import load_dotenv

            load_dotenv(args.root / ".env")
        except ImportError:
            pass

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print(
                "OPENAI_API_KEY is not set. Put it in .env (see .env.example) "
                "or export it, then retry."
            )
            return 1

        from build import generate

        client = generate.make_client(api_key)
        written = generate.generate_all(
            args.root, world=args.world, story=args.story,
            force=args.force, client=client,
        )
        for path in written:
            print(f"wrote {path}")
        print(f"{len(written)} image(s) written")
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
