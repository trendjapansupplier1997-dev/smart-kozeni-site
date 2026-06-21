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

sys.dont_write_bytecode = True

import build_mobile_sim
import monetization

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "home-network"
TEMPLATE_PATH = ROOT / "templates" / "home-network-detail.html"
BASE_URL = "https://smart-kozeni.com"
STYLE_HREF = "/assets/kozeni-home-network.v1.css"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OUTPUT_RE = re.compile(r"^mobile-sim/[a-z0-9]+(?:-[a-z0-9]+)*$")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def load_data(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)

    required = {
        "id", "output", "name", "title", "description", "eyebrow",
        "h1", "lead", "checked_at", "verdict_title", "verdict",
        "badges", "facts", "fit", "not_fit", "checklist", "cautions",
        "related", "faq", "cta", "sources",
    }
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path}: missing keys: {', '.join(missing)}")

    item_id = data["id"]
    if not isinstance(item_id, str) or not ID_RE.fullmatch(item_id):
        raise ValueError(f"{path}: invalid id")
    if path.stem != item_id:
        raise ValueError(f"{path}: filename must match id")
    if not isinstance(data["output"], str) or not OUTPUT_RE.fullmatch(data["output"]):
        raise ValueError(f"{path}: invalid output")

    try:
        data["_checked_at_date"] = date.fromisoformat(data["checked_at"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}: checked_at must be YYYY-MM-DD") from error

    for key in (
        "badges", "facts", "fit", "not_fit", "checklist",
        "cautions", "related", "faq", "sources",
    ):
        value = data.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"{path}: {key} must be a non-empty list")

    for item in data["facts"]:
        if not isinstance(item, dict) or not item.get("label") or not item.get("value"):
            raise ValueError(f"{path}: invalid fact")
    for item in data["related"]:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: invalid related item")
        for key in ("href", "title", "description"):
            if not str(item.get(key, "")).strip():
                raise ValueError(f"{path}: related.{key} is required")
        if not item["href"].startswith("/"):
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


def data_paths(ids: list[str]) -> list[Path]:
    paths = sorted(DATA_DIR.glob("*.json"))
    if not ids:
        return paths
    wanted = set(ids)
    selected = [path for path in paths if path.stem in wanted]
    missing = sorted(wanted - {path.stem for path in selected})
    if missing:
        raise ValueError(f"unknown id(s): {', '.join(missing)}")
    return selected


def output_path(data: dict[str, Any]) -> Path:
    return ROOT / data["output"] / "index.html"


def canonical_url(data: dict[str, Any]) -> str:
    return f"{BASE_URL}/{data['output']}/"


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_facts(items: list[dict[str, str]]) -> str:
    return "".join(
        '<div class="home-facts__row">'
        f'<dt>{esc(item["label"])}</dt>'
        f'<dd>{esc(item["value"])}</dd>'
        '</div>'
        for item in items
    )


def render_related(items: list[dict[str, str]]) -> str:
    return "".join(
        f'<a href="{esc(item["href"])}">'
        f'<strong>{esc(item["title"])}</strong>'
        f'<span>{esc(item["description"])}</span>'
        '</a>'
        for item in items
    )


def render_faq(items: list[dict[str, str]]) -> str:
    return "".join(
        '<details>'
        f'<summary>{esc(item["question"])}</summary>'
        f'<p>{esc(item["answer"])}</p>'
        '</details>'
        for item in items
    )


def render_sources(items: list[dict[str, str]]) -> str:
    return "".join(
        '<li>根拠：'
        f'<a href="{esc(item["url"])}" target="_blank" '
        f'rel="noopener noreferrer">{esc(item["label"])}</a>'
        '</li>'
        for item in items
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
    canonical = canonical_url(data)
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
        "checked_at_display": esc(build_mobile_sim.format_checked_at(checked_at)),
        "verdict_title": esc(data["verdict_title"]),
        "verdict": esc(data["verdict"]),
        "badges": "".join(f"<span>{esc(item)}</span>" for item in data["badges"]),
        "fit": render_list(data["fit"]),
        "not_fit": render_list(data["not_fit"]),
        "checklist": render_list(data["checklist"]),
        "cta": monetization.render_cta(
            data["cta"],
            container_class="sim-cta",
            link_class="sim-cta__button",
            note_class="sim-cta__note",
            tracking_class="sim-cta__tracking",
            creative_class="sim-cta__creative",
        ),
        "facts": render_facts(data["facts"]),
        "cautions": render_list(data["cautions"]),
        "sources": render_sources(data["sources"]),
        "related": render_related(data["related"]),
        "faq": render_faq(data["faq"]),
        "seo_jsonld": render_jsonld(data, canonical).replace("</", "<\\/"),
    }
    rendered = template.substitute(values)
    cleaned = "\n".join(line.rstrip() for line in rendered.splitlines())
    return cleaned.rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("ids", nargs="*")
    args = parser.parse_args()

    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    failures = 0
    try:
        for path in data_paths(args.ids):
            data = load_data(path)
            output = output_path(data)
            rendered = render_page(data, template)
            if args.check:
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
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
