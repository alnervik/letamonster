"""
Bygger creatures_db.json fran en mapp med monster-sprites (gif/png).

Anvandning:
    python build_palette_db.py --input sprites/ --output ../data/creatures_db.json

Forvantar en mapp dar varje fil ar uppkallad efter monstret, t.ex:
    sprites/Swampling.gif
    sprites/Blood Priest.gif
    ...

Algoritmen ar validerad mot 9 kanda Quiz-Ping-facit (se README):
- K-means med k=5 klustrar
- Klustring pa UNIKA fargtripplar (ovagt av pixelfrekvens) - inte rafrekvens
- INGEN filtrering av nastan-svart (svart ar ofta en av de 5 farg-svaren)
- Endast forsta framen i en animerad gif racker (alla-frames gav ingen tydlig forbattring)
- Klusterordning: storst kluster (flest tilldelade pixlar, viktat) forst
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from sklearn.cluster import KMeans


def cluster_sprite(path: Path, k: int = 5, alpha_thresh: int = 128):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im).reshape(-1, 4)
    arr = arr[arr[:, 3] >= alpha_thresh][:, :3]
    if len(arr) == 0:
        return None
    uniq = np.unique(arr, axis=0)
    kk = min(k, len(uniq))
    if kk == 0:
        return None
    km = KMeans(n_clusters=kk, n_init=8, random_state=0).fit(uniq)
    labels_full = km.predict(arr)
    sizes = np.bincount(labels_full, minlength=kk)
    order = np.argsort(-sizes)
    centers = km.cluster_centers_[order].astype(int)
    # pad to k colors if sprite had fewer unique colors than k
    colors = [[int(c[0]), int(c[1]), int(c[2])] for c in centers]
    while len(colors) < k:
        colors.append(colors[-1])
    return colors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Mapp med sprite-bilder")
    ap.add_argument("--output", required=True, help="Var creatures_db.json ska sparas")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    in_dir = Path(args.input)
    out_path = Path(args.output)

    exts = {".gif", ".png", ".jpg", ".jpeg"}
    files = sorted(f for f in in_dir.iterdir() if f.suffix.lower() in exts)

    if not files:
        print(f"Inga bildfiler hittades i {in_dir}", file=sys.stderr)
        sys.exit(1)

    db = {}
    for f in files:
        name = f.stem.replace("_", " ").strip()
        colors = cluster_sprite(f, k=args.k)
        if colors is None:
            print(f"  hoppar over {f.name} (ingen giltig pixel-data)", file=sys.stderr)
            continue
        db[name] = colors
        print(f"  {name}: {colors}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(db, fh, ensure_ascii=False, indent=2)

    print(f"\nKlart. {len(db)} monster sparade i {out_path}")


if __name__ == "__main__":
    main()
