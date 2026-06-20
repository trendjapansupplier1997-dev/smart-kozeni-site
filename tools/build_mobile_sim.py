#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from string import Template
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "mobile-sim"
TEMPLATE_PATH = ROOT / "templates" / "mobile-sim-detail.html"
BASE_URL = "https://smart-kozeni.com"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    required = {
        "slug",
        "name",
        "title",
        "description",
        "eyebrow",
        "h1",
        "lead",
        "checked_at",
        "checked_at_display",
        "verdict_title",
        "verdict",
        "badges",
        "facts",
        "fit",
        "not_fit",
        "points",
        "cautions",
        "related",
        "faq",
        "affiliate_url",
        "source_url",
        "source_label",
        "pr_note",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path}: missing keys: {', '.join(missing)}")

    for key in ("affiliate_url", "source_url"):
        if not str(data[key]).startswith("https://"):
            raise ValueError(f"{path}: {key} must start with https://")

    return data


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_badges(items: list[str]) -> str:
    return "".join(f"<span>{esc(item)}</span>" for item in items)


def render_facts(items: list[dict[str, str]]) -> str:
    rows: list[str] = []
    for item in items:
        rows.append(
            '<div class="sim-facts__row">'
            f"<dt>{esc(item['label'])}</dt>"
            f"<dd>{esc(item['value'])}</dd>"
            "</div>"
        )
    return "".join(rows)


def render_related(items: list[dict[str, str]]) -> str:
    rows: list[str] = []
    for item in items:
        href = str(item["href"])
        if not href.startswith("/"):
            raise ValueError(f"related href must be site-relative: {href}")
        rows.append(
            f'<a href="{esc(href)}">'
            f"<strong>{esc(item['title'])}</strong>"
            f"<span>{esc(item['description'])}</span>"
            "</a>"
        )
    return "".join(rows)


def render_faq(items: list[dict[str, str]]) -> str:
    rows: list[str] = []
    for item in items:
        rows.append(
            "<details>"
            f"<summary>{esc(item['question'])}</summary>"
            f"<p>{esc(item['answer'])}</p>"
            "</details>"
        )
    return "".join(rows)


def render_cta(data: dict[str, Any]) -> str:
    return (
        '<div class="sim-cta">'
        f'<a class="sim-cta__button" href="{esc(data["affiliate_url"])}" '
        'target="_blank" rel="nofollow sponsored noopener noreferrer">'
        "公式条件を見る"
        "</a>"
        f'<p class="sim-cta__note">{esc(data["pr_note"])}</p>'
        "</div>"
    )


def render_jsonld(data: dict[str, Any], canonical: str) -> tuple[str, str]:
    webpage = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": data["title"],
                "description": data["description"],
                "dateModified": data["checked_at"],
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "inLanguage": "ja",
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumb",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "ホーム",
                        "item": f"{BASE_URL}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "スマホ・回線",
                        "item": f"{BASE_URL}/mobile-sim/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": data["name"],
                        "item": canonical,
                    },
                ],
            },
        ],
    }

    faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "@id": f"{canonical}#faq",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"],
                },
            }
            for item in data["faq"]
        ],
    }

    compact = {"ensure_ascii": False, "separators": (",", ":")}
    return json.dumps(webpage, **compact), json.dumps(faq, **compact)


def render_page(data: dict[str, Any], template: Template) -> str:
    canonical = f"{BASE_URL}/mobile-sim/{data['slug']}/"
    seo_jsonld, faq_jsonld = render_jsonld(data, canonical)

    values = {
        "title": esc(data["title"]),
        "description": esc(data["description"]),
        "canonical": esc(canonical),
        "name": esc(data["name"]),
        "eyebrow": esc(data["eyebrow"]),
        "h1": esc(data["h1"]),
        "lead": esc(data["lead"]),
        "checked_at_display": esc(data["checked_at_display"]),
        "verdict_title": esc(data["verdict_title"]),
        "verdict": esc(data["verdict"]),
        "badges": render_badges(data["badges"]),
        "cta": render_cta(data),
        "facts": render_facts(data["facts"]),
        "source_url": esc(data["source_url"]),
        "source_label": esc(data["source_label"]),
        "fit_items": render_list(data["fit"]),
        "not_fit_items": render_list(data["not_fit"]),
        "point_items": render_list(data["points"]),
        "caution_items": render_list(data["cautions"]),
        "related_links": render_related(data["related"]),
        "faq_items": render_faq(data["faq"]),
        "pr_note": esc(data["pr_note"]),
        "seo_jsonld": seo_jsonld.replace("</", "<\\/"),
        "faq_jsonld": faq_jsonld.replace("</", "<\\/"),
    }
    return template.substitute(values).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="生成結果とコミット済みHTMLの差分だけを検査する",
    )
    parser.add_argument(
        "slugs",
        nargs="*",
        help="対象slug。省略時はdata/mobile-sim/*.jsonをすべて生成",
    )
    args = parser.parse_args()

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    paths = sorted(DATA_DIR.glob("*.json"))

    if args.slugs:
        wanted = set(args.slugs)
        paths = [path for path in paths if path.stem in wanted]
        missing = sorted(wanted - {path.stem for path in paths})
        if missing:
            raise SystemExit(f"unknown slug(s): {', '.join(missing)}")

    failures = 0
    for data_path in paths:
        data = load_json(data_path)
        output_path = ROOT / "mobile-sim" / data["slug"] / "index.html"
        rendered = render_page(data, template)

        if args.check:
            current = (
                output_path.read_text(encoding="utf-8")
                if output_path.exists()
                else ""
            )
            if current != rendered:
                print(f"OUTDATED: {output_path.relative_to(ROOT)}")
                failures += 1
            else:
                print(f"OK: {output_path.relative_to(ROOT)}")
            continue

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(rendered, encoding="utf-8")
        print(f"WROTE: {output_path.relative_to(ROOT)}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
