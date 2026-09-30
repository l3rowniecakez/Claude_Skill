#!/usr/bin/env python3
"""Write ONE menu's ER diagram into the App's analysis spreadsheet (the one written by
/git-learn-grouplife-system-analyst), as a new tab "[ER] <source tab title>", and put the
tab link into the "ER-Diagram" column of that menu's row in "Menu Contents".

What it does, in order (all idempotent):
 1. Ensures "Menu Contents" has an "ER-Diagram" header (row 6). If missing, INSERTS a new
    column immediately right of "Sheet URL" (column F; e.g. an existing "การใช้งาน" column
    shifts to G) and styles it like the other headers. Never inserts twice.
 2. Finds the menu's row by exact breadcrumb match (column B). Same rule as the analyst skill:
    a menu that already has an ER link/tab is UPDATED in place (tab cleared + rewritten), never
    duplicated — decided by the gid in the row's ER-Diagram cell, then by tab title.
 3. Draws entity boxes (PK/FK + column + type) in a grid on the left, and on the right the
    Relationships table, the Store/View table and a Mermaid erDiagram text block.
 4. Writes the tab URL into the ER-Diagram cell of that row and touches the date (B4).

stdin JSON:
{
 "spreadsheet_id": "...", "breadcrumb": "<exact เมนูงาน text>", "today": "2026-09-30",
 "program_name": "...", "repo_url": "...", "sub_folder": "...", "source_tab_url": "<Sheet URL cell>",
 "no_image": false,   # optional; true = old cell-box layout, no PNG
 "entities": [ {"name":"OGL_AgentBrokerHD","db":"OGL","kind":"table|view",
                "columns":[{"key":"PK|FK1|PK,FK1|","name":"DocNo","type":"varchar(20)"}]} ],
 "relationships": [ {"from":"OGL_AgentBrokerHD","from_col":"AgentCode","to":"OGL_Agent","to_col":"AgentCode",
                     "from_card":"0..N","to_card":"1",   # cardinality at each end: 1 | 0..1 | 1..N | 0..N
                     "evidence":"FK constraint FK_x | JOIN ใน OGL_ListAgentBrokerHD_NewSW | inferred จากชื่อคอลัมน์",
                     "note":"ความหมายทางธุรกิจ"} ],
 "objects": [ {"name":"OGL_ListAgentBrokerHD_NewSW","kind":"Stored Proc|View","db":"OGL",
               "tables":"OGL_AgentBrokerHD (R), Branch (R)","summary":"..."} ]
}
Prints JSON {tab_gid, tab_url, menu_row, er_column, column_inserted, action}.
Never run concurrently for the same spreadsheet_id.
"""
import sys, os, re, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service

MC = "Menu Contents"
FIRST = 7                       # first data row of Menu Contents
NAVY = {"red": 0.02745098, "green": 0.21568628, "blue": 0.3882353}   # same navy as analyst skill
WHITE = {"red": 1, "green": 1, "blue": 1}
LINE = {"red": 0.2, "green": 0.2, "blue": 0.2}
VIEW_BG = {"red": 0.36, "green": 0.42, "blue": 0.55}
PER_BAND = 3                    # entity boxes per row band
BOX_W = [70, 190, 120]          # key | column | type
STRIDE = 4                      # 3 cols + 1 spacer
SPACER_W = 40
REL_COL = PER_BAND * STRIDE + 1  # first column of the right-hand tables (after one wide gap column)
REL_W = [50, 230, 170, 230, 90, 380]
FORMATTED_ROWS = 400
LEFT = {"1": "||", "0..1": "|o", "1..N": "}|", "0..N": "}o"}
RIGHT = {"1": "||", "0..1": "o|", "1..N": "|{", "0..N": "o{"}


def col_letter(i):
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def gid_of(url):
    m = re.search(r"gid=(\d+)", url or "")
    return int(m.group(1)) if m else None


def card_text(fc, tc):
    many = lambda c: c in ("1..N", "0..N")
    a, b = many(fc), many(tc)
    kind = "many to many" if a and b else "one to many" if (not a and b) else "many to one" if (a and not b) else "one to one"
    opt = " (optional)" if "0" in (fc.split("..")[0], tc.split("..")[0]) else ""
    return f"{'N' if a else '1'} : {'N' if b else '1'}  {kind}{opt}"


