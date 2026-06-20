#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "mobile-sim"

EXACT_PR = (
    "PR：このリンクは広告リンクです。"
    "条件・特典は公式画面で確認してください。"
)

FORBIDDEN_BY_SLUG = {
    "ahamo": (
        "紹介者7,000",
        "紹介された側は契約種別で最大13,000",
        "紹介人数上限",
        "Rakuten Link",
        "楽天会員",
    ),
}


def fail(errors: list[str], path: Path, message: str) -> None:
    errors.append(f"{path.relative_to(ROOT)}: {message}")


def main() -> int:
    errors: list[str] = []

    for data_path in sorted(DATA_DIR.glob("*.json")):
        data = json.loads(data_path.read_text(encoding="utf-8"))
        slug = data["slug"]
        page = ROOT / "mobile-sim" / slug / "index.html"

        if not page.exists():
            fail(errors, page, "generated page is missing")
            continue

        source = page.read_text(encoding="utf-8")

        if source.count("<h1") != 1:
            fail(errors, page, "h1 must appear exactly once")
        if "<style" in source:
            fail(errors, page, "inline <style> is forbidden")
        if source.count('type="application/ld+json"') < 2:
            fail(errors, page, "WebPage/Breadcrumb and FAQ JSON-LD are required")
        if 'class="kozeni-breadcrumb"' not in source:
            fail(errors, page, "visible breadcrumb is required")
        if '/assets/kozeni-sim-detail.v1.css?v=1' not in source:
            fail(errors, page, "shared SIM detail stylesheet is missing")
        if EXACT_PR not in source:
            fail(errors, page, "standard PR note is missing")

        cta = re.search(
            r'<a class="sim-cta__button"([^>]*)>公式条件を見る</a>',
            source,
        )
        if not cta:
            fail(errors, page, "standard CTA is missing")
        else:
            attrs = cta.group(1)
            for token in (
                'target="_blank"',
                "nofollow",
                "sponsored",
                "noopener",
                "noreferrer",
            ):
                if token not in attrs:
                    fail(errors, page, f"CTA missing {token}")

        canonical = f"https://smart-kozeni.com/mobile-sim/{slug}/"
        if f'<link rel="canonical" href="{canonical}">' not in source:
            fail(errors, page, "canonical is incorrect")

        for phrase in FORBIDDEN_BY_SLUG.get(slug, ()):
            if phrase in source:
                fail(errors, page, f"forbidden cross-brand phrase: {phrase}")

    if errors:
        print("AUDIT FAILED")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AUDIT OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
