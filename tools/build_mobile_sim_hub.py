#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import date
from pathlib import Path
from string import Template
from typing import Any

sys.dont_write_bytecode = True

import build_mobile_sim

ROOT = Path(__file__).resolve().parents[1]
HUB_DATA_PATH = ROOT / "data" / "mobile-sim-hub.json"
DETAIL_DATA_DIR = ROOT / "data" / "mobile-sim"
TEMPLATE_PATH = ROOT / "templates" / "mobile-sim-hub.html"
OUTPUT_PATH = ROOT / "mobile-sim" / "index.html"
BASE_URL = "https://smart-kozeni.com"
CANONICAL = f"{BASE_URL}/mobile-sim/"
STYLE_HREF = "/assets/kozeni-mobile-sim-hub.v1.css?v=45.0"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def require_non_empty_list(
    data: dict[str, Any],
    key: str,
    path: Path,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path}: {key} must be a non-empty list")
    return value


def validate_internal_link(item: dict[str, Any], path: Path) -> None:
    for key in ("title", "description", "href"):
        if not str(item.get(key, "")).strip():
            raise ValueError(f"{path}: link item requires {key}")
    if not str(item["href"]).startswith("/"):
        raise ValueError(f"{path}: href must be site-relative")


def load_hub_data(path: Path = HUB_DATA_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    required = {
        "title",
        "description",
        "h1",
        "lead",
        "checked_at",
        "featured_slugs",
        "purpose_links",
        "other_options",
        "home_networks",
        "checklist",
        "note",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path}: missing keys: {', '.join(missing)}")

    try:
        data["_checked_at_date"] = date.fromisoformat(data["checked_at"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}: checked_at must be YYYY-MM-DD") from error

    featured = require_non_empty_list(data, "featured_slugs", path)
    if len(featured) != len(set(featured)):
        raise ValueError(f"{path}: featured_slugs must be unique")

    for key in ("purpose_links", "other_options", "home_networks"):
        for item in require_non_empty_list(data, key, path):
            if not isinstance(item, dict):
                raise ValueError(f"{path}: {key} items must be objects")
            validate_internal_link(item, path)

    require_non_empty_list(data, "checklist", path)

    return data


def load_featured_details(
    slugs: list[str],
) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    required_hub = {
        "label",
        "best_for",
        "price",
        "data",
        "calls",
        "summary",
        "badges",
    }

    for slug in slugs:
        path = DETAIL_DATA_DIR / f"{slug}.json"
        if not path.exists():
            raise ValueError(f"featured detail data is missing: {path}")

        detail = build_mobile_sim.load_data(path)
        hub = detail.get("hub")
        if not isinstance(hub, dict):
            raise ValueError(f"{path}: hub object is required")

        missing = sorted(required_hub - hub.keys())
        if missing:
            raise ValueError(
                f"{path}: hub missing keys: {', '.join(missing)}"
            )

        badges = hub["badges"]
        if not isinstance(badges, list) or not badges:
            raise ValueError(f"{path}: hub.badges must be a non-empty list")

        details.append(detail)

    return details


def render_badges(items: list[str]) -> str:
    return "".join(f"<span>{esc(item)}</span>" for item in items)


def render_featured_cards(
    details: list[dict[str, Any]],
) -> str:
    return "".join(
        f'<a class="hub-featured-card" '
        f'href="/mobile-sim/{esc(detail["slug"])}/">'
        f'<span class="hub-featured-card__label">'
        f'{esc(detail["hub"]["label"])}</span>'
        f'<h3>{esc(detail["name"])}</h3>'
        f'<p>{esc(detail["hub"]["summary"])}</p>'
        f'<div class="hub-badges">'
        f'{render_badges(detail["hub"]["badges"])}</div>'
        f'<span class="hub-featured-card__action">'
        f'料金・注意点を確認する</span>'
        f'</a>'
        for detail in details
    )


def render_comparison_rows(
    details: list[dict[str, Any]],
) -> str:
    return "".join(
        '<tr class="hub-compare__row">'
        f'<th scope="row">{esc(detail["name"])}</th>'
        f'<td>{esc(detail["hub"]["best_for"])}</td>'
        f'<td>{esc(detail["hub"]["price"])}</td>'
        f'<td>{esc(detail["hub"]["data"])}</td>'
        f'<td>{esc(detail["hub"]["calls"])}</td>'
        f'<td><a href="/mobile-sim/{esc(detail["slug"])}/">'
        f'詳細を見る</a></td>'
        '</tr>'
        for detail in details
    )


def render_purpose_links(items: list[dict[str, str]]) -> str:
    return "".join(
        f'<a class="hub-route" href="{esc(item["href"])}">'
        f'<strong>{esc(item["title"])}</strong>'
        f'<span>{esc(item["description"])}</span>'
        f'<em>{esc(item["result"])}</em>'
        f'</a>'
        for item in items
    )


def render_options(
    items: list[dict[str, str]],
    class_name: str,
) -> str:
    return "".join(
        f'<a class="{class_name}" href="{esc(item["href"])}">'
        f'<strong>{esc(item["title"])}</strong>'
        f'<span>{esc(item["description"])}</span>'
        f'</a>'
        for item in items
    )


def render_checklist(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def effective_checked_at(
    hub_data: dict[str, Any],
    details: list[dict[str, Any]],
) -> date:
    dates = [
        hub_data["_checked_at_date"],
        *(detail["_checked_at_date"] for detail in details),
    ]
    return max(dates)


def render_jsonld(
    data: dict[str, Any],
    details: list[dict[str, Any]],
    checked_at: date,
) -> str:
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
                "@type": "CollectionPage",
                "@id": f"{CANONICAL}#webpage",
                "url": CANONICAL,
                "name": data["title"],
                "description": data["description"],
                "dateModified": checked_at.isoformat(),
                "isPartOf": {"@id": f"{BASE_URL}/#website"},
                "publisher": {"@id": f"{BASE_URL}/#organization"},
                "breadcrumb": {"@id": f"{CANONICAL}#breadcrumb"},
                "mainEntity": {"@id": f"{CANONICAL}#featured"},
                "inLanguage": "ja",
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{CANONICAL}#breadcrumb",
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
                        "item": CANONICAL,
                    },
                ],
            },
            {
                "@type": "ItemList",
                "@id": f"{CANONICAL}#featured",
                "name": "最初に比較するスマホ料金3候補",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": index,
                        "name": detail["name"],
                        "url": (
                            f"{BASE_URL}/mobile-sim/"
                            f"{detail['slug']}/"
                        ),
                    }
                    for index, detail in enumerate(details, 1)
                ],
            },
        ],
    }
    return json.dumps(
        graph,
        ensure_ascii=False,
        separators=(",", ":"),
    )


