"""Inventário: lista todas as fotos, tamanho, nitidez (variância do Laplaciano) e duplicatas.
Uso: python3 inventario.py PASTA_CIDADE SAIDA.json"""
import sys, glob, os, json, hashlib
import numpy as np
from PIL import Image

root, out = sys.argv[1], sys.argv[2]
rows, by_hash = [], {}
for f in sorted(glob.glob(os.path.join(root, "*", "*", "*.jpg"))):
    rel = os.path.relpath(f, root)
    data = open(f, "rb").read()
    h = hashlib.md5(data).hexdigest()
    im = Image.open(f)
    w, hh = im.size
    g = im.convert("L")
    g = g.resize((500, max(3, round(500 * hh / w))))
    a = np.asarray(g, float)
    lap = a[1:-1, 1:-1] * 4 - a[:-2, 1:-1] - a[2:, 1:-1] - a[1:-1, :-2] - a[1:-1, 2:]
    rows.append({"rel": rel, "w": w, "h": hh, "md5": h, "sharp": round(float(lap.var()), 1)})
    by_hash.setdefault(h, []).append(rel)
for r in rows:
    r["same"] = [x for x in by_hash[r["md5"]] if x != r["rel"]]
json.dump(rows, open(out, "w"), ensure_ascii=False, indent=0)
print(len(rows), "fotos,", len(by_hash), "conteúdos únicos")
