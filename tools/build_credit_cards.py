#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from string import Template
from typing import Any

sys.dont_write_bytecode = True

import monetization
import public_assets
import site_common

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "credit-card"
HUB_DATA_PATH = ROOT / "data" / "credit-card-hub.json"
DETAIL_TEMPLATE_PATH = ROOT / "templates" / "credit-card-detail.html"
HUB_TEMPLATE_PATH = ROOT / "templates" / "credit-card-hub.html"
STYLE_HREF = "/assets/kozeni-credit-card.v1.css?v=45.0"
BASE_URL = site_common.BASE_URL
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def load_detail(path: Path) -> dict[str, Any]:
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
        "fit",
        "not_fit",
        "checklist",
        "facts",
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
        raise ValueError(f"{path}: filename must match slug")

    data["_checked_at_date"] = site_common.parse_date(
        data["checked_at"],
        path,
    )

    for key in (
        "badges",
        "fit",
        "not_fit",
        "checklist",
        "facts",
        "cautions",
        "related",
        "faq",
        "sources",
    ):
        site_common.require_non_empty_list(data, key, path)

    for item in data["facts"]:
        if not isinstance(item, dict) or not item.get("label") or not item.get("value"):
            raise ValueError(f"{path}: invalid fact")
    for item in data["related"]:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: invalid related item")
        for key in ("href", "title", "description"):
            if not str(item.get(key, "")).strip():
                raise ValueError(f"{path}: related.{key} is required")
        if not str(item["href"]).startswith("/"):
            raise ValueError(f"{path}: related.href must be site-relative")
    for item in data["faq"]:
        if not isinstance(item, dict) or not item.get("question") or not item.get("answer"):
            raise ValueError(f"{path}: invalid FAQ")
    for item in data["sources"]:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: invalid source")
        if not str(item.get("url", "")).startswith("https://"):
            raise ValueError(f"{path}: source URL must use https")
        if not str(item.get("label", "")).strip():
            raise ValueError(f"{path}: source label is required")

    data["cta"] = monetization.resolve_cta(data["cta"], path)
    return data


def detail_paths(slugs: list[str]) -> list[Path]:
    paths = sorted(DATA_DIR.glob("*.json"))
    if not slugs:
        return paths
    wanted = set(slugs)
    selected = [path for path in paths if path.stem in wanted]
    missing = sorted(wanted - {path.stem for path in selected})
    if missing:
        raise ValueError(f"unknown slug(s): {', '.join(missing)}")
    return selected


def load_all_details() -> dict[str, dict[str, Any]]:
    details: dict[str, dict[str, Any]] = {}
    for path in detail_paths([]):
        data = load_detail(path)
        details[data["slug"]] = data
    return details


def load_hub() -> dict[str, Any]:
    with HUB_DATA_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    required = {
        "title",
        "description",
        "h1",
        "lead",
        "checked_at",
        "featured_slugs",
        "purpose_links",
        "checklist",
        "note",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{HUB_DATA_PATH}: missing keys: {', '.join(missing)}")
    data["_checked_at_date"] = site_common.parse_date(
        data["checked_at"],
        HUB_DATA_PATH,
    )
    featured = site_common.require_non_empty_list(
        data,
        "featured_slugs",
        HUB_DATA_PATH,
    )
    if len(featured) != 3 or len(set(featured)) != 3:
        raise ValueError(
            f"{HUB_DATA_PATH}: featured_slugs must contain exactly 3 unique slugs"
        )
    site_common.require_non_empty_list(data, "purpose_links", HUB_DATA_PATH)
    site_common.require_non_empty_list(data, "checklist", HUB_DATA_PATH)
    return data


def detail_output(data: dict[str, Any]) -> Path:
    return ROOT / "credit-card" / data["slug"] / "index.html"


def detail_canonical(data: dict[str, Any]) -> str:
    return f"{BASE_URL}/credit-card/{data['slug']}/"


def render_detail(data: dict[str, Any], template: Template) -> str:
    canonical = detail_canonical(data)
    checked_at = data["_checked_at_date"]
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "canonical": site_common.esc(canonical),
        "name": site_common.esc(data["name"]),
        "eyebrow": site_common.esc(data["eyebrow"]),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "checked_at": site_common.esc(data["checked_at"]),
        "checked_at_display": site_common.esc(site_common.format_date(checked_at)),
        "verdict_title": site_common.esc(data["verdict_title"]),
        "verdict": site_common.esc(data["verdict"]),
        "badges": site_common.render_badges(data["badges"]),
        "fit": site_common.render_list(data["fit"]),
        "not_fit": site_common.render_list(data["not_fit"]),
        "checklist": site_common.render_list(data["checklist"]),
        "cta": monetization.render_cta(
            data["cta"],
            container_class="credit-cta",
            link_class="credit-cta__link",
            note_class="credit-cta__note",
            tracking_class="credit-cta__tracking",
            creative_class="credit-cta__creative",
        ),
        "facts": site_common.render_facts(
            data["facts"],
            "credit-facts__row",
        ),
        "sources": site_common.render_sources(data["sources"]),
        "cautions": site_common.render_list(data["cautions"]),
        "related": site_common.render_related(data["related"]),
        "faq": site_common.render_faq(data["faq"]),
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[
                ("ホーム", f"{BASE_URL}/"),
                ("クレカ", f"{BASE_URL}/credit-card/"),
                (data["name"], canonical),
            ],
        ).replace("</", "<\\/"),
    }
    return site_common.clean_rendered(template.substitute(values))


