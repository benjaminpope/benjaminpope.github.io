#!/usr/bin/env python3
"""
Audit the site's structure to prepare a safe migration:
- Inventory HTML pages and slide decks (Reveal.js usage)
- Find image references and where images live
- Detect affiliation/contact mentions and social links
- Identify orphan pages not linked from index.html
- Summarize reveal.js dependency versions/paths

Outputs:
- scripts/audit_report.md (human-readable summary)
- scripts/audit_report.json (structured data)

Run:
    python3 scripts/audit_site.py
"""

import os
import re
import json
from collections import defaultdict
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
HTML_EXTS = {".html", ".htm"}


RE_A_IMG_SRC = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE)
RE_A_HREF = re.compile(r"<a[^>]+href=[\"']([^\"']+)[\"']", re.IGNORECASE)
RE_REVEAL = re.compile(r"reveal(\.js|/|\\)", re.IGNORECASE)

# Very rough patterns to flag affiliation/contact mentions
AFFILIATION_PATTERNS = {
    "NYU": re.compile(r"\b(New\s*York\s*University|NYU|Center\s*for\s*Cosmology\s*and\s*Particle\s*Physics)\b", re.IGNORECASE),
    "UQ": re.compile(r"\b(University\s*of\s*Queensland|UQ|School\s*of\s*Mathematics\s*and\s*Physics)\b", re.IGNORECASE),
    "Macquarie": re.compile(r"\b(Macquarie\s*University|MQ|School\s*of\s*Mathematical\s*and\s*Physical\s*Sciences)\b", re.IGNORECASE),
    "Sagan Fellow": re.compile(r"\bSagan\s*Fellow\b", re.IGNORECASE),
}

SOCIAL_PATTERNS = {
    "Twitter": re.compile(r"twitter\.com|\B@\w+", re.IGNORECASE),
    "Bluesky": re.compile(r"bsky\.app|benjaminpope\.bsky\.social", re.IGNORECASE),
}

EMAIL_PATTERN = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+")


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def collect_files():
    html_files = []
    image_files = []
    top_level_images = []
    other_files = []

    for root, dirs, files in os.walk(REPO_ROOT):
        root_path = Path(root)
        # Skip common generated directories
        if root_path.name in {".git", "node_modules", "_site"}:
            continue
        for f in files:
            p = root_path / f
            ext = p.suffix.lower()
            if ext in HTML_EXTS:
                html_files.append(p)
            elif ext in IMG_EXTS:
                image_files.append(p)
                if p.parent == REPO_ROOT:
                    top_level_images.append(p)
            else:
                other_files.append(p)
    return html_files, image_files, top_level_images, other_files


def analyze_html(path: Path):
    text = read_text(path)
    imgs = RE_A_IMG_SRC.findall(text)
    hrefs = RE_A_HREF.findall(text)
    uses_reveal = bool(RE_REVEAL.search(text))

    affiliations = [k for k, rx in AFFILIATION_PATTERNS.items() if rx.search(text)]
    socials = [k for k, rx in SOCIAL_PATTERNS.items() if rx.search(text)]
    emails = EMAIL_PATTERN.findall(text)

    return {
        "path": str(path.relative_to(REPO_ROOT)),
        "images": imgs,
        "links": hrefs,
        "uses_reveal": uses_reveal,
        "affiliations": affiliations,
        "socials": socials,
        "emails": sorted(set(emails)),
    }


def resolve_href(base: Path, href: str) -> str:
    # Only consider local site links (html files or folders) for orphan detection
    if href.startswith("http://") or href.startswith("https://") or href.startswith("mailto:"):
        return ""
    if href.startswith("#") or href.strip() == "":
        return ""
    # Normalize by removing query/hash
    href_clean = href.split("?")[0].split("#")[0]
    try:
        resolved = (base.parent / href_clean).resolve()
        if str(resolved).startswith(str(REPO_ROOT)):
            return str(resolved.relative_to(REPO_ROOT))
    except Exception:
        pass
    return href_clean


