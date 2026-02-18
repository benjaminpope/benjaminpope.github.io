#!/usr/bin/env python3
"""
Insert or update a consistent contact/affiliation banner and normalize footer icons across HTML pages.

Changes:
- Adds/updates a contact banner before </body> using values from site-config.json.
- Optional flags:
    - --inject-banner: force add/update banner even if options.injectContact is false
    - --normalize-footer: replace <ul class="icons"> content with normalized social icons
    - --remove-twitter: remove anchors linking to twitter.com
- Dry-run by default; use --apply to write changes.
"""

import os
import re
import json
import argparse
from typing import Optional
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_EXTS = {".html", ".htm"}

# Fallback defaults if site-config.json is missing fields
DEFAULTS = {
    "person": {
        "name": "Benjamin J. S. Pope",
        "title": "Associate Professor of Statistical Data Science",
        "affiliation": "Macquarie University",
        "department": None,
        "email": "benjamin.pope@mq.edu.au",
    },
    "social": {
        "github": None,
        "instagram": None,
        "bluesky": "benjaminpope.bsky.social",
        "orcid": None,
    },
    "options": {
        "injectContact": False,
    },
}

BANNER_MARKER_START = "<!-- contact-banner:start -->"
BANNER_MARKER_END = "<!-- contact-banner:end -->"

# Robust marker regex to remove/replace existing banner blocks
CONTACT_BANNER_RE = re.compile(
    r"<!--\s*contact-banner:start\s*-->.*?<!--\s*contact-banner:end\s*-->",
    re.IGNORECASE | re.DOTALL,
)

UL_ICONS_RE = re.compile(
    r"(<ul[^>]*class\s*=\s*(?:\"[^\"]*\bicons\b[^\"]*\"|'[^']*\bicons\b[^']*')[^>]*>)(.*?)(</ul>)",
    re.IGNORECASE | re.DOTALL,
)

def load_config():
    """Load site-config.json from REPO_ROOT with DEFAULTS fallback."""
    cfg_path = REPO_ROOT / "site-config.json"
    config = json.loads(json.dumps(DEFAULTS))  # deep copy defaults
    if cfg_path.exists():
        try:
            loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
            # Merge loaded into defaults (shallow per section)
            for section in ("person", "social", "options"):
                if section in loaded and isinstance(loaded[section], dict):
                    config[section].update({k: v for k, v in loaded[section].items() if v is not None})
        except Exception:
            # If config is invalid, keep defaults
            pass
    return config


def bluesky_handle_and_url(value: Optional[str]):
    """Return (handle, url) tuple from a config value.

    Accepts either a handle like 'user.bsky.social' or a full URL
    like 'https://bsky.app/profile/user.bsky.social'.
    """
    if not value:
        return None, None
    val = value.strip()
    if val.startswith("http://") or val.startswith("https://"):
        # Try to extract the last path segment
        m = re.search(r"/profile/([^/?#]+)", val)
        handle = m.group(1) if m else val.rstrip("/").split("/")[-1]
        url = f"https://bsky.app/profile/{handle}"
        return handle, url
    else:
        handle = val
        url = f"https://bsky.app/profile/{handle}"
        return handle, url


def build_banner(config: dict):
    person = config.get("person", {})
    name = person.get("name") or DEFAULTS["person"]["name"]
    title = person.get("title") or DEFAULTS["person"]["title"]
    affiliation = person.get("affiliation") or DEFAULTS["person"]["affiliation"]
    department = person.get("department")
    email = person.get("email") or DEFAULTS["person"]["email"]

    social = config.get("social", {})
    bsky_handle, bsky_url = bluesky_handle_and_url(social.get("bluesky"))

    # Title line: Title, Department, Affiliation (if department present)
    if department:
        title_line = f"{title}, {department}, {affiliation}"
    else:
        title_line = f"{title}, {affiliation}"

    banner_lines = [
        f"  <div><strong>{name}</strong> — {title_line}</div>",
        f"  <div>Email: <a href=\"mailto:{email}\">{email}</a></div>",
    ]
    if bsky_url and bsky_handle:
        banner_lines.append(f"  <div>Bluesky: <a href=\"{bsky_url}\">@{bsky_handle}</a></div>")

    banner_html = (
        f"\n{BANNER_MARKER_START}\n"
        "<footer id=\"contact-banner\" style=\"margin-top:2rem;padding:1rem 0;border-top:1px solid #ddd;font-size:0.95rem;\">\n"
        + "\n".join(banner_lines)
        + "\n</footer>\n"
        f"{BANNER_MARKER_END}\n"
    )
    return banner_html


