#!/usr/bin/env python3
"""
Summarize scripts/audit_report.json into a concise, readable output.

Prints:
- Totals (HTML, images, slide decks)
- Top image locations and stray top-level images
- Reveal.js paths and counts
- Orphan pages (first 50)
- Affiliation and social mentions overview
- Pages with emails
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def main():
    audit_json = REPO_ROOT / "scripts" / "audit_report.json"
    if not audit_json.exists():
        print("No audit report found. Run scripts/audit_site.py first.")
        return 1

    data = json.loads(audit_json.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    paths = data.get("paths", {})
    affiliations = data.get("affiliations", {})
    socials = data.get("socials", {})
    emails = data.get("emails", {})

    print("== Totals ==")
    print(f"HTML files: {summary.get('html_files', 0)}")
    print(f"Image files: {summary.get('image_files', 0)}")
    print(f"Slide decks (Reveal.js): {summary.get('slide_decks', 0)}\n")

    # Image locations
    image_files = paths.get("image_files", [])
    top_level_images = paths.get("top_level_images", [])
    print("== Image Locations ==")
    top_counts = {}
    for rel in image_files:
        top = rel.split('/')[0]
        top_counts[top] = top_counts.get(top, 0) + 1
    for top, cnt in sorted(top_counts.items(), key=lambda x: -x[1])[:10]:
        print(f"{top}: {cnt}")
    if top_level_images:
        print("\nTop-level stray images:")
        for img in top_level_images[:20]:
            print(f"- {img}")
    print()

    # Reveal paths
    rev = paths.get("reveal_paths", {})
    print("== Reveal.js Paths ==")
    if rev:
        for href, count in sorted(rev.items(), key=lambda x: -x[1])[:20]:
            print(f"{href}: {count} page(s)")
    else:
        print("None detected explicitly")
    print()

    # Orphan pages
    orphan = paths.get("orphan_pages", [])
    print("== Orphan Pages (not linked from index.html) ==")
    if orphan:
        for rel in orphan[:50]:
            print(f"- {rel}")
    else:
        print("None detected")
    print()

    # Affiliation mentions
    print("== Affiliation Mentions ==")
    if affiliations:
        for aff, pages in sorted(affiliations.items(), key=lambda x: -len(x[1])):
            print(f"{aff}: {len(pages)} page(s)")
    else:
        print("None detected")
    print()

    # Social mentions
    print("== Social Mentions ==")
    if socials:
        for soc, pages in sorted(socials.items(), key=lambda x: -len(x[1])):
            print(f"{soc}: {len(pages)} page(s)")
    else:
        print("None detected")
    print()

    # Emails by page
    print("== Pages with Emails ==")
    if emails:
        for page, ems in list(emails.items())[:50]:
            print(f"- {page}: {', '.join(ems)}")
    else:
        print("None detected")
    print()

    # Side projects heuristic (orphan pages minus slide decks)
    decks = set(paths.get("slide_decks", []))
    side_projects = [p for p in orphan if p not in decks and p.endswith('.html')]
    if side_projects:
        print("== Potential Side Projects ==")
        for p in side_projects[:50]:
            print(f"- {p}")
        print()

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
