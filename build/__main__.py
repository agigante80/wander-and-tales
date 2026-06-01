"""Command line: python -m build {validate,lint,catalog}."""

import argparse
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

    return 2


if __name__ == "__main__":
    sys.exit(main())