def build_footer_icons(config: dict):
    """Build normalized <li> items for a UL.icons block based on config.social.

    Uses Font Awesome v6 classes for GitHub, Bluesky, Email; optional ORCID via Academicons.
    Instagram is intentionally omitted site-wide.
    """
    person = config.get("person", {})
    email = person.get("email") or DEFAULTS["person"]["email"]
    social = config.get("social", {})

    items = []

    gh = social.get("github")
    if gh:
        items.append(
            f"  <li><a href=\"https://github.com/{gh}\" class=\"icon fa-brands fa-github\" aria-label=\"GitHub\"><span class=\"label\">GitHub</span></a></li>"
        )

    # Instagram intentionally not included

    bsky_handle, bsky_url = bluesky_handle_and_url(social.get("bluesky"))
    if bsky_url:
        items.append(
            f"  <li><a href=\"{bsky_url}\" class=\"icon fa-brands fa-bluesky\" aria-label=\"Bluesky\"><span class=\"label\">Bluesky</span></a></li>"
        )

    if email:
        items.append(
            f"  <li><a href=\"mailto:{email}\" class=\"icon fa-solid fa-envelope\" aria-label=\"Email\"><span class=\"label\">Email</span></a></li>"
        )

    orcid = social.get("orcid")
    if orcid:
        # Academicons for ORCID
        items.append(
            f"  <li><a href=\"https://orcid.org/{orcid}\" class=\"icon\" aria-label=\"ORCID\"><i class=\"ai ai-orcid\"></i><span class=\"label\">ORCID</span></a></li>"
        )

    return "\n".join(items) + ("\n" if items else "")

TWITTER_ANCHOR_RE = re.compile(r"<a[^>]+href=[\"']https?://(?:www\.)?twitter\.com/[^\"']+[\"'][^>]*>.*?</a>", re.IGNORECASE | re.DOTALL)

def process_html(path: Path, config: dict, remove_twitter: bool, inject_banner: bool, normalize_footer: bool):
    text = path.read_text(encoding="utf-8", errors="ignore")
    original = text

    # Always remove existing banner blocks first to avoid duplicates
    text = CONTACT_BANNER_RE.sub("", text)

    # Optionally remove Twitter links
    if remove_twitter:
        text = TWITTER_ANCHOR_RE.sub("", text)

    # Inject banner only if requested or config allows
    should_inject = inject_banner or bool(config.get("options", {}).get("injectContact", False))
    if should_inject:
        banner = build_banner(config)
        # Insert before </body> (case-insensitive) if present; else append
        if re.search(r"</body>", text, flags=re.IGNORECASE):
            text = re.sub(r"</body>", banner + "</body>", text, flags=re.IGNORECASE)
        else:
            text = text + banner

    # Normalize footer icons
    if normalize_footer:
        new_items = build_footer_icons(config)
        if new_items:
            def _replace_icons(match: re.Match):
                opening = match.group(1)
                closing = match.group(3)
                return opening + "\n" + new_items + closing

            text = UL_ICONS_RE.sub(_replace_icons, text)

    changed = text != original
    return text, changed


def main():
    parser = argparse.ArgumentParser(description="Update contact banner and normalize footer icons across HTML pages")
    parser.add_argument("--apply", action="store_true", help="Write changes to files (default is dry-run)")
    parser.add_argument("--remove-twitter", action="store_true", help="Remove Twitter links found in pages")
    parser.add_argument("--inject-banner", action="store_true", help="Force add/update contact banner regardless of site-config options.injectContact")
    parser.add_argument("--normalize-footer", action="store_true", help="Normalize <ul class=icons> content based on site-config social values")
    parser.add_argument("--cleanup-markers", action="store_true", help="Remove stray contact-banner markers from vendor HTMLs")
    args = parser.parse_args()

    config = load_config()

    changed_files = []
    skip_dirs = {".git", "node_modules", "_site", "scripts", "assets"}
    for root, dirs, files in os.walk(REPO_ROOT):
        # Prune traversal into skip directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        root_path = Path(root)
        # Skip injection in reveal/Quarto plugin & test paths under talks
        dirs[:] = [d for d in dirs if d not in {"plugin", "test"}]
        for f in files:
            p = root_path / f
            if p.suffix.lower() in HTML_EXTS:
                new_text, changed = process_html(
                    p,
                    config=config,
                    remove_twitter=args.remove_twitter,
                    inject_banner=args.inject_banner,
                    normalize_footer=args.normalize_footer,
                )
                if changed:
                    changed_files.append(str(p.relative_to(REPO_ROOT)))
                    if args.apply:
                        p.write_text(new_text, encoding="utf-8")

    print(f"Changed files: {len(changed_files)}")
    for cf in changed_files[:50]:
        print(f"- {cf}")
    if changed_files and not args.apply:
        print("(Dry-run) Re-run with --apply to write changes.")

    # Optional cleanup: strip stray contact-banner markers from vendor/plugin HTMLs
    # Run separately to avoid injecting into vendor paths
    if getattr(args, "cleanup_markers", False):
        vendor_roots = [
            REPO_ROOT / "assets" / "vendor" / "quarto" / "libs",
            REPO_ROOT / "assets" / "js" / "revealjs",
        ]
        cleaned = []
        for vroot in vendor_roots:
            if not vroot.exists():
                continue
            for root, dirs, files in os.walk(vroot):
                for f in files:
                    vp = Path(root) / f
                    if vp.suffix.lower() in HTML_EXTS:
                        text = vp.read_text(encoding="utf-8", errors="ignore")
                        new_text = CONTACT_BANNER_RE.sub("", text)
                        if new_text != text:
                            cleaned.append(str(vp.relative_to(REPO_ROOT)))
                            if args.apply:
                                vp.write_text(new_text, encoding="utf-8")
        print(f"Marker cleanup in vendor paths: {len(cleaned)} file(s)")
        for cf in cleaned[:50]:
            print(f"- {cf}")


if __name__ == "__main__":
    main()
