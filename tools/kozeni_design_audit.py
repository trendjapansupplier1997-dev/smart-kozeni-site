#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
TOKEN_PATH = ASSETS / "kozeni-tokens.v1.css"
TOKEN_HREF = "/assets/kozeni-tokens.v1.css"
BRAND_HREF = "/assets/kozeni-brand.v1.css"
HTML_FILES = sorted(path for path in ROOT.rglob("*.html") if ".git" not in path.parts)
CSS_FILES = sorted(ASSETS.glob("*.css")) if ASSETS.exists() else []

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGBA_RE = re.compile(r"rgba?\([^)]+\)")
FONT_RE = re.compile(r"font-family\s*:\s*([^;]+);", re.I)
RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;!}]+)", re.I)

SHARED_HEX = {
    "#fff", "#ffffff", "#222831", "#17231d", "#62736b", "#617069",
    "#228c62", "#0f7a55", "#135c43", "#4dbd8c", "#e9f5ef",
    "#f8fffb", "#f7fbf9", "#dcece4", "#f2c94c", "#fff6df",
    "#7a5a00", "#8c6b16", "#5b4910",
}
SHARED_RGB = {
    (255, 255, 255),
    (34, 40, 49),
    (34, 140, 98),
    (77, 189, 140),
    (242, 201, 76),
    (24, 86, 63),
}
SHARED_RADIUS = {"999px", "1rem", "1.25rem", "1.6rem", "2rem"}
REQUIRED_TOKEN_NAMES = {
    "--kozeni-font-sans",
    "--kozeni-font-sans-jp",
    "--kozeni-font-system",
    "--kozeni-white",
    "--kozeni-ink",
    "--kozeni-muted",
    "--kozeni-green",
    "--kozeni-deep",
    "--kozeni-mint",
    "--kozeni-pale",
    "--kozeni-line",
    "--kozeni-shadow-green",
    "--kozeni-radius-pill",
    "--kozeni-space-4",
}
STATUS_WORDS = ["準備中", "一部公開", "強化中", "公開中", "coming soon", "工事中"]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def stylesheet_hrefs(source: str) -> list[str]:
    return re.findall(
        r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']',
        source,
        flags=re.I,
    )


def parse_rgb(value: str) -> tuple[int, int, int] | None:
    match = re.match(
        r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)",
        value,
        flags=re.I,
    )
    if not match:
        return None
    return tuple(map(int, match.groups()))


