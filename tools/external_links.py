#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import Enum
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlsplit

import monetization
import repo_paths

ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "data"
REGISTRY_PATH = DATA_ROOT / "monetization" / "programs.json"
PROGRAM_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TEXT_SUFFIXES = {".css", ".html", ".js", ".json", ".md", ".py", ".txt", ".xml", ".yaml", ".yml"}


class LinkRole(str, Enum):
    AFFILIATE_CLICK = "affiliate-click"
    TRACKING_PIXEL = "tracking-pixel"
    CREATIVE_IMAGE = "creative-image"
    EXTERNAL_ANCHOR = "external-anchor"
    EXTERNAL_ASSET = "external-asset"


@dataclass(frozen=True, slots=True)
class ProgramReference:
    program_id: str
    source: str
    locator: str


@dataclass(frozen=True, slots=True)
class DataLink:
    url: str
    source: str
    locator: str


@dataclass(frozen=True, slots=True)
class RawAffiliateFlag:
    source: str
    locator: str


@dataclass(frozen=True, slots=True)
class HtmlLink:
    url: str
    role: LinkRole
    source: str
    line: int
    attributes: tuple[tuple[str, str], ...]
    program_id: str | None = None


@dataclass(frozen=True, slots=True)
class LiveTarget:
    url: str
    sources: tuple[str, ...]


def is_http_url(value: object) -> bool:
    if not isinstance(value, str):
        return False
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _locator(parts: tuple[object, ...]) -> str:
    result = "$"
    for part in parts:
        if isinstance(part, int):
            result += f"[{part}]"
        else:
            result += f".{part}"
    return result



def _walk_data(
    value: Any,
    *,
    source: str,
    parts: tuple[object, ...],
    references: list[ProgramReference],
    links: list[DataLink],
    raw_affiliate_flags: list[RawAffiliateFlag],
) -> None:
    if isinstance(value, dict):
        if value.get("affiliate") is True:
            raw_affiliate_flags.append(
                RawAffiliateFlag(
                    source=source,
                    locator=_locator((*parts, "affiliate")),
                )
            )
        program_id = value.get("program_id")
        if program_id is not None:
            references.append(
                ProgramReference(
                    program_id=str(program_id),
                    source=source,
                    locator=_locator((*parts, "program_id")),
                )
            )
        for key, nested in value.items():
            _walk_data(
                nested,
                source=source,
                parts=(*parts, key),
                references=references,
                links=links,
                raw_affiliate_flags=raw_affiliate_flags,
            )
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            _walk_data(
                nested,
                source=source,
                parts=(*parts, index),
                references=references,
                links=links,
                raw_affiliate_flags=raw_affiliate_flags,
            )
    elif is_http_url(value):
        links.append(
            DataLink(
                url=str(value),
                source=source,
                locator=_locator(parts),
            )
        )


def discover_data_contract() -> tuple[
    list[ProgramReference],
    list[DataLink],
    list[RawAffiliateFlag],
]:
    references: list[ProgramReference] = []
    links: list[DataLink] = []
    raw_affiliate_flags: list[RawAffiliateFlag] = []
    for path in sorted(DATA_ROOT.rglob("*.json")):
        if path == REGISTRY_PATH:
            continue
        source = path.relative_to(ROOT).as_posix()
        raw = json.loads(path.read_text(encoding="utf-8"))
        _walk_data(
            raw,
            source=source,
            parts=(),
            references=references,
            links=links,
            raw_affiliate_flags=raw_affiliate_flags,
        )
    return references, links, raw_affiliate_flags


class _LinkParser(HTMLParser):
    def __init__(
        self,
        *,
        source: str,
        click_programs: dict[str, str],
        tracking_programs: dict[str, str],
        creative_programs: dict[str, str],
    ) -> None:
        super().__init__(convert_charrefs=True)
        self.source = source
        self.click_programs = click_programs
        self.tracking_programs = tracking_programs
        self.creative_programs = creative_programs
        self.links: list[HtmlLink] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key.lower(): value or "" for key, value in attrs}
        attribute = ""
        if tag.lower() == "a":
            attribute = "href"
        elif tag.lower() in {"img", "script", "iframe", "source"}:
            attribute = "src"
        if not attribute:
            return
        url = attr_map.get(attribute, "")
        if not is_http_url(url):
            return

        program_id: str | None = None
        if attribute == "href" and url in self.click_programs:
            role = LinkRole.AFFILIATE_CLICK
            program_id = self.click_programs[url]
        elif attribute == "src" and url in self.tracking_programs:
            role = LinkRole.TRACKING_PIXEL
            program_id = self.tracking_programs[url]
        elif attribute == "src" and url in self.creative_programs:
            role = LinkRole.CREATIVE_IMAGE
            program_id = self.creative_programs[url]
        elif attribute == "href":
            role = LinkRole.EXTERNAL_ANCHOR
        else:
            role = LinkRole.EXTERNAL_ASSET

        self.links.append(
            HtmlLink(
                url=url,
                role=role,
                source=self.source,
                line=self.getpos()[0],
                attributes=tuple(sorted(attr_map.items())),
                program_id=program_id,
            )
        )


