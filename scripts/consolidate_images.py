#!/usr/bin/env python3
"""
Consolidate image assets under a single top-level folder `images/` with subfolders.

Moves:
- talks/images/*  -> images/slides/*
- photos/*        -> images/photos/*

Optionally, leaves existing images/* as-is for general site graphics.

Then rewrites references in HTML/CSS/JS:
- src, data-background, data-background-image
- CSS url(...)

Dry-run by default; use --apply to perform moves and rewrites.

Usage:
  python3 scripts/consolidate_images.py            # dry-run, print planned changes
  python3 scripts/consolidate_images.py --apply    # execute moves and rewrites
"""
from __future__ import annotations
import argparse
import json
import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

OLD_TO_NEW_DIRS = {
    ROOT / "talks" / "images": ROOT / "images" / "slides",
    ROOT / "photos":            ROOT / "images" / "photos",
}

FILE_GLOBS = [
    "*.html", "*.htm", "*.css", "*.scss", "*.js"
]

# Patterns to rewrite references
# Include Reveal.js-specific 'data-src' along with standard attributes
HTML_IMG_RE = re.compile(r"(src|data-src|data-background|data-background-image)=[\"']([^\"']+)[\"']", re.IGNORECASE)
CSS_URL_RE = re.compile(r"url\(([^)]+)\)", re.IGNORECASE)


def list_files(root: Path) -> list[Path]:
    files = []
    for pattern in FILE_GLOBS:
        files.extend(root.rglob(pattern))
    return files


def build_moves() -> dict[Path, Path]:
    moves: dict[Path, Path] = {}
    for old_dir, new_dir in OLD_TO_NEW_DIRS.items():
        if old_dir.exists():
            for p in old_dir.rglob("*"):
                if p.is_file():
                    rel = p.relative_to(old_dir)
                    target = new_dir / rel
                    moves[p] = target
    return moves


def ensure_dirs(paths: list[Path], dry_run: bool) -> None:
    for d in paths:
        if not d.exists():
            print(f"Create dir: {d}")
            if not dry_run:
                d.mkdir(parents=True, exist_ok=True)


def rewrite_content(text: str, file_path: Path, ref_map: dict[str, str]) -> tuple[str, int]:
    changed = 0

    def replace_path(path_str: str) -> str:
        # Strip quotes for CSS url("...") cases
        path_clean = path_str.strip().strip("'\"")
        new = ref_map.get(path_clean)
        return path_str if new is None else path_str.replace(path_clean, new)

    # HTML attributes
    def html_sub(m: re.Match) -> str:
        attr, val = m.group(1), m.group(2)
        new_val = ref_map.get(val)
        if new_val:
            nonlocal changed
            changed += 1
            return f"{attr}=\"{new_val}\""
        return m.group(0)

    out = HTML_IMG_RE.sub(html_sub, text)

    # CSS url(...)
    def css_sub(m: re.Match) -> str:
        inner = m.group(1)
        replaced = replace_path(inner)
        nonlocal changed
        if replaced != inner:
            changed += 1
            return f"url({replaced})"
        return m.group(0)

    out = CSS_URL_RE.sub(css_sub, out)

    # Additional context-aware rewrites for relative paths
    rel = file_path.relative_to(ROOT)
    # Slides under talks/* often use relative 'images/...'
    if rel.parts and rel.parts[0] == "talks":
        # Replace src/data attrs 'images/...' -> '/images/slides/...'
        out2, c2 = re.subn(r"(src|data-src|data-background|data-background-image)=[\"']images/([^\"']+)[\"']",
                           r"\1=\"/images/slides/\2\"", out, flags=re.IGNORECASE)
        out = out2
        changed += c2
        # Replace CSS url('images/...') similarly
        out2, c3 = re.subn(r"url\((['\"]?)images/([^)\"']+)(['\"]?)\)", r"url(\1/images/slides/\2\3)", out, flags=re.IGNORECASE)
        out = out2
        changed += c3
        # For nested talks (talks/*/*.html), many refs use '../images/...'
        # Rewrite '../images/...'
        # Support optional './' prefix before '../images/...'
        out2, c4a = re.subn(r"(src|data-src|data-background|data-background-image)=[\"'](?:\./)?\.\./images/([^\"']+)[\"']",
                    r"\1=\"../images/slides/\2\"", out, flags=re.IGNORECASE)
        out = out2
        changed += c4a
        out2, c4b = re.subn(r"url\((['\"]?)(?:\./)?\.\./images/([^)\"']+)(['\"]?)\)", r"url(\1../images/slides/\2\3)", out, flags=re.IGNORECASE)
        out = out2
        changed += c4b

    # Global rewrite for photos references: 'photos/...' -> '/images/photos/...'
    out2, c4 = re.subn(r"(src|data-src|data-background|data-background-image)=[\"']photos/([^\"']+)[\"']",
                       r"\1=\"/images/photos/\2\"", out, flags=re.IGNORECASE)
    out = out2
    changed += c4
    out2, c5 = re.subn(r"url\((['\"]?)photos/([^)\"']+)(['\"]?)\)", r"url(\1/images/photos/\2\3)", out, flags=re.IGNORECASE)
    out = out2
    changed += c5

    return out, changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="Apply changes (move files and rewrite references)")
    args = ap.parse_args()
    dry_run = not args.apply

    moves = build_moves()
    if not moves:
        print("No moves detected (source folders missing or empty). Proceeding with reference rewrites.")

    # Ensure target directories
    if moves:
        ensure_dirs(list({t.parent for t in moves.values()}), dry_run)

    # Build reference map: relative paths from repo root
    ref_map: dict[str, str] = {}
    for src, dst in moves.items():
        src_rel = src.relative_to(ROOT).as_posix()
        dst_rel = dst.relative_to(ROOT).as_posix()
        ref_map[src_rel] = dst_rel

    if moves:
        print("Planned file moves:")
        for src, dst in moves.items():
            print(f"  {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")

    # Move/copy files
    if not dry_run and moves:
        for src, dst in moves.items():
            dst.parent.mkdir(parents=True, exist_ok=True)
            print(f"Move {src} -> {dst}")
            shutil.move(str(src), str(dst))

    # Rewrite references in repository files
    files = list_files(ROOT)
    total_changes = 0
    changed_files = []
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")
        except Exception:
            continue
        new_text, changes = rewrite_content(text, f, ref_map)
        if changes > 0:
            print(f"Rewrite {f.relative_to(ROOT)}: {changes} references")
            total_changes += changes
            changed_files.append(f)
            if not dry_run:
                f.write_text(new_text, encoding="utf-8")

    print(f"Total reference updates: {total_changes} in {len(changed_files)} files.")
    print("Done.")


if __name__ == "__main__":
    main()
