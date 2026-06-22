#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from string import Template
from typing import Any

import site_common
import public_assets

ROOT = Path(__file__).resolve().parents[1]
HOME_DATA_PATH = ROOT / "data" / "site-foundation" / "home.json"
PAGE_DIR = ROOT / "data" / "site-foundation" / "pages"
HOME_TEMPLATE_PATH = ROOT / "templates" / "site-home.html"
INFO_TEMPLATE_PATH = ROOT / "templates" / "site-info.html"
EXPECTED_OUTPUTS = {
    "index.html",
    "404.html",
    "about/index.html",
    "contact/index.html",
    "policy/index.html",
    "privacy/index.html",
}
NAV_LINKS = [
    ("/mobile-sim/", "スマホ・回線"),
    ("/point-site/", "ポイ活"),
    ("/shopping/", "買い物"),
    ("/credit-card/", "クレカ"),
    ("/account-opening/", "口座"),
    ("/travel/", "旅行・移動"),
]
INFO_LINKS = [
    ("/policy/", "PR表記"),
    ("/privacy/", "プライバシー"),
    ("/about/", "運営者情報"),
    ("/contact/", "お問い合わせ"),
]


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path}: root must be an object")
    return value


def require_string(path: Path, data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}: {key} must be a non-empty string")
    return value


def require_list(path: Path, data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{path}: {key} must be a list")
    return value


def validate_output(path: Path, output: str) -> None:
    if output not in EXPECTED_OUTPUTS:
        raise ValueError(f"{path}: unsupported output: {output}")


def canonical_for(output: str) -> str:
    if output == "index.html":
        return f"{site_common.BASE_URL}/"
    if output == "404.html":
        return f"{site_common.BASE_URL}/404.html"
    return f"{site_common.BASE_URL}/{output.removesuffix('index.html')}"


def load_home() -> dict[str, Any]:
    path = HOME_DATA_PATH
    data = load_json(path)
    for key in (
        "page_type",
        "output",
        "title",
        "description",
        "eyebrow",
        "h1",
        "lead",
        "checked_at",
    ):
        require_string(path, data, key)
    if data["page_type"] != "home":
        raise ValueError(f"{path}: page_type must be home")
    validate_output(path, data["output"])
    site_common.parse_date(data["checked_at"], path)

    proofs = require_list(path, data, "proofs")
    if not proofs or not all(isinstance(item, str) and item.strip() for item in proofs):
        raise ValueError(f"{path}: proofs must be non-empty strings")

    categories = require_list(path, data, "categories")
    if len(categories) != len(NAV_LINKS):
        raise ValueError(f"{path}: categories must contain {len(NAV_LINKS)} entries")
    seen: set[str] = set()
    for item in categories:
        if not isinstance(item, dict):
            raise ValueError(f"{path}: category entries must be objects")
        for key in ("href", "label", "title", "description"):
            require_string(path, item, key)
        href = item["href"]
        if not href.startswith("/") or not href.endswith("/"):
            raise ValueError(f"{path}: category href must be a site-relative directory URL")
        if href in seen:
            raise ValueError(f"{path}: duplicate category href: {href}")
        seen.add(href)
    if seen != {href for href, _ in NAV_LINKS}:
        raise ValueError(f"{path}: category hrefs must match the main navigation")
    return data


def load_page(path: Path) -> dict[str, Any]:
    data = load_json(path)
    for key in (
        "page_type",
        "output",
        "breadcrumb_label",
        "title",
        "description",
        "eyebrow",
        "h1",
        "lead",
        "checked_at",
    ):
        require_string(path, data, key)
    if data["page_type"] not in {"info", "error"}:
        raise ValueError(f"{path}: page_type must be info or error")
    validate_output(path, data["output"])
    site_common.parse_date(data["checked_at"], path)
    sections = require_list(path, data, "sections")
    actions = require_list(path, data, "actions")
    if data["page_type"] == "info" and not sections:
        raise ValueError(f"{path}: info pages require sections")
    for section in sections:
        if not isinstance(section, dict):
            raise ValueError(f"{path}: section entries must be objects")
        for key in ("label", "title", "body"):
            require_string(path, section, key)
        link = section.get("link")
        if link is not None:
            if not isinstance(link, dict):
                raise ValueError(f"{path}: section link must be an object")
            require_string(path, link, "href")
            require_string(path, link, "label")
            href = link["href"]
            if not (href.startswith("/") or href.startswith("mailto:")):
                raise ValueError(f"{path}: section link must be site-relative or mailto")
    for action in actions:
        if not isinstance(action, dict):
            raise ValueError(f"{path}: action entries must be objects")
        require_string(path, action, "href")
        require_string(path, action, "label")
        if not action["href"].startswith("/"):
            raise ValueError(f"{path}: action href must be site-relative")
    return data


def render_main_nav() -> str:
    return "".join(
        f'<a href="{site_common.esc(href)}">{site_common.esc(label)}</a>'
        for href, label in NAV_LINKS
    )


def render_side_nav() -> str:
    category_links = "".join(
        f'<a href="{site_common.esc(href)}">{site_common.esc(label)}</a>'
        for href, label in NAV_LINKS
    )
    info_links = "".join(
        f'<a href="{site_common.esc(href)}">{site_common.esc(label)}</a>'
        for href, label in INFO_LINKS
    )
    return (
        '<div class="foundation-side-group"><p>主要カテゴリ</p>'
        f'{category_links}</div>'
        '<div class="foundation-side-group"><p>サイト情報</p>'
        f'{info_links}</div>'
    )


def render_footer() -> str:
    links = "".join(
        f'<a href="{site_common.esc(href)}">{site_common.esc(label)}</a>'
        for href, label in INFO_LINKS
    )
    return (
        '<footer class="foundation-footer"><div class="foundation-footer__inner">'
        '<div><strong>スマホ小銭研究所</strong><p>条件を見て、対象なら拾う。</p></div>'
        '<div><nav aria-label="フッター">'
        f'{links}</nav><nav class="foundation-footer-social" aria-label="SNSリンク">'
        '<a href="https://x.com/smart_kozeni" target="_blank" rel="noopener noreferrer">'
        '<img src="/assets/images/social-x.svg?v=social1" alt="" width="20" height="20" loading="lazy" decoding="async"><span>X</span></a>'
        '<a href="https://www.instagram.com/smart_kozeni/" target="_blank" rel="noopener noreferrer">'
        '<img src="/assets/images/social-instagram.svg?v=social1" alt="" width="20" height="20" loading="lazy" decoding="async"><span>Instagram</span></a>'
        '</nav></div></div></footer>'
    )


def render_categories(items: list[dict[str, str]]) -> str:
    return "".join(
        '<a class="foundation-category-card" '
        f'href="{site_common.esc(item["href"])}">'
        f'<small>{site_common.esc(item["label"])}</small>'
        f'<h3>{site_common.esc(item["title"])}</h3>'
        f'<p>{site_common.esc(item["description"])}</p>'
        '<strong>条件を確認する →</strong></a>'
        for item in items
    )


def render_sections(items: list[dict[str, Any]]) -> str:
    rows: list[str] = []
    for item in items:
        link = item.get("link")
        link_html = ""
        if link:
            link_html = (
                f'<a href="{site_common.esc(link["href"])}">'
                f'{site_common.esc(link["label"])}</a>'
            )
        rows.append(
            '<section class="foundation-info-card">'
            f'<p class="foundation-label">{site_common.esc(item["label"])}</p>'
            f'<h2>{site_common.esc(item["title"])}</h2>'
            f'<p>{site_common.esc(item["body"])}</p>'
            f'{link_html}</section>'
        )
    return "".join(rows)


def render_actions(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    links = "".join(
        f'<a href="{site_common.esc(item["href"])}">{site_common.esc(item["label"])}</a>'
        for item in items
    )
    return f'<nav class="foundation-actions" aria-label="次の移動先">{links}</nav>'


def render_home(data: dict[str, Any], template: Template) -> str:
    canonical = canonical_for(data["output"])
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "canonical": canonical,
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=[("ホーム", canonical)],
        ),
        "main_nav": render_main_nav(),
        "side_nav": render_side_nav(),
        "eyebrow": site_common.esc(data["eyebrow"]),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "proofs": "".join(f'<span>{site_common.esc(item)}</span>' for item in data["proofs"]),
        "categories": render_categories(data["categories"]),
        "footer": render_footer(),
    }
    return site_common.clean_rendered(template.safe_substitute(values))


