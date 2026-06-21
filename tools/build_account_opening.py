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
import site_common

ROOT = Path(__file__).resolve().parents[1]
PRODUCT_DIR = ROOT / "data" / "account-opening" / "products"
GUIDE_DIR = ROOT / "data" / "account-opening" / "guides"
HUB_DATA_PATH = ROOT / "data" / "account-opening-hub.json"
PRODUCT_TEMPLATE_PATH = ROOT / "templates" / "account-opening-product.html"
GUIDE_TEMPLATE_PATH = ROOT / "templates" / "account-opening-guide.html"
HUB_TEMPLATE_PATH = ROOT / "templates" / "account-opening-hub.html"
STYLE_HREF = "/assets/kozeni-account-opening.v1.css"
BASE_URL = site_common.BASE_URL
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: root must be an object")
    return data


def _validate_slug(path: Path, data: dict[str, Any], expected_type: str) -> None:
    if data.get("page_type") != expected_type:
        raise ValueError(f"{path}: page_type must be {expected_type!r}")
    slug = data.get("slug")
    if not isinstance(slug, str) or not SLUG_RE.fullmatch(slug):
        raise ValueError(f"{path}: invalid slug")
    if path.stem != slug:
        raise ValueError(f"{path}: filename must match slug")


def _require_strings(path: Path, data: dict[str, Any], keys: set[str]) -> None:
    for key in sorted(keys):
        if not str(data.get(key, "")).strip():
            raise ValueError(f"{path}: {key} is required")


def _validate_related(path: Path, items: list[Any], key: str = "related") -> None:
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: invalid {key} item")
        for field in ("href", "title", "description"):
            if not str(item.get(field, "")).strip():
                raise ValueError(f"{path}: {key}.{field} is required")
        if not str(item["href"]).startswith("/"):
            raise ValueError(f"{path}: {key}.href must be site-relative")


def _validate_sources(path: Path, items: list[Any]) -> None:
    for item in items:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: invalid source")
        if not str(item.get("label", "")).strip():
            raise ValueError(f"{path}: source.label is required")
        if not str(item.get("url", "")).startswith("https://"):
            raise ValueError(f"{path}: source.url must use https")


