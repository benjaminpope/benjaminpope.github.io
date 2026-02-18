#!/usr/bin/env python3
"""
Generate slides/index.html based on scripts/audit_report.json.

It lists all detected slide decks (Reveal.js usage) with links.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def main():
    audit_json = REPO_ROOT / "scripts" / "audit_report.json"
    if not audit_json.exists():
        print("Run scripts/audit_site.py first to create audit_report.json")
        return 1

    data = json.loads(audit_json.read_text(encoding="utf-8"))
    decks = data.get("paths", {}).get("slide_decks", [])
    # Curate: include only real talks/decks, exclude plugin/test/vendor examples
    curated = []
    for d in decks:
        if any(seg in d for seg in ["/plugin/", "/test/"]):
            continue
        if d.startswith("assets/"):
            continue
        # Prefer talks/ and slides/ roots
        if d.startswith("talks/") or d.startswith("slides/"):
            curated.append(d)
        else:
            # fallback: include top-level or other decks not in vendor
            curated.append(d)
    decks = sorted(curated)

    out_dir = REPO_ROOT / "slides"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_html = out_dir / "index.html"

    lines = []
    lines.append("<!doctype html>")
    lines.append("<html lang=\"en\">")
    lines.append("<head>")
    lines.append("  <meta charset=\"utf-8\">")
    lines.append("  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    lines.append("  <title>Slide Decks</title>")
    lines.append("  <style>body{font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:2rem;max-width:900px;margin:auto;} h1{margin-bottom:1rem;} ul{line-height:1.6;} .meta{margin-top:2rem;color:#555;font-size:.95rem}</style>")
    lines.append("</head>")
    lines.append("<body>")
    lines.append("  <h1>Slide Decks</h1>")
    if decks:
        lines.append("  <ul>")
        for d in decks:
            lines.append(f"    <li><a href=\"../{d}\">{d}</a></li>")
        lines.append("  </ul>")
    else:
        lines.append("  <p>No slide decks detected by audit.</p>")
    lines.append("  <div class=\"meta\">Generated from scripts/audit_report.json</div>")
    lines.append("</body>")
    lines.append("</html>")

    out_html.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {out_html}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
