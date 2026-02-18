#!/usr/bin/env python3
"""
Broad local link checker for the repository.
- Scans all HTML files for local href/src-like attributes
- Resolves relative paths against each file location
- Verifies targets exist on disk (skips http/https/mailto)
- Reports missing links per file and a summary count

Run:
    python3 scripts/check_links.py
"""
import os
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(__file__).resolve().parents[1]

HTML_ATTR_PATTERNS = [
    # Common attributes
    re.compile(r"href=\"([^\"]+)\"", re.IGNORECASE),
    re.compile(r"src=\"([^\"]+)\"", re.IGNORECASE),
    # Reveal/Quarto specific
    re.compile(r"data-src=\"([^\"]+)\"", re.IGNORECASE),
    re.compile(r"data-background=\"([^\"]+)\"", re.IGNORECASE),
    re.compile(r"data-background-image=\"([^\"]+)\"", re.IGNORECASE),
]

SKIP_PREFIXES = ("http://", "https://", "mailto:", "tel:", "data:")

# File extensions we consider worth checking for local existence
CHECKABLE_EXTS = {
    ".html", ".htm", ".css", ".js", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp",
    ".mp4", ".webm", ".mp3", ".ogg", ".pdf", ".woff", ".woff2", ".ttf", ".otf"
}


def iter_html_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        pdir = Path(dirpath)
        # Skip common generated dirs
        if pdir.name in {".git", "node_modules", "_site"}:
            continue
        for f in filenames:
            if f.lower().endswith((".html", ".htm")):
                yield pdir / f


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def normalize(href: str) -> str:
    # Strip query and fragment
    href = href.strip()
    href = href.split("#")[0].split("?")[0]
    return href


def is_checkable(href: str) -> bool:
    if not href or href.startswith(SKIP_PREFIXES):
        return False
    # Skip anchors and JS pseudo-links
    if href.startswith("#") or href.lower().startswith("javascript:"):
        return False
    # Only check known resource types if an extension is present
    ext = Path(href).suffix.lower()
    if ext and ext not in CHECKABLE_EXTS:
        return False
    return True


def resolve(base_file: Path, href: str) -> Path:
    # Absolute path from site root
    if href.startswith("/"):
        return (REPO_ROOT / href.lstrip("/"))
    # Relative to the file
    return (base_file.parent / href)


def main():
    missing_by_file = defaultdict(list)
    total_checked = 0
    for html in iter_html_files(REPO_ROOT):
        text = read_text(html)
        # Strip HTML comments to avoid false positives (e.g., legacy IE shims, commented assets)
        text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        links = []
        for rx in HTML_ATTR_PATTERNS:
            links.extend(rx.findall(text))
        for raw in links:
            href = normalize(raw)
            if not is_checkable(href):
                continue
            target = resolve(html, href)
            total_checked += 1
            if not target.exists():
                missing_by_file[str(html.relative_to(REPO_ROOT))].append(href)

    # Report
    if missing_by_file:
        print("== Missing Local Links ==")
        for f, hrefs in sorted(missing_by_file.items()):
            print(f"- {f}")
            for h in sorted(set(hrefs)):
                print(f"  * {h}")
        print("")
        print(f"Checked {total_checked} local links; missing in {len(missing_by_file)} files.")
        # Non-zero exit for CI friendliness
        raise SystemExit(1)
    else:
        print(f"All local links resolve. Checked {total_checked} links across repo.")


if __name__ == "__main__":
    main()
