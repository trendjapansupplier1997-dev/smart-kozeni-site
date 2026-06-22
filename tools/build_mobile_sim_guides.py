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
import public_assets

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "mobile-sim-guides"
DETAIL_DATA_DIR = ROOT / "data" / "mobile-sim"
TEMPLATE_PATH = ROOT / "templates" / "mobile-sim-guide.html"
BASE_URL = "https://smart-kozeni.com"
STYLE_HREF = "/assets/kozeni-mobile-guide.v1.css?v=45.0"
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OUTPUT_RE = re.compile(r"^mobile-sim/[a-z0-9-]+(?:/[a-z0-9-]+)*$")


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def require_list(data: dict[str, Any], key: str, path: Path, empty: bool = False) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or (not empty and not value):
        raise ValueError(f"{path}: {key} must be {'a' if empty else 'a non-empty'} list")
    return value


def load_data(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = {"id","output","parent_slug","show_parent_cta","title","description","breadcrumb_label","eyebrow","h1","lead","checked_at","summary_title","summary","steps","checklist","avoid","next","faq","sources"}
    missing = sorted(required - data.keys())
    if missing:
        raise ValueError(f"{path}: missing keys: {', '.join(missing)}")
    if path.stem != data["id"] or not ID_RE.fullmatch(data["id"]):
        raise ValueError(f"{path}: invalid id")
    if not OUTPUT_RE.fullmatch(data["output"]):
        raise ValueError(f"{path}: invalid output")
    try:
        data["_checked_at_date"] = date.fromisoformat(data["checked_at"])
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}: checked_at must be YYYY-MM-DD") from error
    parent_slug = data["parent_slug"]
    if parent_slug is None:
        data["_parent"] = None
    else:
        parent_path = DETAIL_DATA_DIR / f"{parent_slug}.json"
        if not parent_path.exists():
            raise ValueError(f"{path}: parent detail is missing")
        data["_parent"] = build_mobile_sim.load_data(parent_path)
    if not isinstance(data["show_parent_cta"], bool):
        raise ValueError(f"{path}: show_parent_cta must be boolean")
    if data["show_parent_cta"] and data["_parent"] is None:
        raise ValueError(f"{path}: parent CTA requires parent_slug")
    for key in ("steps","checklist","next","faq"):
        require_list(data, key, path)
    for key in ("avoid","sources"):
        require_list(data, key, path, empty=True)
    for item in data["next"]:
        if not item["href"].startswith("/"):
            raise ValueError(f"{path}: next href must be internal")
    for item in data["sources"]:
        if not item["url"].startswith("https://"):
            raise ValueError(f"{path}: source URL must use https")
    return data


def output_path(data: dict[str, Any]) -> Path:
    return ROOT / data["output"] / "index.html"


def canonical_url(data: dict[str, Any]) -> str:
    return f"{BASE_URL}/{data['output']}/"


def render_steps(items: list[dict[str, str]]) -> str:
    return "".join(f'<article class="guide-step"><span class="guide-num">{i}</span><div><h3>{esc(x["title"])}</h3><p>{esc(x["description"])}</p></div></article>' for i, x in enumerate(items, 1))


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_next(items: list[dict[str, str]]) -> str:
    return "".join(f'<a class="guide-next-link" href="{esc(x["href"])}"><strong>{esc(x["title"])}</strong><span>{esc(x["description"])}</span></a>' for x in items)


def render_faq(items: list[dict[str, str]]) -> str:
    return "".join(f'<details><summary>{esc(x["question"])}</summary><p>{esc(x["answer"])}</p></details>' for x in items)


def render_sources(items: list[dict[str, str]]) -> str:
    if not items:
        return ""
    links = "".join(f'<li>根拠：<a href="{esc(x["url"])}" target="_blank" rel="noopener noreferrer">{esc(x["label"])}</a></li>' for x in items)
    return f'<section class="guide-section" aria-labelledby="source-title"><div class="guide-head"><h2 id="source-title">公式情報の参照先</h2><p>条件や時期は公式画面を優先します。</p></div><ul class="guide-source-list">{links}</ul></section>'


