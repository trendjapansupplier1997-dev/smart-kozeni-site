#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from string import Template
from typing import Any

import monetization
import site_common

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "tiktok-lite" / "pages"
HUB_PATH = ROOT / "data" / "tiktok-lite-hub.json"
GUIDE_TEMPLATE_PATH = ROOT / "templates" / "tiktok-lite-guide.html"
HUB_TEMPLATE_PATH = ROOT / "templates" / "tiktok-lite-hub.html"
STYLE_HREF = "/assets/kozeni-tiktok-lite.v1.css"
PROGRAM_ID = "tiktok-lite-direct-referral"
EXPECTED_SLUGS = {
    "checklist",
    "conditions",
    "earn",
    "invite-code",
    "link-not-open",
    "not-eligible",
    "reward-timing",
}
SLUG_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def require_strings(
    path: Path,
    data: dict[str, Any],
    keys: set[str],
) -> None:
    for key in sorted(keys):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"{path}: {key} must be a non-empty string")


def require_list(
    path: Path,
    data: dict[str, Any],
    key: str,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path}: {key} must be a non-empty list")
    return value


def validate_internal_link(path: Path, item: dict[str, Any]) -> None:
    require_strings(path, item, {"href", "title", "description"})
    if not item["href"].startswith("/"):
        raise ValueError(f"{path}: href must be site-relative: {item['href']}")


def canonical_for_slug(slug: str) -> str:
    return f"{site_common.BASE_URL}/tiktok-lite/{slug}/"


def output_for_slug(slug: str) -> Path:
    return ROOT / "tiktok-lite" / slug / "index.html"


def combined_jsonld(
    *,
    canonical: str,
    title: str,
    description: str,
    checked_at: str,
    breadcrumbs: list[tuple[str, str]],
    faq: list[dict[str, str]],
) -> str:
    graph = json.loads(
        site_common.render_page_jsonld(
            canonical=canonical,
            title=title,
            description=description,
            checked_at=checked_at,
            breadcrumbs=breadcrumbs,
        )
    )
    if faq:
        graph["@graph"].append(
            {
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
                    for item in faq
                ],
            }
        )
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":"))


def load_pages() -> dict[str, dict[str, Any]]:
    pages: dict[str, dict[str, Any]] = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        data = load_json(path)
        require_strings(
            path,
            data,
            {
                "page_type",
                "slug",
                "breadcrumb_label",
                "title",
                "description",
                "eyebrow",
                "h1",
                "lead",
                "checked_at",
                "checklist_title",
                "note",
            },
        )
        if data["page_type"] != "guide":
            raise ValueError(f"{path}: unsupported page_type")
        slug = data["slug"]
        if path.stem != slug or not SLUG_RE.fullmatch(slug):
            raise ValueError(f"{path}: invalid slug")
        if slug in pages:
            raise ValueError(f"{path}: duplicate slug")
        site_common.parse_date(data["checked_at"], path)

        cards = require_list(path, data, "cards")
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError(f"{path}: cards entries must be objects")
            require_strings(path, card, {"label", "title", "description"})

        checklist = require_list(path, data, "checklist")
        if not all(isinstance(item, str) and item.strip() for item in checklist):
            raise ValueError(f"{path}: checklist entries must be strings")

        faq = data.get("faq", [])
        if not isinstance(faq, list):
            raise ValueError(f"{path}: faq must be a list")
        for item in faq:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: faq entries must be objects")
            require_strings(path, item, {"question", "answer"})
        if faq:
            require_strings(path, data, {"faq_title", "faq_intro"})

        steps = data.get("steps", [])
        if not isinstance(steps, list):
            raise ValueError(f"{path}: steps must be a list")
        for item in steps:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: steps entries must be objects")
            require_strings(path, item, {"title", "description"})
        if steps:
            require_strings(path, data, {"steps_title"})

        related = require_list(path, data, "related")
        for item in related:
            if not isinstance(item, dict):
                raise ValueError(f"{path}: related entries must be objects")
            validate_internal_link(path, item)

        cta_spec = data.get("cta")
        if cta_spec is not None:
            data["cta"] = monetization.resolve_cta(cta_spec, path)
            if data["cta"]["program_id"] != PROGRAM_ID:
                raise ValueError(f"{path}: unexpected referral program")
        if data.get("show_referral_code") is True:
            if slug != "invite-code":
                raise ValueError(f"{path}: only invite-code may show referral code")
            if "cta" not in data:
                raise ValueError(f"{path}: referral code page requires CTA")
            if not str(data["cta"].get("referral_code", "")).strip():
                raise ValueError(f"{path}: referral code is missing from registry")
        elif "show_referral_code" in data and data["show_referral_code"] is not False:
            raise ValueError(f"{path}: show_referral_code must be boolean")

        pages[slug] = data

    if set(pages) != EXPECTED_SLUGS:
        raise ValueError(
            f"{DATA_DIR}: expected {sorted(EXPECTED_SLUGS)}, got {sorted(pages)}"
        )
    return pages