def main() -> int:
    print("=== kozeni design audit ===")
    print(f"HTML files: {len(HTML_FILES)}")
    print(f"CSS files: {len(CSS_FILES)}")

    css_refs: Counter[str] = Counter()
    inline_style_pages: list[tuple[str, int]] = []
    inline_script_pages: list[tuple[str, int]] = []
    token_link_problems: list[str] = []
    cache_key_problems: list[str] = []
    status_hits: list[tuple[str, str]] = []

    for path in HTML_FILES:
        source = read(path)
        rel = path.relative_to(ROOT).as_posix()
        raw_hrefs = stylesheet_hrefs(source)
        hrefs = [href.split("?", 1)[0] for href in raw_hrefs]
        css_refs.update(hrefs)

        for raw_href, base_href in zip(raw_hrefs, hrefs, strict=True):
            if base_href != TOKEN_HREF and "?v=" not in raw_href:
                cache_key_problems.append(
                    f"{rel}: immutable CSS needs a versioned URL: {raw_href}"
                )

        if hrefs.count(TOKEN_HREF) != 1:
            token_link_problems.append(
                f"{rel}: {TOKEN_HREF} must appear exactly once"
            )
        elif BRAND_HREF in hrefs and hrefs.index(TOKEN_HREF) > hrefs.index(BRAND_HREF):
            token_link_problems.append(
                f"{rel}: token stylesheet must load before brand stylesheet"
            )

        style_count = len(re.findall(r"<style\b", source, flags=re.I))
        script_inline_count = len(
            re.findall(
                r'<script\b(?![^>]*\bsrc=)'
                r'(?![^>]*type=["\']application/ld\+json["\'])[^>]*>',
                source,
                flags=re.I,
            )
        )
        if style_count:
            inline_style_pages.append((rel, style_count))
        if script_inline_count:
            inline_script_pages.append((rel, script_inline_count))
        for word in STATUS_WORDS:
            if word in source:
                status_hits.append((rel, word))

    token_source = read(TOKEN_PATH) if TOKEN_PATH.exists() else ""
    token_definition_problems = [
        f"{TOKEN_PATH.relative_to(ROOT)}: missing {name}"
        for name in sorted(REQUIRED_TOKEN_NAMES)
        if name not in token_source
    ]
    if not TOKEN_PATH.exists():
        token_definition_problems.insert(0, "assets/kozeni-tokens.v1.css is missing")

    font_decls: Counter[str] = Counter()
    color_hits: Counter[str] = Counter()
    local_colors: Counter[str] = Counter()
    token_usage: Counter[str] = Counter()
    shared_literal_problems: list[str] = []
    font_problems: list[str] = []
    radius_problems: list[str] = []

    for path in CSS_FILES:
        source = read(path)
        rel = path.relative_to(ROOT).as_posix()
        is_token_file = path == TOKEN_PATH

        for name in re.findall(r"var\((--kozeni-[a-z0-9-]+)", source, flags=re.I):
            token_usage[name] += 1

        for font in FONT_RE.findall(source):
            normalized = " ".join(font.strip().split())
            font_decls[normalized] += 1
            if not is_token_file and normalized not in {
                "var(--kozeni-font-sans)",
                "var(--kozeni-font-sans-jp)",
                "var(--kozeni-font-system)",
                "inherit",
                "inherit!important",
            }:
                font_problems.append(f"{rel}: raw font-family remains: {normalized}")

        for color in HEX_RE.findall(source):
            normalized = color.lower()
            color_hits[normalized] += 1
            if not is_token_file:
                local_colors[normalized] += 1
                if normalized in SHARED_HEX:
                    shared_literal_problems.append(
                        f"{rel}: shared color literal must use token: {color}"
                    )

        for color in RGBA_RE.findall(source):
            normalized = re.sub(r"\s+", "", color.lower())
            color_hits[normalized] += 1
            if is_token_file or "var(--kozeni-rgb-" in color:
                continue
            rgb = parse_rgb(color)
            if rgb in SHARED_RGB:
                shared_literal_problems.append(
                    f"{rel}: shared RGB literal must use channel token: {color}"
                )

        if not is_token_file:
            for radius in RADIUS_RE.findall(source):
                normalized = " ".join(radius.strip().split()).lower()
                if normalized in SHARED_RADIUS:
                    radius_problems.append(
                        f"{rel}: shared radius literal must use token: {normalized}"
                    )

    print("\n=== CSS refs ===")
    if css_refs:
        for path, count in css_refs.most_common():
            print(f"{count:>3}  {path}")
    else:
        print("OK: none")

    print("\n=== design token contract ===")
    print(f"token stylesheet refs: {css_refs.get(TOKEN_HREF, 0)}/{len(HTML_FILES)}")
    if token_link_problems or token_definition_problems:
        for problem in [*token_definition_problems, *token_link_problems]:
            print(problem)
    else:
        print("OK: every page loads one token stylesheet before component CSS")

    print("\n=== immutable CSS cache keys ===")
    if cache_key_problems:
        for problem in cache_key_problems:
            print(problem)
    else:
        print("OK: existing CSS assets use versioned URLs")

    unused_css = [
        path.relative_to(ROOT).as_posix()
        for path in CSS_FILES
        if f"/assets/{path.name}" not in css_refs
    ]
    print("\n=== unused CSS assets ===")
    if unused_css:
        for rel in unused_css:
            print(rel)
    else:
        print("OK: every CSS asset is referenced")

    print("\n=== token usage ===")
    if token_usage:
        for name, count in token_usage.most_common(30):
            print(f"{count:>3}  {name}")
    else:
        print("OK: none")

    print("\n=== inline style pages ===")
    print(f"{len(inline_style_pages)} pages")
    for rel, count in inline_style_pages[:80]:
        print(f"{count:>2}  {rel}")

    print("\n=== inline script pages ===")
    print(f"{len(inline_script_pages)} pages")
    for rel, count in inline_script_pages[:80]:
        print(f"{count:>2}  {rel}")

    print("\n=== font-family declarations ===")
    if font_decls:
        for value, count in font_decls.most_common(30):
            print(f"{count:>3}  {value}")
    else:
        print("OK: none")

    print("\n=== remaining local hex colors ===")
    if local_colors:
        for value, count in local_colors.most_common(50):
            print(f"{count:>3}  {value}")
    else:
        print("OK: none")

    print("\n=== shared literal regressions ===")
    regressions = [*shared_literal_problems, *font_problems, *radius_problems]
    if regressions:
        for problem in regressions:
            print(problem)
    else:
        print("OK: shared colors, font, and radius primitives use tokens")

    print("\n=== unfinished/status words ===")
    if status_hits:
        for rel, word in status_hits:
            print(f"{word:>8}  {rel}")
    else:
        print("OK: none")

    print("\n=== result ===")
    blockers: list[str] = []
    if token_definition_problems or token_link_problems:
        blockers.append("design token contract")
    if cache_key_problems:
        blockers.append(f"unversioned immutable CSS: {len(cache_key_problems)}")
    if unused_css:
        blockers.append(f"unused CSS assets: {len(unused_css)}")
    if shared_literal_problems:
        blockers.append(f"shared color literals: {len(shared_literal_problems)}")
    if font_problems:
        blockers.append(f"raw font declarations: {len(font_problems)}")
    if radius_problems:
        blockers.append(f"raw radius primitives: {len(radius_problems)}")
    if inline_style_pages:
        blockers.append(f"inline style pages: {len(inline_style_pages)}")
    if inline_script_pages:
        blockers.append(f"inline script pages: {len(inline_script_pages)}")
    if blockers:
        print("NG: " + ", ".join(blockers))
        return 1
    print("OK: design tokens are centralized with no inline CSS or executable JS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
