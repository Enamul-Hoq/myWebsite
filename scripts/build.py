#!/usr/bin/env python3
"""
Assemble index.html from src/index.template.html.

It injects three things the browser should never have to wait for:
  • the portrait, inlined as a data URI (one less request, never a broken image)
  • the QR codes, inlined as SVG paths from scripts/qr_snippets.json
  • a copy of data/publications.json, used only if the live fetch fails

Run after editing the template, the photo, or any link in scripts/make_qr.py:

    python scripts/make_qr.py     # only if links changed
    python scripts/build.py
"""

import base64
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TEMPLATE = os.path.join(ROOT, "src", "index.template.html")
OUT = os.path.join(ROOT, "index.html")
PHOTO = os.path.join(ROOT, "src", "photo.b64.txt")
QRS = os.path.join(HERE, "qr_snippets.json")
PUBS = os.path.join(ROOT, "data", "publications.json")

# which codes appear on the wall in the Connect section, in order
WALL = ["website", "scholar", "linkedin", "github", "email",
        "jiim2025", "virtualeyes", "rgg2026", "neurips2025", "review2026"]

# the eight photographs, and the two diagrams shown under Selected systems
FEATURED = ["midl-taipei", "mayo-summit", "cancer-retreat"]   # large tiles, own row on top
GALLERY = ["edrn-poster", "datathon-team", "judging", "hackathon",
           "aptec", "poster-session", "caltech", "lab-visit"]
FIGURES = ["pipeline", "model"]


def qr_svg(q, cls=""):
    n = q["size"]
    return (
        f'<div class="qr{cls}"><svg viewBox="-2 -2 {n+4} {n+4}" shape-rendering="crispEdges" '
        f'role="img" aria-label="QR code for {q["label"]}">'
        f'<rect x="-2" y="-2" width="{n+4}" height="{n+4}" fill="#fff"/>'
        f'<path d="{q["path"]}" fill="#0A0E13"/></svg></div>'
    )


def main():
    html = open(TEMPLATE, encoding="utf-8").read()
    qrs = json.load(open(QRS, encoding="utf-8"))
    pubs = json.load(open(PUBS, encoding="utf-8"))
    b64 = open(PHOTO, encoding="utf-8").read().strip()
    gal = json.load(open(os.path.join(ROOT, "src", "gallery.json"), encoding="utf-8"))

    wall = "\n        ".join(
        f'<a class="qr-card" href="{qrs[k]["url"]}" rel="noopener">'
        f'{qr_svg(qrs[k])}<span>{qrs[k]["label"]}</span></a>'
        for k in WALL if k in qrs
    )

    def tile(k):
        return (f'<figure><a href="{gal[k]["file"]}" rel="noopener">'
                f'<img src="data:image/jpeg;base64,{gal[k]["b64"]}" alt="{gal[k]["alt"]}" loading="lazy">'
                f'</a><figcaption>{gal[k]["cap"]}</figcaption></figure>')

    featured = "\n      ".join(tile(k) for k in FEATURED if k in gal)
    gallery = "\n      ".join(tile(k) for k in GALLERY if k in gal)
    figures = "\n      ".join(
        f'<figure class="figure"><img src="data:image/jpeg;base64,{gal[k]["b64"]}" '
        f'alt="{gal[k]["alt"]}" loading="lazy"><figcaption>{gal[k]["cap"]}</figcaption></figure>'
        for k in FIGURES if k in gal
    )

    html = html.replace("{{FEATURED}}", featured)
    html = html.replace("{{GALLERY}}", gallery)
    html = html.replace("{{FIGURES}}", figures)
    html = html.replace("{{QR_CMU}}", qr_svg(qrs["cmu2026"]) if "cmu2026" in qrs else "")
    html = html.replace("{{PHOTO}}", "data:image/jpeg;base64," + b64)
    html = html.replace("{{QR_WALL}}", wall)
    html = html.replace("{{QR_DATA}}", json.dumps(qrs, ensure_ascii=False, separators=(",", ":")))
    html = html.replace("{{PUBS}}", json.dumps(pubs, ensure_ascii=False, separators=(",", ":")))

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)

    left = [t for t in ("{{PHOTO}}", "{{QR_WALL}}", "{{QR_DATA}}", "{{PUBS}}",
                        "{{GALLERY}}", "{{FEATURED}}", "{{FIGURES}}", "{{QR_CMU}}") if t in html]
    print(f"index.html written — {len(html)/1024:.0f} KB, {len(pubs['publications'])} publications, {len(WALL)} QR codes")
    if left:
        print("WARNING: unresolved placeholders:", left)


if __name__ == "__main__":
    main()