def main():
    html_files, image_files, top_level_images, other_files = collect_files()

    analyses = []
    for p in html_files:
        analyses.append(analyze_html(p))

    # Identify index.html (top-level preferred)
    index_path = REPO_ROOT / "index.html"
    index_links = set()
    if index_path.exists():
        idx = analyze_html(index_path)
        for href in idx["links"]:
            resolved = resolve_href(index_path, href)
            if resolved:
                index_links.add(resolved)

    # Orphan pages: html files not referenced from index.html
    orphan_pages = []
    for p in html_files:
        rel = str(p.relative_to(REPO_ROOT))
        if rel == "index.html":
            continue
        # Consider both direct file and folder index
        if rel not in index_links and f"{rel}/index.html" not in index_links:
            orphan_pages.append(rel)

    # Reveal usage summary and slide decks
    slide_decks = []
    reveal_paths = defaultdict(int)
    for a in analyses:
        if a["uses_reveal"]:
            slide_decks.append(a["path"])
            # Try to capture reveal.js path hints from images/links
            for href in a["links"]:
                if "reveal" in href.lower():
                    reveal_paths[href] += 1
            # Also scan script/link tags via raw text
            # already covered indirectly; keep simple

    # Image reference targets
    image_refs = defaultdict(int)
    for a in analyses:
        for src in a["images"]:
            image_refs[src] += 1

    # Group images by location
    img_groups = defaultdict(list)
    for p in image_files:
        rel = str(p.relative_to(REPO_ROOT))
        top = rel.split("/")[0]
        img_groups[top].append(rel)

    # Affiliation/social/email occurrences per page
    affiliation_pages = defaultdict(list)
    social_pages = defaultdict(list)
    email_pages = defaultdict(list)
    for a in analyses:
        for aff in a["affiliations"]:
            affiliation_pages[aff].append(a["path"])
        for soc in a["socials"]:
            social_pages[soc].append(a["path"])
        if a["emails"]:
            email_pages[a["path"]] = a["emails"]

    # Build report structures
    report_json = {
        "summary": {
            "html_files": len(html_files),
            "image_files": len(image_files),
            "top_level_images": len(top_level_images),
            "slide_decks": len(slide_decks),
        },
        "paths": {
            "html_files": sorted(str(p.relative_to(REPO_ROOT)) for p in html_files),
            "image_files": sorted(str(p.relative_to(REPO_ROOT)) for p in image_files),
            "top_level_images": sorted(str(p.relative_to(REPO_ROOT)) for p in top_level_images),
            "slide_decks": sorted(slide_decks),
            "reveal_paths": reveal_paths,
            "image_refs": image_refs,
            "orphan_pages": sorted(orphan_pages),
        },
        "affiliations": affiliation_pages,
        "socials": social_pages,
        "emails": email_pages,
    }

    # Write JSON
    json_out = REPO_ROOT / "scripts" / "audit_report.json"
    json_out.write_text(json.dumps(report_json, indent=2), encoding="utf-8")

    # Write Markdown summary
    md_lines = []
    md_lines.append("# Site Audit Report")
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append(f"- HTML files: {report_json['summary']['html_files']}")
    md_lines.append(f"- Image files: {report_json['summary']['image_files']}")
    md_lines.append(f"- Top-level images: {report_json['summary']['top_level_images']}")
    md_lines.append(f"- Slide decks (Reveal.js detected): {report_json['summary']['slide_decks']}")
    md_lines.append("")
    md_lines.append("## Orphan Pages (not linked from index.html)")
    for rel in sorted(orphan_pages):
        md_lines.append(f"- {rel}")
    if not orphan_pages:
        md_lines.append("- None detected")
    md_lines.append("")
    md_lines.append("## Image Reference Targets (top)" )
    for src, count in sorted(image_refs.items(), key=lambda x: -x[1])[:50]:
        md_lines.append(f"- {src} ({count} refs)")
    md_lines.append("")
    md_lines.append("## Image Locations by Top-Level Folder")
    for top, items in sorted(img_groups.items(), key=lambda x: -len(x[1])):
        md_lines.append(f"- {top}: {len(items)} files")
    md_lines.append("")
    md_lines.append("## Reveal.js Paths Referenced")
    for href, count in sorted(reveal_paths.items(), key=lambda x: -x[1]):
        md_lines.append(f"- {href} ({count} pages)")
    if not reveal_paths:
        md_lines.append("- None detected explicitly")
    md_lines.append("")
    md_lines.append("## Affiliation Mentions")
    for aff, pages in affiliation_pages.items():
        md_lines.append(f"- {aff}: {len(pages)} pages")
    if not affiliation_pages:
        md_lines.append("- None detected")
    md_lines.append("")
    md_lines.append("## Social Mentions")
    for soc, pages in social_pages.items():
        md_lines.append(f"- {soc}: {len(pages)} pages")
    if not social_pages:
        md_lines.append("- None detected")
    md_lines.append("")
    md_lines.append("## Emails by Page")
    for page, emails in email_pages.items():
        md_lines.append(f"- {page}: {', '.join(emails)}")

    md_out = REPO_ROOT / "scripts" / "audit_report.md"
    md_out.write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Wrote {json_out} and {md_out}")


if __name__ == "__main__":
    main()
