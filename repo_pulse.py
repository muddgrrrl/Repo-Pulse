#!/usr/bin/env python3
"""Summarize a local Git checkout without fetching or modifying it."""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


def git(repo, *args, optional=False):
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(repo), *args],
        capture_output=True,
        timeout=20,
        check=False,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    if result.returncode == 0:
        return result.stdout
    if optional:
        return None
    detail = os.fsdecode(result.stderr).strip()
    raise ValueError(detail or f"git {args[0]} failed")


def status_records(output):
    entries = iter(output.split(b"\0"))
    for entry in entries:
        if not entry:
            continue
        status = entry[:2].decode("ascii")
        path = os.fsdecode(entry[3:])
        previous = (
            os.fsdecode(next(entries)) if "R" in status or "C" in status else None
        )
        yield {
            "status": status,
            "path": path,
            **({"previous": previous} if previous else {}),
        }


def summarize(path, limit):
    # Git adds one record terminator. A checkout path can itself end in a newline.
    top = Path(os.fsdecode(git(path, "rev-parse", "--show-toplevel"))[:-1])
    branch = git(top, "symbolic-ref", "--quiet", "--short", "HEAD", optional=True)
    head = git(top, "rev-parse", "--verify", "--short", "HEAD", optional=True)
    upstream = git(
        top,
        "rev-parse",
        "--abbrev-ref",
        "--symbolic-full-name",
        "@{upstream}",
        optional=True,
    )
    ahead = behind = None
    if upstream is not None:
        divergence = git(
            top,
            "rev-list",
            "--left-right",
            "--count",
            "HEAD...@{upstream}",
            optional=True,
        )
        if divergence:
            ahead, behind = map(int, divergence.split())
    changes = list(
        status_records(
            git(top, "status", "--porcelain=v1", "-z", "--untracked-files=normal")
        )
    )
    recent = []
    if head:
        log = git(
            top, "log", "-z", "-n", str(limit), "--format=%h%x00%as%x00%s", "HEAD"
        )
        if log:
            words = (os.fsdecode(word) for word in log.split(b"\0")[:-1])
            recent = [
                {"hash": sha, "date": date, "subject": subject}
                for sha, date, subject in zip(words, words, words)
            ]
    return {
        "repository": str(top),
        "branch": os.fsdecode(branch).rstrip("\n") if branch else None,
        "head": os.fsdecode(head).strip() if head else None,
        "upstream": os.fsdecode(upstream).strip() if upstream else None,
        "ahead": ahead,
        "behind": behind,
        "changes": changes,
        "recent_commits": recent,
    }


def safe(text):
    return "".join(char if char.isprintable() else ascii(char)[1:-1] for char in text)


def print_report(report):
    print(f"{safe(report['repository'])}")
    branch = report["branch"] or "detached HEAD"
    head = report["head"] or "no commits yet"
    print(f"{safe(branch)} · {head}")
    if report["upstream"]:
        delta = (
            ""
            if report["ahead"] is None
            else f" · {report['ahead']} ahead, {report['behind']} behind"
        )
        print(f"Upstream: {safe(report['upstream'])}{delta}")
    changes = report["changes"]
    print(
        f"\n{len(changes)} working-tree changes" if changes else "\nClean working tree"
    )
    for entry in changes:
        path = safe(entry["path"])
        if "previous" in entry:
            path = f"{safe(entry['previous'])} → {path}"
        print(f"  {entry['status']}  {path}")
    if report["recent_commits"]:
        print("\nRecent commits")
        for entry in report["recent_commits"]:
            print(f"  {entry['hash']}  {entry['date']}  {safe(entry['subject'])}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument(
        "--commits", type=int, default=5, help="number of recent commits (0–50)"
    )
    parser.add_argument(
        "--json", action="store_true", help="emit a machine-readable report"
    )
    args = parser.parse_args(argv)
    if not 0 <= args.commits <= 50:
        parser.error("--commits must be between 0 and 50")
    try:
        report = summarize(args.repo, args.commits)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(f"Repo Pulse: {safe(str(error))}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_report(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