def load_product(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    _validate_slug(path, data, "product")
    _require_strings(
        path,
        data,
        {
            "name",
            "category",
            "title",
            "description",
            "eyebrow",
            "h1",
            "lead",
            "checked_at",
            "verdict_title",
            "verdict",
        },
    )
    data["_checked_at_date"] = site_common.parse_date(data["checked_at"], path)
    for key in ("badges", "checklist", "cautions", "sources", "related"):
        site_common.require_non_empty_list(data, key, path)
    _validate_sources(path, data["sources"])
    _validate_related(path, data["related"])
    data["cta"] = monetization.resolve_cta(data.get("cta"), path)
    return data


def load_guide(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    _validate_slug(path, data, "guide")
    _require_strings(
        path,
        data,
        {
            "name",
            "title",
            "description",
            "eyebrow",
            "h1",
            "lead",
            "checked_at",
            "comparison_title",
            "note",
        },
    )
    data["_checked_at_date"] = site_common.parse_date(data["checked_at"], path)
    for key in (
        "badges",
        "conclusion_cards",
        "comparison_headers",
        "comparison_rows",
        "sections",
    ):
        site_common.require_non_empty_list(data, key, path)
    if len(data["conclusion_cards"]) != 2:
        raise ValueError(f"{path}: conclusion_cards must contain exactly two items")
    for item in data["conclusion_cards"]:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: invalid conclusion card")
        for field in ("label", "title", "description"):
            if not str(item.get(field, "")).strip():
                raise ValueError(f"{path}: conclusion_cards.{field} is required")
    if len(data["comparison_headers"]) != 3:
        raise ValueError(f"{path}: comparison_headers must contain three items")
    for row in data["comparison_rows"]:
        if not isinstance(row, list) or len(row) != 3 or not all(str(v).strip() for v in row):
            raise ValueError(f"{path}: each comparison row must contain three values")
    for section in data["sections"]:
        if not isinstance(section, dict) or not str(section.get("title", "")).strip():
            raise ValueError(f"{path}: invalid section")
        paragraphs = section.get("paragraphs", [])
        items = section.get("list", [])
        if not isinstance(paragraphs, list) or not isinstance(items, list):
            raise ValueError(f"{path}: section paragraphs/list must be arrays")
        if not paragraphs and not items:
            raise ValueError(f"{path}: section must contain paragraphs or list")
    next_item = data.get("next")
    if not isinstance(next_item, dict):
        raise ValueError(f"{path}: next must be an object")
    _validate_related(path, [next_item], "next")
    return data


def load_hub() -> dict[str, Any]:
    data = _load_json(HUB_DATA_PATH)
    _require_strings(
        HUB_DATA_PATH,
        data,
        {"title", "description", "h1", "lead", "checked_at", "note"},
    )
    data["_checked_at_date"] = site_common.parse_date(
        data["checked_at"], HUB_DATA_PATH
    )
    for key in ("sections", "guides", "checklist"):
        site_common.require_non_empty_list(data, key, HUB_DATA_PATH)
    _validate_related(HUB_DATA_PATH, data["guides"], "guides")
    section_ids: set[str] = set()
    for section in data["sections"]:
        if not isinstance(section, dict):
            raise ValueError(f"{HUB_DATA_PATH}: invalid section")
        for key in ("id", "title", "description"):
            if not str(section.get(key, "")).strip():
                raise ValueError(f"{HUB_DATA_PATH}: section.{key} is required")
        section_id = str(section["id"])
        if section_id in section_ids:
            raise ValueError(f"{HUB_DATA_PATH}: duplicate section id {section_id}")
        section_ids.add(section_id)
        cards = section.get("cards")
        if not isinstance(cards, list) or not cards:
            raise ValueError(f"{HUB_DATA_PATH}: section.cards must be non-empty")
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError(f"{HUB_DATA_PATH}: invalid card")
            for key in ("tag", "title", "description"):
                if not str(card.get(key, "")).strip():
                    raise ValueError(f"{HUB_DATA_PATH}: card.{key} is required")
            destination_keys = {key for key in ("href", "program_id") if card.get(key)}
            if len(destination_keys) != 1:
                raise ValueError(
                    f"{HUB_DATA_PATH}: card requires exactly one of href/program_id"
                )
            if "href" in destination_keys and not str(card["href"]).startswith("/"):
                raise ValueError(f"{HUB_DATA_PATH}: card.href must be site-relative")
            if "program_id" in destination_keys:
                card["_cta"] = monetization.resolve_cta(
                    {"program_id": card["program_id"]}, HUB_DATA_PATH
                )
    return data


def product_paths(slugs: list[str]) -> list[Path]:
    paths = sorted(PRODUCT_DIR.glob("*.json"))
    if not slugs:
        return paths
    wanted = set(slugs)
    selected = [path for path in paths if path.stem in wanted]
    return selected


def guide_paths(slugs: list[str]) -> list[Path]:
    paths = sorted(GUIDE_DIR.glob("*.json"))
    if not slugs:
        return paths
    wanted = set(slugs)
    selected = [path for path in paths if path.stem in wanted]
    return selected


def all_known_slugs() -> set[str]:
    return {path.stem for path in PRODUCT_DIR.glob("*.json")} | {
        path.stem for path in GUIDE_DIR.glob("*.json")
    }


def output_path(slug: str) -> Path:
    return ROOT / "account-opening" / slug / "index.html"


def canonical_url(slug: str) -> str:
    return f"{BASE_URL}/account-opening/{slug}/"


def render_product(data: dict[str, Any], template: Template) -> str:
    canonical = canonical_url(data["slug"])
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "canonical": site_common.esc(canonical),
        "name": site_common.esc(data["name"]),
        "eyebrow": site_common.esc(data["eyebrow"]),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "checked_at": site_common.esc(data["checked_at"]),
        "checked_at_display": site_common.esc(
            site_common.format_date(data["_checked_at_date"])
        ),
        "verdict_title": site_common.esc(data["verdict_title"]),
        "verdict": site_common.esc(data["verdict"]),
        "badges": site_common.render_badges(data["badges"]),
        "checklist": site_common.render_list(data["checklist"]),
        "cautions": site_common.render_list(data["cautions"]),
        "cta": monetization.render_cta(
            data["cta"],
            container_class="account-cta",
            link_class="account-cta__link",
            note_class="account-cta__note",
            tracking_class="account-cta__tracking",
            creative_class="account-cta__creative",
        ),
        "sources": site_common.render_sources(data["sources"]),
        "related": site_common.render_related(data["related"]),
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[
                ("ホーム", f"{BASE_URL}/"),
                ("口座", f"{BASE_URL}/account-opening/"),
                (data["name"], canonical),
            ],
        ).replace("</", "<\\/"),
    }
    return site_common.clean_rendered(template.substitute(values))


def render_conclusions(items: list[dict[str, str]]) -> str:
    return "".join(
        '<article class="account-conclusion">'
        f'<p class="account-conclusion__label">{site_common.esc(item["label"])}</p>'
        f'<h3>{site_common.esc(item["title"])}</h3>'
        f'<p>{site_common.esc(item["description"])}</p>'
        '</article>'
        for item in items
    )


