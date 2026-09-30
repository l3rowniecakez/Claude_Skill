#!/usr/bin/env python3
"""Render an ER diagram PNG (crow's-foot, boxes like the user's reference image) from the SAME
payload JSON that er_write.py takes (entities / relationships). Pure Pillow, no network.

Usage: er_render.py <payload.json> <out.png>
Layout: the most-connected entity sits in the middle; its parents (it is `from`) go left, its
children (it is `to`) go right; others are placed relative to whoever they attach to. Each line
starts/ends on the row of the FK/PK column it joins (elbow connector) with crow's-foot end marks:
  1 = ||   0..1 = o|   1..N = |<   0..N = o<
"""
import sys, os, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
from PIL import Image, ImageDraw, ImageFont

S = 2                                   # supersample for crisp lines
W_KEY, W_NAME, W_TYPE = 56, 190, 130
BOX_W = W_KEY + W_NAME + W_TYPE
ROW_H, HEAD_H, PAD = 26, 40, 8
COL_GAP, ROW_GAP, MARGIN = 150, 46, 50
DARK, VIEW, LINE, GREY = (38, 38, 42), (92, 107, 140), (40, 40, 40), (110, 110, 110)


FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fonts")   # bundled: same look on every OS


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size * S)   # raises if missing — never silently fall back


def layout(ents, rels):
    names = [e["name"] for e in ents]
    deg = {n: 0 for n in names}
    for r in rels:
        deg[r["from"]] += 1; deg[r["to"]] += 1
    center = max(names, key=lambda n: deg[n])
    col = {center: 0}
    changed = True
    while changed:
        changed = False
        for r in rels:
            f, t = r["from"], r["to"]
            if t in col and f not in col:
                col[f] = col[t] + 1; changed = True      # child of a placed entity -> right
            elif f in col and t not in col:
                col[t] = col[f] - 1; changed = True      # parent of a placed entity -> left
    for n in names:
        col.setdefault(n, 2)
    return col


def draw_end(d, x, y, direction, card):
    """direction = +1 if the line leaves the box to the RIGHT, -1 to the LEFT. Marks drawn along the line."""
    u = direction * S
    w = 2 * S
    def bar(off):
        d.line([(x + u * off, y - 7 * S), (x + u * off, y + 7 * S)], fill=LINE, width=w)
    if card in ("1..N", "0..N"):
        tip = x + u * 14
        for dy in (-8, 0, 8):
            d.line([(x, y + dy * S), (tip, y)], fill=LINE, width=w)
        if card == "1..N":
            bar(18)
        else:
            r = 5 * S
            cx = x + u * 24
            d.ellipse([cx - r, y - r, cx + r, y + r], fill="white", outline=LINE, width=w)
    else:
        bar(8)
        if card == "1":
            bar(15)
        else:
            r = 5 * S
            cx = x + u * 22
            d.ellipse([cx - r, y - r, cx + r, y + r], fill="white", outline=LINE, width=w)


