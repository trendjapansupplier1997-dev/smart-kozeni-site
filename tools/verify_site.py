#!/usr/bin/env python3
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
SITE_WORKFLOW = ROOT / ".github" / "workflows" / "site-verification.yml"
EXTERNAL_LINK_WORKFLOW = ROOT / ".github" / "workflows" / "external-link-verification.yml"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run(label: str, command: list[str]) -> None:
    print(f"\n=== {label} ===", flush=True)
    print("$ " + " ".join(command), flush=True)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def discover_builders() -> list[Path]:
    builders = sorted(TOOLS.glob("build_*.py"), key=lambda path: path.name)
    if not builders:
        raise RuntimeError("no build_*.py generators found")
    return builders




def run_builders(builders: list[Path], *, check: bool) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    def execute(builder: Path) -> subprocess.CompletedProcess[str]:
        command = [sys.executable, str(builder)]
        if check:
            command.append("--check")
        return subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

    workers = min(4, len(builders))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = dict(zip(builders, pool.map(execute, builders), strict=True))

    failed: list[str] = []
    action = "check" if check else "generate"
    suffix = " --check" if check else ""
    for builder in builders:
        result = results[builder]
        print(f"\n=== {action} {builder.stem} ===")
        print(f"$ {sys.executable} {builder}{suffix}")
        if result.stdout:
            print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
        if result.returncode != 0:
            failed.append(builder.name)

    if failed:
        raise RuntimeError(f"generator {action} failed: " + ", ".join(failed))

def check_json_files() -> None:
    paths = {
        path
        for pattern in ("*.json", "*.webmanifest")
        for path in ROOT.rglob(pattern)
        if ".git" not in path.parts
    }
    if not paths:
        raise RuntimeError("no JSON documents found")

    for path in sorted(paths):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"{rel(path)}: invalid JSON: {error}") from error
    print(f"OK: {len(paths)} JSON document(s)")


def check_javascript_files() -> None:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node is required for JavaScript syntax checks")

    paths = sorted(
        path
        for path in ROOT.rglob("*.js")
        if ".git" not in path.parts
    )
    if not paths:
        raise RuntimeError("no JavaScript files found")

    for path in paths:
        subprocess.run(
            [node, "--check", str(path)],
            cwd=ROOT,
            check=True,
        )
    print(f"OK: {len(paths)} JavaScript file(s)")


def _check_one_workflow(
    path: Path,
    *,
    command: str,
    required: tuple[str, ...],
    forbidden: tuple[str, ...],
) -> None:
    if not path.exists():
        raise RuntimeError(f"{rel(path)} is missing")
    source = path.read_text(encoding="utf-8")
    if source.count(command) != 1:
        raise RuntimeError(f"{rel(path)} must call `{command}` exactly once")
    for token in forbidden:
        if token in source:
            raise RuntimeError(f"{rel(path)} duplicates verification logic: {token}")
    for token in required:
        if token not in source:
            raise RuntimeError(f"{rel(path)} is missing required contract: {token}")


def check_workflow_contract() -> None:
    _check_one_workflow(
        SITE_WORKFLOW,
        command="python3 tools/verify_site.py",
        required=("pull_request:", "workflow_dispatch:", "contents: read"),
        forbidden=(
            "tools/build_",
            "tools/kozeni_site_audit.py",
            "tools/kozeni_design_audit.py",
            "tools/check_external_links.py",
        ),
    )
    _check_one_workflow(
        EXTERNAL_LINK_WORKFLOW,
        command="python3 tools/check_external_links.py --live",
        required=("schedule:", "cron:", "workflow_dispatch:", "contents: read"),
        forbidden=(
            "tools/build_",
            "tools/verify_site.py",
            "tools/kozeni_site_audit.py",
            "tools/kozeni_design_audit.py",
        ),
    )
    print("OK: local and scheduled workflows each delegate to one command")


def git_output(arguments: Iterable[str]) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def check_git_repository() -> None:
    try:
        git_output(("rev-parse", "--show-toplevel"))
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("verification must run inside a Git repository") from error


def check_ci_clean_worktree() -> None:
    if os.environ.get("CI", "").lower() not in {"1", "true", "yes"}:
        print("SKIP: clean-worktree enforcement is CI-only")
        return

    status = git_output(("status", "--porcelain=v1", "--untracked-files=all"))
    if status:
        print(status, end="", file=sys.stderr)
        raise RuntimeError("CI verification changed the worktree or checkout was dirty")
    print("OK: CI worktree is clean")


def verify(write: bool) -> None:
    check_git_repository()
    builders = discover_builders()

    print("============================================================")
    print(" SMART KOZENI SITE VERIFICATION")
    print(f" Mode: {'write + check' if write else 'check'}")
    print(f" Generators: {len(builders)} (auto-discovered)")
    print("============================================================")

    if write:
        run_builders(builders, check=False)
    else:
        run_builders(builders, check=True)

    print("\n=== JSON syntax ===")
    check_json_files()

    print("\n=== JavaScript syntax ===")
    check_javascript_files()

    print("\n=== GitHub Actions contract ===")
    check_workflow_contract()

    run(
        "integrated site audit",
        [sys.executable, str(TOOLS / "kozeni_site_audit.py")],
    )
    run(
        "design audit",
        [sys.executable, str(TOOLS / "kozeni_design_audit.py")],
    )
    run("unstaged whitespace check", ["git", "diff", "--check"])
    run("staged whitespace check", ["git", "diff", "--cached", "--check"])

    print("\n=== CI clean worktree ===")
    check_ci_clean_worktree()

    print("\n=== result ===")
    print("OK: site verification passed")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run every Smart Kozeni generator and audit from one command."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="regenerate every generated page before running all checks",
    )
    args = parser.parse_args()

    try:
        verify(write=args.write)
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print("\n=== result ===", file=sys.stderr)
        print(f"NG: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
