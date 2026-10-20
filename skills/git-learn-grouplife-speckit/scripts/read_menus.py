#!/usr/bin/env python3
"""List the analyzed menus of an App spreadsheet ("Menu Contents" tab, header row 6, data from row 7)
and, for one menu, dump the source analysis tab (Component/Event/DB/Call Store rows).

Usage:
  read_menus.py list <spreadsheet_id>
      -> JSON {program_name, repo_url, sub_folder, speckit_header_url, menus:[{row, no, breadcrumb, description,
         delphi_path_file, sheet_url, gid, tab_title, er_url, er_gid, speckit_url, is_child, parent_row,
         child_rows, descendant_rows, external_spreadsheet_id}]}
         - er_url / speckit_url = value of the "ER-Diagram" / "SpecKit" column if present, else ""
         - is_child = this row is a child-form row written by the analyst's Phase 5.5, i.e. its breadcrumb is
           "<parent breadcrumb> => [ปุ่ม: ...] <form>" — it is one more SCREEN of the parent menu
         - external_spreadsheet_id = non-empty when the row is a WinExec stamp pointing into ANOTHER App's spreadsheet
         - speckit_header_url = value of header row 5 "Speckit URL" (B5) if already stamped
  read_menus.py tab <spreadsheet_id> <gid>
      -> JSON {tab_title, header:{...rows 1-6 label:value}, rows:[{component, description, caption,
         event, db, call_store}], manual_steps:[...]}
  read_menus.py er <spreadsheet_id> <gid>
      -> JSON {tab_title, cells:[[...],...]}  raw text of the "[ER] ..." tab (all non-empty rows, A1:Z2000)
Read-only.
"""
import sys, os, re, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service

MC = "Menu Contents"
CHILD_MARK = " => [ปุ่ม:"


def gid_of(url):
    m = re.search(r"gid=(\d+)", url or "")
    return int(m.group(1)) if m else None


def sid_of(url):
    m = re.search(r"/d/([A-Za-z0-9_-]+)", url or "")
    return m.group(1) if m else None


def link_children(menus):
    for m in menus:
        m.update(is_child=False, parent_row=None, child_rows=[], descendant_rows=[])
    for m in menus:
        best = None
        for p in menus:
            if p is not m and m["breadcrumb"].startswith(p["breadcrumb"] + CHILD_MARK):
                if best is None or len(p["breadcrumb"]) > len(best["breadcrumb"]):
                    best = p
        if best:
            m["is_child"], m["parent_row"] = True, best["row"]
            best["child_rows"].append(m["row"])
    by_row = {m["row"]: m for m in menus}

    def walk(m):
        out = []
        for r in m["child_rows"]:
            out.append(r)
            out += walk(by_row[r])
        return out
    for m in menus:
        m["descendant_rows"] = walk(m)


def cmd_list(sheets, sid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
    titles = {s["properties"]["sheetId"]: s["properties"]["title"] for s in meta["sheets"]}
    vals = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A1:Z2000").execute().get("values", [])
    g = lambda r, c: (vals[r][c] if r < len(vals) and c < len(vals[r]) else "")
    hdr = vals[5] if len(vals) > 5 else []
    col = lambda name: next((i for i, h in enumerate(hdr) if str(h).strip().lower() == name.lower()), None)
    er_col, sk_col = col("ER-Diagram"), col("SpecKit")
    menus = []
    for i in range(6, len(vals)):
        row = vals[i]
        if len(row) < 2 or not str(row[1]).strip():
            continue
        url = row[4] if len(row) > 4 else ""
        gid = gid_of(url)
        ext = sid_of(url)
        er_url = row[er_col] if er_col is not None and len(row) > er_col else ""
        menus.append({
            "row": i + 1, "no": row[0], "breadcrumb": row[1].strip(),
            "description": row[2] if len(row) > 2 else "",
            "delphi_path_file": row[3] if len(row) > 3 else "",
            "sheet_url": url, "gid": gid, "tab_title": titles.get(gid, ""),
            "er_url": er_url, "er_gid": gid_of(er_url),
            "speckit_url": (row[sk_col] if sk_col is not None and len(row) > sk_col else ""),
            "external_spreadsheet_id": (ext if ext and ext != sid and str(row[3] if len(row) > 3 else "").startswith("WinExec") else ""),
        })
    link_children(menus)
    hdr_label = str(g(4, 0)).strip()
    print(json.dumps({"program_name": g(0, 1), "repo_url": g(1, 1), "sub_folder": g(2, 1),
                      "speckit_header_url": g(4, 1) if hdr_label == "Speckit URL" else "", "menus": menus},
                     ensure_ascii=False, indent=2))


def title_of(sheets, sid, gid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
    return next(s["properties"]["title"] for s in meta["sheets"] if s["properties"]["sheetId"] == int(gid))


def cmd_tab(sheets, sid, gid):
    title = title_of(sheets, sid, gid)
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


def cmd_er(sheets, sid, gid):
    title = title_of(sheets, sid, gid)
    vals = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{title}'!A1:Z2000").execute().get("values", [])
    cells = [[str(c) for c in r] for r in vals if any(str(c).strip() for c in r)]
    print(json.dumps({"tab_title": title, "cells": cells}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    sheets = sheets_service()
    if len(sys.argv) >= 3 and sys.argv[1] == "list":
        cmd_list(sheets, sys.argv[2])
    elif len(sys.argv) >= 4 and sys.argv[1] == "tab":
        cmd_tab(sheets, sys.argv[2], sys.argv[3])
    elif len(sys.argv) >= 4 and sys.argv[1] == "er":
        cmd_er(sheets, sys.argv[2], sys.argv[3])
    else:
        print(__doc__); sys.exit(1)
