#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
from string import Template
from typing import Any, Mapping
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import repo_paths

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = "https://smart-kozeni.com"
SITE_NAME = "スマホ小銭研究所"
OG_LOCALE = "ja_JP"
SITEMAP_PATH = ROOT / "sitemap.xml"


@dataclass(frozen=True)
class PageRecord:
    output: str
    title: str
    description: str
    modified: str
    og_type: str
    indexable: bool = True

    @property
    def canonical(self) -> str:
        return canonical_for_output(self.output)


def canonical_for_output(output: str) -> str:
    if output == "index.html":
        return f"{BASE_URL}/"
    if output == "404.html":
        return f"{BASE_URL}/404.html"
    if not output.endswith("/index.html"):
        raise ValueError(f"unsupported generated HTML output: {output}")
    return f"{BASE_URL}/{output.removesuffix('index.html')}"


def _load(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: root must be an object")
    return data


def _require_text(data: Mapping[str, Any], key: str, path: Path) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path.relative_to(ROOT)}: {key} must be a non-empty string")
    return value


def _record(
    path: Path,
    data: Mapping[str, Any],
    output: str,
    *,
    og_type: str,
    indexable: bool = True,
) -> PageRecord:
    title = _require_text(data, "title", path)
    description = _require_text(data, "description", path)
    modified = _require_text(data, "checked_at", path)
    try:
        date.fromisoformat(modified)
    except ValueError as error:
        raise ValueError(f"{path.relative_to(ROOT)}: checked_at must be YYYY-MM-DD") from error
    if og_type not in {"article", "website"}:
        raise ValueError(f"unsupported og:type: {og_type}")
    return PageRecord(output, title, description, modified, og_type, indexable)


def page_catalog() -> tuple[PageRecord, ...]:
    records: list[PageRecord] = []

    home_path = ROOT / "data/site-foundation/home.json"
    home = _load(home_path)
    records.append(_record(home_path, home, home["output"], og_type="website"))
    for path in sorted((ROOT / "data/site-foundation/pages").glob("*.json")):
        data = _load(path)
        records.append(_record(
            path,
            data,
            data["output"],
            og_type="website",
            indexable=data.get("robots") != "noindex,follow",
        ))

    for folder in ("products", "guides"):
        for path in sorted((ROOT / "data/account-opening" / folder).glob("*.json")):
            data = _load(path)
            records.append(_record(
                path, data, f"account-opening/{data['slug']}/index.html", og_type="article"
            ))
    path = ROOT / "data/account-opening-hub.json"
    records.append(_record(path, _load(path), "account-opening/index.html", og_type="website"))

    for path in sorted((ROOT / "data/credit-card").glob("*.json")):
        data = _load(path)
        records.append(_record(
            path, data, f"credit-card/{data['slug']}/index.html", og_type="article"
        ))
    path = ROOT / "data/credit-card-hub.json"
    records.append(_record(path, _load(path), "credit-card/index.html", og_type="website"))

    for path in sorted((ROOT / "data/home-network").glob("*.json")):
        data = _load(path)
        records.append(_record(path, data, f"{data['output']}/index.html", og_type="article"))

    for path in sorted((ROOT / "data/lifestyle").glob("**/*.json")):
        data = _load(path)
        records.append(_record(
            path,
            data,
            data["output"],
            og_type="website" if data["page_type"] == "hub" else "article",
        ))

    mobile_root = ROOT / "data/mobile-sim"
    mobile_data: dict[str, dict[str, Any]] = {}
    for path in sorted(mobile_root.glob("*.json")):
        data = _load(path)
        mobile_data[data["slug"]] = data
        records.append(_record(
            path, data, f"mobile-sim/{data['slug']}/index.html", og_type="article"
        ))
    for path in sorted((ROOT / "data/mobile-sim-guides").glob("*.json")):
        data = _load(path)
        records.append(_record(path, data, f"{data['output']}/index.html", og_type="article"))
    hub_path = ROOT / "data/mobile-sim-hub.json"
    hub = _load(hub_path)
    hub_data = dict(hub)
    hub_data["checked_at"] = max(
        [hub["checked_at"], *(mobile_data[slug]["checked_at"] for slug in hub["featured_slugs"])]
    )
    records.append(_record(hub_path, hub_data, "mobile-sim/index.html", og_type="website"))

    point_root = ROOT / "data/point-site"
    for path in sorted((point_root / "sites").glob("*.json")):
        data = _load(path)
        records.append(_record(
            path, data, f"point-site/{data['slug']}/index.html", og_type="article"
        ))
        earn = data.get("earn")
        if not isinstance(earn, dict):
            raise ValueError(f"{path.relative_to(ROOT)}: earn must be an object")
        records.append(_record(
            path, earn, f"point-site/{data['slug']}/earn/index.html", og_type="article"
        ))
    for path in sorted((point_root / "guides").glob("*.json")):
        data = _load(path)
        records.append(_record(
            path, data, f"point-site/{data['slug']}/index.html", og_type="article"
        ))
    path = ROOT / "data/point-site-hub.json"
    records.append(_record(path, _load(path), "point-site/index.html", og_type="website"))

    for path in sorted((ROOT / "data/tiktok-lite/pages").glob("*.json")):
        data = _load(path)
        records.append(_record(
            path, data, f"tiktok-lite/{data['slug']}/index.html", og_type="article"
        ))
    path = ROOT / "data/tiktok-lite-hub.json"
    records.append(_record(path, _load(path), "tiktok-lite/index.html", og_type="website"))

    outputs = [record.output for record in records]
    duplicates = sorted(output for output, count in Counter(outputs).items() if count > 1)
    if duplicates:
        raise ValueError(f"duplicate SEO outputs: {', '.join(duplicates)}")
    if len(records) != 67:
        raise ValueError(f"expected 67 SEO page records, got {len(records)}")
    return tuple(sorted(records, key=lambda record: record.output))


