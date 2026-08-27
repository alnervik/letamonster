"""
Skrapar TibiaWiki efter Bestiary-monster och laddar ner en bild per monster.

Tva steg:
  1) Hamtar listan av alla Bestiary-monster via TibiaWiki:s MediaWiki-API
     (Category:Bestiary_Creatures, paginerat).
  2) For varje monster: hamtar wiki-sidan via API:t, letar upp infobox-bilden
     (forsta <img> i "portable-infobox"), laddar ner den till --outdir.

Anvandning:
    python scrape_creatures.py --outdir sprites/ --limit 50   # testkorning
    python scrape_creatures.py --outdir sprites/              # alla ~819

Var snall mot wikin: default 1 sekunds fordrojning mellan anrop.
Anpassa gladeligen till samma requests/parsing-monster du redan har i
itemleta-skraparen om den har battre felhantering/retries.
"""
import argparse
import html
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

import requests

API = "https://tibia.fandom.com/api.php"
HEADERS = {"User-Agent": "tibia-palette-matcher/0.1 (personligt projekt)"}


def get_creature_names(limit=None, delay=1.0):
    names = []
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Bestiary_Creatures",
        "cmlimit": "500",
        "format": "json",
    }
    while True:
        r = requests.get(API, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        for m in data.get("query", {}).get("categorymembers", []):
            title = m["title"]
            if title.startswith("Category:"):
                continue
            if title.lower() in ("free account bestiary",):
                continue
            names.append(title)
            if limit and len(names) >= limit:
                return names
        cont = data.get("continue", {}).get("cmcontinue")
        if not cont:
            break
        params["cmcontinue"] = cont
        time.sleep(delay)
    return names


def get_infobox_image_url(page_title, delay=1.0):
    params = {
        "action": "parse",
        "page": page_title,
        "prop": "text",
        "format": "json",
    }
    r = requests.get(API, params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    data = r.json()
    page_html = data.get("parse", {}).get("text", {}).get("*", "")
    # forsta bilden i infoboxen
    m = re.search(r'class="[^"]*pi-image-thumbnail[^"]*"[^>]*src="([^"]+)"', page_html)
    if not m:
        m = re.search(r'class="[^"]*image[^"]*"[^>]*>\s*<img[^>]*src="([^"]+)"', page_html)
    if not m:
        return None
    url = html.unescape(m.group(1))  # &amp; -> & osv, annars 404 pa riktiga anrop
    # ta bort ev. thumbnail-nedskalning i URL:en for att fa originalbilden
    url = re.sub(r"/scale-to-width-down/\d+", "", url)
    return url


def download(url, dest, delay=1.0):
    r = requests.get(url, headers=HEADERS, timeout=30)
    r.raise_for_status()
    dest.write_bytes(r.content)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--limit", type=int, default=None, help="Begransa antal monster (for test)")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print("Hamtar monsterlista...")
    names = get_creature_names(limit=args.limit, delay=args.delay)
    print(f"Hittade {len(names)} monster.")

    manifest = {}
    for i, name in enumerate(names, 1):
        safe_name = re.sub(r'[\\/*?:"<>|]', "_", name)
        ext_guess = ".gif"
        dest = outdir / f"{safe_name}{ext_guess}"
        if dest.exists():
            print(f"[{i}/{len(names)}] {name}: redan nedladdad, hoppar over")
            continue
        try:
            img_url = get_infobox_image_url(name, delay=args.delay)
            if not img_url:
                print(f"[{i}/{len(names)}] {name}: ingen bild hittad")
                continue
            real_ext = Path(img_url.split("?")[0]).suffix or ".gif"
            dest = outdir / f"{safe_name}{real_ext}"
            download(img_url, dest, delay=args.delay)
            manifest[name] = str(dest.name)
            print(f"[{i}/{len(names)}] {name}: OK -> {dest.name}")
        except Exception as e:
            print(f"[{i}/{len(names)}] {name}: FEL ({e})")
        time.sleep(args.delay)

    with open(outdir / "_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)

    print(f"\nKlart. {len(manifest)} bilder nedladdade till {outdir}")


if __name__ == "__main__":
    main()
