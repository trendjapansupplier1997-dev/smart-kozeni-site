#!/usr/bin/env python3
from pathlib import Path
import re
from collections import Counter

root = Path(__file__).resolve().parents[1]
html_files = sorted(p for p in root.rglob("*.html") if ".git" not in p.parts)

css_refs = Counter()
js_refs = Counter()
missing_title = []
missing_description = []
missing_canonical = []
status_hits = []
old_url_hits = []
backup_files = []

status_words = ["準備中", "一部公開", "強化中", "公開中", "coming soon", "工事中"]
old_url_patterns = [
    ("old mobile href", r'href=["\']/mobile(?:/|["\'])'),
    ("old trip-mile href", r'href=["\']/point-site/trip-mile(?:/|["\'])'),
    ("old start-here href", r'href=["\']/start-here(?:/|["\'])'),
    ("old referral-code href", r'href=["\']/point-site/referral-code(?:/|["\'])'),
]

for p in html_files:
    text = p.read_text(encoding="utf-8", errors="ignore")
    rel = p.relative_to(root).as_posix()

    for m in re.findall(r'<link[^>]+href=["\']([^"\']+\.css[^"\']*)["\']', text):
        css_refs[m.split("?")[0]] += 1
    for m in re.findall(r'<script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', text):
        js_refs[m.split("?")[0]] += 1

    if not re.search(r"<title>.*?</title>", text, flags=re.I | re.S):
        missing_title.append(rel)
    if 'name="description"' not in text and "name='description'" not in text:
        missing_description.append(rel)
    if 'rel="canonical"' not in text and "rel='canonical'" not in text:
        missing_canonical.append(rel)

    for word in status_words:
        if word in text:
            status_hits.append((rel, word))

    for label, pattern in old_url_patterns:
        if re.search(pattern, text):
            old_url_hits.append((rel, label))

for pat in ["*.bak*", "*.tmp", "*.old", "*.orig", "*~"]:
    for p in root.rglob(pat):
        if ".git" not in p.parts:
            backup_files.append(p.relative_to(root).as_posix())

print("=== kozeni site audit ===")
print(f"HTML files: {len(html_files)}")

print("\n=== CSS refs ===")
for path, count in css_refs.most_common():
    print(f"{count:>3}  {path}")

print("\n=== JS refs ===")
for path, count in js_refs.most_common():
    print(f"{count:>3}  {path}")

problems = []

def show_list(title, items):
    print(f"\n=== {title} ===")
    if not items:
        print("OK: none")
    else:
        for item in items:
            print(item)
        problems.extend(items)

show_list("missing title", missing_title)
show_list("missing description", missing_description)
show_list("missing canonical", missing_canonical)
show_list("unfinished/status words", [f"{rel}: {word}" for rel, word in status_hits])
show_list("old internal URL hrefs", [f"{rel}: {label}" for rel, label in old_url_hits])
show_list("backup/temp files", backup_files)

print("\n=== result ===")
if problems:
    print(f"NG: {len(problems)} issue(s) found")
    raise SystemExit(1)
print("OK: no blocking hygiene issues")
