#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from string import Template
from typing import Any

sys.dont_write_bytecode = True

import build_mobile_sim
import build_mobile_sim_hub
import build_mobile_sim_guides
import build_home_network
import build_credit_cards
import build_account_opening
import build_point_sites
import build_tiktok_lite
import build_lifestyle
import build_site_foundation
import monetization
import external_links
import public_assets
import seo

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(
    path for path in ROOT.rglob("*.html")
    if ".git" not in path.parts and "templates" not in path.parts
)
DATA_DIR = ROOT / "data" / "mobile-sim"
TEMPLATE_PATH = ROOT / "templates" / "mobile-sim-detail.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
STYLE_HREF = "/assets/kozeni-sim-detail.v2.css?v=45.0"

STATUS_WORDS = [
    "準備中",
    "一部公開",
    "強化中",
    "公開中",
    "coming soon",
    "工事中",
]

INLINE_EXECUTABLE_SCRIPT_RE = re.compile(
    r'<script\b(?![^>]*\bsrc\s*=)(?![^>]*\btype\s*=\s*["\']application/ld\+json["\'])[^>]*>',
    re.I,
)

OLD_URL_PATTERNS = [
    ("old mobile href", r'href=["\']/mobile(?:/|["\'])'),
    (
        "old trip-mile href",
        r'href=["\']/point-site/trip-mile(?:/|["\'])',
    ),
    ("old start-here href", r'href=["\']/start-here(?:/|["\'])'),
    (
        "old referral-code href",
        r'href=["\']/point-site/referral-code(?:/|["\'])',
    ),
]

FORBIDDEN_BY_SLUG = {'ahamo': ('紹介者7,000',
           '最大13,000ポイント',
           '紹介人数上限',
           'Rakuten Link',
           '楽天最強',
           'マイピタ',
           'マイそく'),
 'rakuten-mobile': ('大盛り110GB', '5分以内の国内通話無料', 'マイピタ', 'マイそく', 'dアカウント'),
 'mineo': ('Rakuten Link', '楽天最強', '大盛り110GB', '5分以内の国内通話無料', 'dアカウント'),
 'linemo': ('紹介者7,000', '大盛り110GB', 'マイピタ', '20GB超は3,278円'),
 'povo': ('紹介者7,000', '5分以内の国内通話無料', 'マイピタ', 'LINEMOベストプランV'),
 'nihon-tsushin': ('紹介者7,000', 'Rakuten Link', '大盛り110GB', 'LINEMOベストプランV', 'マイピタ'),
 'iijmio': ('Rakuten Link', '大盛り110GB', 'LINEMOベストプランV', 'トクトクプラン2', 'シンプル3 L'),
 'uq-mobile': ('Rakuten Link', '大盛り110GB', 'LINEMOベストプランV', 'ギガプランの音声SIM', 'シンプル3 L'),
 'ymobile': ('Rakuten Link', '大盛り110GB', 'トクトクプラン2', 'コミコミプランバリュー', 'ギガプランの音声SIM')}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def local_target_exists(href: str) -> bool:
    if href == "/":
        return (ROOT / "index.html").exists()
    if not href.startswith("/") or href.startswith("//"):
        return True

    clean = href.split("#", 1)[0].split("?", 1)[0]
    if not clean:
        return True
    target = ROOT / clean.lstrip("/")
    if clean.endswith("/"):
        target = target / "index.html"
    return target.exists()


def sitemap_urls() -> set[str]:
    if not SITEMAP_PATH.exists():
        return set()
    tree = ET.parse(SITEMAP_PATH)
    return {
        element.text.strip()
        for element in tree.getroot().iter()
        if element.tag.endswith("loc") and element.text
    }


def audit_generated_mobile_sim() -> list[str]:
    problems: list[str] = []
    template = public_assets.load_template(TEMPLATE_PATH)
    sitemap = sitemap_urls()

    for data_path in sorted(DATA_DIR.glob("*.json")):
        try:
            data = build_mobile_sim.load_data(data_path)
            rendered = build_mobile_sim.render_page(data, template)
        except Exception as error:
            problems.append(
                f"{data_path.relative_to(ROOT)}: invalid data: {error}"
            )
            continue

        slug = data["slug"]
        page = ROOT / "mobile-sim" / slug / "index.html"
        rel = page.relative_to(ROOT).as_posix()
        canonical = f"{build_mobile_sim.BASE_URL}/mobile-sim/{slug}/"

        if not page.exists():
            problems.append(f"{rel}: generated page is missing")
            continue

        source = read(page)
        if source != rendered:
            problems.append(f"{rel}: generated HTML is outdated")
        if source.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in source:
            problems.append(f"{rel}: inline style is forbidden")
        if source.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if '"@type":"FAQPage"' in source:
            problems.append(f"{rel}: FAQPage JSON-LD must not be emitted")
        if '"@type":"BreadcrumbList"' not in source:
            problems.append(f"{rel}: BreadcrumbList JSON-LD is required")
        if '"@type":"WebSite"' not in source:
            problems.append(f"{rel}: WebSite JSON-LD is required")
        if '"@type":"Organization"' not in source:
            problems.append(f"{rel}: Organization JSON-LD is required")
        if 'class="kozeni-breadcrumb"' not in source:
            problems.append(f"{rel}: visible breadcrumb is required")
        if f'href="{STYLE_HREF}"' not in source:
            problems.append(f"{rel}: shared SIM detail v2 CSS is missing")
        if "kozeni-sim-detail.v1.css" in source:
            problems.append(f"{rel}: legacy SIM detail CSS is referenced")
        if source.count("<details>") != len(data["faq"]):
            problems.append(f"{rel}: visible FAQ count differs from data")
        if f'<link rel="canonical" href="{canonical}">' not in source:
            problems.append(f"{rel}: canonical is incorrect")
        if f'"dateModified":"{data["checked_at"]}"' not in source:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if canonical not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")

        scripts = re.findall(
            r'<script type="application/ld\+json">(.*?)</script>',
            source,
            flags=re.S,
        )
        for script in scripts:
            try:
                json.loads(script)
            except json.JSONDecodeError as error:
                problems.append(f"{rel}: invalid JSON-LD: {error}")

        cta = data["cta"]
        ctas = re.findall(
            r'<a class="sim-cta__button"([^>]*)>'
            r'(.*?)</a>',
            source,
            flags=re.S,
        )
        if len(ctas) != 1:
            problems.append(f"{rel}: exactly one main CTA is required")
        else:
            attrs, body = ctas[0]
            expected_href = html.escape(cta["url"], quote=True)
            required_tokens = [
                f'href="{expected_href}"',
                'target="_blank"',
                "noopener",
                "noreferrer",
                'referrerpolicy="no-referrer-when-downgrade"',
            ]
            if cta["affiliate"]:
                required_tokens.extend(("nofollow", "sponsored"))
            for token in required_tokens:
                if token not in attrs:
                    problems.append(f"{rel}: CTA missing {token}")
            if html.escape(cta["label"]) not in body:
                problems.append(f"{rel}: CTA label differs from data")

        note_nodes = re.findall(
            r'<p class="sim-cta__note">(.*?)</p>',
            source,
            flags=re.S,
        )
        expected_note = html.escape(cta["note"])
        if expected_note:
            note_is_valid = note_nodes == [expected_note]
        else:
            note_is_valid = not note_nodes
        if not note_is_valid:
            problems.append(
                f"{rel}: CTA note differs from data"
            )

        tracking = cta.get("tracking_pixel_url")
        if tracking:
            expected = html.escape(tracking, quote=True)
            if source.count(expected) != 1:
                problems.append(
                    f"{rel}: tracking pixel URL must appear exactly once"
                )
        elif "sim-cta__tracking" in source:
            problems.append(f"{rel}: unexpected tracking pixel")

        source_lists = re.findall(
            r'<ul class="sim-source-list"[^>]*>(.*?)</ul>',
            source,
            flags=re.S,
        )
        if len(source_lists) != 1:
            problems.append(
                f"{rel}: exactly one official source list is required"
            )
        else:
            actual_sources = re.findall(
                r'<li>根拠：<a href="([^"]+)" '
                r'target="_blank" rel="noopener noreferrer">'
                r'(.*?)</a></li>',
                source_lists[0],
                flags=re.S,
            )
            expected_sources = [
                (
                    html.escape(item["url"], quote=True),
                    html.escape(item["label"]),
                )
                for item in data["sources"]
            ]
            if actual_sources != expected_sources:
                problems.append(
                    f"{rel}: official source list differs from data"
                )

        for item in data["related"]:
            href = item["href"]
            if not local_target_exists(href):
                problems.append(f"{rel}: broken related link: {href}")

        for phrase in FORBIDDEN_BY_SLUG.get(slug, ()):
            if phrase in source:
                problems.append(
                    f"{rel}: forbidden cross-brand phrase: {phrase}"
                )

    return problems



