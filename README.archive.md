# ARCHIVED: Streamlining Tools and Change Log (2023–2026)

This file was previously used to track the streamlining and modernization of the benjaminpope.github.io site, including tool usage, migration plans, and maintenance notes. It is now archived for historical reference.

## Quick Start (Historical)

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

Edit `site-config.json` for affiliation, contact, and canonical folders. Set your email before applying.

## What Was Consolidated

- Images moved to top-level `images/` and references updated.
- Shared `reveal.js` v4 vendor centralized under `assets/js/revealjs/` and references updated.
- Orphan pages reported; optional insertion on `index.html` under a new "Side Projects" section.

## Safety

- Dry-run writes reports but does not modify files.
- Apply copies assets to new canonical locations and updates HTML; original files remain unless you remove them after review.
- Review the diff before pushing or deploying.

## Maintenance Notes (Historical)

- Font Awesome v6: Root pages use `fa-brands`/`fa-solid` classes via CDN. Local FA v4/v5 bundles (CSS + fonts) have been removed from `assets/css`, `assets/sass`, and all `talks/*` subfolders to reduce weight and avoid conflicts. If a deck needs icons, include the FA6 CDN in its HTML.
- Socials: Twitter links replaced with Bluesky site-wide; Academicons loaded via jsDelivr for ORCID.
- Contact banner: Managed via `site-config.json` with markers `<!-- contact-banner:start -->` and `<!-- contact-banner:end -->` retained for scripted injection.
- Quarto libs: Consolidated under `assets/vendor/quarto/libs` and referenced by Quarto-generated decks (e.g., `talks/uqai.html`).

---

This file is no longer updated. See `README.txt` or project documentation for current usage and maintenance instructions.