def ensure_er_column(sheets, sid, mc_id):
    hdr = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A6:Z6").execute().get("values", [[]])
    hdr = hdr[0] if hdr else []
    for i, h in enumerate(hdr):
        if str(h).strip() == "ER-Diagram":
            return i, False
    url_idx = next((i for i, h in enumerate(hdr) if str(h).strip() == "Sheet URL"), 4)
    er = url_idx + 1
    reqs = [
        {"insertDimension": {"range": {"sheetId": mc_id, "dimension": "COLUMNS", "startIndex": er, "endIndex": er + 1},
                             "inheritFromBefore": True}},
        # copy header styling (navy, white bold, centered) + wrap/top alignment down the column from "Sheet URL"
        {"copyPaste": {"source": {"sheetId": mc_id, "startRowIndex": 0, "endRowIndex": 2000,
                                  "startColumnIndex": url_idx, "endColumnIndex": url_idx + 1},
                       "destination": {"sheetId": mc_id, "startRowIndex": 0, "endRowIndex": 2000,
                                       "startColumnIndex": er, "endColumnIndex": er + 1},
                       "pasteType": "PASTE_FORMAT"}},
        {"updateDimensionProperties": {"range": {"sheetId": mc_id, "dimension": "COLUMNS", "startIndex": er, "endIndex": er + 1},
                                       "properties": {"pixelSize": 250}, "fields": "pixelSize"}},
    ]
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": reqs}).execute()
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{MC}'!{col_letter(er)}6",
                                          valueInputOption="USER_ENTERED", body={"values": [["ER-Diagram"]]}).execute()
    return er, True


