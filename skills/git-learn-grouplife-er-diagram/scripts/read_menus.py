#!/usr/bin/env python3
"""List the analyzed menus of an App spreadsheet ("Menu Contents" tab, header row 6, data from row 7)
and, for one menu, dump the source analysis tab (Component/Event/DB/Call Store rows).

Usage:
  read_menus.py list <spreadsheet_id>
      -> JSON {program_name, repo_url, sub_folder, menus:[{row, no, breadcrumb, description,
         delphi_path_file, sheet_url, gid, tab_title, er_url}]}
         (er_url = value of the "ER-Diagram" column if that column exists, else "")
  read_menus.py tab <spreadsheet_id> <gid>
      -> JSON {tab_title, header:{...rows 1-6 label:value}, rows:[{component, description, caption,
         event, db, call_store}], manual_steps:[...]}
Read-only.
"""
import sys, os, re, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service

MC = "Menu Contents"


def gid_of(url):
    m = re.search(r"gid=(\d+)", url or "")
    return int(m.group(1)) if m else None


def cmd_list(sheets, sid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
    titles = {s["properties"]["sheetId"]: s["properties"]["title"] for s in meta["sheets"]}
    vals = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A1:Z2000").execute().get("values", [])
    g = lambda r, c: (vals[r][c] if r < len(vals) and c < len(vals[r]) else "")
    hdr = vals[5] if len(vals) > 5 else []
    er_col = next((i for i, h in enumerate(hdr) if str(h).strip() == "ER-Diagram"), None)
    menus = []
    for i in range(6, len(vals)):
        row = vals[i]
        if len(row) < 2 or not str(row[1]).strip():
            continue
        url = row[4] if len(row) > 4 else ""
        gid = gid_of(url)
        menus.append({
            "row": i + 1, "no": row[0], "breadcrumb": row[1].strip(),
            "description": row[2] if len(row) > 2 else "",
            "delphi_path_file": row[3] if len(row) > 3 else "",
            "sheet_url": url, "gid": gid, "tab_title": titles.get(gid, ""),
            "er_url": (row[er_col] if er_col is not None and len(row) > er_col else ""),
        })
    print(json.dumps({"program_name": g(0, 1), "repo_url": g(1, 1), "sub_folder": g(2, 1), "menus": menus},
                     ensure_ascii=False, indent=2))


def cmd_tab(sheets, sid, gid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
    title = next(s["properties"]["title"] for s in meta["sheets"] if s["properties"]["sheetId"] == int(gid))
    vals = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{title}'!A1:Z2000").execute().get("values", [])
    header = {str(r[0]): (r[1] if len(r) > 1 else "") for r in vals[:6] if r}
    rows, steps, mode = [], [], "hdr"
    for r in vals[6:]:
        if not r:
            continue
        if r[0] == "Component Name":
            mode = "rows"; continue
        if str(r[0]).startswith("ขั้นตอนการใช้งาน"):
            mode = "steps"; continue
        if mode == "rows":
            r = list(r) + [""] * 6
            rows.append({"component": r[0], "description": r[1], "caption": r[2], "event": r[3],
                         "db": r[4], "call_store": r[5]})
        elif mode == "steps":
            steps.append(r[0])
    print(json.dumps({"tab_title": title, "header": header, "rows": rows, "manual_steps": steps},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sheets = sheets_service()
    if len(sys.argv) >= 3 and sys.argv[1] == "list":
        cmd_list(sheets, sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "tab":
        cmd_tab(sheets, sys.argv[2], sys.argv[3])
    else:
        print(__doc__); sys.exit(1)
