#!/usr/bin/env python3
"""Sync a Git worktree from GitHub's REST API when git transport is unavailable.

This is a fallback for environments where `git fetch` / `git pull` against
github.com hang or fail, but the GitHub REST API and tarball downloads still
work.

The script only supports fast-forwarding a branch from the remote branch
history. If local history is not an ancestor of the remote branch, use
`--rebuild` to recreate the branch from the remote commit chain.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


OFFSET_CHOICES = []
for total_minutes in range(-12 * 60, 14 * 60 + 1, 15):
    sign = "+" if total_minutes >= 0 else "-"
    minutes = abs(total_minutes)
    OFFSET_CHOICES.append(f"{sign}{minutes // 60:02d}{minutes % 60:02d}")


class SyncError(RuntimeError):
    """Raised when the fallback sync cannot proceed safely."""


@dataclass
class CommitMaterialization:
    sha: str
    offset: str
    message_suffix: str


class GitHubRepo:
    def __init__(self, repo: str, token: str | None = None) -> None:
        self.repo = repo
        self.api_base = f"https://api.github.com/repos/{repo}"
        self.headers = {
            "User-Agent": "tianyan-sync-fallback",
            "Accept": "application/vnd.github+json",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def request_json(self, path: str) -> dict | list:
        request = urllib.request.Request(self.api_base + path, headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SyncError(f"GitHub API request failed: {path} -> {exc.code} {body}") from exc

    def list_commits(self, branch: str) -> list[dict]:
        commits: list[dict] = []
        page = 1
        while True:
            page_commits = self.request_json(
                f"/commits?sha={urllib.parse.quote(branch)}&per_page=100&page={page}"
            )
            if not page_commits:
                break
            if not isinstance(page_commits, list):
                raise SyncError("Unexpected GitHub API response while listing commits")
            commits.extend(page_commits)
            if len(page_commits) < 100:
                break
            page += 1
        if not commits:
            raise SyncError(f"No commits found for branch {branch!r}")
        commits.reverse()
        return commits

    def get_commit(self, sha: str) -> dict:
        commit = self.request_json(f"/git/commits/{sha}")
        if not isinstance(commit, dict):
            raise SyncError(f"Unexpected commit payload for {sha}")
        return commit

    def download_tarball(self, sha: str, destination: Path) -> None:
        request = urllib.request.Request(f"{self.api_base}/tarball/{sha}", headers=self.headers)
        try:
            with urllib.request.urlopen(request, timeout=120) as response, destination.open("wb") as handle:
                shutil.copyfileobj(response, handle)
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise SyncError(f"GitHub tarball download failed for {sha}: {exc.code} {body}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fallback sync for GitHub repos when native git transport is unusable."
    )
    parser.add_argument("--repo", help="GitHub repo in owner/name format. Defaults to origin URL.")
    parser.add_argument("--branch", default="main", help="Remote branch to sync. Default: main")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the local branch from remote history if local HEAD is not in remote history.",
    )
    parser.add_argument(
        "--offset",
        default="auto",
        help="Commit timezone offset to use when reconstructing commits, e.g. +0800. Default: auto",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be synced without changing the repository.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow sync even if the worktree contains local changes or ignored files.",
    )
    return parser.parse_args()


def run_git(
    repo_root: Path,
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> str:
    process = subprocess.run(
        ["git", *args],
        cwd=str(repo_root),
        env=env,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and process.returncode != 0:
        raise SyncError(
            f"git {' '.join(args)} failed\nstdout:\n{process.stdout.decode()}\nstderr:\n{process.stderr.decode()}"
        )
    return process.stdout.decode().strip()


def ensure_git_repo(repo_root: Path) -> None:
    git_dir = repo_root / ".git"
    if git_dir.exists():
        return
    run_git(repo_root, ["init", "-q"])


def infer_repo_from_origin(repo_root: Path) -> str:
    origin = run_git(repo_root, ["config", "--get", "remote.origin.url"], check=False)
    if not origin:
        raise SyncError("No origin remote configured. Pass --repo owner/name explicitly.")
    if origin.startswith("git@github.com:"):
        repo = origin.removeprefix("git@github.com:")
    elif origin.startswith("https://github.com/"):
        repo = origin.removeprefix("https://github.com/")
    else:
        raise SyncError(f"Unsupported origin URL: {origin}")
    return repo.removesuffix(".git").strip("/")


def check_worktree_clean(repo_root: Path) -> None:
    status = run_git(repo_root, ["status", "--porcelain=v1", "--untracked-files=all"], check=False)
    ignored = run_git(
        repo_root,
        ["ls-files", "--others", "-i", "--exclude-standard"],
        check=False,
    )
    if status or ignored:
        detail = []
        if status:
            detail.append(status)
        if ignored:
            detail.append(ignored)
        raise SyncError(
            "Refusing to sync over a dirty worktree. Commit, stash, or remove local files first.\n"
            + "\n".join(detail)
        )


def clear_worktree(repo_root: Path) -> None:
    for child in repo_root.iterdir():
        if child.name == ".git":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()


def copy_snapshot(source_root: Path, repo_root: Path) -> None:
    clear_worktree(repo_root)
    for child in source_root.iterdir():
        target = repo_root / child.name
        if child.is_dir() and not child.is_symlink():
            shutil.copytree(child, target, copy_function=shutil.copy2)
        elif child.is_symlink():
            target.symlink_to(os.readlink(child))
        else:
            shutil.copy2(child, target)


def git_date(iso_z: str, offset: str) -> str:
    timestamp = int(datetime.fromisoformat(iso_z.replace("Z", "+00:00")).timestamp())
    return f"{timestamp} {offset}"


def make_commit(
    repo_root: Path,
    tree_sha: str,
    detail: dict,
    offset: str,
    message_suffix: str,
) -> str:
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = detail["author"]["name"]
    env["GIT_AUTHOR_EMAIL"] = detail["author"]["email"]
    env["GIT_AUTHOR_DATE"] = git_date(detail["author"]["date"], offset)
    env["GIT_COMMITTER_NAME"] = detail["committer"]["name"]
    env["GIT_COMMITTER_EMAIL"] = detail["committer"]["email"]
    env["GIT_COMMITTER_DATE"] = git_date(detail["committer"]["date"], offset)

    command = ["commit-tree", tree_sha]
    for parent in detail["parents"]:
        command.extend(["-p", parent["sha"]])
    message = detail["message"] + message_suffix
    return run_git(repo_root, command, env=env, input_bytes=message.encode("utf-8"))


def materialize_commit(
    repo_root: Path,
    tree_sha: str,
    detail: dict,
    *,
    preferred_offsets: Iterable[str],
) -> CommitMaterialization:
    target_sha = detail["sha"]
    offsets = []
    seen = set()
    for offset in preferred_offsets:
        if offset not in seen:
            offsets.append(offset)
            seen.add(offset)
    for offset in OFFSET_CHOICES:
        if offset not in seen:
            offsets.append(offset)
            seen.add(offset)

    for offset in offsets:
        for message_suffix in ("\n", ""):
            actual_sha = make_commit(repo_root, tree_sha, detail, offset, message_suffix)
            if actual_sha == target_sha:
                return CommitMaterialization(
                    sha=actual_sha,
                    offset=offset,
                    message_suffix=message_suffix,
                )

    raise SyncError(
        f"Could not reproduce commit {target_sha}. Try rerunning with --offset +0800 "
        "or rebuild from a clean repo."
    )


def extract_snapshot(tarball: Path, destination: Path) -> Path:
    with tarfile.open(tarball, "r:gz") as archive:
        archive.extractall(destination, filter="fully_trusted")
    roots = list(destination.iterdir())
    if len(roots) != 1:
        raise SyncError(f"Unexpected tarball layout in {tarball}")
    return roots[0]


def main() -> int:
    args = parse_args()
    repo_root = Path.cwd()
    ensure_git_repo(repo_root)

    if not args.allow_dirty:
        check_worktree_clean(repo_root)

    repo = args.repo or infer_repo_from_origin(repo_root)
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    github = GitHubRepo(repo, token=token)

    remote_commits = github.list_commits(args.branch)
    remote_shas = [commit["sha"] for commit in remote_commits]
    remote_head = remote_shas[-1]

    local_head = run_git(repo_root, ["rev-parse", "--verify", f"refs/heads/{args.branch}"], check=False)
    if local_head == remote_head:
        print(f"{args.branch} is already up to date at {remote_head}")
        if not args.dry_run:
            run_git(repo_root, ["update-ref", f"refs/remotes/origin/{args.branch}", remote_head])
            run_git(repo_root, ["remote", "remove", "origin"], check=False)
            run_git(repo_root, ["remote", "add", "origin", f"https://github.com/{repo}.git"])
            run_git(repo_root, ["config", f"branch.{args.branch}.remote", "origin"])
            run_git(repo_root, ["config", f"branch.{args.branch}.merge", f"refs/heads/{args.branch}"])
        return 0

    start_index = 0
    if local_head:
        if local_head in remote_shas:
            start_index = remote_shas.index(local_head) + 1
        elif not args.rebuild:
            raise SyncError(
                f"Local {args.branch} HEAD {local_head} is not an ancestor of remote {args.branch}. "
                "Run again with --rebuild from a clean worktree if you want to replace local history."
            )

    pending = remote_commits[start_index:]
    if not pending:
        print(f"No new commits to sync for {args.branch}")
        if not args.dry_run:
            run_git(repo_root, ["update-ref", f"refs/remotes/origin/{args.branch}", remote_head])
        return 0

    print(f"Syncing {len(pending)} commit(s) from {repo}@{args.branch}")
    print(f"Target HEAD: {remote_head}")
    if args.dry_run:
        for commit in pending:
            print(f"  {commit['sha']} {commit['commit']['message'].splitlines()[0]}")
        return 0

    if start_index == 0 and local_head:
        print(f"Rebuilding local {args.branch} from remote history")
        shutil.rmtree(repo_root / ".git", ignore_errors=True)
        ensure_git_repo(repo_root)

    run_git(repo_root, ["symbolic-ref", "HEAD", f"refs/heads/{args.branch}"])
    run_git(repo_root, ["config", "gc.auto", "0"])

    preferred_offsets = [args.offset] if args.offset != "auto" else []

    with tempfile.TemporaryDirectory(prefix="github-sync-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        created = set(run_git(repo_root, ["rev-list", "--all"], check=False).splitlines())

        for index, commit in enumerate(remote_commits if start_index == 0 else pending, start=1):
            sha = commit["sha"]
            if sha in created:
                continue

            detail = github.get_commit(sha)
            tarball = temp_dir / f"{sha}.tar.gz"
            snapshot_root = temp_dir / f"extract-{sha}"
            snapshot_root.mkdir()
            github.download_tarball(sha, tarball)
            extracted_root = extract_snapshot(tarball, snapshot_root)
            copy_snapshot(extracted_root, repo_root)

            run_git(repo_root, ["add", "-A", "-f", "."])
            tree_sha = run_git(repo_root, ["write-tree"])
            expected_tree = detail["tree"]["sha"]
            if tree_sha != expected_tree:
                raise SyncError(
                    f"Tree mismatch while reconstructing {sha}: local {tree_sha}, remote {expected_tree}"
                )

            materialized = materialize_commit(
                repo_root,
                tree_sha,
                detail,
                preferred_offsets=preferred_offsets,
            )
            preferred_offsets = [materialized.offset]
            created.add(materialized.sha)
            run_git(repo_root, ["update-ref", "HEAD", materialized.sha])
            print(f"[{index}/{len(remote_commits if start_index == 0 else pending)}] {sha[:12]} synced")

    run_git(repo_root, ["update-ref", f"refs/heads/{args.branch}", remote_head])
    run_git(repo_root, ["update-ref", f"refs/remotes/origin/{args.branch}", remote_head])
    run_git(repo_root, ["symbolic-ref", "HEAD", f"refs/heads/{args.branch}"])
    run_git(repo_root, ["reset", "--hard", remote_head])
    run_git(repo_root, ["remote", "remove", "origin"], check=False)
    run_git(repo_root, ["remote", "add", "origin", f"https://github.com/{repo}.git"])
    run_git(repo_root, ["config", f"branch.{args.branch}.remote", "origin"])
    run_git(repo_root, ["config", f"branch.{args.branch}.merge", f"refs/heads/{args.branch}"])

    print(f"Sync complete. {args.branch} -> {remote_head}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SyncError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)