def discover_html_links(
    programs: dict[str, dict[str, Any]] | None = None,
) -> list[HtmlLink]:
    programs = programs or monetization.load_registry()
    click_programs = {
        str(program["click_url"]): program_id
        for program_id, program in programs.items()
    }
    tracking_programs = {
        str(program["tracking_pixel_url"]): program_id
        for program_id, program in programs.items()
        if program.get("tracking_pixel_url")
    }
    creative_programs = {
        str(program["creative"]["image_url"]): program_id
        for program_id, program in programs.items()
        if isinstance(program.get("creative"), dict)
    }

    links: list[HtmlLink] = []
    for path in sorted(repo_paths.iter_files(ROOT, "*.html")):
        if "templates" in path.relative_to(ROOT).parts:
            continue
        source = path.relative_to(ROOT).as_posix()
        parser = _LinkParser(
            source=source,
            click_programs=click_programs,
            tracking_programs=tracking_programs,
            creative_programs=creative_programs,
        )
        parser.feed(path.read_text(encoding="utf-8", errors="ignore"))
        links.extend(parser.links)
    return links


def monetization_urls(programs: dict[str, dict[str, Any]]) -> dict[str, tuple[str, str]]:
    values: dict[str, tuple[str, str]] = {}
    for program_id, program in programs.items():
        values[str(program["click_url"])] = (program_id, "click_url")
        tracking = program.get("tracking_pixel_url")
        if tracking:
            values[str(tracking)] = (program_id, "tracking_pixel_url")
        creative = program.get("creative")
        if isinstance(creative, dict):
            values[str(creative["image_url"])] = (program_id, "creative.image_url")
    return values


def _canonical_source_files() -> Iterable[Path]:
    for path in repo_paths.iter_files(ROOT, "*"):
        if not path.is_file():
            continue
        if path == REGISTRY_PATH or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.suffix.lower() == ".html" and "templates" not in path.parts:
            continue
        yield path