def audit_mobile_sim_hub() -> list[str]:
    problems: list[str] = []
    rel = "mobile-sim/index.html"
    page = ROOT / rel

    try:
        data = build_mobile_sim_hub.load_hub_data()
        details = build_mobile_sim_hub.load_featured_details(
            data["featured_slugs"]
        )
        template = public_assets.load_template(build_mobile_sim_hub.TEMPLATE_PATH)
        rendered = build_mobile_sim_hub.render_page(
            data,
            details,
            template,
        )
    except Exception as error:
        return [f"{rel}: invalid hub data: {error}"]

    if not page.exists():
        return [f"{rel}: generated hub page is missing"]

    source = read(page)
    checked_at = build_mobile_sim_hub.effective_checked_at(
        data,
        details,
    )

    if source != rendered:
        problems.append(f"{rel}: generated hub HTML is outdated")
    if source.count("<h1") != 1:
        problems.append(f"{rel}: h1 must appear exactly once")
    if "<style" in source:
        problems.append(f"{rel}: inline style is forbidden")
    if source.count('type="application/ld+json"') != 1:
        problems.append(f"{rel}: exactly one JSON-LD graph is required")
    if INLINE_EXECUTABLE_SCRIPT_RE.search(source):
        problems.append(f"{rel}: executable inline script is forbidden")
    if (
        f'href="{build_mobile_sim_hub.STYLE_HREF}"'
        not in source
    ):
        problems.append(f"{rel}: shared hub stylesheet is missing")
    if (
        f'<link rel="canonical" '
        f'href="{build_mobile_sim_hub.CANONICAL}">'
        not in source
    ):
        problems.append(f"{rel}: canonical is incorrect")
    if (
        f'"dateModified":"{checked_at.isoformat()}"'
        not in source
    ):
        problems.append(f"{rel}: dateModified is incorrect")
    if build_mobile_sim_hub.CANONICAL not in sitemap_urls():
        problems.append(f"{rel}: canonical URL is missing from sitemap")

    scripts = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        source,
        flags=re.S,
    )
    for script in scripts:
        try:
            json.loads(script)
        except json.JSONDecodeError as error:
            problems.append(f"{rel}: invalid JSON-LD: {error}")

    expected_rows = len(data["featured_slugs"])
    if source.count('class="hub-compare__row"') != expected_rows:
        problems.append(f"{rel}: comparison row count is incorrect")

    positions: list[int] = []
    for slug in data["featured_slugs"]:
        href = f'href="/mobile-sim/{slug}/"'
        position = source.find(href)
        if position < 0:
            problems.append(f"{rel}: featured link is missing: {slug}")
        positions.append(position)
    if positions != sorted(positions):
        problems.append(f"{rel}: featured order differs from data")

    for href in re.findall(r'href="(/[^"]*)"', source):
        if not local_target_exists(href):
            problems.append(f"{rel}: broken internal link: {href}")

    for token in (
        "trafficgate.net",
        "accesstrade.net",
        "affiliate-sp.docomo.ne.jp",
        "data-kozeni-route",
        "kozeni-line-quiz",
        "kozeni-helper-v40",
        "kozeni-sim-focus",
    ):
        if token in source:
            problems.append(f"{rel}: forbidden hub token: {token}")

    return problems



