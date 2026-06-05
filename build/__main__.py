"""Command line: python -m build {validate,lint,render-tale-book,render-atlas,render-guide,render-world,render-examples,rebuild,prompts,generate-images}."""

import argparse
import os
import sys
from pathlib import Path

from build import content, lint


def _add_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=Path("."), help="repo root")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build")
    sub = parser.add_subparsers(dest="command", required=True)

    _add_root(sub.add_parser("validate", help="load and validate all content"))
    _add_root(sub.add_parser("lint", help="run structural lint"))

    tale_parser = sub.add_parser("render-tale-book", help="build a Tale Book PDF")
    _add_root(tale_parser)
    tale_parser.add_argument("--world", required=True)
    tale_parser.add_argument("--story", required=True)
    tale_parser.add_argument("--locale", required=True)
    tale_parser.add_argument("--reading-level", required=True,
                             choices=("simple", "rich"))
    tale_parser.add_argument("--out-dir", type=Path, default=None)

    atlas_parser = sub.add_parser("render-atlas", help="build an Atlas PDF")
    _add_root(atlas_parser)
    atlas_parser.add_argument("--world", required=True)
    atlas_parser.add_argument("--story", required=True)
    atlas_parser.add_argument("--locale", required=True)
    atlas_parser.add_argument("--out-dir", type=Path, default=None)

    guide_parser = sub.add_parser("render-guide", help="build the Guide PDF")
    _add_root(guide_parser)
    guide_parser.add_argument("--locale", required=True)
    guide_parser.add_argument("--out-dir", type=Path, default=None)

    world_parser = sub.add_parser("render-world", help="build a World Book PDF")
    _add_root(world_parser)
    world_parser.add_argument("--world", required=True)
    world_parser.add_argument("--locale", required=True)
    world_parser.add_argument("--out-dir", type=Path, default=None)

    examples_parser = sub.add_parser(
        "render-examples", help="build a world's example-hero sheets PDF"
    )
    _add_root(examples_parser)
    examples_parser.add_argument("--world", required=True)
    examples_parser.add_argument("--locale", required=True)
    examples_parser.add_argument("--out-dir", type=Path, default=None)

    rebuild_parser = sub.add_parser(
        "rebuild", help="build the whole library, prune old versions, refresh README and catalogue"
    )
    _add_root(rebuild_parser)
    rebuild_parser.add_argument("--out-dir", type=Path, default=None)

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

    if args.command == "render-tale-book":
        from build.render import tale_book

        out = tale_book.build_tale_book(
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
        vi = ver.version_info(
            args.root, ver.guide_inputs(args.root, args.locale), ver.render_sources(args.root)
        )
        out = out_dir / "guides" / f"Guide_for_the_Grown-Up_{args.locale}-{vi.label}.pdf"
        qr = f"{PROJECT_URL}/tree/main/kits/guides"
        pages.render_guide(src, out, args.locale, version=vi, qr_url=qr)
        qs = out_dir / "guides" / f"How_to_Play_{args.locale}-{vi.label}.pdf"
        pages.build_quickstart(qs, args.locale, version=vi)
        print(f"built {out}")
        print(f"built {qs}")
        return 0

    if args.command == "render-atlas":
        from build.render import atlas

        out = atlas.build_atlas(
            args.root, args.world, args.story, args.locale, out_dir=args.out_dir
        )
        print(f"built {out}")
        return 0

    if args.command == "render-world":
        from build.render import world_pdf

        out = world_pdf.build_world_pdf(
            args.root, args.world, args.locale, out_dir=args.out_dir
        )
        print(f"built {out}")
        return 0

    if args.command == "render-examples":
        from build.render import examples

        out = examples.build_example_heroes(
            args.root, args.world, args.locale, out_dir=args.out_dir
        )
        print(f"built {out}")
        return 0

    if args.command == "rebuild":
        from build.render import library

        out_dir = args.out_dir if args.out_dir is not None else args.root / "kits"
        built = library.rebuild(args.root, out_dir)
        total = (
            len(built.tale_books) + len(built.atlases)
            + len(built.world_books) + len(built.guides)
            + len(built.quickstarts)
        )
        print(f"rebuilt {total} artifact(s) into {out_dir}")
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