def render_page_jsonld(
    *,
    canonical: str,
    title: str,
    description: str,
    checked_at: str,
    breadcrumbs: list[tuple[str, str]],
) -> str:
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": f"{BASE_URL}/#website",
                "url": f"{BASE_URL}/",
                "name": SITE_NAME,
                "inLanguage": "ja",
            },
            {
                "@type": "Organization",
                "@id": f"{BASE_URL}/#organization",
                "name": SITE_NAME,
                "url": f"{BASE_URL}/",
            },
            {
                "@type": "WebPage",
                "@id": f"{canonical}#webpage",
                "url": canonical,
                "name": title,
                "description": description,
                "dateModified": checked_at,
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
                        "position": position,
                        "name": name,
                        "item": url,
                    }
                    for position, (name, url) in enumerate(breadcrumbs, 1)
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":"))


def render_head_fragment(
    *,
    title: str,
    description: str,
    canonical: str,
    jsonld: str,
    og_type: str,
    robots: str = "",
) -> str:
    lines = [
        f"  <title>{title}</title>",
        f'  <meta name="description" content="{description}">',
    ]
    if robots:
        lines.append(f'  <meta name="robots" content="{robots}">')
    lines.extend((
        f'  <link rel="canonical" href="{canonical}">',
        f'  <meta property="og:title" content="{title}">',
        f'  <meta property="og:description" content="{description}">',
        f'  <meta property="og:url" content="{canonical}">',
        f'  <meta property="og:type" content="{og_type}">',
        f'  <meta property="og:site_name" content="{SITE_NAME}">',
        f'  <meta property="og:locale" content="{OG_LOCALE}">',
        '  <meta name="twitter:card" content="summary">',
        f'  <meta name="twitter:title" content="{title}">',
        f'  <meta name="twitter:description" content="{description}">',
        f'  <script type="application/ld+json">{jsonld}</script>',
    ))
    return "\n".join(lines)


class SeoTemplate(Template):
    def __init__(self, template: str, *, path: Path):
        super().__init__(template)
        markers = [
            marker
            for marker in ("seo_head_article", "seo_head_website", "seo_head_dynamic")
            if f"${marker}" in template
        ]
        if len(markers) != 1:
            raise ValueError(
                f"{path.relative_to(ROOT)}: exactly one SEO head marker is required"
            )
        self._seo_marker = markers[0]

    def _values(
        self,
        mapping: Mapping[str, object] | None,
        kws: Mapping[str, object],
    ) -> dict[str, object]:
        values: dict[str, object] = {}
        if mapping is not None:
            values.update(mapping)
        values.update(kws)
        required = ("title", "description", "canonical", "seo_jsonld")
        missing = [key for key in required if key not in values]
        if missing:
            raise KeyError("missing SEO template values: " + ", ".join(missing))
        if self._seo_marker == "seo_head_dynamic":
            og_type = str(values.get("og_type", ""))
        else:
            og_type = self._seo_marker.removeprefix("seo_head_")
        if og_type not in {"article", "website"}:
            raise ValueError(f"invalid SEO og_type: {og_type}")
        values[self._seo_marker] = render_head_fragment(
            title=str(values["title"]),
            description=str(values["description"]),
            canonical=str(values["canonical"]),
            jsonld=str(values["seo_jsonld"]),
            og_type=og_type,
            robots=str(values.get("robots", "")),
        )
        return values

    def substitute(self, mapping: Mapping[str, object] | None = None, /, **kws: object) -> str:
        return super().substitute(self._values(mapping, kws))

    def safe_substitute(self, mapping: Mapping[str, object] | None = None, /, **kws: object) -> str:
        return super().safe_substitute(self._values(mapping, kws))