def load_hub() -> dict[str, Any]:
    data = load_json(HUB_PATH)
    require_strings(
        HUB_PATH,
        data,
        {"title", "description", "h1", "lead", "checked_at", "note"},
    )
    site_common.parse_date(data["checked_at"], HUB_PATH)

    route_cards = require_list(HUB_PATH, data, "route_cards")
    for item in route_cards:
        if not isinstance(item, dict):
            raise ValueError(f"{HUB_PATH}: route_cards entries must be objects")
        require_strings(
            HUB_PATH,
            item,
            {"tag", "title", "description", "href", "label"},
        )
        if not item["href"].startswith("/"):
            raise ValueError(f"{HUB_PATH}: route href must be site-relative")

    sections = require_list(HUB_PATH, data, "sections")
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError(f"{HUB_PATH}: sections entries must be objects")
        require_strings(HUB_PATH, section, {"title"})
        cards = require_list(HUB_PATH, section, "cards")
        for card in cards:
            if not isinstance(card, dict):
                raise ValueError(f"{HUB_PATH}: cards entries must be objects")
            require_strings(
                HUB_PATH,
                card,
                {"href", "tag", "title", "description"},
            )
            if not card["href"].startswith("/"):
                raise ValueError(f"{HUB_PATH}: card href must be site-relative")

    checks = require_list(HUB_PATH, data, "checks")
    for item in checks:
        if not isinstance(item, dict):
            raise ValueError(f"{HUB_PATH}: checks entries must be objects")
        require_strings(HUB_PATH, item, {"label", "title", "description"})

    data["cta"] = monetization.resolve_cta(data.get("cta"), HUB_PATH)
    if data["cta"]["program_id"] != PROGRAM_ID:
        raise ValueError(f"{HUB_PATH}: unexpected referral program")
    return data


def render_cards(items: list[dict[str, str]]) -> str:
    return "".join(
        '<article class="tiktok-card">'
        f'<span class="tiktok-tag">{site_common.esc(item["label"])}</span>'
        f'<h3>{site_common.esc(item["title"])}</h3>'
        f'<p>{site_common.esc(item["description"])}</p>'
        "</article>"
        for item in items
    )


def render_related(items: list[dict[str, str]]) -> str:
    return site_common.render_related(items)


def render_cta(cta: dict[str, Any]) -> str:
    return monetization.render_cta(
        cta,
        container_class="tiktok-cta",
        link_class="tiktok-cta__link",
        note_class="tiktok-cta__note",
        tracking_class="tiktok-cta__tracking",
        creative_class="tiktok-cta__creative",
    )


def render_page(data: dict[str, Any], template: Template) -> str:
    canonical = canonical_for_slug(data["slug"])
    faq = data.get("faq", [])
    cards = render_cards(data["cards"])
    checklist = site_common.render_list(data["checklist"])

    steps_section = ""
    if data.get("steps"):
        steps = "".join(
            '<div class="tiktok-step">'
            f'<span class="tiktok-step__no">{index}</span>'
            '<div>'
            f'<strong>{site_common.esc(item["title"])}</strong>'
            f'<span>{site_common.esc(item["description"])}</span>'
            "</div></div>"
            for index, item in enumerate(data["steps"], 1)
        )
        steps_section = (
            '<section class="tiktok-panel" aria-labelledby="steps-title">'
            '<p class="tiktok-label">流れ</p>'
            f'<h2 id="steps-title">{site_common.esc(data["steps_title"])}</h2>'
            f'<div class="tiktok-steps">{steps}</div>'
            "</section>"
        )

    referral_code_section = ""
    if data.get("show_referral_code"):
        referral_code_section = (
            '<section class="tiktok-panel tiktok-code" '
            'aria-labelledby="referral-code-title">'
            '<p class="tiktok-label">控え</p>'
            '<h2 id="referral-code-title">招待コード</h2>'
            f'<code>{site_common.esc(data["cta"]["referral_code"])}</code>'
            '<p>入力欄が表示された場合だけ使用し、公式画面の案内を優先してください。</p>'
            "</section>"
        )

    cta_section = ""
    if data.get("cta"):
        cta_section = (
            '<section class="tiktok-panel" aria-labelledby="register-title">'
            '<p class="tiktok-label">紹介リンク</p>'
            '<h2 id="register-title">現在の条件を確認して進む</h2>'
            '<p>対象条件、必要タスク、期限は遷移先の公式表示で確認してください。</p>'
            f'{render_cta(data["cta"])}'
            "</section>"
        )

    faq_section = ""
    if faq:
        faq_section = (
            '<section class="tiktok-panel" aria-labelledby="faq-title">'
            f'<h2 id="faq-title">{site_common.esc(data["faq_title"])}</h2>'
            f'<p>{site_common.esc(data["faq_intro"])}</p>'
            f'<div class="tiktok-faq">{site_common.render_faq(faq)}</div>'
            "</section>"
        )

    rendered = template.substitute(
        title=site_common.esc(data["title"]),
        description=site_common.esc(data["description"]),
        canonical=canonical,
        seo_jsonld=combined_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[
                ("ホーム", f"{site_common.BASE_URL}/"),
                ("ポイ活", f"{site_common.BASE_URL}/point-site/"),
                ("TikTok Lite", f"{site_common.BASE_URL}/tiktok-lite/"),
                (data["breadcrumb_label"], canonical),
            ],
            faq=faq,
        ),
        breadcrumb_label=site_common.esc(data["breadcrumb_label"]),
        eyebrow=site_common.esc(data["eyebrow"]),
        h1=site_common.esc(data["h1"]),
        lead=site_common.esc(data["lead"]),
        checked_at=data["checked_at"],
        checked_at_display=site_common.format_date(
            site_common.parse_date(data["checked_at"], DATA_DIR / f'{data["slug"]}.json')
        ),
        cards=cards,
        referral_code_section=referral_code_section,
        checklist_title=site_common.esc(data["checklist_title"]),
        checklist=checklist,
        note=site_common.esc(data["note"]),
        steps_section=steps_section,
        cta_section=cta_section,
        faq_section=faq_section,
        related=render_related(data["related"]),
    )
    return site_common.clean_rendered(rendered)


