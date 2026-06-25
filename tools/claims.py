#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
import json
from pathlib import Path
import re
import sys
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "claims.json"
TOKEN_RE = re.compile(
    r"\{\{claim:([a-z0-9]+(?:-[a-z0-9]+)*)\.([a-z][a-z0-9_]*)\}\}"
)
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VARIANT_RE = re.compile(r"^[a-z][a-z0-9_]*$")
STATUSES = {"active", "paused", "retired"}
CLAIM_KEYS = {
    "status",
    "checked_at",
    "review_after_days",
    "expires_at",
    "source_url",
    "texts",
    "retired_texts",
}


@dataclass(frozen=True)
class Claim:
    id: str
    status: str
    checked_at: date
    review_after_days: int
    expires_at: date | None
    source_url: str
    texts: dict[str, str]
    retired_texts: tuple[str, ...]


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise RuntimeError(f"{rel(path)}: cannot read: {error}") from error
    except json.JSONDecodeError as error:
        raise RuntimeError(f"{rel(path)}: invalid JSON: {error}") from error


def parse_date(value: object, label: str) -> date:
    require(isinstance(value, str), f"{label} must be YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise RuntimeError(f"{label} must be YYYY-MM-DD") from error


def load_claims() -> dict[str, Claim]:
    document = read_json(REGISTRY_PATH)
    require(isinstance(document, dict), f"{rel(REGISTRY_PATH)}: root must be an object")
    require(
        set(document) == {"version", "claims"} and document["version"] == 1,
        f"{rel(REGISTRY_PATH)}: expected version 1 and claims",
    )
    raw_claims = document["claims"]
    require(
        isinstance(raw_claims, dict) and raw_claims,
        f"{rel(REGISTRY_PATH)}: claims must be a non-empty object",
    )

    today = date.today()
    claims: dict[str, Claim] = {}
    for claim_id, raw in raw_claims.items():
        prefix = f"{rel(REGISTRY_PATH)}: {claim_id}"
        require(
            isinstance(claim_id, str) and ID_RE.fullmatch(claim_id) is not None,
            f"{prefix}: invalid id",
        )
        require(isinstance(raw, dict), f"{prefix}: claim must be an object")
        require(set(raw) == CLAIM_KEYS, f"{prefix}: invalid keys")

        status = raw["status"]
        require(status in STATUSES, f"{prefix}: invalid status")

        checked_at = parse_date(raw["checked_at"], f"{prefix}.checked_at")
        require(checked_at <= today, f"{prefix}.checked_at is in the future")

        review_days = raw["review_after_days"]
        require(
            isinstance(review_days, int)
            and not isinstance(review_days, bool)
            and 1 <= review_days <= 366,
            f"{prefix}.review_after_days must be 1..366",
        )

        expires_at = (
            None
            if raw["expires_at"] is None
            else parse_date(raw["expires_at"], f"{prefix}.expires_at")
        )
        require(
            expires_at is None or expires_at >= checked_at,
            f"{prefix}.expires_at precedes checked_at",
        )

        source_url = raw["source_url"]
        require(
            isinstance(source_url, str) and source_url.startswith("https://"),
            f"{prefix}.source_url must use https",
        )

        raw_texts = raw["texts"]
        require(
            isinstance(raw_texts, dict) and raw_texts,
            f"{prefix}.texts must be a non-empty object",
        )
        texts: dict[str, str] = {}
        for variant, text in raw_texts.items():
            require(
                isinstance(variant, str) and VARIANT_RE.fullmatch(variant) is not None,
                f"{prefix}: invalid variant {variant!r}",
            )
            require(
                isinstance(text, str) and bool(text) and text == text.strip(),
                f"{prefix}.{variant} must be a non-empty trimmed string",
            )
            require("{{claim:" not in text, f"{prefix}.{variant} cannot contain a token")
            texts[variant] = text
        require(len(set(texts.values())) == len(texts), f"{prefix}: duplicate text values")

        raw_retired = raw["retired_texts"]
        require(isinstance(raw_retired, list), f"{prefix}.retired_texts must be a list")
        retired = tuple(raw_retired)
        require(
            all(isinstance(text, str) and bool(text) and text == text.strip() for text in retired),
            f"{prefix}.retired_texts must contain non-empty trimmed strings",
        )
        require(len(set(retired)) == len(retired), f"{prefix}: duplicate retired texts")
        require(
            not (set(texts.values()) & set(retired)),
            f"{prefix}: active and retired texts overlap",
        )

        claims[claim_id] = Claim(
            id=claim_id,
            status=status,
            checked_at=checked_at,
            review_after_days=review_days,
            expires_at=expires_at,
            source_url=source_url,
            texts=texts,
            retired_texts=retired,
        )
    return claims


def resolve_data(value: Any, path: Path) -> Any:
    claims = load_claims()

    def resolve(current: Any) -> Any:
        if isinstance(current, str):
            def replace(match: re.Match[str]) -> str:
                claim_id, variant = match.groups()
                claim = claims.get(claim_id)
                require(claim is not None, f"{rel(path)}: unknown claim {claim_id}")
                require(
                    claim.status == "active",
                    f"{rel(path)}: {claim.status} claim is referenced: {claim_id}",
                )
                require(
                    variant in claim.texts,
                    f"{rel(path)}: unknown variant {claim_id}.{variant}",
                )
                return claim.texts[variant]

            result = TOKEN_RE.sub(replace, current)
            require("{{claim:" not in result, f"{rel(path)}: malformed claim token")
            return result
        if isinstance(current, list):
            return [resolve(item) for item in current]
        if isinstance(current, dict):
            return {key: resolve(item) for key, item in current.items()}
        return current

    return resolve(value)


def source_urls(document: dict[str, Any]) -> set[str]:
    sources = document.get("sources")
    if not isinstance(sources, list):
        return set()
    return {
        item["url"]
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("url"), str)
    }