def build_grid(p, source_title):
    """Returns (cells{(r,c):value}, fmt_requests_fn(sheet_id)->list, end_row)."""
    cells, boxes, pk_cells, hdr_rows = {}, [], [], []
    info = [("โปรแกรม", p.get("program_name", "")), ("Repo URL", p.get("repo_url", "")),
            ("Sub Folder", p.get("sub_folder", "")), ("เมนูงาน", p["breadcrumb"]),
            ("วิเคราะห์จาก Tab", f"{source_title}  {p.get('source_tab_url','')}".strip()),
            ("วันที่อัพเดท Sheet ล่าสุด", p["today"])]
    for i, (k, v) in enumerate(info):
        cells[(i, 0)] = k
        cells[(i, 2)] = v
    img_rows = p.get("_img_rows", 0)     # >0 = picture mode: PNG floats at A9, tables go BELOW it, no cell boxes
    cells[(7, 0)] = ("ER Diagram (รูปด้านล่าง; ตาราง Relationships / Store / Mermaid อยู่ใต้รูป)" if img_rows else
                     "ER Diagram — 1 กล่อง = 1 Table/View ที่เมนูนี้ใช้ (PK = คีย์หลัก, FK = คีย์นอก; เส้นความสัมพันธ์ดูตาราง Relationships ทางขวา)")

    r0, band_h, col_i = 9, 0, 0
    for n, e in enumerate([] if img_rows else p["entities"]):
        if col_i == PER_BAND:
            r0 += band_h + 2; band_h = 0; col_i = 0
        c0 = col_i * STRIDE
        tag = "«view» " if e.get("kind") == "view" else ""
        cells[(r0, c0)] = f"{tag}{e['name']}" + (f"  [{e['db']}]" if e.get("db") else "")
        cols = e["columns"]
        for j, col in enumerate(cols):
            r = r0 + 1 + j
            cells[(r, c0)] = col.get("key", "")
            cells[(r, c0 + 1)] = col["name"]
            cells[(r, c0 + 2)] = col.get("type", "")
            if "PK" in col.get("key", ""):
                pk_cells.append((r, c0 + 1))
        hdr_rows.append((r0, c0, e.get("kind") == "view"))
        h = len(cols) + 1
        boxes.append((r0, c0, h))
        band_h = max(band_h, h)
        col_i += 1
    diagram_end = r0 + band_h

    # right-hand tables
    rc = 0 if img_rows else REL_COL
    T0 = (8 + img_rows) if img_rows else 7      # first row (0-indexed) of the tables block
    cells[(T0, rc)] = "Relationships (ความสัมพันธ์ระหว่าง Table)"
    rr = T0 + 1
    for j, h in enumerate(["No", "From (Table.Column)", "Cardinality", "To (Table.Column)", "Notation", "หลักฐาน / ความหมาย"]):
        cells[(rr, rc + j)] = h
    rel_hdr = rr
    for i, rel in enumerate(p.get("relationships", [])):
        r = rr + 1 + i
        fc, tc = rel.get("from_card", "0..N"), rel.get("to_card", "1")
        cells[(r, rc)] = i + 1
        cells[(r, rc + 1)] = f"{rel['from']}.{rel['from_col']}"
        cells[(r, rc + 2)] = card_text(fc, tc)
        cells[(r, rc + 3)] = f"{rel['to']}.{rel['to_col']}"
        cells[(r, rc + 4)] = f"{LEFT[fc]}--{RIGHT[tc]}"
        cells[(r, rc + 5)] = " — ".join(x for x in [rel.get("evidence", ""), rel.get("note", "")] if x)
    rr = rr + 1 + len(p.get("relationships", [])) + 2

    cells[(rr, rc)] = "Store / View ที่เกี่ยวข้อง (อ่าน code แล้วสรุปเป็น ER)"
    rr += 1
    obj_hdr = rr
    for j, h in enumerate(["No", "ชื่อ Object", "ประเภท / DB", "Table ที่เกี่ยวข้อง (R/W)", "", "สรุปการทำงาน"]):
        cells[(rr, rc + j)] = h
    for i, o in enumerate(p.get("objects", [])):
        r = rr + 1 + i
        cells[(r, rc)] = i + 1
        cells[(r, rc + 1)] = o["name"]
        cells[(r, rc + 2)] = f"{o.get('kind','')} / {o.get('db','')}"
        cells[(r, rc + 3)] = o.get("tables", "")
        cells[(r, rc + 5)] = o.get("summary", "")
    rr = rr + 1 + len(p.get("objects", [])) + 2

    cells[(rr, rc)] = "Mermaid erDiagram (คัดลอกไปวางที่ https://mermaid.live เพื่อดูเป็นรูปเส้นเชื่อม)"
    mm_start = rr + 1
    lines = ["erDiagram"]
    for rel in p.get("relationships", []):
        fc, tc = rel.get("from_card", "0..N"), rel.get("to_card", "1")
        lab = (rel.get("from_col") or "rel").replace('"', "")
        lines.append(f'    {rel["to"]} {LEFT[tc]}--{RIGHT[fc]} {rel["from"]} : "{lab}"')
    for e in p["entities"]:
        lines.append(f"    {e['name']} {{")
        for col in e["columns"]:
            ty = re.sub(r"[^A-Za-z0-9_]", "", col.get("type", "") or "col") or "col"
            keys = [k.strip() for k in col.get("key", "").split(",") if k.strip()]
            mk = ",".join(("PK" if k.startswith("PK") else "FK") for k in keys)
            lines.append(f"        {ty} {col['name']}" + (f" {mk}" if mk else ""))
        lines.append("    }")
    for i, ln in enumerate(lines):
        cells[(mm_start + i, rc + 1)] = ln
    end_row = mm_start + len(lines)

    INFO_END = 6 if img_rows else PER_BAND * STRIDE - 1

    def fmt(sheet_id):
        R = []
        def rng(r1, r2, c1, c2):
            return {"sheetId": sheet_id, "startRowIndex": r1, "endRowIndex": r2, "startColumnIndex": c1, "endColumnIndex": c2}
        def cell(r1, r2, c1, c2, uf, fields):
            R.append({"repeatCell": {"range": rng(r1, r2, c1, c2), "cell": {"userEnteredFormat": uf}, "fields": fields}})
        # base: top-align + wrap everywhere, then mono for mermaid
        cell(0, FORMATTED_ROWS, 0, REL_COL + 6, {"verticalAlignment": "TOP", "wrapStrategy": "WRAP"},
             "userEnteredFormat.verticalAlignment,userEnteredFormat.wrapStrategy")
        # header info block
        for i in range(6):
            R.append({"mergeCells": {"range": rng(i, i + 1, 0, 2), "mergeType": "MERGE_ALL"}})
            R.append({"mergeCells": {"range": rng(i, i + 1, 2, INFO_END), "mergeType": "MERGE_ALL"}})
        cell(0, 6, 0, 2, {"backgroundColor": NAVY, "textFormat": {"bold": True, "foregroundColor": WHITE}},
             "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat")
        cell(0, 6, 2, INFO_END, {"wrapStrategy": "OVERFLOW_CELL"}, "userEnteredFormat.wrapStrategy")
        for r in (7,):
            cell(r, r + 1, 0, 1, {"wrapStrategy": "OVERFLOW_CELL", "textFormat": {"bold": True}}, "userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat")
        cell(T0, T0 + 1, rc, rc + 1, {"wrapStrategy": "OVERFLOW_CELL", "textFormat": {"bold": True}}, "userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat")
        # entity boxes
        for (r0_, c0_, isview) in hdr_rows:
            R.append({"mergeCells": {"range": rng(r0_, r0_ + 1, c0_, c0_ + 3), "mergeType": "MERGE_ALL"}})
            cell(r0_, r0_ + 1, c0_, c0_ + 3,
                 {"backgroundColor": VIEW_BG if isview else {"red": 0.18, "green": 0.18, "blue": 0.2},
                  "textFormat": {"bold": True, "foregroundColor": WHITE}, "horizontalAlignment": "CENTER"},
                 "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment")
        for (r0_, c0_, h) in boxes:
            cell(r0_ + 1, r0_ + h, c0_, c0_ + 1, {"textFormat": {"bold": True}, "horizontalAlignment": "CENTER"},
                 "userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment")
            cell(r0_ + 1, r0_ + h, c0_ + 2, c0_ + 3, {"textFormat": {"foregroundColor": {"red": .4, "green": .4, "blue": .4}}},
                 "userEnteredFormat.textFormat")
            b = {"style": "SOLID_MEDIUM", "color": LINE}
            R.append({"updateBorders": {"range": rng(r0_, r0_ + h, c0_, c0_ + 3), "top": b, "bottom": b, "left": b, "right": b}})
            R.append({"updateBorders": {"range": rng(r0_ + 1, r0_ + 2, c0_, c0_ + 3),
                                        "top": {"style": "SOLID", "color": LINE}}})
            R.append({"updateBorders": {"range": rng(r0_ + 1, r0_ + h, c0_, c0_ + 1),
                                        "right": {"style": "SOLID", "color": LINE}}})
        for (r, c) in pk_cells:
            cell(r, r + 1, c, c + 1, {"textFormat": {"bold": True, "underline": True}},
                 "userEnteredFormat.textFormat")
        # right tables
        for (hr, n) in ((rel_hdr, 6), (obj_hdr, 6)):
            cell(hr, hr + 1, rc, rc + n, {"backgroundColor": NAVY, "textFormat": {"bold": True, "foregroundColor": WHITE},
                                          "horizontalAlignment": "CENTER"},
                 "userEnteredFormat.backgroundColor,userEnteredFormat.textFormat,userEnteredFormat.horizontalAlignment")
        cell(obj_hdr - 1, obj_hdr, rc, rc + 1, {"wrapStrategy": "OVERFLOW_CELL", "textFormat": {"bold": True}},
             "userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat")
        cell(mm_start - 1, mm_start, rc, rc + 1, {"wrapStrategy": "OVERFLOW_CELL", "textFormat": {"bold": True}},
             "userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat")
        cell(mm_start, end_row, rc + 1, rc + 2, {"wrapStrategy": "OVERFLOW_CELL",
                                                 "textFormat": {"fontFamily": "Roboto Mono", "fontSize": 9}},
             "userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat")
        # widths
        widths = []
        for _ in range(PER_BAND):
            widths += BOX_W + [SPACER_W]
        widths += [30]  # gap col (index PER_BAND*STRIDE) — REL_COL-1 handled below
        widths = [] if img_rows else widths[:REL_COL]
        for i, w in enumerate(widths):
            R.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                                                    "properties": {"pixelSize": w}, "fields": "pixelSize"}})
        for j, w in enumerate(REL_W):
            R.append({"updateDimensionProperties": {"range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": rc + j, "endIndex": rc + j + 1},
                                                    "properties": {"pixelSize": w}, "fields": "pixelSize"}})
        cell(7, 8, 0, 1, {"wrapStrategy": "OVERFLOW_CELL", "textFormat": {"bold": True}}, "userEnteredFormat.wrapStrategy,userEnteredFormat.textFormat")
        R.append({"updateSheetProperties": {"properties": {"sheetId": sheet_id, "gridProperties": {"hideGridlines": True}},
                                            "fields": "gridProperties.hideGridlines"}})
        return R
    return cells, fmt


