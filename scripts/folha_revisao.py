"""Gera folhas de revisão (20 fotos por folha) com grade de 10% para escolher o zoom.
Uso: python3 folha_revisao.py PASTA_CIDADE inv.json SAIDA_DIR"""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont

root, inv, outd = sys.argv[1:4]
rows = json.load(open(inv))
seen, uniq = set(), []
for r in rows:
    if r["md5"] in seen:
        continue
    seen.add(r["md5"])
    uniq.append(r)
json.dump([r["rel"] for r in uniq], open(os.path.join(outd, "ordem.json"), "w"), ensure_ascii=False)
CW, CH, COLS, ROWS = 300, 420, 5, 4
font = ImageFont.load_default(size=18)
small = ImageFont.load_default(size=11)
for p in range(0, len(uniq), COLS * ROWS):
    sheet = Image.new("RGB", (CW * COLS, CH * ROWS), (40, 40, 40))
    d = ImageDraw.Draw(sheet, "RGBA")
    for k, r in enumerate(uniq[p:p + COLS * ROWS]):
        i = p + k
        im = Image.open(os.path.join(root, r["rel"])).convert("RGB")
        im.thumbnail((CW - 24, CH - 30))
        ox = (k % COLS) * CW + 20
        oy = (k // COLS) * CH + 26
        sheet.paste(im, (ox, oy))
        for t in range(1, 10):
            x = ox + im.width * t / 10
            y = oy + im.height * t / 10
            a = 150 if t == 5 else 80
            d.line([(x, oy), (x, oy + im.height)], fill=(255, 255, 0, a))
            d.line([(ox, y), (ox + im.width, y)], fill=(255, 255, 0, a))
            d.text((x - 3, oy + im.height + 1), str(t), fill="yellow", font=small)
            d.text((ox - 12, y - 6), str(t), fill="yellow", font=small)
        tag = f"#{i}  s={r['sharp']:.0f}  {r['w']}x{r['h']}"
        d.text(((k % COLS) * CW + 4, (k // COLS) * CH + 3), tag,
               fill="red" if r["sharp"] < 60 else "white", font=font)
    sheet.save(os.path.join(outd, f"folha_{p // 20:03d}.jpg"), quality=85)
print(len(uniq), "únicas,", (len(uniq) + 19) // 20, "folhas")