def verify_registry(*, strict_stale: bool = False) -> None:
    claims = load_claims()
    data_paths = sorted(
        path
        for path in (ROOT / "data").rglob("*.json")
        if path != REGISTRY_PATH and path.is_file()
    )
    raw_by_path = {
        path: path.read_text(encoding="utf-8")
        for path in data_paths
    }
    references: dict[str, list[tuple[Path, str]]] = {
        claim_id: [] for claim_id in claims
    }

    for path, source in raw_by_path.items():
        matches = list(TOKEN_RE.finditer(source))
        require(
            "{{claim:" not in source or bool(matches),
            f"{rel(path)}: malformed claim token",
        )
        for match in matches:
            claim_id, variant = match.groups()
            claim = claims.get(claim_id)
            require(claim is not None, f"{rel(path)}: unknown claim {claim_id}")
            require(
                variant in claim.texts,
                f"{rel(path)}: unknown variant {claim_id}.{variant}",
            )
            references[claim_id].append((path, variant))

    today = date.today()
    stale: list[str] = []
    active_count = 0
    reference_count = 0

    for claim_id, claim in claims.items():
        refs = references[claim_id]
        if claim.status == "active":
            require(refs, f"{rel(REGISTRY_PATH)}: unused active claim {claim_id}")
        else:
            require(not refs, f"{rel(REGISTRY_PATH)}: {claim.status} claim is referenced: {claim_id}")

        used_variants = {variant for _, variant in refs}
        if claim.status == "active":
            missing = sorted(set(claim.texts) - used_variants)
            require(not missing, f"{rel(REGISTRY_PATH)}: unused variants for {claim_id}: {missing}")

        for variant, text in claim.texts.items():
            for path, source in raw_by_path.items():
                require(
                    text not in source,
                    f"{rel(path)}: raw text duplicates {claim_id}.{variant}; use a token",
                )

        for path in sorted({path for path, _ in refs}):
            document = read_json(path)
            require(isinstance(document, dict), f"{rel(path)}: claim data must be an object")
            page_checked = parse_date(document.get("checked_at"), f"{rel(path)}.checked_at")
            require(
                page_checked >= claim.checked_at,
                f"{rel(path)}: checked_at predates {claim_id}",
            )
            require(
                claim.source_url in source_urls(document),
                f"{rel(path)}: sources must include {claim_id}.source_url",
            )

            scope = [path]
            output = document.get("output")
            if isinstance(output, str) and output:
                generated = ROOT / output / "index.html"
                require(generated.exists(), f"{rel(path)}: missing {rel(generated)}")
                scope.append(generated)

            for old_text in claim.retired_texts:
                for scope_path in scope:
                    require(
                        old_text not in scope_path.read_text(encoding="utf-8"),
                        f"{rel(scope_path)}: retired text remains for {claim_id}: {old_text}",
                    )

        if claim.status != "active":
            continue
        active_count += 1
        reference_count += len(refs)
        require(
            claim.expires_at is None or today <= claim.expires_at,
            f"expired active claim: {claim_id}",
        )
        age = (today - claim.checked_at).days
        if age > claim.review_after_days:
            stale.append(
                f"{claim_id} ({age} days; limit {claim.review_after_days})"
            )

    if stale and strict_stale:
        raise RuntimeError("stale active claims: " + ", ".join(stale))
    for message in stale:
        print(f"WARNING: stale claim: {message}", file=sys.stderr)

    print(
        f"OK: {active_count} active claim(s), "
        f"{reference_count} reference(s), {len(stale)} stale"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate time-sensitive public claims."
    )
    parser.add_argument(
        "--strict-stale",
        action="store_true",
        help="fail after review_after_days",
    )
    args = parser.parse_args()
    try:
        verify_registry(strict_stale=args.strict_stale)
    except RuntimeError as error:
        print(f"NG: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
