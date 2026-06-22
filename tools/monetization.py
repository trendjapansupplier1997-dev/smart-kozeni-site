#!/usr/bin/env python3
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from site_common import esc

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "monetization" / "programs.json"
VALID_FORMATS = {"text", "banner"}
VALID_STATUSES = {"approved", "paused", "retired"}


@lru_cache(maxsize=1)
def load_registry() -> dict[str, dict[str, Any]]:
    with REGISTRY_PATH.open(encoding="utf-8") as handle:
        root = json.load(handle)
    if root.get("version") != 1:
        raise ValueError(f"{REGISTRY_PATH}: unsupported version")
    programs = root.get("programs")
    if not isinstance(programs, dict) or not programs:
        raise ValueError(f"{REGISTRY_PATH}: programs must be a non-empty object")
    for program_id, program in programs.items():
        _validate_program(program_id, program)
    return programs


def _validate_program(program_id: str, program: Any) -> None:
    if not isinstance(program, dict):
        raise ValueError(f"{REGISTRY_PATH}: {program_id} must be an object")
    for key in (
        "asp",
        "advertiser",
        "status",
        "format",
        "click_url",
        "label",
        "pr_note",
    ):
        if not str(program.get(key, "")).strip():
            raise ValueError(f"{REGISTRY_PATH}: {program_id}.{key} is required")
    if program["status"] not in VALID_STATUSES:
        raise ValueError(f"{REGISTRY_PATH}: {program_id}.status is invalid")
    if program["format"] not in VALID_FORMATS:
        raise ValueError(f"{REGISTRY_PATH}: {program_id}.format is invalid")
    if not program["click_url"].startswith("https://"):
        raise ValueError(f"{REGISTRY_PATH}: {program_id}.click_url must use https")
    tracking = program.get("tracking_pixel_url")
    if tracking is not None and not str(tracking).startswith("https://"):
        raise ValueError(
            f"{REGISTRY_PATH}: {program_id}.tracking_pixel_url must use https"
        )
    referral_code = program.get("referral_code")
    if referral_code is not None:
        if not isinstance(referral_code, str) or not referral_code.strip():
            raise ValueError(
                f"{REGISTRY_PATH}: {program_id}.referral_code must be a non-empty string"
            )
        if len(referral_code) > 64:
            raise ValueError(
                f"{REGISTRY_PATH}: {program_id}.referral_code is too long"
            )
    creative = program.get("creative")
    if program["format"] == "banner":
        if not isinstance(creative, dict):
            raise ValueError(f"{REGISTRY_PATH}: {program_id}.creative is required")
        for key in ("id", "image_url", "width", "height", "alt"):
            if key not in creative:
                raise ValueError(
                    f"{REGISTRY_PATH}: {program_id}.creative.{key} is required"
                )
        if not str(creative["image_url"]).startswith("https://"):
            raise ValueError(
                f"{REGISTRY_PATH}: {program_id}.creative.image_url must use https"
            )
        if not isinstance(creative["width"], int) or creative["width"] <= 0:
            raise ValueError(
                f"{REGISTRY_PATH}: {program_id}.creative.width is invalid"
            )
        if not isinstance(creative["height"], int) or creative["height"] <= 0:
            raise ValueError(
                f"{REGISTRY_PATH}: {program_id}.creative.height is invalid"
            )
    elif creative is not None:
        raise ValueError(
            f"{REGISTRY_PATH}: {program_id}.creative is only valid for banner"
        )


def resolve_cta(spec: Any, path: Path) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise ValueError(f"{path}: cta must be an object")

    program_id = spec.get("program_id")
    if program_id is not None:
        if set(spec) != {"program_id"}:
            raise ValueError(
                f"{path}: program CTA must contain only program_id"
            )
        programs = load_registry()
        if program_id not in programs:
            raise ValueError(f"{path}: unknown monetization program {program_id!r}")
        program = dict(programs[program_id])
        if program["status"] != "approved":
            raise ValueError(
                f"{path}: monetization program {program_id!r} is not active"
            )
        program["program_id"] = program_id
        program["affiliate"] = True
        program["url"] = program.pop("click_url")
        program["note"] = program.pop("pr_note")
        return program

    required = {"url", "label", "affiliate", "note"}
    missing = sorted(required - spec.keys())
    if missing:
        raise ValueError(f"{path}: cta missing keys: {', '.join(missing)}")
    if spec["affiliate"]:
        raise ValueError(
            f"{path}: affiliate CTA must reference data/monetization/programs.json"
        )
    if not str(spec["url"]).startswith("https://"):
        raise ValueError(f"{path}: cta.url must use https")
    if not isinstance(spec["affiliate"], bool):
        raise ValueError(f"{path}: cta.affiliate must be boolean")
    result = dict(spec)
    result.setdefault("format", "text")
    return result


def render_cta(
    cta: dict[str, Any],
    *,
    container_class: str,
    link_class: str,
    note_class: str,
    tracking_class: str,
    creative_class: str,
) -> str:
    rel = ["noopener", "noreferrer"]
    if cta["affiliate"]:
        rel = ["nofollow", "sponsored", *rel]

    is_banner = cta.get("format", "text") == "banner"
    tracking = ""
    if cta.get("tracking_pixel_url"):
        tracking = (
            f'<img class="{esc(tracking_class)}" '
            f'src="{esc(cta["tracking_pixel_url"])}" '
            'width="1" height="1" alt="">'
        )

    if is_banner:
        creative = cta["creative"]
        rendered_link_class = f"{link_class} {link_class}--banner"
        link_body = (
            f'<img class="{esc(creative_class)}" '
            f'src="{esc(creative["image_url"])}" '
            f'width="{creative["width"]}" height="{creative["height"]}" '
            f'alt="{esc(creative["alt"])}" loading="lazy" decoding="async">'
            f'<span class="sr-only">{esc(cta["label"])}</span>'
        )
        tracking_after_link = tracking
    else:
        rendered_link_class = link_class
        link_body = f'{esc(cta["label"])}{tracking}'
        tracking_after_link = ""

    note = ""
    if cta.get("note"):
        note = f'<p class="{esc(note_class)}">{esc(cta["note"])}</p>'

    return (
        f'<div class="{esc(container_class)}">'
        f'<a class="{esc(rendered_link_class)}" href="{esc(cta["url"])}" '
        'target="_blank" '
        f'rel="{" ".join(rel)}" '
        'referrerpolicy="no-referrer-when-downgrade">'
        f'{link_body}</a>'
        f'{tracking_after_link}{note}'
        '</div>'
    )