def render_featured(
    slugs: list[str],
    details: dict[str, dict[str, Any]],
) -> str:
    rows: list[str] = []
    for slug in slugs:
        if slug not in details:
            raise ValueError(f"featured card is missing: {slug}")
        data = details[slug]
        tag = data["badges"][0]
        rows.append(
            f'<a href="/credit-card/{site_common.esc(slug)}/">'
            f'<span class="credit-featured__tag">{site_common.esc(tag)}</span>'
            f'<strong>{site_common.esc(data["name"])}</strong>'
            f'<span>{site_common.esc(data["verdict_title"])}</span>'
            '</a>'
        )
    return "".join(rows)


def render_purpose_links(items: list[dict[str, str]]) -> str:
    return site_common.render_related(items)


def render_checklist(items: list[str]) -> str:
    return "".join(
        f'<li><span>{index}</span>{site_common.esc(item)}</li>'
        for index, item in enumerate(items, 1)
    )


def render_hub(
    data: dict[str, Any],
    details: dict[str, dict[str, Any]],
    template: Template,
) -> str:
    canonical = f"{BASE_URL}/credit-card/"
    checked_at = data["_checked_at_date"]
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "canonical": site_common.esc(canonical),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "checked_at": site_common.esc(data["checked_at"]),
        "checked_at_display": site_common.esc(site_common.format_date(checked_at)),
        "featured_cards": render_featured(data["featured_slugs"], details),
        "purpose_links": render_purpose_links(data["purpose_links"]),
        "checklist": render_checklist(data["checklist"]),
        "note": site_common.esc(data["note"]),
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[
                ("ホーム", f"{BASE_URL}/"),
                ("クレカ", canonical),
            ],
        ).replace("</", "<\\/"),
    }
    return site_common.clean_rendered(template.substitute(values))


def build(*, check: bool, slugs: list[str]) -> int:
    detail_template = public_assets.load_template(DETAIL_TEMPLATE_PATH)
    hub_template = public_assets.load_template(HUB_TEMPLATE_PATH)
    failures = 0

    for path in detail_paths(slugs):
        data = load_detail(path)
        output = detail_output(data)
        rendered = render_detail(data, detail_template)
        if check:
            current = output.read_text(encoding="utf-8") if output.exists() else ""
            if current != rendered:
                print(f"OUTDATED: {output.relative_to(ROOT)}")
                failures += 1
            else:
                print(f"OK: {output.relative_to(ROOT)}")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
            print(f"WROTE: {output.relative_to(ROOT)}")

    if not slugs:
        hub_data = load_hub()
        details = load_all_details()
        rendered = render_hub(hub_data, details, hub_template)
        output = ROOT / "credit-card" / "index.html"
        if check:
            current = output.read_text(encoding="utf-8") if output.exists() else ""
            if current != rendered:
                print(f"OUTDATED: {output.relative_to(ROOT)}")
                failures += 1
            else:
                print(f"OK: {output.relative_to(ROOT)}")
        else:
            output.write_text(rendered, encoding="utf-8")
            print(f"WROTE: {output.relative_to(ROOT)}")

    return 1 if failures else 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("slugs", nargs="*")
    args = parser.parse_args()
    try:
        return build(check=args.check, slugs=args.slugs)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
