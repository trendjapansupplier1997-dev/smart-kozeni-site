#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys

sys.dont_write_bytecode = True

import seo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate sitemap.xml from canonical page metadata."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        rendered = seo.render_sitemap()
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1

    if args.check:
        current = seo.SITEMAP_PATH.read_text(encoding="utf-8") if seo.SITEMAP_PATH.exists() else ""
        if current != rendered:
            print("NG: sitemap.xml")
            return 1
        print("OK: sitemap.xml")
        return 0

    seo.SITEMAP_PATH.write_text(rendered, encoding="utf-8")
    print("WROTE: sitemap.xml")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
