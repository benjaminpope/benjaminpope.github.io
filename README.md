This README has been archived.

See README.archive.md for the historical log and streamlining notes.
- Audits: Use `scripts/audit_site.py` and `scripts/summarize_audit.py` to verify path updates and find orphans before deleting legacy folders.

## Streamlining Changes (2026)

- Analytics: Removed legacy Universal Analytics (`analytics.js`, `UA-40227049-3`) from all pages. No GA4/Plausible/Matomo added.
- Contact Injection Scope: Updated `scripts/update_contact.py` to skip vendor paths and talk `plugin/`/`test/` folders; added `--cleanup-markers` to strip stray markers from vendor HTMLs.
- Slides Curation: `scripts/generate_slide_index.py` filters out plugin/test/example entries; homepage “Slides” now links to `talks/index.html`.
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
