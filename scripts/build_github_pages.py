#!/usr/bin/env python3
"""
Build a clean GitHub Pages artifact for Tianyan.

This avoids publishing backend code, tests, or local-only assets by copying only
the static site files needed for the Pages experience.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / ".site"
COPY_TARGETS = [
    ".nojekyll",
    "index.html",
    "favicon.svg",
    "assets",
    "campaigns",
    "cases",
    "content",
    "dashboard",
    "data",
    "docs/index.html",
    "docs/robots.txt",
    "docs/investor_deck.md",
    "docs/mckinsey_methodology.md",
    "docs/methodology.md",
    "docs/business_plan.md",
    "docs/algorithm_filing.md",
    "docs/realistic_strategy.md",
    "docs/strategic_blueprint.md",
    "docs/growth_launch_playbook.md",
    "docs/xiaohongshu_content_pack.md",
    "docs/xiaohongshu_cover_pack.md",
    "docs/douyin_content_pack.md",
    "docs/douyin_shotlist.md",
    "docs/douyin_livestream_outline.md",
    "docs/digital_human_content_pack.md",
    "docs/digital_human_production_sheet.md",
    "docs/deepseek_backend_contract.md",
    "docs/wechat_miniprogram_start.md",
    "library",
    "skills",
    "虚拟细胞",
]


def copy_target(relative_path: str, output_dir: Path) -> None:
    source = ROOT / relative_path
    if not source.exists():
        return

    destination = output_dir / relative_path
    destination.parent.mkdir(parents=True, exist_ok=True)

    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
        return

    shutil.copy2(source, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build GitHub Pages artifact.")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output directory")
    args = parser.parse_args()

    output_dir = Path(args.output).resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for target in COPY_TARGETS:
        copy_target(target, output_dir)

    # Ensure Pages serves plain files without Jekyll processing.
    (output_dir / ".nojekyll").touch()

    print(f"Built GitHub Pages site at {output_dir}")


if __name__ == "__main__":
    main()
