#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import public_assets

ROOT = Path(__file__).resolve().parents[1]


def write_or_check(path: Path, rendered: str, *, check: bool) -> bool:
    rel = path.relative_to(ROOT)
    if check:
        if not path.exists() or path.read_text(encoding="utf-8") != rendered:
            print(f"NG: {rel}")
            return False
        print(f"OK: {rel}")
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    print(f"WROTE: {rel}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate the web app manifest and shared analytics runtime from one SSOT."
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    try:
        config = public_assets.load_config()
        outputs = (
            (public_assets.MANIFEST_PATH, public_assets.render_manifest(config)),
            (
                ROOT / config["analytics"]["output"],
                public_assets.render_analytics(config),
            ),
        )
        ok = all(
            write_or_check(path, rendered, check=args.check)
            for path, rendered in outputs
        )
    except (OSError, ValueError) as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
