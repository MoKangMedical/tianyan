#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import fnmatch
import json
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from build_github_pages import COPY_TARGETS, ROOT


IGNORE_NAMES = {".git", ".DS_Store", "__pycache__"}
IGNORE_PATTERNS = ("*.pyc",)


class PublishError(RuntimeError):
    """Raised when the GitHub Pages publish flow cannot complete safely."""


class GitHubAPI:
    def __init__(self, repo: str, username: str, password: str) -> None:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "Authorization": f"Basic {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "tianyan-pages-publisher",
        }

    def request(self, method: str, path: str, payload: dict | None = None) -> dict:
        data = None
        headers = dict(self.headers)
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            self.api_base + path,
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = response.read().decode("utf-8")
                return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise PublishError(f"{method} {path} failed: {exc.code} {body}") from exc

    def get(self, path: str) -> dict:
        return self.request("GET", path)

    def post(self, path: str, payload: dict) -> dict:
        return self.request("POST", path, payload)

    def patch(self, path: str, payload: dict) -> dict:
        return self.request("PATCH", path, payload)


def get_github_credentials() -> tuple[str, str]:
    payload = b"protocol=https\nhost=github.com\n\n"
    result = subprocess.run(
        ["git", "credential", "fill"],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise PublishError(f"git credential fill failed: {result.stderr.decode('utf-8', 'ignore')}")

    fields: dict[str, str] = {}
    for line in result.stdout.decode("utf-8", "ignore").splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            fields[key] = value

    username = fields.get("username", "")
    password = fields.get("password", "")
    if not username or not password:
        raise PublishError("No GitHub credential found in git credential helper.")
    return username, password


def iter_target_files(relative: str) -> list[Path]:
    path = ROOT / relative
    if not path.exists():
        raise PublishError(f"Missing publish target: {relative}")
    if path.is_file():
        return [path]

    files: list[Path] = []
    for candidate in sorted(path.rglob("*")):
        if candidate.is_dir():
            continue
        if any(part in IGNORE_NAMES for part in candidate.parts):
            continue
        if any(fnmatch.fnmatch(candidate.name, pattern) for pattern in IGNORE_PATTERNS):
            continue
        files.append(candidate)
    return files


def collect_publish_files() -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()
    for target in COPY_TARGETS:
        for file_path in iter_target_files(target):
            if file_path in seen:
                continue
            seen.add(file_path)
            files.append(file_path)
    return files


def create_backup_branch(api: GitHubAPI, branch: str, sha: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_branch = f"codex/pages-backup-{timestamp}"
    api.post("/git/refs", {"ref": f"refs/heads/{backup_branch}", "sha": sha})
    print(f"Created backup branch {backup_branch} at {sha}")
    return backup_branch


def create_blob_entries(api: GitHubAPI, files: list[Path]) -> list[dict]:
    entries: list[dict] = []
    total = len(files)
    for index, file_path in enumerate(files, start=1):
        relative_path = file_path.relative_to(ROOT).as_posix()
        content = base64.b64encode(file_path.read_bytes()).decode("ascii")
        blob = api.post("/git/blobs", {"content": content, "encoding": "base64"})
        entries.append({
            "path": urllib.parse.unquote(relative_path),
            "mode": "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        print(f"[{index}/{total}] staged {relative_path}")
    return entries


def request_pages_build(api: GitHubAPI) -> None:
    try:
        api.post("/pages/builds", {})
        print("Requested a GitHub Pages rebuild.")
    except PublishError as exc:
        print(f"Pages rebuild request skipped: {exc}")


def wait_for_pages(api: GitHubAPI, expected_commit: str, timeout: int) -> dict:
    deadline = time.time() + timeout
    last_status = None
    while time.time() < deadline:
        latest = api.get("/pages/builds/latest")
        status = latest.get("status")
        commit = latest.get("commit")
        error = latest.get("error", {})
        if status != last_status:
            print(f"Pages build status: {status} (commit={commit})")
            last_status = status
        if status == "built" and commit == expected_commit:
            return latest
        if status == "errored":
            raise PublishError(f"GitHub Pages build errored: {error}")
        time.sleep(5)
    raise PublishError("Timed out waiting for GitHub Pages to finish building.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Publish Tianyan static pages via GitHub API.")
    parser.add_argument("--repo", default="MoKangMedical/tianyan", help="GitHub repo in owner/name form.")
    parser.add_argument("--branch", default="main", help="Branch backing GitHub Pages. Default: main")
    parser.add_argument(
        "--message",
        default="Publish GitHub Pages site",
        help="Commit message used for the publish commit.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="Max seconds to wait for GitHub Pages build completion.",
    )
    parser.add_argument(
        "--skip-build-wait",
        action="store_true",
        help="Do not wait for the GitHub Pages build result after pushing the commit.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the files that would be published without creating a commit.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = collect_publish_files()
    print(f"Collected {len(files)} publishable files.")
    if args.dry_run:
        for file_path in files:
            print(file_path.relative_to(ROOT).as_posix())
        return 0

    username, password = get_github_credentials()
    api = GitHubAPI(args.repo, username, password)

    pages = api.get("/pages")
    if pages.get("source", {}).get("branch") != args.branch or pages.get("source", {}).get("path") != "/":
        raise PublishError(
            f"Unexpected Pages source: {pages.get('source')}. "
            f"Expected branch={args.branch!r} path='/'."
        )

    ref = api.get(f"/git/ref/heads/{args.branch}")
    head_sha = ref["object"]["sha"]
    backup_branch = create_backup_branch(api, args.branch, head_sha)

    head_commit = api.get(f"/git/commits/{head_sha}")
    base_tree_sha = head_commit["tree"]["sha"]
    entries = create_blob_entries(api, files)
    tree = api.post("/git/trees", {"base_tree": base_tree_sha, "tree": entries})
    commit = api.post("/git/commits", {
        "message": args.message,
        "tree": tree["sha"],
        "parents": [head_sha],
    })
    commit_sha = commit["sha"]
    api.patch(f"/git/refs/heads/{args.branch}", {"sha": commit_sha, "force": False})

    print(f"Published commit {commit_sha} to {args.branch}.")
    print(f"Backup branch preserved at {backup_branch}.")
    request_pages_build(api)

    if not args.skip_build_wait:
        latest = wait_for_pages(api, commit_sha, args.timeout)
        print("GitHub Pages build completed.")
        print(json.dumps({
            "page_url": pages.get("html_url"),
            "build_status": latest.get("status"),
            "commit": latest.get("commit"),
        }, ensure_ascii=False))
    else:
        print(f"GitHub Pages URL: {pages.get('html_url')}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PublishError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