def render_page(
    data: dict[str, Any],
    details: list[dict[str, Any]],
    template: Template,
) -> str:
    checked_at = effective_checked_at(data, details)
    values = {
        "title": esc(data["title"]),
        "description": esc(data["description"]),
        "canonical": CANONICAL,
        "h1": esc(data["h1"]),
        "lead": esc(data["lead"]),
        "checked_at": checked_at.isoformat(),
        "checked_at_display": esc(
            build_mobile_sim.format_checked_at(checked_at)
        ),
        "featured_cards": render_featured_cards(details),
        "comparison_rows": render_comparison_rows(details),
        "purpose_links": render_purpose_links(data["purpose_links"]),
        "other_options": render_options(
            data["other_options"],
            "hub-option",
        ),
        "home_networks": render_options(
            data["home_networks"],
            "hub-network",
        ),
        "checklist": render_checklist(data["checklist"]),
        "note": esc(data["note"]),
        "seo_jsonld": render_jsonld(
            data,
            details,
            checked_at,
        ).replace("</", "<\\/"),
    }
    return template.substitute(values).rstrip() + "\n"


def build() -> str:
    data = load_hub_data()
    details = load_featured_details(data["featured_slugs"])
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return render_page(data, details, template)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="生成結果とmobile-sim/index.htmlの一致を検査する",
    )
    args = parser.parse_args()

    try:
        rendered = build()
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if args.check:
        current = (
            OUTPUT_PATH.read_text(encoding="utf-8")
            if OUTPUT_PATH.exists()
            else ""
        )
        if current != rendered:
            print("OUTDATED: mobile-sim/index.html")
            return 1
        print("OK: mobile-sim/index.html")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print("WROTE: mobile-sim/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
