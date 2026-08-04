#!/usr/bin/env python3
"""
Generate the QR codes used on the site.

Two outputs:
  1. assets/qr/<key>.png      — high-resolution, for posters, slides and business cards
  2. scripts/qr_snippets.json — inline SVG paths that get injected into index.html

Run it after you change any link in LINKS below:

    pip install "qrcode[pil]" pillow
    python scripts/make_qr.py
    python scripts/build.py          # re-injects the SVGs into index.html
"""

import json
import os
import qrcode
from qrcode.constants import ERROR_CORRECT_M

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- links
# key -> (label shown under the code, url)
LINKS = {
    "website":    ("Website",            "https://enamul-hoq.github.io/myWebsite/"),
    "scholar":    ("Google Scholar",     "https://scholar.google.com/citations?user=mP_LvPoAAAAJ&hl=en"),
    "linkedin":   ("LinkedIn",           "https://www.linkedin.com/in/mhoq89/"),
    "github":     ("GitHub",             "https://github.com/Enamul-Hoq"),
    "email":      ("Email",              "mailto:mdenamulmte@gmail.com"),
    "jiim2025":   ("RAD-DINO · JIIM", "https://doi.org/10.1007/s10278-025-01748-4"),
    "virtualeyes":("Virtual-Eyes", "https://arxiv.org/abs/2512.24294"),
    "review2026": ("LDCT review",   "https://doi.org/10.20944/preprints202606.1208.v1"),
    "rgg2026":    ("RGG · Ital-IA",  "https://arxiv.org/abs/2605.00893"),
    "neurips2025":("NeurIPS 2025", "https://openreview.net/forum?id=yNVDkAjGjw"),
    "cmu2026":    ("CMU × NVIDIA story", "https://www.library.cmu.edu/about/news/2026-02/NVIDIA-hackathon"),
}


def matrix(url: str):
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(url)
    qr.make(fit=True)
    return qr


def svg_path(mods):
    """Collapse each row of dark modules into horizontal runs -> compact SVG path."""
    n = len(mods)
    parts = []
    for y, row in enumerate(mods):
        x = 0
        while x < n:
            if row[x]:
                start = x
                while x < n and row[x]:
                    x += 1
                parts.append(f"M{start} {y}h{x - start}v1h-{x - start}z")
            else:
                x += 1
    return "".join(parts), n


def main():
    out_dir = os.path.join(ROOT, "assets", "qr")
    os.makedirs(out_dir, exist_ok=True)
    snippets = {}

    for key, (label, url) in LINKS.items():
        qr = matrix(url)
        img = qr.make_image(fill_color="#0A0E13", back_color="white")
        img.save(os.path.join(out_dir, f"{key}.png"))

        d, n = svg_path(qr.get_matrix())
        snippets[key] = {"label": label, "url": url, "size": n, "path": d}
        print(f"{key:12s} {n}x{n} modules  ->  assets/qr/{key}.png")

    with open(os.path.join(HERE, "qr_snippets.json"), "w") as f:
        json.dump(snippets, f, indent=1)
    print(f"\nwrote {len(snippets)} snippets to scripts/qr_snippets.json")


if __name__ == "__main__":
    main()