def render_page(data: dict[str, Any], template: Template) -> str:
    canonical = canonical_for(data["output"])
    breadcrumbs = [
        ("ホーム", f"{site_common.BASE_URL}/"),
        (data["breadcrumb_label"], canonical),
    ]
    values = {
        "title": site_common.esc(data["title"]),
        "description": site_common.esc(data["description"]),
        "robots": site_common.esc(data.get("robots", "index,follow,max-image-preview:large")),
        "canonical": canonical,
        "seo_jsonld": site_common.render_page_jsonld(
            canonical=canonical,
            title=data["title"],
            description=data["description"],
            checked_at=data["checked_at"],
            breadcrumbs=breadcrumbs,
        ),
        "body_class": "foundation-error" if data["page_type"] == "error" else "",
        "main_nav": render_main_nav(),
        "breadcrumb_label": site_common.esc(data["breadcrumb_label"]),
        "eyebrow": site_common.esc(data["eyebrow"]),
        "h1": site_common.esc(data["h1"]),
        "lead": site_common.esc(data["lead"]),
        "checked_at": site_common.esc(data["checked_at"]),
        "checked_at_display": site_common.format_date(site_common.parse_date(data["checked_at"], Path(data["output"]))),
        "sections": render_sections(data["sections"]),
        "actions": render_actions(data["actions"]),
        "footer": render_footer(),
    }
    return site_common.clean_rendered(template.safe_substitute(values))


def build_records() -> list[tuple[Path, dict[str, Any], Path, str]]:
    home_template = public_assets.load_template(HOME_TEMPLATE_PATH)
    info_template = public_assets.load_template(INFO_TEMPLATE_PATH)
    home = load_home()
    records: list[tuple[Path, dict[str, Any], Path, str]] = [
        (HOME_DATA_PATH, home, ROOT / home["output"], render_home(home, home_template))
    ]
    for path in sorted(PAGE_DIR.glob("*.json")):
        data = load_page(path)
        records.append((path, data, ROOT / data["output"], render_page(data, info_template)))
    outputs = {output.relative_to(ROOT).as_posix() for _, _, output, _ in records}
    if outputs != EXPECTED_OUTPUTS:
        raise ValueError(f"expected {sorted(EXPECTED_OUTPUTS)}, got {sorted(outputs)}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failed = False
    for _, _, output, rendered in build_records():
        rel = output.relative_to(ROOT)
        if args.check:
            if not output.exists() or output.read_text(encoding="utf-8") != rendered:
                print(f"NG: {rel}")
                failed = True
            else:
                print(f"OK: {rel}")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(rendered, encoding="utf-8")
            print(f"WROTE: {rel}")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
