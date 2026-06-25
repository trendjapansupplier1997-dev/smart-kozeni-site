#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import struct
from functools import lru_cache
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import repo_paths

import seo

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "data" / "site-runtime.json"
MANIFEST_PATH = ROOT / "site.webmanifest"
MENU_SCRIPT = "/assets/kozeni-foundation-menu.v1.js"
ANALYTICS_SCRIPT = "/assets/kozeni-analytics.v1.js"

RETIRED_PATHS = (
    "manifest.webmanifest",
    "version.json",
    "assets/kozeni-site-foundation.v1.js",
    "assets/brand-logo.svg",
    "assets/brand-mark.svg",
    "assets/favicon.svg",
    "favicon.svg",
    "assets/images/ogp.png",
    "assets/images/x-icon-source.png",
    "assets/social/instagram-app-icon-v4.svg",
    "assets/social/x-app-icon-v4.svg",
)
DIRECT_PUBLIC_ENDPOINTS = {
    "favicon.ico",
    "humans.txt",
    "llms.txt",
    "robots.txt",
    "site.webmanifest",
    "sitemap.xml",
    "sw.js",
}
ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
GA_RE = re.compile(r"^G-[A-Z0-9]+$")
SIZE_RE = re.compile(r"^(\d+)x(\d+)$")


def _require_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: {key} must be a non-empty string")
    return value


def _local_path(url: str) -> Path:
    parsed = urlsplit(url)
    if parsed.scheme or parsed.netloc or not parsed.path.startswith("/"):
        raise ValueError(f"site runtime asset must be root-relative: {url}")
    return ROOT / parsed.path.lstrip("/")


@lru_cache(maxsize=1)
def load_config() -> dict[str, Any]:
    data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: root must be an object")
    if data.get("schema_version") != 1:
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: schema_version must be 1")
    for key in (
        "site_name",
        "short_name",
        "description",
        "start_url",
        "scope",
        "display",
        "background_color",
        "theme_color",
        "icon_cache_key",
    ):
        _require_string(data, key)
    if data["start_url"] != "/" or data["scope"] != "/":
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: start_url and scope must be /")
    if data["display"] not in {"standalone", "minimal-ui", "browser"}:
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: unsupported display mode")
    if not ID_RE.fullmatch(data["icon_cache_key"]):
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: invalid icon_cache_key")

    head_icons = data.get("head_icons")
    if not isinstance(head_icons, list) or len(head_icons) != 3:
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: head_icons must contain 3 entries")
    seen_head: set[tuple[str, str]] = set()
    for icon in head_icons:
        if not isinstance(icon, dict):
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: head icon must be an object")
        rel = str(icon.get("rel", ""))
        href = str(icon.get("href", ""))
        sizes = str(icon.get("sizes", ""))
        if rel not in {"icon", "apple-touch-icon"}:
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: invalid head icon rel")
        _local_path(href)
        if not SIZE_RE.fullmatch(sizes):
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: invalid head icon sizes")
        key = (rel, sizes)
        if key in seen_head:
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: duplicate head icon {key}")
        seen_head.add(key)
        if rel == "icon" and icon.get("type") != "image/png":
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: PNG favicon type is required")

    manifest_icons = data.get("manifest_icons")
    if not isinstance(manifest_icons, list) or len(manifest_icons) != 2:
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: manifest_icons must contain 2 entries")
    for icon in manifest_icons:
        if not isinstance(icon, dict):
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: manifest icon must be an object")
        _local_path(str(icon.get("src", "")))
        if not SIZE_RE.fullmatch(str(icon.get("sizes", ""))):
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: invalid manifest icon sizes")
        if icon.get("type") != "image/png" or icon.get("purpose") != "any":
            raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: manifest icons must be PNG purpose=any")

    analytics = data.get("analytics")
    if not isinstance(analytics, dict):
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: analytics must be an object")
    output = str(analytics.get("output", ""))
    if output != ANALYTICS_SCRIPT.lstrip("/"):
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: analytics.output must be {ANALYTICS_SCRIPT.lstrip('/')}")
    if not GA_RE.fullmatch(str(analytics.get("ga4_measurement_id", ""))):
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: invalid GA4 measurement ID")
    if not ID_RE.fullmatch(str(analytics.get("clarity_project_id", ""))):
        raise ValueError(f"{CONFIG_PATH.relative_to(ROOT)}: invalid Clarity project ID")
    return data