def render_comparison(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{site_common.esc(value)}</th>" for value in headers)
    body = "".join(
        "<tr>"
        f"<th>{site_common.esc(row[0])}</th>"
        f"<td>{site_common.esc(row[1])}</td>"
        f"<td>{site_common.esc(row[2])}</td>"
        "</tr>"
        for row in rows
    )
    return f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody>"


def render_sections(items: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for index, item in enumerate(items, 1):
        paragraphs = "".join(
            f"<p>{site_common.esc(value)}</p>" for value in item.get("paragraphs", [])
        )
        listed = item.get("list", [])
        list_html = (
            f'<ul class="account-list">{site_common.render_list(listed)}</ul>'
            if listed
            else ""
        )
        rendered.append(
            f'<section class="account-panel account-section" aria-labelledby="section-{index}-title">'
            f'<h2 id="section-{index}-title">{site_common.esc(item["title"])}</h2>'
            f'{paragraphs}{list_html}</section>'
        )
    return "".join(rendered)


def render_guide(data: dict[str, Any], template: Template) -> str:
    canonical = canonical_url(data["slug"])
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "canonical": site_common.esc(canonical),
        "name": site_common.esc(data["name"]),
        "eyebrow": site_common.esc(data["eyebrow"]),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "checked_at": site_common.esc(data["checked_at"]),
        "checked_at_display": site_common.esc(
            site_common.format_date(data["_checked_at_date"])
        ),
        "badges": site_common.render_badges(data["badges"]),
        "conclusion_cards": render_conclusions(data["conclusion_cards"]),
        "comparison_title": site_common.esc(data["comparison_title"]),
        "comparison_table": render_comparison(
            data["comparison_headers"], data["comparison_rows"]
        ),
        "sections": render_sections(data["sections"]),
        "note": site_common.esc(data["note"]),
        "next_link": site_common.render_related([data["next"]]),
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[
                ("ホーム", f"{BASE_URL}/"),
                ("口座", f"{BASE_URL}/account-opening/"),
                (data["name"], canonical),
            ],
        ).replace("</", "<\\/"),
    }
    return site_common.clean_rendered(template.substitute(values))


def render_hub_card(card: dict[str, Any]) -> str:
    classes = ["account-card"]
    attrs = ""
    tracking = ""
    if card.get("program_id"):
        cta = card["_cta"]
        classes.append("account-card--affiliate")
        attrs = (
            f'href="{site_common.esc(cta["url"])}" target="_blank" '
            'rel="nofollow sponsored noopener noreferrer" '
            'referrerpolicy="no-referrer-when-downgrade"'
        )
        if cta.get("tracking_pixel_url"):
            tracking = (
                f'<img class="account-cta__tracking" '
                f'src="{site_common.esc(cta["tracking_pixel_url"])}" '
                'width="1" height="1" alt="">'
            )
    else:
        attrs = f'href="{site_common.esc(card["href"])}"'
    return (
        f'<a class="{" ".join(classes)}" {attrs}>'
        f'<span class="account-card__tag">{site_common.esc(card["tag"])}</span>'
        f'<strong>{site_common.esc(card["title"])}</strong>'
        f'<span>{site_common.esc(card["description"])}</span>'
        f'{tracking}</a>'
    )


def render_hub_sections(items: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for item in items:
        cards = "".join(render_hub_card(card) for card in item["cards"])
        affiliate_notes = [
            card["_cta"]["note"] for card in item["cards"] if card.get("program_id")
        ]
        note = (
            "".join(
                f'<p class="account-affiliate-note">{site_common.esc(value)}</p>'
                for value in affiliate_notes
            )
            if affiliate_notes
            else ""
        )
        rows.append(
            f'<section class="account-panel account-hub-section" aria-labelledby="{site_common.esc(item["id"])}-title">'
            f'<div class="account-hub-head"><p class="account-label">目的別</p>'
            f'<h2 id="{site_common.esc(item["id"])}-title">{site_common.esc(item["title"])}</h2>'
            f'<p>{site_common.esc(item["description"])}</p></div>'
            f'<div class="account-card-grid">{cards}</div>{note}</section>'
        )
    return "".join(rows)


def render_checklist(items: list[str]) -> str:
    return "".join(
        f'<li><span>{index}</span>{site_common.esc(item)}</li>'
        for index, item in enumerate(items, 1)
    )


def render_hub(data: dict[str, Any], template: Template) -> str:
    canonical = f"{BASE_URL}/account-opening/"
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "canonical": site_common.esc(canonical),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "checked_at": site_common.esc(data["checked_at"]),
        "checked_at_display": site_common.esc(
            site_common.format_date(data["_checked_at_date"])
        ),
        "guides": site_common.render_related(data["guides"]),
        "sections": render_hub_sections(data["sections"]),
        "checklist": render_checklist(data["checklist"]),
        "note": site_common.esc(data["note"]),
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[("ホーム", f"{BASE_URL}/"), ("口座", canonical)],
        ).replace("</", "<\\/"),
    }
    return site_common.clean_rendered(template.substitute(values))


def build(*, check: bool, slugs: list[str]) -> int:
    known = all_known_slugs()
    unknown = sorted(set(slugs) - known)
    if unknown:
        raise ValueError(f"unknown slug(s): {', '.join(unknown)}")

    product_template = Template(PRODUCT_TEMPLATE_PATH.read_text(encoding="utf-8"))
    guide_template = Template(GUIDE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    hub_template = Template(HUB_TEMPLATE_PATH.read_text(encoding="utf-8"))
    failures = 0

    for path in product_paths(slugs):
        data = load_product(path)
        output = output_path(data["slug"])
        rendered = render_product(data, product_template)
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

    for path in guide_paths(slugs):
        data = load_guide(path)
        output = output_path(data["slug"])
        rendered = render_guide(data, guide_template)
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
        data = load_hub()
        output = ROOT / "account-opening" / "index.html"
        rendered = render_hub(data, hub_template)
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
