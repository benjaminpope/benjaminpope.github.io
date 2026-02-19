# Restructuring Plan (Work-in-Progress)

This branch will streamline site structure while preserving the current production behavior.

## Goals
- Ensure affiliation and contact details are consistent across all pages.
- Consolidate images into a single top-level folder and fix references.
- Consolidate slide files into a clear structure; centralize Reveal.js dependencies to common folders.
- Link side projects (e.g. `rps.html`) from the home page where appropriate.
- Update JS/font dependencies where necessary.
- (Lower priority) Create shared boilerplate via templates/includes to ease future updates.

## Branch Workflow

```bash
# Create and switch to the restructuring branch
git checkout -b restructure/site-streamlining

# Run audit to gather the current state
python3 scripts/audit_site.py

# Review report
open scripts/audit_report.md

# Commit audit artifacts
git add scripts/audit_report.*
git commit -m "Audit site structure before restructuring"
```

## Proposed Target Structure

- `images/` — single consolidated folder for all images (including previous `talks/images`, `photos`, and any root-level image files).
- `slides/` — unified slide decks directory:
	- `slides/decks/` — individual deck HTMLs.
	- `slides/assets/` — shared images used only by slides.
	- `slides/reveal/` — common Reveal.js distribution (single version if compatible; otherwise versioned subfolders like `reveal-v4/`, `reveal-v3/`).
- `_includes/` and `_layouts/` — optional Jekyll includes/layouts to centralize boilerplate (header/footer/contact/social). Only introduced after other tasks.

## Migration Steps (High-Level)
1. Inventory and confirm slide deck locations and Reveal.js versions (from the audit report).
2. Decide on Reveal.js baseline (prefer a single modern version if slides remain compatible; otherwise keep multiple versioned folders).
3. Move images into `images/` (preserving relative subpaths where helpful); update `<img src>` references across all HTML files.
4. Move slide decks into `slides/decks/`; update internal links and Reveal.js asset paths to the chosen common folders.
5. Update home page to link side projects (e.g., `rps.html`) and slide index.
6. Standardize affiliation/contact details, replacing inconsistent instances.
7. (Optional, later) Introduce Jekyll includes/layouts and a small `_data/site.yml` for contact/affiliation fields.

## Rollback Plan
- All changes occur in `restructure/site-streamlining` branch.
- Keep commits small and task-oriented so we can revert specific changes.
- Avoid altering production branch until reviewed.

## Notes
- The audit intentionally does not make changes; it produces a `scripts/audit_report.md/json` to guide safe edits.
- For image moves and path rewrites, a helper script can be added to minimize mechanical errors.
- For slides, test locally by opening `slides/decks/<deck>.html` after migration to verify Reveal initializes correctly.