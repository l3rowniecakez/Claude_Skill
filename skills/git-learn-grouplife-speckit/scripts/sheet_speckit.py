#!/usr/bin/env python3
"""Stamp SpecKit Drive URLs into the App's analyst spreadsheet ("Menu Contents" tab).

Two places (locked with the user 2026-10-20, see image example in SKILL.md):
  1. Column "SpecKit" in the table header (row 6), inserted to the RIGHT of "ER-Diagram" (if the ER column does not
     exist yet: right of "Sheet URL"). One cell per menu row = URL of that menu's SpecKit folder on Drive.
  2. Header block: a row labelled "Speckit URL" holding the App's SpecKit folder URL. The block is rows 1-4
     (โปรแกรม / Repo URL / Sub Folder / วันที่อัพเดท) + blank row 5 + table header row 6, and EVERY sibling skill
     (analyst sheet_write.py, er_write.py, read_menus.py) hard-codes "table header = row 6, data from row 7" — inserting a
     real row would shift the table and break them. So the label goes into the existing BLANK row 5 (A5="Speckit URL",
     B5=<folder url>), styled like A1:A4. If A5 already holds something else the script stops and writes nothing.

Usage:
  sheet_speckit.py header <spreadsheet_id> <app_folder_url> <today>
  sheet_speckit.py menu   <spreadsheet_id> <breadcrumb> <speckit_folder_url> <today>
      breadcrumb must equal the "เมนูงาน" cell (column B) of the menu row EXACTLY.
  sheet_speckit.py menus  <spreadsheet_id> <today>      (JSON [{"breadcrumb","url"},...] on stdin; one batch)

Writes ONLY: the "SpecKit" column (header cell + url cells), A5/B5, and B4 (date). Never touches analysis tabs,
never touches the ER-Diagram column. Never run two writers against the same spreadsheet at the same time.
"""
import sys, os, re, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service

MC = "Menu Contents"
FIRST = 7                       # first data row of Menu Contents
LABEL = "Speckit URL"
HEADER = "SpecKit"
WIDTH = 250


def col_letter(i):
    s, i = "", i + 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def mc_sheet_id(sheets, sid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties(sheetId,title)").execute()
    mc = next((s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == MC), None)
    if mc is None:
        raise SystemExit(f"no '{MC}' tab in {sid} — run /git-learn-grouplife-system-analyst for this App first")
    return mc


def header_row(sheets, sid):
    h = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A6:Z6").execute().get("values", [[]])
    return h[0] if h else []


def ensure_speckit_column(sheets, sid, mc_id):
    """Returns (column_index, inserted_now)."""
    hdr = header_row(sheets, sid)
    for i, h in enumerate(hdr):
        if str(h).strip().lower() == HEADER.lower():
            return i, False
    find = lambda name: next((i for i, h in enumerate(hdr) if str(h).strip() == name), None)
    anchor = find("ER-Diagram")
    if anchor is None:
        anchor = find("Sheet URL")
    if anchor is None:
        raise SystemExit("Menu Contents row 6 has neither 'ER-Diagram' nor 'Sheet URL' header — unexpected layout, nothing written")
    new = anchor + 1
    reqs = [
        {"insertDimension": {"range": {"sheetId": mc_id, "dimension": "COLUMNS", "startIndex": new, "endIndex": new + 1},
                             "inheritFromBefore": True}},
        # header style (navy, white bold, centered) + wrap/top alignment down the whole column, copied from the anchor column
        {"copyPaste": {"source": {"sheetId": mc_id, "startRowIndex": 0, "endRowIndex": 2000,
                                  "startColumnIndex": anchor, "endColumnIndex": anchor + 1},
                       "destination": {"sheetId": mc_id, "startRowIndex": 0, "endRowIndex": 2000,
                                       "startColumnIndex": new, "endColumnIndex": new + 1},
                       "pasteType": "PASTE_FORMAT"}},
        {"updateDimensionProperties": {"range": {"sheetId": mc_id, "dimension": "COLUMNS", "startIndex": new, "endIndex": new + 1},
                                       "properties": {"pixelSize": WIDTH}, "fields": "pixelSize"}},
    ]
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": reqs}).execute()
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{MC}'!{col_letter(new)}6",
                                          valueInputOption="USER_ENTERED", body={"values": [[HEADER]]}).execute()
    return new, True


