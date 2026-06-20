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

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(
    path for path in ROOT.rglob("*.html")
    if ".git" not in path.parts
)
DATA_DIR = ROOT / "data" / "mobile-sim"
TEMPLATE_PATH = ROOT / "templates" / "mobile-sim-detail.html"
SITEMAP_PATH = ROOT / "sitemap.xml"
STYLE_HREF = "/assets/kozeni-sim-detail.v2.css"

STATUS_WORDS = [
    "準備中",
    "一部公開",
    "強化中",
    "公開中",
    "coming soon",
    "工事中",
]

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
    template = Template(read(TEMPLATE_PATH))
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
        template = Template(
            read(build_mobile_sim_hub.TEMPLATE_PATH)
        )
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
    if re.search(
        r'<script(?![^>]*type="application/ld\+json")',
        source,
        flags=re.I,
    ):
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
    template = Template(read(build_mobile_sim_guides.TEMPLATE_PATH))
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
        if text != rendered:
            problems.append(f"{rel}: generated guide is outdated")
        if text.count("<h1") != 1:
            problems.append(f"{rel}: h1 must appear exactly once")
        if "<style" in text:
            problems.append(f"{rel}: inline style is forbidden")
        if text.count('type="application/ld+json"') != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        if re.search(r'<script(?![^>]*type="application/ld\+json")', text, flags=re.I):
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

    print("\n=== result ===")
    if problems:
        print(f"NG: {len(problems)} issue(s) found")
        return 1

    print("OK: no blocking hygiene issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
