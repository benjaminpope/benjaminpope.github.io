#!/usr/bin/env python3
"""
Automated link and asset path fixes across HTML files:
- Add https:// scheme to bare domains (benjaminpope.github.io, nexcsci.caltech.edu, github.com, tinyurl.com, nature.com)
- Replace sciencedirect placeholder with homepage URL
- Switch Reveal theme 'black.css' to existing 'quarto.css'
- Normalize Pleiades background paths to deck-relative images folder
- Fix qrcode image paths to deck-local files
- Correct specific missing images (exoplanets UQ image -> uq.png)
- Fix MCMC lecture image paths (both deck and top-level page)
- Update Quarto CSS reference in uqai.html
- Fix talks.html missing .html for MAD link
- Fix http// typos in rps.html
- Specific: replace missing atca.jpg with vlbi.jpg in greenwich/apep.html

Run:
    python3 scripts/fix_links.py
"""
import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

def iter_html_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        pdir = Path(dirpath)
        if pdir.name in {".git", "node_modules", "_site"}:
            continue
        for f in filenames:
            if f.lower().endswith((".html", ".htm")):
                yield pdir / f

# Patterns and replacements
REPLACEMENTS = [
    (re.compile(r"href=\"benjaminpope\.github\.io"), 'href="https://benjaminpope.github.io'),
    (re.compile(r"href=\"nexsci\.caltech\.edu"), 'href="https://nexsci.caltech.edu'),
    (re.compile(r"href=\"github\.com"), 'href="https://github.com'),
    (re.compile(r"href=\"tinyurl\.com"), 'href="https://tinyurl.com'),
    (re.compile(r"href=\"nature\.com/"), 'href="https://www.nature.com/'),
    (re.compile(r"href=\"sciencedirect\""), 'href="https://www.sciencedirect.com/"'),
    (re.compile(r"(/assets/js/revealjs/dist/theme/)black\.css"), r"\1quarto.css"),
    (re.compile(r"data-background(?:-image)?=\"\./pleiades\.jpg\""), 'data-background-image="../images/slides/pleiades.jpg"'),
    (re.compile(r"/images/slides/uq\.jpg"), '/images/slides/uq.png'),
]

# qrcode: change '../../images/slides/qrcode_*.png' to local 'qrcode_*.png'
RE_QRCODE = re.compile(r"src=\"\.\.\/\.\.\/images\/slides\/(qrcode_[A-Za-z0-9_.-]+)\"")

# mcmc lecture (deck version): '../../images/slides/<name>' -> '<name>'
MCMC_NAMES = ["hubble.png", "mr2t2.png", "rosenbluth.jpeg", "rosenbluth_headline.png", "ulam.png"]
RE_MCMC_DECK = re.compile(r"src=\"\.\.\/\.\.\/images\/slides\/(" + "|".join(map(re.escape, MCMC_NAMES)) + r")\"")
# mcmc lecture (top-level talks page): '../images/slides/<name>' -> 'mcmc/<name>'
RE_MCMC_TOP = re.compile(r"src=\"\.\.\/images\/slides\/(" + "|".join(map(re.escape, MCMC_NAMES)) + r")\"")

# uqai.css fix
RE_UQAI_CSS = re.compile(r"quarto-syntax-highlighting-dark\.css")

# talks.html MAD link fix
RE_TALKS_MAD = re.compile(r"href=\"\./talks/mad/mad\"")

# rps.html http// -> https://
RE_RPS_HTTP_TYPO = re.compile(r"href=\"http//")

# greenwich/apep atca fix
RE_ATCA = re.compile(r"src=\"\.\.\/\.\.\/images\/slides\/atca\.jpg\"")


def process_file(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="ignore")
    orig = text

    # General replacements
    for rx, rep in REPLACEMENTS:
        text = rx.sub(rep, text)

    # qrcode -> local
    text = RE_QRCODE.sub(lambda m: f'src="{m.group(1)}"', text)

    # MCMC deck localize
    if path.name == "mcmc_lecture.html" and path.parent.name == "mcmc":
        text = RE_MCMC_DECK.sub(lambda m: f'src="{m.group(1)}"', text)

    # MCMC top-level talks page
    if path.name == "mcmc_lecture.html" and path.parent.name == "talks":
        text = RE_MCMC_TOP.sub(lambda m: f'src="mcmc/{m.group(1)}"', text)

    # uqai.css
    if path.name == "uqai.html" and path.parent.name == "talks":
        text = RE_UQAI_CSS.sub("quarto-syntax-highlighting.css", text)
        # normalize local './images/<name>' to repo images/slides
        text = re.sub(r"data-background-image=\"\./images/([^\"]+)\"", r"data-background-image=\"../images/slides/\1\"", text)
        text = re.sub(r"src=\"\./images/([^\"]+)\"", r"src=\"../images/slides/\1\"", text)
        text = re.sub(r"data-src=\"\./images/([^\"]+)\"", r"data-src=\"../images/slides/\1\"", text)

    # talks.html MAD link
    if path.name == "talks.html" and path.parent == REPO_ROOT:
        text = RE_TALKS_MAD.sub('href="./talks/mad/mad.html"', text)

    # rps.html http typo
    if path.name == "rps.html" and path.parent == REPO_ROOT:
        text = RE_RPS_HTTP_TYPO.sub('href="https://', text)

    # greenwich/apep atca fix
    if path.name == "apep.html" and path.parent.name == "greenwich":
        text = RE_ATCA.sub('src="../../images/slides/vlbi.jpg"', text)

    if text != orig:
        path.write_text(text, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    for html in iter_html_files(REPO_ROOT):
        if process_file(html):
            changed += 1
    print(f"Updated {changed} files with link fixes.")


if __name__ == "__main__":
    main()