def audit_mobile_sim_guides() -> list[str]:
    problems: list[str] = []
    template = public_assets.load_template(build_mobile_sim_guides.TEMPLATE_PATH)
    sitemap = sitemap_urls()
    for data_path in build_mobile_sim_guides.data_paths([]):
        try:
            data = build_mobile_sim_guides.load_data(data_path)
            rendered = build_mobile_sim_guides.render_page(data, template)
        except Exception as error:
            problems.append(f"{data_path.relative_to(ROOT)}: invalid data: {error}")
            continue
        page = build_mobile_sim_guides.output_path(data)
        rel = page.relative_to(ROOT).as_posix()
        canonical = build_mobile_sim_guides.canonical_url(data)
        if not page.exists():
            problems.append(f"{rel}: generated guide is missing")
            continue
        text = read(page)
        if re.search(r"[ \\t]+$", text, flags=re.M):
            problems.append(
                f"{rel}: generated guide contains trailing whitespace"
            )
        if text != rendered:
            problems.append(f"{rel}: generated guide is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{rel}: inline style is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if f'href="{build_mobile_sim_guides.STYLE_HREF}"' not in text:
            problems.append(f"{rel}: shared guide CSS is missing")
        if f'<link rel="canonical" href="{canonical}">' not in text:
            problems.append(f"{rel}: canonical is incorrect")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if canonical not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if text.count("<details>") != len(data["faq"]):
            problems.append(f"{rel}: visible FAQ count differs from data")
        expected_cta = 1 if data["show_parent_cta"] else 0
        if text.count('class="sim-cta__button"') != expected_cta:
            problems.append(f"{rel}: main CTA count differs from data")
        if expected_cta:
            parent_cta = data["_parent"]["cta"]
            href = html.escape(parent_cta["url"], quote=True)
            if f'href="{href}"' not in text:
                problems.append(f"{rel}: parent CTA URL is missing")
            if parent_cta["affiliate"]:
                for token in ("nofollow", "sponsored", "noopener", "noreferrer"):
                    if token not in text:
                        problems.append(f"{rel}: affiliate CTA missing {token}")
        lists = re.findall(r'<ul class="guide-source-list">(.*?)</ul>', text, flags=re.S)
        expected_count = 1 if data["sources"] else 0
        if len(lists) != expected_count:
            problems.append(f"{rel}: source list count differs from data")
        elif data["sources"]:
            actual = re.findall(r'<li>根拠：<a href="([^"]+)" target="_blank" rel="noopener noreferrer">(.*?)</a></li>', lists[0], flags=re.S)
            expected = [(html.escape(x["url"], quote=True), html.escape(x["label"])) for x in data["sources"]]
            if actual != expected:
                problems.append(f"{rel}: official source list differs from data")
        for href in re.findall(r'href="(/[^"]*)"', text):
            if not local_target_exists(href):
                problems.append(f"{rel}: broken internal link: {href}")
        for token in ("brand-micro", "kozeni-helper-v40", "data-kozeni-route", "MOBILE CHECK"):
            if token in text:
                problems.append(f"{rel}: forbidden legacy guide token: {token}")
    return problems


def audit_home_network() -> list[str]:
    problems: list[str] = []
    template = public_assets.load_template(build_home_network.TEMPLATE_PATH)
    sitemap = sitemap_urls()

    for data_path in build_home_network.data_paths([]):
        try:
            data = build_home_network.load_data(data_path)
            rendered = build_home_network.render_page(data, template)
        except Exception as error:
            problems.append(
                f"{data_path.relative_to(ROOT)}: invalid data: {error}"
            )
            continue

        page = build_home_network.output_path(data)
        rel = page.relative_to(ROOT).as_posix()
        canonical = build_home_network.canonical_url(data)

        if not page.exists():
            problems.append(f"{rel}: generated home-network page is missing")
            continue

        text = read(page)
        if re.search(r"[ \t]+$", text, flags=re.M):
            problems.append(f"{rel}: trailing whitespace")
        if text != rendered:
            problems.append(f"{rel}: generated home-network HTML is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{rel}: inline style is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if f'href="{build_home_network.STYLE_HREF}"' not in text:
            problems.append(f"{rel}: shared home-network CSS is missing")
        if f'<link rel="canonical" href="{canonical}">' not in text:
            problems.append(f"{rel}: canonical is incorrect")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if canonical not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if text.count("<details>") != len(data["faq"]):
            problems.append(f"{rel}: visible FAQ count differs from data")

        cta = data["cta"]
        ctas = re.findall(
            r'<a class="sim-cta__button"([^>]*)>(.*?)</a>',
            text,
            flags=re.S,
        )
        if len(ctas) != 1:
            problems.append(f"{rel}: exactly one main CTA is required")
        else:
            attrs, body = ctas[0]
            expected_href = html.escape(cta["url"], quote=True)
            required = [
                f'href="{expected_href}"',
                'target="_blank"',
                "noopener",
                "noreferrer",
                'referrerpolicy="no-referrer-when-downgrade"',
            ]
            if cta["affiliate"]:
                required.extend(("nofollow", "sponsored"))
            for token in required:
                if token not in attrs:
                    problems.append(f"{rel}: CTA missing {token}")
            if html.escape(cta["label"]) not in body:
                problems.append(f"{rel}: CTA label differs from data")

        notes = re.findall(
            r'<p class="sim-cta__note">(.*?)</p>',
            text,
            flags=re.S,
        )
        expected_note = html.escape(cta["note"])
        if notes != ([expected_note] if expected_note else []):
            problems.append(f"{rel}: CTA note differs from data")

        tracking = cta.get("tracking_pixel_url")
        if tracking:
            expected = html.escape(tracking, quote=True)
            if text.count(expected) != 1:
                problems.append(
                    f"{rel}: tracking pixel URL must appear exactly once"
                )
        elif "sim-cta__tracking" in text:
            problems.append(f"{rel}: unexpected tracking pixel")

        source_lists = re.findall(
            r'<ul class="home-source-list">(.*?)</ul>',
            text,
            flags=re.S,
        )
        if len(source_lists) != 1:
            problems.append(f"{rel}: exactly one source list is required")
        else:
            actual = re.findall(
                r'<li>根拠：<a href="([^"]+)" '
                r'target="_blank" rel="noopener noreferrer">'
                r'(.*?)</a></li>',
                source_lists[0],
                flags=re.S,
            )
            expected = [
                (
                    html.escape(item["url"], quote=True),
                    html.escape(item["label"]),
                )
                for item in data["sources"]
            ]
            if actual != expected:
                problems.append(f"{rel}: official source list differs from data")

        for item in data["related"]:
            if not local_target_exists(item["href"]):
                problems.append(
                    f"{rel}: broken related link: {item['href']}"
                )

        for token in (
            "brand-micro",
            "data-kozeni-route",
            "kozeni-helper-v40",
            "homeWifiQuiz",
            "rakutenHikariQuiz",
        ):
            if token in text:
                problems.append(
                    f"{rel}: forbidden legacy home-network token: {token}"
                )

    redirects_path = ROOT / "_redirects"
    redirects = read(redirects_path) if redirects_path.exists() else ""
    for rule in (
        "/mobile-sim/no-construction-wifi /mobile-sim/home-wifi/ 301",
        "/mobile-sim/no-construction-wifi/ /mobile-sim/home-wifi/ 301",
    ):
        if rule not in redirects.splitlines():
            problems.append(f"_redirects: missing rule: {rule}")

    old_page = ROOT / "mobile-sim" / "no-construction-wifi" / "index.html"
    if old_page.exists():
        problems.append(
            "mobile-sim/no-construction-wifi/index.html: "
            "legacy redirect page must be deleted"
        )
    old_url = (
        "https://smart-kozeni.com/mobile-sim/no-construction-wifi/"
    )
    if old_url in sitemap:
        problems.append(
            "sitemap.xml: legacy no-construction-wifi URL must be removed"
        )

    return problems


def audit_monetization_registry() -> list[str]:
    problems: list[str] = []
    try:
        programs = monetization.load_registry()
    except Exception as error:
        return [f"data/monetization/programs.json: {error}"]

    if "tokyu-card-afb" not in programs:
        problems.append("data/monetization/programs.json: tokyu-card-afb is missing")
    else:
        program = programs["tokyu-card-afb"]
        if program.get("campaign_id") != "C980560u":
            problems.append("data/monetization/programs.json: TOKYU campaign_id differs from approved CSV")
        if program.get("media_id") != "H13605n":
            problems.append("data/monetization/programs.json: TOKYU media_id differs from approved CSV")
        creative = program.get("creative", {})
        if creative.get("id") != "450756":
            problems.append("data/monetization/programs.json: TOKYU creative id differs from approved CSV")
        if creative.get("width") != 320 or creative.get("height") != 100:
            problems.append("data/monetization/programs.json: TOKYU creative size differs from approved CSV")

    problems.extend(external_links.audit_contract(programs))

    return problems


def audit_credit_cards() -> list[str]:
    problems: list[str] = []
    sitemap = sitemap_urls()
    detail_template = public_assets.load_template(build_credit_cards.DETAIL_TEMPLATE_PATH)
    hub_template = public_assets.load_template(build_credit_cards.HUB_TEMPLATE_PATH)

    try:
        details = build_credit_cards.load_all_details()
    except Exception as error:
        return [f"data/credit-card: invalid detail data: {error}"]

    for slug, data in details.items():
        page = build_credit_cards.detail_output(data)
        rel = page.relative_to(ROOT).as_posix()
        canonical = build_credit_cards.detail_canonical(data)
        try:
            rendered = build_credit_cards.render_detail(data, detail_template)
        except Exception as error:
            problems.append(f"{rel}: render failed: {error}")
            continue
        if not page.exists():
            problems.append(f"{rel}: generated credit-card page is missing")
            continue
        text = read(page)
        if text != rendered:
            problems.append(f"{rel}: generated credit-card HTML is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{rel}: inline style is forbidden")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if f'href="{build_credit_cards.STYLE_HREF}"' not in text:
            problems.append(f"{rel}: shared credit-card CSS is missing")
        if f'<link rel="canonical" href="{canonical}">' not in text:
            problems.append(f"{rel}: canonical is incorrect")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if canonical not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if text.count("<details>") != len(data["faq"]):
            problems.append(f"{rel}: visible FAQ count differs from data")

        cta = data["cta"]
        anchors = re.findall(
            r'<a class="credit-cta__link(?: [^"]*)?"([^>]*)>(.*?)</a>',
            text,
            flags=re.S,
        )
        if len(anchors) != 1:
            problems.append(f"{rel}: exactly one credit CTA is required")
        else:
            attrs, body = anchors[0]
            expected_href = html.escape(cta["url"], quote=True)
            required = [
                f'href="{expected_href}"',
                'target="_blank"',
                "noopener",
                "noreferrer",
                'referrerpolicy="no-referrer-when-downgrade"',
            ]
            if cta["affiliate"]:
                required.extend(("nofollow", "sponsored"))
            for token in required:
                if token not in attrs:
                    problems.append(f"{rel}: CTA missing {token}")
            if cta.get("format", "text") == "banner":
                creative = cta["creative"]
                for token in (
                    html.escape(creative["image_url"], quote=True),
                    f'width="{creative["width"]}"',
                    f'height="{creative["height"]}"',
                    html.escape(creative["alt"]),
                ):
                    if token not in body:
                        problems.append(f"{rel}: banner CTA missing {token}")
            elif html.escape(cta["label"]) not in body:
                problems.append(f"{rel}: CTA label differs from data")

        notes = re.findall(
            r'<p class="credit-cta__note">(.*?)</p>',
            text,
            flags=re.S,
        )
        expected_note = html.escape(cta["note"])
        if notes != ([expected_note] if expected_note else []):
            problems.append(f"{rel}: CTA note differs from data")
        tracking = cta.get("tracking_pixel_url")
        if tracking:
            expected = html.escape(tracking, quote=True)
            if text.count(expected) != 1:
                problems.append(f"{rel}: tracking pixel must appear exactly once")
        elif "credit-cta__tracking" in text:
            problems.append(f"{rel}: unexpected tracking pixel")

        source_lists = re.findall(
            r'<ul class="credit-source-list"[^>]*>(.*?)</ul>',
            text,
            flags=re.S,
        )
        if len(source_lists) != 1:
            problems.append(f"{rel}: exactly one official source list is required")
        else:
            actual = re.findall(
                r'<li>根拠：<a href="([^"]+)" '
                r'target="_blank" rel="noopener noreferrer">(.*?)</a></li>',
                source_lists[0],
                flags=re.S,
            )
            expected = [
                (
                    html.escape(item["url"], quote=True),
                    html.escape(item["label"]),
                )
                for item in data["sources"]
            ]
            if actual != expected:
                problems.append(f"{rel}: official source list differs from data")
        for item in data["related"]:
            if not local_target_exists(item["href"]):
                problems.append(f"{rel}: broken related link: {item['href']}")
        for token in (
            "quiz-question",
            "quiz-submit",
            "credit-action-cta",
            "data-kozeni-route",
            "kozeni-helper-v40",
        ):
            if token in text:
                problems.append(f"{rel}: forbidden legacy credit-card token: {token}")

    try:
        hub_data = build_credit_cards.load_hub()
        rendered_hub = build_credit_cards.render_hub(
            hub_data,
            details,
            hub_template,
        )
    except Exception as error:
        problems.append(f"credit-card/index.html: hub render failed: {error}")
        return problems

    hub_page = ROOT / "credit-card" / "index.html"
    hub_rel = hub_page.relative_to(ROOT).as_posix()
    hub_canonical = f"{build_credit_cards.BASE_URL}/credit-card/"
    if not hub_page.exists():
        problems.append(f"{hub_rel}: generated credit-card hub is missing")
    else:
        text = read(hub_page)
        if text != rendered_hub:
            problems.append(f"{hub_rel}: generated credit-card hub is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{hub_rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{hub_rel}: inline style is forbidden")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{hub_rel}: executable inline script is forbidden")
        if f'href="{build_credit_cards.STYLE_HREF}"' not in text:
            problems.append(f"{hub_rel}: shared credit-card CSS is missing")
        if f'<link rel="canonical" href="{hub_canonical}">' not in text:
            problems.append(f"{hub_rel}: canonical is incorrect")
        if hub_canonical not in sitemap:
            problems.append(f"{hub_rel}: canonical URL is missing from sitemap")
        if text.count('class="credit-featured__tag"') != 3:
            problems.append(f"{hub_rel}: exactly three featured cards are required")
        positions = [
            text.find(f'href="/credit-card/{slug}/"')
            for slug in hub_data["featured_slugs"]
        ]
        if any(position < 0 for position in positions):
            problems.append(f"{hub_rel}: featured card link is missing")
        elif positions != sorted(positions):
            problems.append(f"{hub_rel}: featured card order differs from data")
        for domain in (
            "trafficgate.net",
            "valuecommerce.com",
            "afi-b.com",
            "accesstrade.net",
        ):
            if domain in text:
                problems.append(f"{hub_rel}: hub must not link directly to affiliate domain {domain}")
        for item in hub_data["purpose_links"]:
            if not local_target_exists(item["href"]):
                problems.append(f"{hub_rel}: broken purpose link: {item['href']}")

    tokyu = details.get("tokyu-card")
    if not tokyu or tokyu["cta"].get("program_id") != "tokyu-card-afb":
        problems.append("data/credit-card/tokyu-card.json: approved AFB program is not connected")

    return problems


def _audit_account_page_common(
    *,
    page: Path,
    rendered: str,
    canonical: str,
    sitemap: set[str],
) -> list[str]:
    problems: list[str] = []
    rel = page.relative_to(ROOT).as_posix()
    if not page.exists():
        return [f"{rel}: generated account-opening page is missing"]
    text = read(page)
    if text != rendered:
        problems.append(f"{rel}: generated account-opening HTML is outdated")
    if text.count("<h1") != 1:
        problems.append(f"{rel}: h1 must appear exactly once")
    if "<style" in text:
        problems.append(f"{rel}: inline style is forbidden")
    if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
        problems.append(f"{rel}: executable inline script is forbidden")
    if f'href="{build_account_opening.STYLE_HREF}"' not in text:
        problems.append(f"{rel}: shared account-opening CSS is missing")
    if f'<link rel="canonical" href="{canonical}">' not in text:
        problems.append(f"{rel}: canonical is incorrect")
    if canonical not in sitemap:
        problems.append(f"{rel}: canonical URL is missing from sitemap")
    for token in (
        "brand-micro",
        "data-filter",
        "accountFilters",
        "quiz-question",
        "quiz-submit",
        "data-kozeni-route",
        "kozeni-helper-v40",
    ):
        if token in text:
            problems.append(f"{rel}: forbidden legacy account-opening token: {token}")
    if re.search(r'\sstyle=["\']', text, flags=re.I):
        problems.append(f"{rel}: inline style attribute is forbidden")
    return problems


def audit_account_opening() -> list[str]:
    problems: list[str] = []
    sitemap = sitemap_urls()
    product_template = public_assets.load_template(build_account_opening.PRODUCT_TEMPLATE_PATH)
    guide_template = public_assets.load_template(build_account_opening.GUIDE_TEMPLATE_PATH)
    hub_template = public_assets.load_template(build_account_opening.HUB_TEMPLATE_PATH)

    products: dict[str, dict[str, Any]] = {}
    for data_path in build_account_opening.product_paths([]):
        try:
            data = build_account_opening.load_product(data_path)
            products[data["slug"]] = data
            rendered = build_account_opening.render_product(data, product_template)
        except Exception as error:
            problems.append(
                f"{data_path.relative_to(ROOT)}: product render failed: {error}"
            )
            continue

        page = build_account_opening.output_path(data["slug"])
        canonical = build_account_opening.canonical_url(data["slug"])
        problems.extend(
            _audit_account_page_common(
                page=page,
                rendered=rendered,
                canonical=canonical,
                sitemap=sitemap,
            )
        )
        if not page.exists():
            continue
        rel = page.relative_to(ROOT).as_posix()
        text = read(page)
        cta = data["cta"]
        anchors = re.findall(
            r'<a class="account-cta__link[^"]*"([^>]*)>(.*?)</a>',
            text,
            flags=re.S,
        )
        if len(anchors) != 1:
            problems.append(f"{rel}: exactly one CTA is required")
        else:
            attrs, body = anchors[0]
            required = [
                f'href="{html.escape(cta["url"], quote=True)}"',
                'target="_blank"',
                "noopener",
                "noreferrer",
                'referrerpolicy="no-referrer-when-downgrade"',
            ]
            if cta["affiliate"]:
                required.extend(("nofollow", "sponsored"))
            for token in required:
                if token not in attrs:
                    problems.append(f"{rel}: CTA missing {token}")
            if html.escape(cta["label"]) not in body:
                problems.append(f"{rel}: CTA label differs from data")

        expected_note = html.escape(cta["note"])
        notes = re.findall(
            r'<p class="account-cta__note">(.*?)</p>', text, flags=re.S
        )
        if notes != ([expected_note] if expected_note else []):
            problems.append(f"{rel}: CTA note differs from data")
        tracking = cta.get("tracking_pixel_url")
        if tracking:
            if text.count(html.escape(tracking, quote=True)) != 1:
                problems.append(f"{rel}: tracking pixel must appear exactly once")
        elif "account-cta__tracking" in text:
            problems.append(f"{rel}: unexpected tracking pixel")

        source_lists = re.findall(
            r'<ul class="account-source-list">(.*?)</ul>', text, flags=re.S
        )
        if len(source_lists) != 1:
            problems.append(f"{rel}: exactly one official source list is required")
        else:
            actual = re.findall(
                r'<li>根拠：<a href="([^"]+)" '
                r'target="_blank" rel="noopener noreferrer">(.*?)</a></li>',
                source_lists[0],
                flags=re.S,
            )
            expected = [
                (
                    html.escape(item["url"], quote=True),
                    html.escape(item["label"]),
                )
                for item in data["sources"]
            ]
            if actual != expected:
                problems.append(f"{rel}: official source list differs from data")
        for item in data["related"]:
            if not local_target_exists(item["href"]):
                problems.append(f"{rel}: broken related link: {item['href']}")

    guides: dict[str, dict[str, Any]] = {}
    for data_path in build_account_opening.guide_paths([]):
        try:
            data = build_account_opening.load_guide(data_path)
            guides[data["slug"]] = data
            rendered = build_account_opening.render_guide(data, guide_template)
        except Exception as error:
            problems.append(
                f"{data_path.relative_to(ROOT)}: guide render failed: {error}"
            )
            continue
        page = build_account_opening.output_path(data["slug"])
        canonical = build_account_opening.canonical_url(data["slug"])
        problems.extend(
            _audit_account_page_common(
                page=page,
                rendered=rendered,
                canonical=canonical,
                sitemap=sitemap,
            )
        )
        if page.exists():
            rel = page.relative_to(ROOT).as_posix()
            text = read(page)
            if "account-cta" in text:
                problems.append(f"{rel}: guide page must not contain a revenue CTA")
            if not local_target_exists(data["next"]["href"]):
                problems.append(f"{rel}: broken next link: {data['next']['href']}")

    try:
        hub_data = build_account_opening.load_hub()
        rendered_hub = build_account_opening.render_hub(hub_data, hub_template)
    except Exception as error:
        problems.append(f"account-opening/index.html: hub render failed: {error}")
        return problems

    hub_page = ROOT / "account-opening" / "index.html"
    hub_canonical = f"{build_account_opening.BASE_URL}/account-opening/"
    problems.extend(
        _audit_account_page_common(
            page=hub_page,
            rendered=rendered_hub,
            canonical=hub_canonical,
            sitemap=sitemap,
        )
    )
    if hub_page.exists():
        hub_rel = hub_page.relative_to(ROOT).as_posix()
        text = read(hub_page)
        expected_internal: set[str] = set()
        affiliate_cards: list[dict[str, Any]] = []
        for section in hub_data["sections"]:
            for card in section["cards"]:
                if card.get("href"):
                    expected_internal.add(card["href"])
                    if not local_target_exists(card["href"]):
                        problems.append(
                            f"{hub_rel}: broken hub card link: {card['href']}"
                        )
                else:
                    affiliate_cards.append(card)
        for href in expected_internal:
            if f'href="{html.escape(href, quote=True)}"' not in text:
                problems.append(f"{hub_rel}: hub card is missing: {href}")
        for item in hub_data["guides"]:
            if not local_target_exists(item["href"]):
                problems.append(
                    f"{hub_rel}: broken guide link: {item['href']}"
                )
        if len(affiliate_cards) != 1:
            problems.append(f"{hub_rel}: exactly one affiliate hub card is required")
        else:
            cta = affiliate_cards[0]["_cta"]
            expected_url = html.escape(cta["url"], quote=True)
            if text.count(expected_url) != 1:
                problems.append(
                    f"{hub_rel}: affiliate hub URL must appear exactly once"
                )
            for token in (
                "nofollow",
                "sponsored",
                "noopener",
                "noreferrer",
                'referrerpolicy="no-referrer-when-downgrade"',
            ):
                if token not in text:
                    problems.append(f"{hub_rel}: affiliate hub card missing {token}")
            if html.escape(cta["note"]) not in text:
                problems.append(f"{hub_rel}: affiliate PR note differs from registry")

    if products.get("matsui-sec", {}).get("cta", {}).get("program_id") != "matsui-ideco-a8":
        problems.append(
            "data/account-opening/products/matsui-sec.json: A8 program is not connected"
        )
    hub_programs = {
        card.get("program_id")
        for section in hub_data["sections"]
        for card in section["cards"]
        if card.get("program_id")
    }
    if "rakuten-securities-trafficgate" not in hub_programs:
        problems.append(
            "data/account-opening-hub.json: Rakuten Securities program is not connected"
        )
    return problems


def audit_point_sites() -> list[str]:
    problems: list[str] = []
    sitemap = sitemap_urls()
    try:
        outputs = build_point_sites.build_outputs()
        sites = build_point_sites.load_all_sites()
    except Exception as error:
        return [f"data/point-site: invalid point-site data: {error}"]

    if len(outputs) != 19:
        problems.append(f"point-site: expected 19 generated pages, got {len(outputs)}")

    expected_programs = {
        "chobirich-direct-referral",
        "hapitas-direct-referral",
        "kurashiru-reward-direct-referral",
        "moppy-direct-referral",
        "point-income-direct-referral",
        "pointtown-direct-referral",
        "powl-direct-referral",
        "trima-direct-referral",
    }
    actual_programs = {
        data["cta"]["program_id"]
        for data in sites.values()
    }
    if actual_programs != expected_programs:
        problems.append("data/point-site/sites: referral program set differs from expected")

    for page, rendered in sorted(outputs.items()):
        rel = page.relative_to(ROOT).as_posix()
        if not page.exists():
            problems.append(f"{rel}: generated point-site page is missing")
            continue
        text = read(page)
        if text != rendered:
            problems.append(f"{rel}: generated point-site HTML is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{rel}: inline style is forbidden")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'href="{build_point_sites.STYLE_HREF}"' not in text:
            problems.append(f"{rel}: shared point-site CSS is missing")
        if "kozeni-point.v1.css" in text:
            problems.append(f"{rel}: legacy mixed point CSS is referenced")
        if "data-kozeni-quiz" in text or "data-register-url" in text:
            problems.append(f"{rel}: legacy quiz contract remains")
        canonical_match = re.search(r'<link rel="canonical" href="([^"]+)">', text)
        if not canonical_match:
            problems.append(f"{rel}: canonical is missing")
        elif canonical_match.group(1) not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if 'class="kozeni-breadcrumb"' not in text:
            problems.append(f"{rel}: visible breadcrumb is required")

    for slug, data in sites.items():
        page = build_point_sites.detail_output(data)
        text = read(page)
        cta = data["cta"]
        expected_url = html.escape(cta["url"], quote=True)
        if text.count(expected_url) != 1:
            problems.append(f"{page.relative_to(ROOT)}: referral URL must appear exactly once")
        for token in ("nofollow", "sponsored", "noopener", "noreferrer", 'referrerpolicy="no-referrer-when-downgrade"'):
            if token not in text:
                problems.append(f"{page.relative_to(ROOT)}: CTA missing {token}")
        if html.escape(cta["note"]) not in text:
            problems.append(f"{page.relative_to(ROOT)}: PR note differs from registry")
        earn_text = read(build_point_sites.earn_output(data))
        if cta["url"] in earn_text:
            problems.append(f"{slug}/earn: referral URL must not be emitted")

    return problems



def audit_tiktok_lite() -> list[str]:
    problems: list[str] = []
    sitemap = sitemap_urls()
    try:
        outputs = build_tiktok_lite.build_outputs()
        pages = build_tiktok_lite.load_pages()
        hub = build_tiktok_lite.load_hub()
    except Exception as error:
        return [f"data/tiktok-lite: invalid TikTok Lite data: {error}"]

    if len(outputs) != 8:
        problems.append(
            f"tiktok-lite: expected 8 generated pages, got {len(outputs)}"
        )

    if hub["cta"]["program_id"] != build_tiktok_lite.PROGRAM_ID:
        problems.append(
            "data/tiktok-lite-hub.json: referral program differs from expected"
        )

    referral_url = hub["cta"]["url"]
    referral_code = str(hub["cta"].get("referral_code", ""))
    page_by_output = {
        build_tiktok_lite.output_for_slug(slug): data
        for slug, data in pages.items()
    }

    for page, rendered in sorted(outputs.items()):
        rel = page.relative_to(ROOT).as_posix()
        if not page.exists():
            problems.append(f"{rel}: generated TikTok Lite page is missing")
            continue
        text = read(page)
        if text != rendered:
            problems.append(f"{rel}: generated TikTok Lite HTML is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{rel}: inline style is forbidden")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'href="{build_tiktok_lite.STYLE_HREF}"' not in text:
            problems.append(f"{rel}: shared TikTok Lite CSS is missing")
        if "kozeni-point.v1.css" in text:
            problems.append(f"{rel}: legacy mixed point CSS is referenced")
        for token in (
            "data-kozeni-quiz",
            "data-register-url",
            "quiz-submit",
            "quiz-question",
        ):
            if token in text:
                problems.append(f"{rel}: legacy interactive token remains: {token}")
        canonical_match = re.search(
            r'<link rel="canonical" href="([^"]+)">',
            text,
        )
        if not canonical_match:
            problems.append(f"{rel}: canonical is missing")
        elif canonical_match.group(1) not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if 'class="kozeni-breadcrumb"' not in text:
            problems.append(f"{rel}: visible breadcrumb is required")

        data = page_by_output.get(page)
        cta = hub["cta"] if data is None else data.get("cta")
        if cta:
            expected_url = html.escape(referral_url, quote=True)
            if text.count(expected_url) != 1:
                problems.append(
                    f"{rel}: referral URL must appear exactly once"
                )
            for token in (
                "nofollow",
                "sponsored",
                "noopener",
                "noreferrer",
                'referrerpolicy="no-referrer-when-downgrade"',
            ):
                if token not in text:
                    problems.append(f"{rel}: referral CTA missing {token}")
            if html.escape(cta["note"]) not in text:
                problems.append(f"{rel}: PR note differs from registry")
        elif referral_url in text:
            problems.append(f"{rel}: page without CTA contains referral URL")

        if data is not None:
            if text.count("<details>") != len(data.get("faq", [])):
                problems.append(f"{rel}: visible FAQ count differs from data")
            for item in data["related"]:
                if not local_target_exists(item["href"]):
                    problems.append(
                        f"{rel}: broken related link: {item['href']}"
                    )

    invite_page = build_tiktok_lite.output_for_slug("invite-code")
    invite_text = read(invite_page)
    if not referral_code:
        problems.append(
            "data/monetization/programs.json: TikTok Lite referral_code is missing"
        )
    elif invite_text.count(html.escape(referral_code)) != 1:
        problems.append(
            "tiktok-lite/invite-code/index.html: referral code must appear once"
        )
    for page in outputs:
        if page != invite_page and referral_code and referral_code in read(page):
            problems.append(
                f"{page.relative_to(ROOT)}: referral code must only appear on invite-code"
            )

    for route in hub["route_cards"]:
        if not local_target_exists(route["href"]):
            problems.append(
                f"tiktok-lite/index.html: broken route link: {route['href']}"
            )
    for section in hub["sections"]:
        for card in section["cards"]:
            if not local_target_exists(card["href"]):
                problems.append(
                    f"tiktok-lite/index.html: broken card link: {card['href']}"
                )
    return problems


def audit_lifestyle() -> list[str]:
    problems: list[str] = []
    sitemap = sitemap_urls()
    try:
        records = build_lifestyle.build_records()
    except Exception as error:
        return [f"data/lifestyle: invalid lifestyle data: {error}"]

    if len(records) != 4:
        problems.append(f"lifestyle: expected 4 generated pages, got {len(records)}")

    for data_path, data, page, rendered in records:
        rel = page.relative_to(ROOT).as_posix()
        canonical = f"{build_lifestyle.site_common.BASE_URL}/" + data["output"].removesuffix("index.html")
        if not page.exists():
            problems.append(f"{rel}: generated lifestyle page is missing")
            continue
        text = read(page)
        if text != rendered:
            problems.append(f"{rel}: generated lifestyle HTML is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text or re.search(r"\sstyle=[\"']", text, flags=re.I):
            problems.append(f"{rel}: inline style is forbidden")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if f'href="{build_lifestyle.STYLE_HREF}"' not in text:
            problems.append(f"{rel}: shared lifestyle CSS is missing")
        if f'<link rel="canonical" href="{canonical}">' not in text:
            problems.append(f"{rel}: canonical is incorrect")
        if canonical not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if 'class="kozeni-breadcrumb"' not in text:
            problems.append(f"{rel}: visible breadcrumb is required")
        for token in ("shopping-main", "check-main", "travel-main", "cancel-main"):
            if token in text:
                problems.append(f"{rel}: legacy lifestyle token remains: {token}")

        for offer in data["offers"]:
            cta = offer["cta"]
            expected = html.escape(cta["url"], quote=True)
            if text.count(expected) != 1:
                problems.append(f"{rel}: {cta['program_id']} URL must appear exactly once")
            for token in ("nofollow", "sponsored", "noopener", "noreferrer", 'referrerpolicy="no-referrer-when-downgrade"'):
                if token not in text:
                    problems.append(f"{rel}: offer link missing {token}")
            if html.escape(cta["advertiser"]) not in text:
                problems.append(f"{rel}: offer advertiser differs from registry")

        for item in data["related"]:
            if not local_target_exists(item["href"]):
                problems.append(f"{rel}: broken related link: {item['href']}")
        if data["page_type"] == "hub":
            for card in data["cards"]:
                if "href" in card and not local_target_exists(card["href"]):
                    problems.append(f"{rel}: broken card link: {card['href']}")

    return problems


def audit_site_foundation() -> list[str]:
    problems: list[str] = []
    sitemap = sitemap_urls()
    try:
        records = build_site_foundation.build_records()
    except Exception as error:
        return [f"data/site-foundation: invalid foundation data: {error}"]

    if len(records) != 6:
        problems.append(
            f"site foundation: expected 6 generated pages, got {len(records)}"
        )

    forbidden_assets = (
        "assets/style.v36.css",
        "assets/kozeni-nav.v36.3.css",
        "assets/script.v36.js",
        "assets/kozeni-nav.v36.3.js",
        "assets/kozeni-home.v1.css",
        "assets/kozeni-menu.v1.css",
        "assets/kozeni-menu.v1.js",
    )
    for rel in forbidden_assets:
        if (ROOT / rel).exists():
            problems.append(f"{rel}: retired asset must be deleted")

    forbidden_tokens = (
        "style.v36.css",
        "kozeni-nav.v36.3",
        "script.v36.js",
        "kozeni-home.v1.css",
        "kozeni-menu.v1",
        "kozeni-nav-fallback",
        "sk-menu-toggle",
        "sk-left-menu",
        "kozeni-v363",
    )

    for _, data, page, rendered in records:
        rel = page.relative_to(ROOT).as_posix()
        canonical = build_site_foundation.canonical_for(rel)
        if not page.exists():
            problems.append(f"{rel}: generated foundation page is missing")
            continue
        text = read(page)
        if text != rendered:
            problems.append(f"{rel}: generated foundation HTML is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text or re.search(r"\sstyle=[\"']", text, flags=re.I):
            problems.append(f"{rel}: inline style is forbidden")
        if INLINE_EXECUTABLE_SCRIPT_RE.search(text):
            problems.append(f"{rel}: executable inline script is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if f'"dateModified":"{data["checked_at"]}"' not in text:
            problems.append(f"{rel}: dateModified differs from checked_at")
        if 'href="/assets/kozeni-site-foundation.v1.css?v=45.0"' not in text:
            problems.append(f"{rel}: shared foundation CSS is missing")
        if rel == "index.html" and 'src="/assets/kozeni-foundation-menu.v1.js"' not in text:
            problems.append(f"{rel}: foundation menu JS is missing")
        if f'<link rel="canonical" href="{canonical}">' not in text:
            problems.append(f"{rel}: canonical is incorrect")
        if rel != "404.html" and canonical not in sitemap:
            problems.append(f"{rel}: canonical URL is missing from sitemap")
        if rel == "404.html" and '<meta name="robots" content="noindex,follow">' not in text:
            problems.append(f"{rel}: 404 must be noindex,follow")
        if rel == "index.html":
            if 'data-foundation-menu-toggle' not in text or 'data-foundation-menu' not in text:
                problems.append(f"{rel}: home menu contract is missing")
        elif 'class="foundation-breadcrumb"' not in text:
            problems.append(f"{rel}: visible breadcrumb is required")
        for token in forbidden_tokens:
            if token in text:
                problems.append(f"{rel}: retired token remains: {token}")

        for href in re.findall(r'href=["\']([^"\']+)["\']', text, flags=re.I):
            if href.startswith("/") and not local_target_exists(href):
                problems.append(f"{rel}: broken local link: {href}")

    return problems

def show_list(
    title: str,
    items: list[str],
    problems: list[str],
) -> None:
    print(f"\n=== {title} ===")
    if not items:
        print("OK: none")
        return
    for item in items:
        print(item)
    problems.extend(items)


def main() -> int:
    css_refs: Counter[str] = Counter()
    js_refs: Counter[str] = Counter()
    missing_title: list[str] = []
    missing_description: list[str] = []
    missing_canonical: list[str] = []
    status_hits: list[str] = []
    old_url_hits: list[str] = []

    for path in HTML_FILES:
        text = read(path)
        rel = path.relative_to(ROOT).as_posix()

        for href in re.findall(
            r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']',
            text,
            flags=re.I,
        ):
            css_refs[href.split("?")[0]] += 1

        for src in re.findall(
            r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']',
            text,
            flags=re.I,
        ):
            js_refs[src.split("?")[0]] += 1

        if not re.search(r"<title>.*?</title>", text, flags=re.I | re.S):
            missing_title.append(rel)
        if not re.search(
            r'<meta[^>]+name=["\']description["\']',
            text,
            flags=re.I,
        ):
            missing_description.append(rel)
        if not re.search(
            r'<link[^>]+rel=["\']canonical["\']',
            text,
            flags=re.I,
        ):
            missing_canonical.append(rel)

        for word in STATUS_WORDS:
            if word in text:
                status_hits.append(f"{rel}: {word}")

        for label, pattern in OLD_URL_PATTERNS:
            if re.search(pattern, text):
                old_url_hits.append(f"{rel}: {label}")

    backup_files: list[str] = []
    for pattern in ("*.bak*", "*.tmp", "*.old", "*.orig", "*~"):
        for path in ROOT.rglob(pattern):
            if ".git" not in path.parts:
                backup_files.append(path.relative_to(ROOT).as_posix())

    mobile_sim_problems = audit_generated_mobile_sim()
    mobile_sim_hub_problems = audit_mobile_sim_hub()
    mobile_sim_guide_problems = audit_mobile_sim_guides()
    home_network_problems = audit_home_network()
    monetization_problems = audit_monetization_registry()
    credit_card_problems = audit_credit_cards()
    account_opening_problems = audit_account_opening()
    point_site_problems = audit_point_sites()
    tiktok_lite_problems = audit_tiktok_lite()
    lifestyle_problems = audit_lifestyle()
    site_foundation_problems = audit_site_foundation()
    public_asset_problems = public_assets.audit_public_assets()
    seo_problems = seo.audit_seo()

    print("=== kozeni site audit ===")
    print(f"HTML files: {len(HTML_FILES)}")

    print("\n=== CSS refs ===")
    for path, count in css_refs.most_common():
        print(f"{count:>3} {path}")

    print("\n=== JS refs ===")
    for path, count in js_refs.most_common():
        print(f"{count:>3} {path}")

    problems: list[str] = []
    show_list("missing title", missing_title, problems)
    show_list("missing description", missing_description, problems)
    show_list("missing canonical", missing_canonical, problems)
    show_list("unfinished/status words", status_hits, problems)
    show_list("old internal URL hrefs", old_url_hits, problems)
    show_list("backup/temp files", sorted(set(backup_files)), problems)
    show_list(
        "generated mobile SIM pages",
        mobile_sim_problems,
        problems,
    )
    show_list(
        "generated mobile SIM hub",
        mobile_sim_hub_problems,
        problems,
    )
    show_list(
        "generated mobile SIM guides",
        mobile_sim_guide_problems,
        problems,
    )
    show_list(
        "generated home network pages",
        home_network_problems,
        problems,
    )
    show_list(
        "monetization registry",
        monetization_problems,
        problems,
    )
    show_list(
        "generated credit-card pages",
        credit_card_problems,
        problems,
    )
    show_list(
        "generated account-opening pages",
        account_opening_problems,
        problems,
    )
    show_list(
        "generated point-site pages",
        point_site_problems,
        problems,
    )
    show_list(
        "generated TikTok Lite pages",
        tiktok_lite_problems,
        problems,
    )
    show_list(
        "generated shopping/travel pages",
        lifestyle_problems,
        problems,
    )
    show_list(
        "generated site foundation pages",
        site_foundation_problems,
        problems,
    )
    show_list(
        "public assets and site runtime",
        public_asset_problems,
        problems,
    )
    show_list(
        "SEO metadata, structured data, sitemap, and internal links",
        seo_problems,
        problems,
    )

    print("\n=== result ===")
    if problems:
        print(f"NG: {len(problems)} issue(s) found")
        return 1

    print("OK: no blocking hygiene issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
