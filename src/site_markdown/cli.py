from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .crawler import CrawlError, crawl, render_document, write_document


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="site-markdown",
        description="Crawl a website section into one Markdown file.",
    )
    parser.add_argument("url", help="starting HTTP(S) URL")
    parser.add_argument("-o", "--output", type=Path, default=Path("website.md"))
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--delay", type=float, default=0.25, help="seconds between page requests")
    parser.add_argument("--timeout", type=float, default=20, help="request timeout in seconds")
    parser.add_argument(
        "--scope",
        choices=("linked", "path", "host"),
        default="linked",
        help="linked follows all links; path and host restrict the crawl (default: linked)",
    )
    parser.add_argument("--ignore-robots", action="store_true", help="do not consult robots.txt")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = crawl(
            args.url,
            max_pages=args.max_pages,
            delay=args.delay,
            timeout=args.timeout,
            scope=args.scope,
            respect_robots=not args.ignore_robots,
            progress=lambda url: print(f"Fetching {url}", file=sys.stderr),
        )
        write_document(args.output, render_document(result, args.url))
    except (CrawlError, ValueError) as exc:
        print(f"site-markdown: error: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {len(result.pages)} page(s) to {args.output}")
    if result.errors:
        print(f"Skipped {len(result.errors)} URL(s):", file=sys.stderr)
        for url, reason in result.errors:
            print(f"  {url}: {reason}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
