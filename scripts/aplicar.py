"""Aplica as decisões de recorte e gera as montagens + planilha de revisão.

decisoes.txt — uma linha por foto (índice da ordem de revisão):
  IDX X0 Y0 X1 Y1 [| observação]   -> zoom na caixa (coordenadas em décimos da foto, 0–10)
  IDX R X0 Y0 X1 Y1 | observação    -> gera, mas marca "Revisar"
  IDX B [| obs]                       -> borrada, não gera
  IDX N [| obs]                       -> sem poste, não gera

Uso: python3 aplicar.py PASTA_ORIGEM PASTA_SAIDA inv.json ordem.json decisoes.txt planilha.xlsx [filtro_prefixo]
"""
import sys, os, json
from PIL import Image, ImageFilter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment

W, H = 2000, 1219
LEFT_W, GAP = 915, 10
RIGHT_W = W - LEFT_W - GAP
MIN_ZOOM_PX = 260  # largura mínima do recorte do zoom antes de marcar baixa resolução


def fit_box(box, iw, ih, ratio):
    x0, y0, x1, y1 = box
    cx, cy, w, h = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0, y1 - y0
    if w / h < ratio:
        w = h * ratio
    else:
        h = w / ratio
    if w > iw:
        w, h = iw, iw / ratio
    if h > ih:
        h, w = ih, ih * ratio
    x0 = min(max(cx - w / 2, 0), iw - w)
    y0 = min(max(cy - h / 2, 0), ih - h)
    return (round(x0), round(y0), round(x0 + w), round(y0 + h))


def painel_esquerdo(img, cx):
    """Foto completa. Se a proporção for próxima, preenche; senão encaixa com fundo desfocado."""
    tr = LEFT_W / H
    r = img.width / img.height
    if 0.85 * tr <= r:  # foto em pé ou deitada: recorta centrando no poste
        s = max(LEFT_W / img.width, H / img.height)
        nw, nh = round(img.width * s), round(img.height * s)
        big = img.resize((nw, nh), Image.LANCZOS)
        x = min(max(round(cx * nw - LEFT_W / 2), 0), nw - LEFT_W)
        y = (nh - H) // 2
        return big.crop((x, y, x + LEFT_W, y + H))
    s = max(LEFT_W / img.width, H / img.height)
    bg = img.resize((round(img.width * s), round(img.height * s)))
    bx, by = (bg.width - LEFT_W) // 2, (bg.height - H) // 2
    bg = bg.crop((bx, by, bx + LEFT_W, by + H)).filter(ImageFilter.GaussianBlur(25))
    bg = Image.blend(bg, Image.new("RGB", bg.size, "white"), 0.35)
    s = min(LEFT_W / img.width, H / img.height)
    fg = img.resize((round(img.width * s), round(img.height * s)), Image.LANCZOS)
    bg.paste(fg, ((LEFT_W - fg.width) // 2, (H - fg.height) // 2))
    return bg


def montar(src, dst, box10):
    img = Image.open(src).convert("RGB")
    iw, ih = img.size
    box = [box10[0] * iw / 10, box10[1] * ih / 10, box10[2] * iw / 10, box10[3] * ih / 10]
    zb = fit_box(box, iw, ih, RIGHT_W / H)
    canvas = Image.new("RGB", (W, H), "white")
    canvas.paste(painel_esquerdo(img, (zb[0] + zb[2]) / 2 / iw), (0, 0))
    canvas.paste(img.crop(zb).resize((RIGHT_W, H), Image.LANCZOS), (LEFT_W + GAP, 0))
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    canvas.save(dst, "JPEG", quality=85, optimize=True)
    return zb


def ler_decisoes(path):
    dec = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln or ln.startswith("#"):
            continue
        cmd, _, obs = ln.partition("|")
        p = cmd.split()
        idx, rest = int(p[0]), p[1:]
        kind = "OK"
        if rest and rest[0] in ("R", "B", "N"):
            kind, rest = rest[0], rest[1:]
        dec[idx] = (kind, [float(v) for v in rest], obs.strip())
    return dec


def main():
    src_root, out_root, inv, ordem, decf, xlsx = sys.argv[1:7]
    filtro = sys.argv[7] if len(sys.argv) > 7 else ""
    inv = {r["rel"]: r for r in json.load(open(inv))}
    ordem = json.load(open(ordem))
    idx_of_md5 = {inv[rel]["md5"]: i for i, rel in enumerate(ordem)}
    dec = ler_decisoes(decf)
    linhas, feitos, pend = [], 0, 0
    for rel in sorted(inv):
        r = inv[rel]
        i = idx_of_md5[r["md5"]]
        if i not in dec:
            pend += 1
            continue
        kind, box, obs = dec[i]
        notas = [obs] if obs else []
        outros_ids = [x for x in r["same"] if os.path.basename(x) != os.path.basename(rel)]
        if outros_ids:
            notas.append("Foto idêntica a: " + ", ".join(outros_ids) + " (verificar se o ID está certo)")
        status, gerada = {"OK": "OK", "R": "Revisar", "B": "Borrada", "N": "Sem poste"}[kind], "Não"
        if kind in ("OK", "R"):
            if not filtro or rel.startswith(filtro):
                zb = montar(os.path.join(src_root, rel), os.path.join(out_root, rel), box)
                if zb[2] - zb[0] < MIN_ZOOM_PX:
                    notas.append(f"Foto original pequena ({r['w']}x{r['h']}): zoom com pouca nitidez")
                    status = "Revisar"
                feitos += 1
            gerada = "Sim"
            if outros_ids and status == "OK":
                status = "Revisar"
        t, le = rel.split(os.sep)[:2]
        linhas.append([t, le, os.path.basename(rel), status, gerada, "; ".join(notas)])
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatório"
    ws.append(["T", "LE", "Arquivo", "Status", "Imagem gerada?", "Observação"])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="305496")
    cores = {"OK": "C6EFCE", "Revisar": "FFEB9C", "Sem poste": "FFC7CE", "Borrada": "FFC7CE"}
    for ln in linhas:
        ws.append(ln)
        ws.cell(ws.max_row, 4).fill = PatternFill("solid", fgColor=cores[ln[3]])
        ws.cell(ws.max_row, 6).alignment = Alignment(wrap_text=True, vertical="top")
    for col, w in zip("ABCDEF", (6, 8, 26, 11, 15, 100)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    res = wb.create_sheet("Resumo")
    from collections import Counter
    cnt = Counter(l[3] for l in linhas)
    res.append(["Status", "Quantidade"])
    for k in ("OK", "Revisar", "Borrada", "Sem poste"):
        res.append([k, cnt.get(k, 0)])
    res.append(["Total", len(linhas)])
    res.column_dimensions["A"].width = 14
    wb.save(xlsx)
    print(f"geradas agora: {feitos}  linhas: {len(linhas)}  sem decisão: {pend}  {dict(cnt)}")


if __name__ == "__main__":
    main()
