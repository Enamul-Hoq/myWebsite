#!/usr/bin/env python3
"""
Keep data/publications.json in sync with the literature, without touching
anything written by hand.

How it works
------------
1. Finds your author record on OpenAlex (free, no key, indexes Crossref +
   PubMed + arXiv + DataCite, so journal papers and most preprints show up).
2. Pulls every work attached to that record.
3. Adds anything that is not already in the file, and refreshes citation
   counts and DOIs on entries that match.
4. Entries marked "pinned": true keep their hand-written title, venue and
   notes for ever. The updater will only ever add a citation count to them.

Run locally:   python scripts/update_publications.py
On GitHub:     .github/workflows/update-publications.yml runs it weekly.

The one thing worth doing by hand
---------------------------------
Set OPENALEX_AUTHOR_ID or ORCID below. Name matching works, but an ID is
exact and will never pick up a different Hoq. Find yours by opening
https://api.openalex.org/authors?search=Enamul%20Hoq and copying the "id".
"""

import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

# ------------------------------------------------------------------ config
OPENALEX_AUTHOR_ID = ""          # e.g. "A5012345678" — leave empty to search by name
ORCID = ""                        # e.g. "0000-0002-1234-5678" — used if set and no author id
AUTHOR_SEARCH = "Enamul Hoq"
INSTITUTION_HINTS = ["arkansas", "uams", "mayo", "southeastern louisiana"]
CONTACT_EMAIL = "mhoq@uams.edu"   # OpenAlex asks for this; it buys a faster rate limit
MIN_YEAR = 2018                   # ignore anything older than your first output

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(os.path.dirname(HERE), "data", "publications.json")
API = "https://api.openalex.org"

TYPE_MAP = {
    "article": "journal",
    "preprint": "preprint",
    "book-chapter": "chapter",
    "dissertation": "thesis",
    "review": "journal",
    "proceedings-article": "conference",
}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": f"hoq-site-updater ({CONTACT_EMAIL})"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def norm(s):
    """Loose key for matching titles across sources."""
    return re.sub(r"[^a-z0-9]+", "", (s or "").lower())[:90]


def resolve_author():
    if OPENALEX_AUTHOR_ID:
        return OPENALEX_AUTHOR_ID
    if ORCID:
        a = get(f"{API}/authors/orcid:{ORCID}?mailto={CONTACT_EMAIL}")
        return a["id"].rsplit("/", 1)[-1]

    q = urllib.parse.quote(AUTHOR_SEARCH)
    res = get(f"{API}/authors?search={q}&per_page=25&mailto={CONTACT_EMAIL}").get("results", [])
    best = None
    for a in res:
        inst = ((a.get("last_known_institution") or {}).get("display_name") or "").lower()
        insts = " ".join(
            (i.get("display_name") or "").lower()
            for i in (a.get("last_known_institutions") or [])
        )
        hay = inst + " " + insts
        if any(h in hay for h in INSTITUTION_HINTS):
            best = a
            break
        if best is None:
            best = a
    if not best:
        return None
    print(f"  matched author: {best['display_name']} — {best['id']} ({best.get('works_count')} works)")
    print("  pin this by setting OPENALEX_AUTHOR_ID at the top of this script")
    return best["id"].rsplit("/", 1)[-1]


def fetch_works(author_id):
    works, cursor = [], "*"
    while cursor:
        url = (
            f"{API}/works?filter=authorships.author.id:{author_id},"
            f"from_publication_date:{MIN_YEAR}-01-01"
            f"&per-page=200&cursor={cursor}&mailto={CONTACT_EMAIL}"
        )
        page = get(url)
        works += page.get("results", [])
        cursor = page.get("meta", {}).get("next_cursor")
        time.sleep(0.4)
    return works


def to_entry(w):
    auths = [a["author"]["display_name"] for a in w.get("authorships", [])][:12]
    first = bool(auths) and "hoq" in auths[0].lower()
    venue = (
        ((w.get("primary_location") or {}).get("source") or {}).get("display_name")
        or w.get("type", "").replace("-", " ").title()
    )
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    return {
        "id": w["id"].rsplit("/", 1)[-1].lower(),
        "pinned": False,
        "source": "openalex",
        "title": (w.get("title") or "").strip(),
        "authors": ", ".join(auths),
        "venue": venue,
        "year": w.get("publication_year"),
        "type": TYPE_MAP.get(w.get("type"), "journal"),
        "status": "Preprint" if w.get("type") == "preprint" else "Peer-reviewed",
        "firstAuthor": first,
        "doi": doi,
        "url": w.get("doi") or (w.get("primary_location") or {}).get("landing_page_url"),
        "citations": w.get("cited_by_count", 0),
        "tags": [],
    }


def main():
    with open(DATA) as f:
        data = json.load(f)
    existing = data["publications"]

    by_doi = {(p.get("doi") or "").lower(): p for p in existing if p.get("doi")}
    by_title = {norm(p["title"]): p for p in existing}

    print("resolving author…")
    author_id = resolve_author()
    if not author_id:
        print("no author record found — file left untouched")
        return 0

    print(f"fetching works for {author_id}…")
    try:
        works = fetch_works(author_id)
    except Exception as e:                                     # noqa: BLE001
        print(f"OpenAlex unavailable ({e}) — file left untouched")
        return 0
    print(f"  {len(works)} works returned")

    added, refreshed = [], 0
    for w in works:
        e = to_entry(w)
        if not e["title"]:
            continue
        match = by_doi.get((e["doi"] or "").lower()) or by_title.get(norm(e["title"]))
        if match:
            if e["citations"] and match.get("citations") != e["citations"]:
                match["citations"] = e["citations"]
                refreshed += 1
            if e["doi"] and not match.get("doi"):
                match["doi"] = e["doi"]
                match["url"] = match.get("url") or e["url"]
            continue
        existing.append(e)
        by_title[norm(e["title"])] = e
        if e["doi"]:
            by_doi[e["doi"].lower()] = e
        added.append(e)

    existing.sort(key=lambda p: (-(p.get("year") or 0), not p.get("firstAuthor"), p["title"]))
    data["publications"] = existing
    data["updated"] = time.strftime("%Y-%m-%d")

    with open(DATA, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    for e in added:
        print(f"  + {e['year']}  {e['title'][:70]}")
    print(f"\ndone — {len(added)} added, {refreshed} citation counts refreshed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