def audit_contract(
    programs: dict[str, dict[str, Any]] | None = None,
) -> list[str]:
    problems: list[str] = []
    try:
        programs = programs or monetization.load_registry()
        references, data_links, raw_affiliate_flags = discover_data_contract()
        html_links = discover_html_links(programs)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        return [f"external link discovery failed: {error}"]

    for flag in raw_affiliate_flags:
        problems.append(
            f"{flag.source}{flag.locator}: affiliate CTA must use program_id"
        )

    for program_id in programs:
        if not PROGRAM_ID_RE.fullmatch(program_id):
            problems.append(
                f"{REGISTRY_PATH.relative_to(ROOT)}: invalid program_id: {program_id}"
            )

    click_url_counts = Counter(str(program["click_url"]) for program in programs.values())
    for url, count in sorted(click_url_counts.items()):
        if count > 1:
            problems.append(f"{REGISTRY_PATH.relative_to(ROOT)}: duplicate click_url: {url}")

    reference_counts = Counter(reference.program_id for reference in references)
    for reference in references:
        if reference.program_id not in programs:
            problems.append(
                f"{reference.source}{reference.locator}: unknown program_id {reference.program_id!r}"
            )

    for program_id, program in sorted(programs.items()):
        status = str(program.get("status", ""))
        count = reference_counts.get(program_id, 0)
        if status == "approved" and count == 0:
            problems.append(
                f"{REGISTRY_PATH.relative_to(ROOT)}: approved program is unused: {program_id}"
            )
        if status != "approved" and count:
            problems.append(
                f"{REGISTRY_PATH.relative_to(ROOT)}: inactive program is still referenced: {program_id}"
            )

    registered_urls = monetization_urls(programs)
    for link in data_links:
        if link.url in registered_urls:
            program_id, field = registered_urls[link.url]
            problems.append(
                f"{link.source}{link.locator}: {program_id}.{field} must only exist in the monetization registry"
            )
        if urlsplit(link.url).scheme != "https":
            problems.append(f"{link.source}{link.locator}: external URL must use https")

    for path in _canonical_source_files():
        source = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(ROOT).as_posix()
        for url, (program_id, field) in registered_urls.items():
            if url in source:
                problems.append(
                    f"{rel}: raw {program_id}.{field} is duplicated outside the registry/generated HTML"
                )

    click_links: defaultdict[str, list[HtmlLink]] = defaultdict(list)
    tracking_links: defaultdict[str, list[HtmlLink]] = defaultdict(list)
    creative_links: defaultdict[str, list[HtmlLink]] = defaultdict(list)
    for link in html_links:
        attrs = {key: value for key, value in link.attributes}
        if link.role in {LinkRole.EXTERNAL_ANCHOR, LinkRole.AFFILIATE_CLICK}:
            rel_tokens = set(attrs.get("rel", "").split())
            if attrs.get("target") != "_blank":
                problems.append(
                    f"{link.source}:{link.line}: external anchor must use target=_blank"
                )
            for token in ("noopener", "noreferrer"):
                if token not in rel_tokens:
                    problems.append(
                        f"{link.source}:{link.line}: external anchor missing rel={token}"
                    )
            if link.role == LinkRole.AFFILIATE_CLICK:
                assert link.program_id is not None
                click_links[link.program_id].append(link)
                for token in ("nofollow", "sponsored"):
                    if token not in rel_tokens:
                        problems.append(
                            f"{link.source}:{link.line}: affiliate anchor missing rel={token}"
                        )
                if attrs.get("referrerpolicy") != "no-referrer-when-downgrade":
                    problems.append(
                        f"{link.source}:{link.line}: affiliate anchor has invalid referrerpolicy"
                    )
            elif "sponsored" in rel_tokens:
                problems.append(
                    f"{link.source}:{link.line}: sponsored anchor is not registered monetization"
                )
        elif link.role == LinkRole.TRACKING_PIXEL:
            assert link.program_id is not None
            tracking_links[link.program_id].append(link)
        elif link.role == LinkRole.CREATIVE_IMAGE:
            assert link.program_id is not None
            creative_links[link.program_id].append(link)
        else:
            problems.append(
                f"{link.source}:{link.line}: unregistered external asset: {link.url}"
            )

    for program_id, program in sorted(programs.items()):
        if program.get("status") != "approved":
            continue
        click_count = len(click_links[program_id])
        if click_count == 0:
            problems.append(
                f"{REGISTRY_PATH.relative_to(ROOT)}: approved program has no generated anchor: {program_id}"
            )
        tracking = program.get("tracking_pixel_url")
        tracking_count = len(tracking_links[program_id])
        if tracking and tracking_count != click_count:
            problems.append(
                f"{program_id}: tracking pixel count {tracking_count} differs from anchor count {click_count}"
            )
        if not tracking and tracking_count:
            problems.append(f"{program_id}: unexpected tracking pixel")

        creative = program.get("creative")
        creative_count = len(creative_links[program_id])
        if isinstance(creative, dict) and creative_count != click_count:
            problems.append(
                f"{program_id}: creative image count {creative_count} differs from anchor count {click_count}"
            )
        if not isinstance(creative, dict) and creative_count:
            problems.append(f"{program_id}: unexpected creative image")

    return problems


def live_targets(
    programs: dict[str, dict[str, Any]] | None = None,
) -> tuple[list[LiveTarget], int]:
    programs = programs or monetization.load_registry()
    registered = set(monetization_urls(programs))
    html_links = discover_html_links(programs)

    grouped_sources: defaultdict[str, set[str]] = defaultdict(set)
    skipped = 0
    for link in html_links:
        if link.url in registered:
            skipped += 1
            continue
        if link.role != LinkRole.EXTERNAL_ANCHOR:
            continue
        grouped_sources[link.url].add(f"{link.source}:{link.line}")

    targets = [
        LiveTarget(
            url=url,
            sources=tuple(sorted(grouped_sources[url])),
        )
        for url in sorted(grouped_sources)
    ]
    return targets, skipped