def main():
    p = json.load(open(sys.argv[1], encoding="utf-8"))
    ents, rels = p["entities"], p["relationships"]
    col = layout(ents, rels)
    by = {e["name"]: e for e in ents}
    hgt = {e["name"]: HEAD_H + PAD + len(e["columns"]) * ROW_H + PAD for e in ents}
    cols = sorted(set(col.values()))
    colidx = {c: i for i, c in enumerate(cols)}
    pos = {}
    col_h = {}
    for c in cols:
        members = [n for n in by if col[n] == c]
        col_h[c] = sum(hgt[n] for n in members) + ROW_GAP * (len(members) - 1)
    total_h = max(col_h.values())
    for c in cols:
        y = MARGIN + (total_h - col_h[c]) / 2
        for n in [n for n in by if col[n] == c]:
            pos[n] = (MARGIN + colidx[c] * (BOX_W + COL_GAP), y)
            y += hgt[n] + ROW_GAP
    Wpx = MARGIN * 2 + len(cols) * BOX_W + (len(cols) - 1) * COL_GAP
    Hpx = MARGIN * 2 + total_h
    img = Image.new("RGB", (Wpx * S, Hpx * S), "white")
    d = ImageDraw.Draw(img)
    f_h, f_b, f_t = font(14, True), font(12), font(11)
    f_pk = font(12, True)

    def rowy(n, colname):
        x, y = pos[n]
        for i, c in enumerate(by[n]["columns"]):
            if c["name"] == colname:
                return y + HEAD_H + PAD + i * ROW_H + ROW_H / 2
        return y + hgt[n] / 2

    # connectors first (under boxes)
    used = {}
    for r in rels:
        a, b = r["from"], r["to"]
        (ax, ay), (bx, by_) = pos[a], pos[b]
        y1, y2 = rowy(a, r["from_col"]), rowy(b, r["to_col"])
        if colidx[col[a]] == colidx[col[b]]:      # same column: route around the right side
            x1, x2, dr1, dr2 = ax + BOX_W, bx + BOX_W, 1, 1
            k = used.get("same", 0); used["same"] = k + 1
            midx = x1 + 30 + 14 * k
        else:
            left_to_right = ax < bx
            x1 = ax + BOX_W if left_to_right else ax
            x2 = bx if left_to_right else bx + BOX_W
            dr1, dr2 = (1, -1) if left_to_right else (-1, 1)
            gap_key = (min(colidx[col[a]], colidx[col[b]]),)
            k = used.get(gap_key, 0); used[gap_key] = k + 1
            gx = min(x1, x2) + (COL_GAP / 2 if abs(x1 - x2) < COL_GAP * 1.5 else (MARGIN + 0))
            midx = (x1 + x2) / 2 + (k % 5 - 2) * 12
        pts = [(x1, y1), (midx, y1), (midx, y2), (x2, y2)]
        d.line([(px * S, py * S) for px, py in pts], fill=LINE, width=2 * S, joint="curve")
        draw_end(d, x1 * S, y1 * S, dr1, r["from_card"])
        draw_end(d, x2 * S, y2 * S, dr2, r["to_card"])

    for n, e in by.items():
        x, y = pos[n]
        H = hgt[n]
        d.rounded_rectangle([x * S, y * S, (x + BOX_W) * S, (y + H) * S], radius=10 * S, fill="white", outline=LINE, width=2 * S)
        d.rounded_rectangle([x * S, y * S, (x + BOX_W) * S, (y + HEAD_H + 6) * S], radius=10 * S,
                            fill=VIEW if e.get("kind") == "view" else DARK)
        d.rectangle([x * S + 2, (y + HEAD_H) * S, (x + BOX_W) * S - 2, (y + HEAD_H + 6) * S], fill="white")
        title = ("«view» " if e.get("kind") == "view" else "") + n
        tw = d.textlength(title, font=f_h)
        d.text((x * S + (BOX_W * S - tw) / 2, (y + 10) * S), title, font=f_h, fill="white")
        if e.get("db"):
            dbt = f"[{e['db']}]"
            tw2 = d.textlength(dbt, font=f_t)
            d.text((x * S + (BOX_W * S - tw2) / 2, (y + 25) * S), dbt, font=f_t, fill=(200, 200, 205))
        d.line([(x * S, (y + HEAD_H) * S), ((x + BOX_W) * S, (y + HEAD_H) * S)], fill=LINE, width=2 * S)
        d.line([((x + W_KEY) * S, (y + HEAD_H) * S), ((x + W_KEY) * S, (y + H) * S)], fill=(150, 150, 150), width=S)
        for i, c in enumerate(e["columns"]):
            ry = y + HEAD_H + PAD + i * ROW_H
            key = c.get("key", "")
            if key:
                d.text(((x + 8) * S, (ry + 5) * S), key, font=f_pk, fill=LINE)
            nm = c["name"]
            d.text(((x + W_KEY + 8) * S, (ry + 5) * S), nm, font=f_b, fill=(0, 0, 0))
            if "PK" in key:
                w = d.textlength(nm, font=f_b)
                d.line([((x + W_KEY + 8) * S, (ry + 20) * S), ((x + W_KEY + 8) * S + w, (ry + 20) * S)], fill=(0, 0, 0), width=S)
            d.text(((x + W_KEY + W_NAME + 4) * S, (ry + 6) * S), c.get("type", ""), font=f_t, fill=GREY)
    img = img.resize((Wpx, Hpx), Image.LANCZOS)
    img.save(sys.argv[2])
    print(json.dumps({"png": sys.argv[2], "size": [Wpx, Hpx]}))


if __name__ == "__main__":
    main()
