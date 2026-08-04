# enamul-hoq.github.io — personal site

A single-page academic site with a publication list that updates itself.

**Design note:** the whole page is styled like a radiology reading room. The corner
text in the hero is a DICOM viewport annotation, and the light/dark control in the
top right is labelled the way a radiologist would label it — **Lung** (WL −600 /
WW 1500) and **Soft tissue** (WL 40 / WW 400). Cyan is CT, pink is H&E, violet is
modelling, amber is recognition. That colour logic runs through every button, chip
and section marker on the page.

---

## 1. Publish it

Every photograph is now **inside `index.html`** as data, so nothing depends on your
old image files and no picture can break. Optimised full-size copies also ship in
`assets/img/gallery/` (your originals were 2–4 MB each; these are 130–450 KB).

### If you keep the same address

`https://enamul-hoq.github.io/myWebsite/` — unzip into your local clone of the
`myWebsite` repo, replacing what is there, then:

```bash
git add -A
git commit -m "Rebuild site"
git push
```

Confirm **repo → Settings → Pages → Source: Deploy from a branch → `main` / `(root)`**.
Live in about a minute.

### If you want a cleaner address

`https://enamul-hoq.github.io/` — with no `/myWebsite` on the end. Create a new
public repository named exactly **`enamul-hoq.github.io`**, push these files to it,
and set Pages to `main / (root)` the same way. GitHub treats a repo named after your
username as your root site. Keep the old repo as it is; both can run at once.

If you take this route, change the `canonical`, `og:image` and `website` QR links to
the new address, then run `python scripts/make_qr.py && python scripts/build.py`.

### Your own domain, later

Buy a domain, add a `CNAME` file containing just the domain name, and point a CNAME
DNS record at `enamul-hoq.github.io`. Settings → Pages → Custom domain.

Opening `index.html` by double-clicking works too — everything except the live
publication feed is baked into the file.

---

## 2. The publication list updates itself

`.github/workflows/update-publications.yml` runs every Monday at 06:00 UTC. It calls
`scripts/update_publications.py`, which asks OpenAlex for everything published under
your name, adds anything new to `data/publications.json`, refreshes citation counts,
and commits. GitHub Pages redeploys on that commit. You do nothing.

**Do this once, though.** Open

```
https://api.openalex.org/authors?search=Enamul%20Hoq
```

find your record, and paste the id (looks like `A5012345678`) into
`OPENALEX_AUTHOR_ID` at the top of `scripts/update_publications.py`. Without it the
script matches on name plus institution, which works but is a guess. If you have an
ORCID, put it in `ORCID` instead — that is exact.

To run it now instead of waiting for Monday: **Actions → Update publications → Run
workflow**.

### Adding something the robot can't see

MIDL and Ital-IA acceptances, conference abstracts and theses often aren't indexed
anywhere. Add them by hand to `data/publications.json` and set `"pinned": true` —
pinned entries are never overwritten or reordered away, and the updater will only
ever attach a citation count to them.

```json
{
  "id": "short-unique-slug",
  "pinned": true,
  "title": "Title of the paper",
  "authors": "Hoq ME, Coauthor A, Prior F",
  "venue": "Where it appeared",
  "year": 2026,
  "type": "journal",          // journal | conference | preprint | abstract | thesis
  "status": "Accepted",       // Peer-reviewed | Accepted | Preprint | Abstract
  "firstAuthor": true,
  "doi": "10.xxxx/xxxxx",
  "url": "https://doi.org/10.xxxx/xxxxx",
  "qr": "jiim2025",           // optional, a key from scripts/make_qr.py
  "note": "One sentence a non-specialist would understand.",
  "tags": ["Screening CT"]
}
```

Commit it. The page picks it up on load — no rebuild needed.

---

## 3. QR codes

Eleven codes ship with the site. Ten form the wall in **Connect** — website, Google
Scholar, LinkedIn, GitHub, email, then RAD-DINO (JIIM 2025), Virtual-Eyes (MIDL 2026),
RGG (Ital-IA 2026), the NeurIPS diffusion paper, and the LDCT review. The eleventh
sits in the CMU press panel. Any publication with a `"qr"` key also gets a **QR**
button in the list.

**When the CEUR-WS volume for Ital-IA 2026 appears,** swap the arXiv link for it in
`LINKS["rgg2026"]` and in the `italia-2026-captioning` entry of
`data/publications.json`, then regenerate.

Print-quality PNGs are in `assets/qr/` — good for poster corners, slide footers and
business cards.

To change a link or add a code, edit `LINKS` in `scripts/make_qr.py`, then:

```bash
pip install "qrcode[pil]" pillow
python scripts/make_qr.py     # regenerates PNGs and the inline SVGs
python scripts/build.py       # re-injects them into index.html
```

---

## 4. Editing the site

Edit `src/index.template.html`, then run `python scripts/build.py`. Never edit
`index.html` directly — it is generated, and your changes would be overwritten.

The build step exists only to inline the portrait and the QR codes. Everything else
— every heading, project, and line of copy — is plain HTML in the template.

| File | What it holds |
|---|---|
| `src/index.template.html` | the site: structure, styling, behaviour |
| `src/photo.b64.txt` | the portrait, base64, inlined at build time |
| `scripts/build.py` | assembles `index.html` |
| `scripts/make_qr.py` | link list → QR PNGs and inline SVGs |
| `scripts/update_publications.py` | the OpenAlex sync |
| `data/publications.json` | the publication list |
| `assets/img/` | portrait, full size and square (used for link previews) |
| `assets/*.pdf` | CV and résumé, linked from the hero |
| `.nojekyll` | tells GitHub Pages to serve the files as they are |

### Changing the photo

Replace `assets/img/enamul-hoq.jpg`, then regenerate the inlined copy:

```python
import base64
from PIL import Image
im = Image.open("assets/img/enamul-hoq.jpg")
im.thumbnail((680, 900))
im.save("/tmp/p.jpg", quality=78, optimize=True)
open("src/photo.b64.txt", "w").write(base64.b64encode(open("/tmp/p.jpg","rb").read()).decode())
```

Then `python scripts/build.py`.

---

### Adding a photo to the gallery

Drop the image in `assets/img/gallery/`, add an entry to `GALLERY` in
`scripts/build.py`, and add a matching record to `src/gallery.json` (run the snippet
in `scripts/` history or copy the shape of an existing entry: `file`, `cap`, `alt`,
`b64`). Then `python scripts/build.py`.

---

## 5. Email

`mdenamulmte@gmail.com` is the primary address on the page; `mhoq@uams.edu` is
listed underneath as the academic one. A `mailto:` link only opens if the visitor
has a mail app configured, which is why every address also has a **Copy** button —
that always works.

---

## 6. Three things worth doing soon

1. **Get an ORCID** (orcid.org, five minutes) and add it to
   `scripts/update_publications.py`. It makes the auto-update exact, and journals
   will ask for it anyway.
2. **Swap the Virtual-Eyes arXiv link** for the MIDL proceedings version once it is
   out, and the RGG link for the CEUR-WS volume.
3. **Add the hackathon photo** from the CMU story to the gallery if you appear in
   one of theirs and they allow reuse — ask the Libraries first.