def set_date(sheets, sid, today):
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{MC}'!B4", valueInputOption="USER_ENTERED",
                                          body={"values": [[today]]}).execute()


def read_rows(sheets, sid):
    return sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A{FIRST}:Z2000").execute().get("values", [])


def write_header(sheets, sid, url, today):
    mc_id = mc_sheet_id(sheets, sid)
    cur = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A5:B5").execute().get("values", [[]])
    cur = cur[0] if cur else []
    a5 = str(cur[0]).strip() if cur else ""
    if a5 and a5 != LABEL:
        raise SystemExit(f"A5 already holds '{a5}' (not '{LABEL}') — refusing to overwrite; nothing written")
    sheets.spreadsheets().values().update(spreadsheetId=sid, range=f"'{MC}'!A5:B5", valueInputOption="USER_ENTERED",
                                          body={"values": [[LABEL, url]]}).execute()
    # label cell styled exactly like the other label cells (A4), value cell like B3 (wrap/top)
    sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": [
        {"copyPaste": {"source": {"sheetId": mc_id, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": 0, "endColumnIndex": 1},
                       "destination": {"sheetId": mc_id, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 0, "endColumnIndex": 1},
                       "pasteType": "PASTE_FORMAT"}},
        {"copyPaste": {"source": {"sheetId": mc_id, "startRowIndex": 2, "endRowIndex": 3, "startColumnIndex": 1, "endColumnIndex": 2},
                       "destination": {"sheetId": mc_id, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": 1, "endColumnIndex": 2},
                       "pasteType": "PASTE_FORMAT"}},
    ]}).execute()
    set_date(sheets, sid, today)
    return {"label_cell": "A5", "url_cell": "B5", "url": url}


def write_menus(sheets, sid, items, today):
    mc_id = mc_sheet_id(sheets, sid)
    col, inserted = ensure_speckit_column(sheets, sid, mc_id)
    rows = read_rows(sheets, sid)
    by_bc = {}
    for i, r in enumerate(rows):
        if len(r) > 1 and str(r[1]).strip():
            by_bc.setdefault(r[1].strip(), i)
    data, missing, written = [], [], []
    for it in items:
        bc = it["breadcrumb"].strip()
        i = by_bc.get(bc)
        if i is None:
            missing.append(bc); continue
        row = FIRST + i
        data.append({"range": f"'{MC}'!{col_letter(col)}{row}", "values": [[it["url"]]]})
        written.append({"row": row, "breadcrumb": bc, "url": it["url"]})
    if data:
        sheets.spreadsheets().values().batchUpdate(spreadsheetId=sid, body={"valueInputOption": "USER_ENTERED", "data": data}).execute()
        set_date(sheets, sid, today)
    return {"speckit_column": col_letter(col), "column_inserted": inserted, "written": written, "breadcrumb_not_found": missing}


def main():
    a = sys.argv[1:]
    sheets = sheets_service()
    if len(a) == 4 and a[0] == "header":
        out = write_header(sheets, a[1], a[2], a[3])
    elif len(a) == 5 and a[0] == "menu":
        out = write_menus(sheets, a[1], [{"breadcrumb": a[2], "url": a[3]}], a[4])
    elif len(a) == 3 and a[0] == "menus":
        out = write_menus(sheets, a[1], json.load(sys.stdin), a[2])
    else:
        print(__doc__); sys.exit(1)
    if out.get("breadcrumb_not_found"):
        print(json.dumps(out, ensure_ascii=False, indent=2)); sys.exit(2)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
