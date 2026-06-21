#!/usr/bin/env python3
from pathlib import Path
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts)
CSS_FILES = sorted(p for p in (ROOT / "assets").glob("*.css")) if (ROOT / "assets").exists() else []

HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGBA_RE = re.compile(r"rgba?\([^)]+\)")
FONT_RE = re.compile(r"font-family\s*:\s*([^;]+);", re.I)

ALLOWED_HEX = {
    "#10241d",
    "#5d7168",
    "#0f7a55",
    "#0b3024",
    "#f4fbf7",
    "#ecfdf5",
    "#c9962e",
    "#ffffff",
    "#fff",
}

STATUS_WORDS = ["準備中", "一部公開", "強化中", "公開中", "coming soon", "工事中"]

def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def collect_text_files():
    return list(HTML_FILES) + list(CSS_FILES)

def main() -> int:
    print("=== kozeni design audit ===")
    print(f"HTML files: {len(HTML_FILES)}")
    print(f"CSS files: {len(CSS_FILES)}")

    css_refs = Counter()
    inline_style_pages = []
    inline_script_pages = []
    status_hits = []
    font_decls = Counter()
    color_hits = Counter()
    non_token_colors = Counter()

    for p in HTML_FILES:
        text = read(p)
        rel = p.relative_to(ROOT)

        for href in re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']', text, flags=re.I):
            css_refs[href.split("?")[0]] += 1

        style_count = len(re.findall(r"<style\b", text, flags=re.I))
        script_inline_count = len(
            re.findall(
                r'<script\b(?![^>]*\bsrc=)'
                r'(?![^>]*type=["\']application/ld\+json["\'])[^>]*>',
                text,
                flags=re.I,
            )
        )
        if style_count:
            inline_style_pages.append((str(rel), style_count))
        if script_inline_count:
            inline_script_pages.append((str(rel), script_inline_count))

        for word in STATUS_WORDS:
            if word in text:
                status_hits.append((str(rel), word))

    for p in collect_text_files():
        text = read(p)

        for font in FONT_RE.findall(text):
            normalized = " ".join(font.strip().split())
            font_decls[normalized] += 1

        for color in HEX_RE.findall(text):
            key = color.lower()
            color_hits[key] += 1
            if key not in ALLOWED_HEX:
                non_token_colors[key] += 1

        for color in RGBA_RE.findall(text):
            normalized = re.sub(r"\s+", "", color.lower())
            color_hits[normalized] += 1

    print("\n=== CSS refs ===")
    if css_refs:
        for k, v in css_refs.most_common():
            mark = "  legacy" if "v36" in k else ""
            print(f"{v:>3}  {k}{mark}")
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
        for k, v in font_decls.most_common(30):
            print(f"{v:>3}  {k}")
    else:
        print("OK: none")

    print("\n=== most used colors ===")
    if color_hits:
        for k, v in color_hits.most_common(40):
            print(f"{v:>3}  {k}")
    else:
        print("OK: none")

    print("\n=== non-token hex colors ===")
    if non_token_colors:
        for k, v in non_token_colors.most_common(50):
            print(f"{v:>3}  {k}")
    else:
        print("OK: none")

    print("\n=== unfinished/status words ===")
    if status_hits:
        for rel, word in status_hits:
            print(f"{word:>8}  {rel}")
    else:
        print("OK: none")

    print("\n=== result ===")
    print("OK: audit completed. Treat v36 refs and inline styles as migration targets, not immediate failures.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
