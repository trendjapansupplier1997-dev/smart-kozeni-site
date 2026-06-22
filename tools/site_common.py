#!/usr/bin/env python3
from __future__ import annotations

import html
from datetime import date
from pathlib import Path
from typing import Any

import seo

BASE_URL = seo.BASE_URL


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def require_non_empty_list(
    data: dict[str, Any],
    key: str,
    path: Path,
) -> list[Any]:
    value = data.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path}: {key} must be a non-empty list")
    return value


def parse_date(value: object, path: Path, key: str = "checked_at") -> date:
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError) as error:
        raise ValueError(f"{path}: {key} must be YYYY-MM-DD") from error


def format_date(value: date) -> str:
    return f"{value.year}年{value.month}月{value.day}日"


def render_list(items: list[str]) -> str:
    return "".join(f"<li>{esc(item)}</li>" for item in items)


def render_badges(items: list[str]) -> str:
    return "".join(f"<span>{esc(item)}</span>" for item in items)


def render_facts(
    items: list[dict[str, str]],
    row_class: str,
) -> str:
    return "".join(
        f'<div class="{esc(row_class)}">'
        f'<dt>{esc(item["label"])}</dt>'
        f'<dd>{esc(item["value"])}</dd>'
        '</div>'
        for item in items
    )


def render_sources(
    items: list[dict[str, str]],
) -> str:
    return "".join(
        '<li>根拠：'
        f'<a href="{esc(item["url"])}" '
        'target="_blank" rel="noopener noreferrer">'
        f'{esc(item["label"])}</a>'
        '</li>'
        for item in items
    )


def render_related(
    items: list[dict[str, str]],
    link_class: str | None = None,
) -> str:
    rows: list[str] = []
    class_attr = f' class="{esc(link_class)}"' if link_class else ""
    for item in items:
        href = str(item["href"])
        if not href.startswith("/"):
            raise ValueError(f"related href must be site-relative: {href}")
        rows.append(
            f'<a{class_attr} href="{esc(href)}">'
            f'<strong>{esc(item["title"])}</strong>'
            f'<span>{esc(item["description"])}</span>'
            '</a>'
        )
    return "".join(rows)


def render_faq(items: list[dict[str, str]]) -> str:
    return "".join(
        '<details>'
        f'<summary>{esc(item["question"])}</summary>'
        f'<p>{esc(item["answer"])}</p>'
        '</details>'
        for item in items
    )


def render_page_jsonld(
    *,
    canonical: str,
    title: str,
    description: str,
    checked_at: str,
    breadcrumbs: list[tuple[str, str]],
) -> str:
    return seo.render_page_jsonld(
        canonical=canonical,
        title=title,
        description=description,
        checked_at=checked_at,
        breadcrumbs=breadcrumbs,
    )


def clean_rendered(value: str) -> str:
    cleaned = "\n".join(line.rstrip() for line in value.splitlines())
    return cleaned.rstrip() + "\n"