def render_sitemap(records: tuple[PageRecord, ...] | None = None) -> str:
    records = records or page_catalog()
    namespace = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ET.register_namespace("", namespace)
    root = ET.Element(f"{{{namespace}}}urlset")
    for record in sorted(
        (record for record in records if record.indexable),
        key=lambda record: urlsplit(record.canonical).path,
    ):
        node = ET.SubElement(root, f"{{{namespace}}}url")
        ET.SubElement(node, f"{{{namespace}}}loc").text = record.canonical
        ET.SubElement(node, f"{{{namespace}}}lastmod").text = record.modified
    ET.indent(root, space="  ")
    body = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


class _SeoParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.in_title = False
        self.meta: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []
        self.h1_count = 0
        self.hrefs: list[str] = []
        self.times: list[str] = []
        self.jsonld_parts: list[list[str]] = []
        self._jsonld: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        tag = tag.lower()
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            self.meta.append(values)
        elif tag == "link":
            self.links.append(values)
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and values.get("href"):
            self.hrefs.append(values["href"])
        elif tag == "time" and values.get("datetime"):
            self.times.append(values["datetime"])
        elif tag == "script" and values.get("type") == "application/ld+json":
            self._jsonld = []
            self.jsonld_parts.append(self._jsonld)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self.in_title = False
        elif tag.lower() == "script":
            self._jsonld = None

    def handle_data(self, data: str) -> None:
        if self.in_title:
            self.title_parts.append(data)
        if self._jsonld is not None:
            self._jsonld.append(data)

    def one_meta(self, *, name: str = "", prop: str = "") -> tuple[int, str]:
        matches = [
            item.get("content", "")
            for item in self.meta
            if (name and item.get("name") == name)
            or (prop and item.get("property") == prop)
        ]
        return len(matches), matches[0] if len(matches) == 1 else ""

    def one_link(self, rel: str) -> tuple[int, str]:
        matches = [item.get("href", "") for item in self.links if item.get("rel") == rel]
        return len(matches), matches[0] if len(matches) == 1 else ""


def _route_for_output(output: str) -> str:
    return urlsplit(canonical_for_output(output)).path