def render_hub(data: dict[str, Any], template: Template) -> str:
    canonical = f"{site_common.BASE_URL}/tiktok-lite/"
    route_cards = "".join(
        f'<a href="{site_common.esc(item["href"])}">'
        f'<span class="tiktok-tag">{site_common.esc(item["tag"])}</span>'
        f'<strong>{site_common.esc(item["title"])}</strong>'
        f'<span>{site_common.esc(item["description"])}</span>'
        f'<span class="tiktok-action">{site_common.esc(item["label"])} →</span>'
        "</a>"
        for item in data["route_cards"]
    )
    sections = "".join(
        '<section class="tiktok-panel">'
        f'<h2>{site_common.esc(section["title"])}</h2>'
        '<div class="tiktok-card-grid">'
        + "".join(
            f'<a class="tiktok-card" href="{site_common.esc(card["href"])}">'
            f'<span class="tiktok-tag">{site_common.esc(card["tag"])}</span>'
            f'<h3>{site_common.esc(card["title"])}</h3>'
            f'<p>{site_common.esc(card["description"])}</p>'
            '<span class="tiktok-action">確認する →</span>'
            "</a>"
            for card in section["cards"]
        )
        + "</div></section>"
        for section in data["sections"]
    )
    checks = render_cards(data["checks"])
    rendered = template.substitute(
        title=site_common.esc(data["title"]),
        description=site_common.esc(data["description"]),
        canonical=canonical,
        seo_jsonld=combined_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[
                ("ホーム", f"{site_common.BASE_URL}/"),
                ("ポイ活", f"{site_common.BASE_URL}/point-site/"),
                ("TikTok Lite", canonical),
            ],
            faq=[],
        ),
        h1=site_common.esc(data["h1"]),
        lead=site_common.esc(data["lead"]),
        checked_at=data["checked_at"],
        checked_at_display=site_common.format_date(
            site_common.parse_date(data["checked_at"], HUB_PATH)
        ),
        route_cards=route_cards,
        cta=render_cta(data["cta"]),
        sections=sections,
        checks=checks,
        note=site_common.esc(data["note"]),
    )
    return site_common.clean_rendered(rendered)


def build_outputs() -> dict[Path, str]:
    pages = load_pages()
    hub = load_hub()
    guide_template = Template(GUIDE_TEMPLATE_PATH.read_text(encoding="utf-8"))
    hub_template = Template(HUB_TEMPLATE_PATH.read_text(encoding="utf-8"))
    outputs = {
        output_for_slug(slug): render_page(data, guide_template)
        for slug, data in pages.items()
    }
    outputs[ROOT / "tiktok-lite" / "index.html"] = render_hub(hub, hub_template)
    if len(outputs) != 8:
        raise ValueError(f"expected 8 outputs, got {len(outputs)}")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failed = False
    for path, rendered in sorted(build_outputs().items()):
        rel = path.relative_to(ROOT)
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != rendered:
                print(f"NG: {rel}")
                failed = True
            else:
                print(f"OK: {rel}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
            print(f"WROTE: {rel}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