def render_avoid(items: list[str]) -> str:
    if not items:
        return ""
    return f'<section class="guide-section" aria-labelledby="avoid-title"><div class="guide-head"><h2 id="avoid-title">避けたい進め方</h2><p>条件確認前の再申込や経路変更を避けます。</p></div><ul class="guide-list guide-avoid">{render_list(items)}</ul></section>'


def render_jsonld(data: dict[str, Any], canonical: str) -> str:
    crumbs = [
        {"@type":"ListItem","position":1,"name":"ホーム","item":f"{BASE_URL}/"},
        {"@type":"ListItem","position":2,"name":"スマホ・回線","item":f"{BASE_URL}/mobile-sim/"},
    ]
    parent = data["_parent"]
    if parent:
        crumbs.append({"@type":"ListItem","position":3,"name":parent["name"],"item":f"{BASE_URL}/mobile-sim/{parent['slug']}/"})
    crumbs.append({"@type":"ListItem","position":len(crumbs)+1,"name":data["breadcrumb_label"],"item":canonical})
    graph = {"@context":"https://schema.org","@graph":[
        {"@type":"WebSite","@id":f"{BASE_URL}/#website","url":f"{BASE_URL}/","name":"スマホ小銭研究所","inLanguage":"ja"},
        {"@type":"Organization","@id":f"{BASE_URL}/#organization","name":"スマホ小銭研究所","url":f"{BASE_URL}/"},
        {"@type":"WebPage","@id":f"{canonical}#webpage","url":canonical,"name":data["title"],"description":data["description"],"dateModified":data["checked_at"],"isPartOf":{"@id":f"{BASE_URL}/#website"},"publisher":{"@id":f"{BASE_URL}/#organization"},"breadcrumb":{"@id":f"{canonical}#breadcrumb"},"inLanguage":"ja"},
        {"@type":"BreadcrumbList","@id":f"{canonical}#breadcrumb","itemListElement":crumbs},
    ]}
    return json.dumps(graph, ensure_ascii=False, separators=(",", ":"))


def render_page(data: dict[str, Any], template: Template) -> str:
    parent = data["_parent"]
    if parent:
        parent_href = f"/mobile-sim/{parent['slug']}/"
        parent_breadcrumb = f'<span aria-hidden="true">›</span><a href="{parent_href}">{esc(parent["name"])}</a>'
        return_href, return_label = parent_href, parent["name"]
    else:
        parent_breadcrumb = ""
        return_href, return_label = "/mobile-sim/", "スマホ・回線一覧"
    cta = build_mobile_sim.render_cta(parent["cta"]) if data["show_parent_cta"] else ""
    canonical = canonical_url(data)
    values = {
        "title":esc(data["title"]),"description":esc(data["description"]),"canonical":esc(canonical),
        "parent_breadcrumb":parent_breadcrumb,"breadcrumb_label":esc(data["breadcrumb_label"]),"eyebrow":esc(data["eyebrow"]),"h1":esc(data["h1"]),"lead":esc(data["lead"]),
        "checked_at":esc(data["checked_at"]),"checked_at_display":esc(build_mobile_sim.format_checked_at(data["_checked_at_date"])),"summary_title":esc(data["summary_title"]),"summary":esc(data["summary"]),
        "steps":render_steps(data["steps"]),"checklist":render_list(data["checklist"]),"avoid_section":render_avoid(data["avoid"]),"cta":cta,"source_section":render_sources(data["sources"]),
        "next_links":render_next(data["next"]),"faq_items":render_faq(data["faq"]),"return_href":esc(return_href),"return_label":esc(return_label),"seo_jsonld":render_jsonld(data, canonical).replace("</", "<\\/")
    }
    rendered = template.substitute(values)
    cleaned = "\n".join(
        line.rstrip() for line in rendered.splitlines()
    )
    return cleaned.rstrip() + "\n"


def data_paths(ids: list[str]) -> list[Path]:
    paths = sorted(DATA_DIR.glob("*.json"))
    if not ids:
        return paths
    wanted = set(ids)
    selected = [p for p in paths if p.stem in wanted]
    missing = sorted(wanted - {p.stem for p in selected})
    if missing:
        raise ValueError(f"unknown guide id(s): {', '.join(missing)}")
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("ids", nargs="*")
    args = parser.parse_args()
    template = public_assets.load_template(TEMPLATE_PATH)
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