def audit_seo() -> list[str]:
    problems: list[str] = []
    try:
        records = page_catalog()
        expected_sitemap = render_sitemap(records)
    except (OSError, ValueError, json.JSONDecodeError, KeyError, TypeError) as error:
        return [f"SEO page catalog failed: {error}"]

    if not SITEMAP_PATH.exists():
        problems.append("sitemap.xml: generated sitemap is missing")
    elif SITEMAP_PATH.read_text(encoding="utf-8") != expected_sitemap:
        problems.append("sitemap.xml: generated sitemap is stale or manually edited")

    generated = {
        path.relative_to(ROOT).as_posix(): path
        for path in repo_paths.iter_files(ROOT, "*.html")
        if "templates" not in path.relative_to(ROOT).parts
    }
    expected_outputs = {record.output for record in records}
    for output in sorted(expected_outputs - generated.keys()):
        problems.append(f"{output}: catalogued generated page is missing")
    for output in sorted(generated.keys() - expected_outputs):
        problems.append(f"{output}: generated page is missing from SEO catalog")

    routes = {_route_for_output(record.output): record for record in records}
    incoming: Counter[str] = Counter()
    unique_values: dict[str, defaultdict[str, list[str]]] = {
        key: defaultdict(list) for key in ("title", "description", "canonical")
    }

    for record in records:
        path = generated.get(record.output)
        if path is None:
            continue
        rel = record.output
        parser = _SeoParser()
        parser.feed(path.read_text(encoding="utf-8"))
        title = "".join(parser.title_parts).strip()
        _, description = parser.one_meta(name="description")
        _, canonical = parser.one_link("canonical")
        actual = {"title": title, "description": description, "canonical": canonical}
        expected = {
            "title": record.title,
            "description": record.description,
            "canonical": record.canonical,
        }
        for key, value in actual.items():
            unique_values[key][value].append(rel)
            if value != expected[key]:
                problems.append(f"{rel}: {key} differs from canonical page data")

        if not 8 <= len(title) <= 60:
            problems.append(f"{rel}: title length must be 8..60 characters, got {len(title)}")
        if not 25 <= len(description) <= 120:
            problems.append(
                f"{rel}: description length must be 25..120 characters, got {len(description)}"
            )
        if parser.h1_count != 1:
            problems.append(f"{rel}: h1 must appear exactly once")

        expected_meta = {
            ("property", "og:title"): record.title,
            ("property", "og:description"): record.description,
            ("property", "og:url"): record.canonical,
            ("property", "og:type"): record.og_type,
            ("property", "og:site_name"): SITE_NAME,
            ("property", "og:locale"): OG_LOCALE,
            ("name", "twitter:card"): "summary",
            ("name", "twitter:title"): record.title,
            ("name", "twitter:description"): record.description,
        }
        for (kind, key), value in expected_meta.items():
            count, found = parser.one_meta(**{("prop" if kind == "property" else kind): key})
            if count != 1:
                problems.append(f"{rel}: {key} must appear exactly once")
            elif found != value:
                problems.append(f"{rel}: {key} differs from canonical page data")

        robots_count, robots = parser.one_meta(name="robots")
        if record.indexable:
            if robots_count and "noindex" in robots.lower():
                problems.append(f"{rel}: indexable page must not be noindex")
        elif (robots_count, robots) != (1, "noindex,follow"):
            problems.append(f"{rel}: non-indexable page must use noindex,follow")

        if len(parser.jsonld_parts) != 1:
            problems.append(f"{rel}: exactly one JSON-LD graph is required")
        else:
            try:
                document = json.loads("".join(parser.jsonld_parts[0]))
                graph = document.get("@graph")
                if not isinstance(graph, list):
                    raise ValueError("@graph must be an array")
                websites = [node for node in graph if node.get("@type") == "WebSite"]
                organizations = [node for node in graph if node.get("@type") == "Organization"]
                pages = [
                    node for node in graph
                    if node.get("@type") in {"WebPage", "CollectionPage"}
                ]
                breadcrumbs = [node for node in graph if node.get("@type") == "BreadcrumbList"]
                if len(websites) != 1 or websites[0].get("@id") != f"{BASE_URL}/#website":
                    problems.append(f"{rel}: JSON-LD must contain one canonical WebSite")
                if len(organizations) != 1 or organizations[0].get("@id") != f"{BASE_URL}/#organization":
                    problems.append(f"{rel}: JSON-LD must contain one canonical Organization")
                if len(pages) != 1:
                    problems.append(f"{rel}: JSON-LD must contain one page node")
                else:
                    node = pages[0]
                    for key, value in (
                        ("url", record.canonical),
                        ("name", record.title),
                        ("description", record.description),
                        ("dateModified", record.modified),
                    ):
                        if node.get(key) != value:
                            problems.append(f"{rel}: JSON-LD {key} differs from canonical page data")
                if len(breadcrumbs) != 1:
                    problems.append(f"{rel}: JSON-LD must contain one BreadcrumbList")
                else:
                    items = breadcrumbs[0].get("itemListElement")
                    if not isinstance(items, list) or not items:
                        problems.append(f"{rel}: JSON-LD breadcrumb items are missing")
                    else:
                        positions = [item.get("position") for item in items]
                        if positions != list(range(1, len(items) + 1)):
                            problems.append(f"{rel}: JSON-LD breadcrumb positions are invalid")
                        if items[0].get("item") != f"{BASE_URL}/":
                            problems.append(f"{rel}: JSON-LD breadcrumb must start at home")
                        if items[-1].get("item") != record.canonical:
                            problems.append(f"{rel}: JSON-LD breadcrumb must end at canonical URL")
            except (json.JSONDecodeError, ValueError, AttributeError) as error:
                problems.append(f"{rel}: invalid JSON-LD: {error}")

        if parser.times and record.modified not in parser.times:
            problems.append(f"{rel}: visible update date differs from dateModified")

        for href in parser.hrefs:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = parsed.path
            if target.startswith("/assets/") or target in {
                "/favicon.ico", "/site.webmanifest", "/sitemap.xml", "/robots.txt"
            }:
                continue
            if target not in routes:
                problems.append(f"{rel}: broken internal page link: {href}")
            else:
                incoming[target] += 1

    for key, groups in unique_values.items():
        for value, outputs in groups.items():
            if value and len(outputs) > 1:
                problems.append(
                    f"duplicate {key} across generated pages: {', '.join(sorted(outputs))}"
                )

    for route, record in sorted(routes.items()):
        if route in {"/", "/404.html"} or not record.indexable:
            continue
        if incoming[route] == 0:
            problems.append(f"{record.output}: indexable page has no incoming internal link")

    return problems
