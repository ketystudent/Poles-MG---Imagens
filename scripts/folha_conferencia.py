"""Folha de conferência das montagens geradas (20 por folha). Uso: folha_conferencia.py SAIDA_DIR ordem.json inv.json IDX_INI IDX_FIM destino.jpg"""
import sys, json, os
from PIL import Image, ImageDraw, ImageFont
out, ordem, inv, a, b, dst = sys.argv[1:7]
ordem = json.load(open(ordem)); a, b = int(a), int(b)
f = ImageFont.load_default(size=20)
c = Image.new("RGB", (2000, 1550), (40, 40, 40)); d = ImageDraw.Draw(c)
for k, i in enumerate(range(a, min(b, len(ordem)))):
    p = os.path.join(out, ordem[i]); x, y = (k % 4) * 500, (k // 4) * 310
    if os.path.exists(p):
        c.paste(Image.open(p).resize((496, 302)), (x, y))
    d.text((x + 4, y + 2), f"#{i}", fill="red", font=f, stroke_width=2, stroke_fill="white")
c.save(dst, quality=80)
