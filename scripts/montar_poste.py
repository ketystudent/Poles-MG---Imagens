"""Gera a montagem de documentação do poste (2000x1219 JPG).

Esquerda: foto original (poste completo) | faixa branca | Direita: zoom na fiação.

Uso:
  python3 montar_poste.py ORIGEM.jpg SAIDA.jpg X0 Y0 X1 Y1
  (X0,Y0,X1,Y1 = caixa do zoom em pixels da foto original)
"""
import sys
from PIL import Image

W, H = 2000, 1219
LEFT_W, GAP = 915, 10
RIGHT_W = W - LEFT_W - GAP  # 1075


def cover(img, tw, th, cx=0.5, cy=0.5):
    """Redimensiona preenchendo tw x th, cortando o excesso em torno de (cx, cy)."""
    s = max(tw / img.width, th / img.height)
    nw, nh = round(img.width * s), round(img.height * s)
    img = img.resize((nw, nh), Image.LANCZOS)
    x = min(max(round(cx * nw - tw / 2), 0), nw - tw)
    y = min(max(round(cy * nh - th / 2), 0), nh - th)
    return img.crop((x, y, x + tw, y + th))


def fit_box(box, img_w, img_h, ratio):
    """Expande a caixa para a proporção ratio (w/h) mantendo o centro, dentro da imagem."""
    x0, y0, x1, y1 = box
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    w, h = x1 - x0, y1 - y0
    if w / h < ratio:
        w = h * ratio
    else:
        h = w / ratio
    w, h = min(w, img_w), min(h, img_h)
    x0 = min(max(cx - w / 2, 0), img_w - w)
    y0 = min(max(cy - h / 2, 0), img_h - h)
    return (round(x0), round(y0), round(x0 + w), round(y0 + h))


def montar(src, dst, box, left_cx=0.5):
    img = Image.open(src).convert("RGB")
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(cover(img, LEFT_W, H, cx=left_cx), (0, 0))
    zb = fit_box(box, img.width, img.height, RIGHT_W / H)
    canvas.paste(img.crop(zb).resize((RIGHT_W, H), Image.LANCZOS), (LEFT_W + GAP, 0))
    canvas.save(dst, "JPEG", quality=92)
    return zb


if __name__ == "__main__":
    s, d, *b = sys.argv[1:]
    print(montar(s, d, tuple(map(int, b[:4])), *(map(float, b[4:5]))))
