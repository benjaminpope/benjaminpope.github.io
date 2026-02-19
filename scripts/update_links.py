#!/usr/bin/env python3
"""
Rewrite asset paths in HTML files across the repo.

Use cases:
- After consolidating images into `images/`, update `<img src>` references.
- After moving slide decks and centralizing Reveal.js, update paths to `slides/reveal/`.

Dry-run by default; use `--apply` to write changes.

Examples:
    python3 scripts/update_links.py --from talks/images --to images
    python3 scripts/update_links.py --from photos --to images/photos
    python3 scripts/update_links.py --from sagan_slides/reveal.js --to slides/reveal

Multiple mappings can be provided.
"""

import os
import re
import argparse
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

HTML_EXTS = {".html", ".htm"}

IMG_SRC_RE = re.compile(r"(<img[^>]+src=[\"'])([^\"']+)([\"'])", re.IGNORECASE)
LINK_HREF_RE = re.compile(r"(<a[^>]+href=[\"'])([^\"']+)([\"'])", re.IGNORECASE)
SCRIPT_SRC_RE = re.compile(r"(<script[^>]+src=[\"'])([^\"']+)([\"'])", re.IGNORECASE)
LINK_TAG_RE = re.compile(r"(<link[^>]+href=[\"'])([^\"']+)([\"'])", re.IGNORECASE)


def build_mappings(pairs):
    mappings = []
    for src, dst in pairs:
        # Normalize with trailing slash to avoid partial matches
        s = src if src.endswith("/") else src + "/"
        d = dst if dst.endswith("/") else dst + "/"
        mappings.append((s, d))
    # Sort by descending length so deeper paths replace before shallow
    mappings.sort(key=lambda x: -len(x[0]))
    return mappings


def rewrite_url(url: str, mappings):
    for src, dst in mappings:
        if url.startswith(src) or ("/" + url).startswith("/" + src):
            return url.replace(src, dst, 1)
    return url


def process_file(path: Path, mappings, apply=False):
    text = path.read_text(encoding="utf-8", errors="ignore")
    original = text

    def sub_fn(regex):
        def repl(m):
            pre, url, post = m.groups()
            new_url = rewrite_url(url, mappings)
            return pre + new_url + post
        return regex.sub(repl, text)

    text = IMG_SRC_RE.sub(lambda m: m.group(1) + rewrite_url(m.group(2), mappings) + m.group(3), text)
    text = LINK_HREF_RE.sub(lambda m: m.group(1) + rewrite_url(m.group(2), mappings) + m.group(3), text)
    text = SCRIPT_SRC_RE.sub(lambda m: m.group(1) + rewrite_url(m.group(2), mappings) + m.group(3), text)
    text = LINK_TAG_RE.sub(lambda m: m.group(1) + rewrite_url(m.group(2), mappings) + m.group(3), text)

    changed = text != original
    if changed and apply:
        path.write_text(text, encoding="utf-8")
    return changed


def main():
    parser = argparse.ArgumentParser(description="Rewrite asset URLs in HTML files")
    parser.add_argument("--from", dest="from_paths", action="append", default=[], help="Source base path to rewrite (can be given multiple times)")
    parser.add_argument("--to", dest="to_paths", action="append", default=[], help="Destination base path (can be given multiple times)")
    parser.add_argument("--apply", action="store_true", help="Write changes to files (default is dry-run)")
    args = parser.parse_args()

    if len(args.from_paths) != len(args.to_paths) or not args.from_paths:
        print("Provide matching --from and --to pairs.")
        return 1

    mappings = build_mappings(list(zip(args.from_paths, args.to_paths)))

    changed_files = []
    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)
        if root_path.name in {".git", "node_modules", "_site", "scripts"}:
            continue
        for f in files:
            p = root_path / f
            if p.suffix.lower() in HTML_EXTS:
                if process_file(p, mappings, apply=args.apply):
                    changed_files.append(str(p.relative_to(REPO_ROOT)))

    print(f"Mappings: {mappings}")
    print(f"Changed files: {len(changed_files)}")
    for cf in changed_files[:50]:
        print(f"- {cf}")
    if changed_files and not args.apply:
        print("(Dry-run) Re-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
