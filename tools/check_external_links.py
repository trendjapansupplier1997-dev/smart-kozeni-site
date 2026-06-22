#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import json
import socket
import ssl
import sys
import time
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

sys.dont_write_bytecode = True

import external_links

USER_AGENT = (
    "Mozilla/5.0 (compatible; SmartKozeniLinkAudit/1.0; "
    "+https://smart-kozeni.com/contact/)"
)
RESTRICTED_STATUSES = {401, 403, 405, 406, 409, 423, 425, 429}
TRANSIENT_STATUSES = {408, 500, 502, 503, 504}
DEAD_STATUSES = {404, 410}


@dataclass(frozen=True, slots=True)
class CheckResult:
    url: str
    outcome: str
    status: int | None
    final_url: str | None
    detail: str
    sources: tuple[str, ...]
    elapsed_ms: int


def display_url(url: str) -> str:
    from urllib.parse import urlsplit, urlunsplit

    parsed = urlsplit(url)
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path or "/", "", ""))


def classify_status(status: int) -> tuple[str, str]:
    if 200 <= status < 400:
        return "PASS", f"HTTP {status}"
    if status in DEAD_STATUSES:
        return "FAIL", f"HTTP {status}"
    if status in RESTRICTED_STATUSES:
        return "WARN", f"HTTP {status} (access policy or bot restriction)"
    if status in TRANSIENT_STATUSES or 500 <= status < 600:
        return "WARN", f"HTTP {status} (transient server response)"
    if 400 <= status < 500:
        return "FAIL", f"HTTP {status}"
    return "WARN", f"unexpected HTTP {status}"


def classify_error(error: BaseException) -> tuple[str, str]:
    reason = error.reason if isinstance(error, URLError) else error
    if isinstance(reason, socket.gaierror):
        return "FAIL", f"DNS error: {reason}"
    if isinstance(reason, ssl.SSLError):
        return "FAIL", f"TLS error: {reason}"
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return "WARN", f"timeout: {reason}"
    return "WARN", f"network error: {reason}"


def request_once(url: str, *, method: str, timeout: float) -> tuple[int, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.5",
        "Accept-Language": "ja,en;q=0.5",
        "Cache-Control": "no-cache",
    }
    if method == "GET":
        headers["Range"] = "bytes=0-0"
    request = Request(url, method=method, headers=headers)
    opener = build_opener()
    try:
        with opener.open(request, timeout=timeout) as response:
            if method == "GET":
                response.read(1)
            return int(response.status), response.geturl()
    except HTTPError as error:
        return int(error.code), error.geturl()


def check_target(
    target: external_links.LiveTarget,
    *,
    timeout: float,
    retries: int,
) -> CheckResult:
    started = time.monotonic()
    last_error: BaseException | None = None
    for attempt in range(retries + 1):
        try:
            status, final_url = request_once(target.url, method="HEAD", timeout=timeout)
            if status in {400, 403, 405, 406, 501}:
                status, final_url = request_once(target.url, method="GET", timeout=timeout)
            outcome, detail = classify_status(status)
            return CheckResult(
                url=target.url,
                outcome=outcome,
                status=status,
                final_url=final_url,
                detail=detail,
                sources=target.sources,
                elapsed_ms=round((time.monotonic() - started) * 1000),
            )
        except (OSError, URLError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(0.4 * (attempt + 1))
    assert last_error is not None
    outcome, detail = classify_error(last_error)
    return CheckResult(
        url=target.url,
        outcome=outcome,
        status=None,
        final_url=None,
        detail=detail,
        sources=target.sources,
        elapsed_ms=round((time.monotonic() - started) * 1000),
    )


def write_report(path: Path, results: Iterable[CheckResult]) -> None:
    payload = {
        "schema_version": 1,
        "results": [asdict(result) for result in results],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def run_live(
    *,
    timeout: float,
    retries: int,
    workers: int,
    report: Path | None,
    strict_warnings: bool,
) -> int:
    targets, skipped = external_links.live_targets()
    print(f"Targets: {len(targets)} non-monetization external URL(s)")
    print(
        "SKIP: "
        f"{skipped} monetization anchor/asset occurrence(s) are never requested "
        "to avoid synthetic affiliate clicks or impressions"
    )

    with ThreadPoolExecutor(max_workers=min(workers, max(1, len(targets)))) as pool:
        results = list(
            pool.map(
                lambda target: check_target(
                    target,
                    timeout=timeout,
                    retries=retries,
                ),
                targets,
            )
        )

    order = {"FAIL": 0, "WARN": 1, "PASS": 2}
    results.sort(key=lambda result: (order[result.outcome], result.url))
    for result in results:
        final = ""
        if result.final_url and result.final_url != result.url:
            final = f" -> {display_url(result.final_url)}"
        print(
            f"{result.outcome:4} {display_url(result.url)} "
            f"[{result.elapsed_ms}ms] {result.detail}{final}"
        )
        if result.outcome != "PASS":
            print("     source: " + ", ".join(result.sources))

    if report is not None:
        write_report(report, results)
        print(f"REPORT: {report}")

    failures = sum(result.outcome == "FAIL" for result in results)
    warnings = sum(result.outcome == "WARN" for result in results)
    passes = sum(result.outcome == "PASS" for result in results)
    print(f"RESULT: pass={passes} warn={warnings} fail={failures}")
    if failures:
        return 1
    if strict_warnings and warnings:
        return 2
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit Smart Kozeni external-link structure and optionally check "
            "non-monetization destinations over the network."
        )
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="request only non-monetization external anchors over the network",
    )
    parser.add_argument("--timeout", type=float, default=12.0)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--strict-warnings", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()

    if args.timeout <= 0 or args.retries < 0 or args.workers <= 0:
        parser.error("timeout/workers must be positive and retries must be non-negative")

    print("=== external link structural contract ===")
    problems = external_links.audit_contract()
    if problems:
        for problem in problems:
            print(f"NG: {problem}", file=sys.stderr)
        print(f"RESULT: {len(problems)} structural problem(s)", file=sys.stderr)
        return 1
    print("OK: monetization registry, canonical data, and generated HTML agree")

    if not args.live:
        print("SKIP: network requests require --live")
        return 0

    print("\n=== live non-monetization link check ===")
    return run_live(
        timeout=args.timeout,
        retries=args.retries,
        workers=args.workers,
        report=args.report,
        strict_warnings=args.strict_warnings,
    )


if __name__ == "__main__":
    raise SystemExit(main())