def render_manifest(config: dict[str, Any] | None = None) -> str:
    config = config or load_config()
    payload = {
        "name": config["site_name"],
        "short_name": config["short_name"],
        "description": config["description"],
        "start_url": config["start_url"],
        "scope": config["scope"],
        "display": config["display"],
        "background_color": config["background_color"],
        "theme_color": config["theme_color"],
        "icons": config["manifest_icons"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_analytics(config: dict[str, Any] | None = None) -> str:
    config = config or load_config()
    analytics = config["analytics"]
    ga_id = json.dumps(analytics["ga4_measurement_id"])
    clarity_id = json.dumps(analytics["clarity_project_id"])
    return f"""(() => {{
  'use strict';
  if (window.__kozeniAnalyticsLoaded) return;
  window.__kozeniAnalyticsLoaded = true;

  const gaId = {ga_id};
  const clarityId = {clarity_id};

  window.dataLayer = window.dataLayer || [];
  window.gtag = window.gtag || function gtag() {{
    window.dataLayer.push(arguments);
  }};
  window.gtag('js', new Date());
  window.gtag('config', gaId);

  const ga = document.createElement('script');
  ga.async = true;
  ga.src = `https://www.googletagmanager.com/gtag/js?id=${{encodeURIComponent(gaId)}}`;
  document.head.appendChild(ga);

  window.clarity = window.clarity || function clarity() {{
    (window.clarity.q = window.clarity.q || []).push(arguments);
  }};
  const clarity = document.createElement('script');
  clarity.async = true;
  clarity.src = `https://www.clarity.ms/tag/${{clarityId}}`;
  document.head.appendChild(clarity);
}})();
"""


def render_head(config: dict[str, Any] | None = None) -> str:
    config = config or load_config()
    cache_key = config["icon_cache_key"]
    lines: list[str] = []
    for icon in config["head_icons"]:
        attrs = [f'rel="{icon["rel"]}"']
        if icon.get("type"):
            attrs.append(f'type="{icon["type"]}"')
        attrs.append(f'sizes="{icon["sizes"]}"')
        attrs.append(f'href="{icon["href"]}?v={cache_key}"')
        lines.append("  <link " + " ".join(attrs) + ">")
    lines.append('  <link rel="manifest" href="/site.webmanifest">')
    lines.append(f'  <script defer src="{ANALYTICS_SCRIPT}"></script>')
    return "\n".join(lines)


def load_template(path: Path) -> seo.SeoTemplate:
    source = path.read_text(encoding="utf-8")
    marker = "$site_runtime_head"
    if source.count(marker) != 1:
        raise ValueError(f"{path.relative_to(ROOT)}: must contain {marker} exactly once")
    return seo.SeoTemplate(source.replace(marker, render_head()), path=path)


def _png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        raise ValueError("not a PNG file")
    return struct.unpack(">II", data[16:24])


class _AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.local_assets: set[str] = set()
        self.script_srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key.lower(): value or "" for key, value in attrs}
        if tag.lower() == "script" and values.get("src"):
            self.script_srcs.append(values["src"])
        for key in ("href", "src"):
            value = values.get(key, "")
            if value.startswith("/assets/"):
                self.local_assets.add(urlsplit(value).path)


def audit_public_assets() -> list[str]:
    problems: list[str] = []
    try:
        config = load_config()
        expected_manifest = render_manifest(config)
        expected_analytics = render_analytics(config)
        expected_head = render_head(config)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"site runtime configuration failed: {error}"]

    analytics_path = ROOT / config["analytics"]["output"]
    for path, expected in ((MANIFEST_PATH, expected_manifest), (analytics_path, expected_analytics)):
        if not path.exists():
            problems.append(f"{path.relative_to(ROOT)}: generated runtime asset is missing")
        elif path.read_text(encoding="utf-8") != expected:
            problems.append(f"{path.relative_to(ROOT)}: generated runtime asset is stale")

    referenced_assets: set[str] = set()
    html_files = sorted(
        path for path in repo_paths.iter_files(ROOT, "*.html")
        if "templates" not in path.relative_to(ROOT).parts
    )
    for path in html_files:
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.count(expected_head) != 1:
            problems.append(f"{rel}: shared site runtime head must appear exactly once")
        parser = _AssetParser()
        parser.feed(text)
        referenced_assets.update(parser.local_assets)
        if parser.script_srcs.count(ANALYTICS_SCRIPT) != 1:
            problems.append(f"{rel}: analytics script must appear exactly once")
        has_menu = "data-foundation-menu-toggle" in text or "data-foundation-menu" in text
        menu_count = parser.script_srcs.count(MENU_SCRIPT)
        if has_menu and menu_count != 1:
            problems.append(f"{rel}: foundation menu script must appear exactly once")
        if not has_menu and menu_count:
            problems.append(f"{rel}: foundation menu script is not allowed without menu markup")
        allowed_scripts = {ANALYTICS_SCRIPT}
        if has_menu:
            allowed_scripts.add(MENU_SCRIPT)
        unexpected = sorted(
            src for src in parser.script_srcs
            if src.startswith("/") and src not in allowed_scripts
        )
        if unexpected:
            problems.append(f"{rel}: unexpected local executable script(s): {', '.join(unexpected)}")

    manifest = json.loads(expected_manifest)
    for icon in manifest["icons"]:
        referenced_assets.add(urlsplit(icon["src"]).path)
    referenced_assets.add(MENU_SCRIPT)
    referenced_assets.add(ANALYTICS_SCRIPT)

    css_url_re = re.compile(r"url\(\s*['\"]?(/assets/[^)'\"?#]+)")
    for path in sorted((ROOT / "assets").rglob("*.css")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        referenced_assets.update(css_url_re.findall(text))

    for url in sorted(referenced_assets):
        target = ROOT / url.lstrip("/")
        if not target.exists():
            problems.append(f"missing referenced public asset: {url}")

    asset_files = {
        "/" + path.relative_to(ROOT).as_posix()
        for path in (ROOT / "assets").rglob("*")
        if path.is_file()
    }
    unused = sorted(asset_files - referenced_assets)
    for url in unused:
        problems.append(f"unused public asset: {url}")

    for icon in [*config["head_icons"], *config["manifest_icons"]]:
        url = str(icon.get("href") or icon.get("src"))
        path = _local_path(url)
        match = SIZE_RE.fullmatch(str(icon["sizes"]))
        assert match is not None
        expected = (int(match.group(1)), int(match.group(2)))
        try:
            actual = _png_size(path)
        except (OSError, ValueError) as error:
            problems.append(f"{path.relative_to(ROOT)}: invalid PNG icon: {error}")
            continue
        if actual != expected:
            problems.append(
                f"{path.relative_to(ROOT)}: icon size {actual[0]}x{actual[1]} != {expected[0]}x{expected[1]}"
            )

    for rel in RETIRED_PATHS:
        if (ROOT / rel).exists():
            problems.append(f"{rel}: retired public asset must be deleted")

    for rel in DIRECT_PUBLIC_ENDPOINTS:
        if not (ROOT / rel).exists():
            problems.append(f"{rel}: required direct public endpoint is missing")

    sw_path = ROOT / "sw.js"
    if sw_path.exists():
        source = sw_path.read_text(encoding="utf-8", errors="ignore")
        for token in ("self.registration.unregister()", "caches.keys()", "self.skipWaiting()"):
            if token not in source:
                problems.append(f"sw.js: retirement worker is missing {token}")
        if re.search(r"addEventListener\(\s*['\"]fetch['\"]", source):
            problems.append("sw.js: retired service worker must not intercept fetch events")

    headers = (ROOT / "_headers").read_text(encoding="utf-8", errors="ignore")
    if "/sw.js\n  Cache-Control: no-cache, no-store, must-revalidate" not in headers:
        problems.append("_headers: sw.js retirement endpoint must disable caching")
    if "/site.webmanifest\n  Cache-Control: public, max-age=3600, must-revalidate" not in headers:
        problems.append("_headers: site.webmanifest must use short revalidation caching")

    privacy_path = ROOT / "data" / "site-foundation" / "pages" / "privacy.json"
    if privacy_path.exists():
        privacy = privacy_path.read_text(encoding="utf-8")
        for token in ("全ページ", "Google Analytics 4", "Microsoft Clarity"):
            if token not in privacy:
                problems.append(f"{privacy_path.relative_to(ROOT)}: analytics disclosure is missing {token}")

    return problems
