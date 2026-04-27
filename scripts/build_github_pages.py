#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".site"

COPY_TARGETS = [
    "index.html",
    "favicon.svg",
    "assets",
    "library",
    "content",
    "docs",
    "skills",
    "cases/medislim",
    "tianyan/report_generator.py",
    "虚拟细胞/docs",
]


def copy_path(source: Path, destination: Path) -> None:
    if source.is_dir():
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns(".git", ".DS_Store", "__pycache__", "*.pyc"),
        )
        return

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def build(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    for relative in COPY_TARGETS:
        source = ROOT / relative
        if not source.exists():
            raise FileNotFoundError(f"Missing GitHub Pages asset: {relative}")

        destination = output_dir / relative
        copy_path(source, destination)

    (output_dir / ".nojekyll").write_text("", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Tianyan GitHub Pages artifact.")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output directory for the static site artifact.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output).resolve()
    build(output_dir)
    print(output_dir)


if __name__ == "__main__":
    main()
