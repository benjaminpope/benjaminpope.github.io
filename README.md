 # Benjamin Pope Academic Website — Streamlining Tools
 
 These tools help consolidate images, unify slide dependencies, surface side projects, and standardize contact info in a safe new branch.
 
 ## Quick Start
 
 1. Create and switch to a new branch:
 
 ```bash
 git checkout -b site-streamline-2026
 ```
 
 2. Install dependencies:
 
 ```bash
 npm install
 ```
 
 3. Review planned changes (dry-run):
 
 ```bash
 npm run streamline:dry
 ```
 
 Reports are written under `tools/reports/`.
 
 4. Apply changes when satisfied:
 
 ```bash
 npm run streamline:apply
 ```
 
 5. Update the home page with side projects:
 
 ```bash
 npm run streamline:update-index
 ```
 
 ## Configuration
 
 Edit [site-config.json](site-config.json) for affiliation, contact, and canonical folders. Set your email before applying.
 
 ## What gets consolidated
 
 - Images moved to top-level `images/` and references updated.
- Shared `reveal.js` v4 vendor centralized under `assets/js/revealjs/` and references updated.
 - Orphan pages reported; optional insertion on `index.html` under a new "Side Projects" section.
 
 ## Safety
 
 - Dry-run writes reports but does not modify files.
 - Apply copies assets to new canonical locations and updates HTML; original files remain unless you remove them after review.
 - Review the diff before pushing or deploying.# benjaminpope.github.io
GitHub Homepage

## Maintenance Notes

- Font Awesome v6: Root pages use `fa-brands`/`fa-solid` classes via CDN. Local FA v4/v5 bundles (CSS + fonts) have been removed from `assets/css`, `assets/sass`, and all `talks/*` subfolders to reduce weight and avoid conflicts. If a deck needs icons, include the FA6 CDN in its HTML.
- Socials: Twitter links replaced with Bluesky site-wide; Academicons loaded via jsDelivr for ORCID.
- Contact banner: Managed via `site-config.json` with markers `<!-- contact-banner:start -->` and `<!-- contact-banner:end -->` retained for scripted injection.
- Quarto libs: Consolidated under `assets/vendor/quarto/libs` and referenced by Quarto-generated decks (e.g., `talks/uqai.html`).
- Audits: Use `scripts/audit_site.py` and `scripts/summarize_audit.py` to verify path updates and find orphans before deleting legacy folders.

## Streamlining Changes (2026)

- Analytics: Removed legacy Universal Analytics (`analytics.js`, `UA-40227049-3`) from all pages. No GA4/Plausible/Matomo added.
- Contact Injection Scope: Updated `scripts/update_contact.py` to skip vendor paths and talk `plugin/`/`test/` folders; added `--cleanup-markers` to strip stray markers from vendor HTMLs.
- Slides Curation: `scripts/generate_slide_index.py` filters out plugin/test/example entries; homepage “Slides” now links to `slides/index.html`.
- Demo/Template Pruning: Deleted `talks/*/plugin/` and `talks/*/test/` directories and removed local Font Awesome assets across talks.
- Orphans to Resources: Added a Legacy & Side Projects section to `resources.html` linking older pages (e.g., `tauceti.html`, `planets.html`).

## Verification

Run these checks before deployment:

```bash
# Analytics removed
grep -RIl --include='*.html' 'UA-40227049-3' .
grep -RIl --include='*.html' 'analytics.js' .

# No vendor marker contamination
grep -RIl --include='*.html' 'contact-banner:start' assets vendor talks/*/plugin talks/*/test || true

# No local FA bundles
find talks -type f \( -name 'fa-*.svg' -o -name 'fa-*.woff' -o -name 'fa-*.woff2' -o -name 'fontawesome*.css' -o -name 'font-awesome*.css' \) | wc -l

# Slides curated
python3 scripts/audit_site.py && python3 scripts/generate_slide_index.py && python3 scripts/summarize_audit.py | tail -n 40
```