def main():
    p = json.load(sys.stdin)
    sheets = sheets_service()
    sid = p["spreadsheet_id"]
    meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
    by_title = {s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]}
    by_id = {v: k for k, v in by_title.items()}
    mc_id = by_title[MC]

    er_col, inserted = ensure_er_column(sheets, sid, mc_id)
    rows = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A{FIRST}:Z2000").execute().get("values", [])
    bc = p["breadcrumb"].strip()
    row_idx = next((i for i, r in enumerate(rows) if len(r) > 1 and r[1].strip() == bc), None)
    if row_idx is None:
        print(json.dumps({"error": f"breadcrumb not found in Menu Contents: {bc}"}), file=sys.stderr); sys.exit(1)
    row = rows[row_idx]
    menu_row = FIRST + row_idx
    src_url = row[4] if len(row) > 4 else ""
    src_title = by_id.get(gid_of(src_url), "")
    p["source_tab_url"] = p.get("source_tab_url") or src_url
    er_cell = row[er_col] if len(row) > er_col else ""

    title = f"[ER] {src_title or 'menu'}"[:100]
    existing_gid = gid_of(er_cell)
    if existing_gid in by_id:
        title = by_id[existing_gid]
    sheet_id = by_title.get(title)
    action = "updated" if sheet_id is not None else "inserted"
    picture = None
    if p.get("no_image"):
        if sheet_id is None:
            sheet_id = sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
                {"addSheet": {"properties": {"title": title}}}]}).execute()["replies"][0]["addSheet"]["properties"]["sheetId"]
        else:
            full = {"sheetId": sheet_id}
            sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
                {"unmergeCells": {"range": full}},
                {"updateCells": {"range": full, "fields": "userEnteredValue,userEnteredFormat,userEnteredFormat.borders"}}]}).execute()
    else:
        # picture mode: render PNG, then er_insert_image builds the tab (replacing any old one) with the
        # picture floating at A9; the tables are written below it.
        import subprocess, tempfile
        here = os.path.dirname(os.path.abspath(__file__))
        tmp = tempfile.mkdtemp()
        pj, png = os.path.join(tmp, "payload.json"), os.path.join(tmp, "er.png")
        json.dump(p, open(pj, "w", encoding="utf-8"), ensure_ascii=False)
        subprocess.check_call([sys.executable, os.path.join(here, "er_render.py"), pj, png], stdout=subprocess.DEVNULL)
        res = json.loads(subprocess.check_output([sys.executable, os.path.join(here, "er_insert_image.py"),
                                                  sid, title, png, "--anchor-row", "9"]))
        sheet_id = res["tab_gid"]
        p["_img_rows"] = res["rows_reserved"]
        # the PNG itself is kept in <Group folder>/ER-Picture (not next to the spreadsheets)
        from er_upload_png import upload
        picture = upload(sid, title, png)

    cells, fmt = build_grid(p, src_title)
    maxr = max(r for r, _ in cells) + 1
    maxc = max(c for _, c in cells) + 1
    grid = [[""] * maxc for _ in range(maxr)]
    for (r, c), v in cells.items():
        grid[r][c] = v
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{title}'!A1", valueInputOption="USER_ENTERED",
                                          body={"values": grid}).execute()
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": fmt(sheet_id)}).execute()

    tab_url = f"https://docs.google.com/spreadsheets/d/{sid}/edit?gid={sheet_id}#gid={sheet_id}"
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{MC}'!{col_letter(er_col)}{menu_row}",
                                          valueInputOption="USER_ENTERED", body={"values": [[tab_url]]}).execute()
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{MC}'!B4", valueInputOption="USER_ENTERED",
                                          body={"values": [[p["today"]]]}).execute()
    print(json.dumps({"picture_url": (picture or {}).get("url"), "tab_gid": sheet_id, "tab_url": tab_url, "menu_row": menu_row, "er_column": col_letter(er_col),
                      "column_inserted": inserted, "action": action}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
