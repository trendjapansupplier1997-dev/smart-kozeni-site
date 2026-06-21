#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from string import Template
from typing import Any

import monetization
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "mobile-sim"
TEMPLATE_PATH = ROOT / "templates" / "mobile-sim-detail.html"
BASE_URL = "https://smart-kozeni.com"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def require_list(data: dict[str, Any], key: str, path: Path) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path}: {key} must be a non-empty list")
    return value


def load_data(path: Path) -> dict[str, Any]:
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
        "cta",
        "sources",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path}: missing keys: {', '.join(missing)}")

    slug = data["slug"]
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise ValueError(f"{path}: invalid slug")
    if path.stem != slug:
        raise ValueError(f"{path}: filename must match slug {slug!r}")

    try:
        checked_at = date.fromisoformat(data["checked_at"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}: checked_at must be YYYY-MM-DD") from error

    for key in (
        "badges",
        "facts",
        "fit",
        "not_fit",
        "points",
        "cautions",
        "related",
        "faq",
        "sources",
    ):
        require_list(data, key, path)

    data["cta"] = monetization.resolve_cta(data["cta"], path)

    for source in data["sources"]:
        if not isinstance(source, dict):
            raise ValueError(f"{path}: every source must be an object")
        if not str(source.get("url", "")).startswith("https://"):
            raise ValueError(f"{path}: source.url must start with https://")
        if not str(source.get("label", "")).strip():
            raise ValueError(f"{path}: source.label is required")

    data["_checked_at_date"] = checked_at
    return data


def format_checked_at(value: date) -> str:
    return f"{value.year}年{value.month}月{value.day}日"


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_badges(items: list[str]) -> str:
    return "".join(f"<span>{esc(item)}</span>" for item in items)


def render_facts(items: list[dict[str, str]]) -> str:
    return "".join(
        '<div class="sim-facts__row">'
        f"<dt>{esc(item['label'])}</dt>"
        f"<dd>{esc(item['value'])}</dd>"
        "</div>"
        for item in items
    )


def render_sources(items: list[dict[str, str]]) -> str:
    return "".join(
        "<li>根拠："
        f'<a href="{esc(item["url"])}" '
        'target="_blank" rel="noopener noreferrer">'
        f'{esc(item["label"])}</a>'
        "</li>"
        for item in items
    )


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
    return "".join(
        "<details>"
        f"<summary>{esc(item['question'])}</summary>"
        f"<p>{esc(item['answer'])}</p>"
        "</details>"
        for item in items
    )


def render_cta(cta: dict[str, Any]) -> str:
    return monetization.render_cta(
        cta,
        container_class="sim-cta",
        link_class="sim-cta__button",
        note_class="sim-cta__note",
        tracking_class="sim-cta__tracking",
        creative_class="sim-cta__creative",
    )


def render_jsonld(data: dict[str, Any], canonical: str) -> str:
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": "スマホ小銭研究所",
                "inLanguage": "ja",
            },
            {
                "@type": "Organization",
                "@id": f"{BASE_URL}/#organization",
                "name": "スマホ小銭研究所",
                "url": f"{BASE_URL}/",
            },
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": data["title"],
                "description": data["description"],
                "dateModified": data["checked_at"],
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "publisher": {"@id": f"{BASE_URL}/#organization"},
                "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
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
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":"))


def render_page(data: dict[str, Any], template: Template) -> str:
    canonical = f"{BASE_URL}/mobile-sim/{data['slug']}/"
    checked_at: date = data["_checked_at_date"]
    values = {
        "title": esc(data["title"]),
        "description": esc(data["description"]),
        "canonical": esc(canonical),
        "name": esc(data["name"]),
        "eyebrow": esc(data["eyebrow"]),
        "h1": esc(data["h1"]),
        "lead": esc(data["lead"]),
        "checked_at": esc(data["checked_at"]),
        "checked_at_display": esc(format_checked_at(checked_at)),
        "verdict_title": esc(data["verdict_title"]),
        "verdict": esc(data["verdict"]),
        "badges": render_badges(data["badges"]),
        "cta": render_cta(data["cta"]),
        "facts": render_facts(data["facts"]),
        "source_links": render_sources(data["sources"]),
        "fit_items": render_list(data["fit"]),
        "not_fit_items": render_list(data["not_fit"]),
        "point_items": render_list(data["points"]),
        "caution_items": render_list(data["cautions"]),
        "related_links": render_related(data["related"]),
        "faq_items": render_faq(data["faq"]),
        "seo_jsonld": render_jsonld(data, canonical).replace("</", "<\\/"),
    }
    return template.substitute(values).rstrip() + "\n"


def data_paths(slugs: list[str]) -> list[Path]:
    paths = sorted(DATA_DIR.glob("*.json"))
    if not slugs:
        return paths

    wanted = set(slugs)
    selected = [path for path in paths if path.stem in wanted]
    missing = sorted(wanted - {path.stem for path in selected})
    if missing:
        raise ValueError(f"unknown slug(s): {', '.join(missing)}")
    return selected


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
    failures = 0

    try:
        paths = data_paths(args.slugs)
        for path in paths:
            data = load_data(path)
            output = ROOT / "mobile-sim" / data["slug"] / "index.html"
            rendered = render_page(data, template)

            if args.check:
                current = (
                    output.read_text(encoding="utf-8")
                    if output.exists()
                    else ""
                )
                if current != rendered:
                    print(f"OUTDATED: {output.relative_to(ROOT)}")
                    failures += 1
                else:
                    print(f"OK: {output.relative_to(ROOT)}")
                continue

            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
            print(f"WROTE: {output.relative_to(ROOT)}")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
