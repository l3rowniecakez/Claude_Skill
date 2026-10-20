#!/usr/bin/env python3
"""Stamp the SpecKit link of an external App back onto the ORIGIN App's "Menu Contents" (column "SpecKit").

Same situation as the ER skill's er_stamp_origin.py: a menu that only WinExec's another standalone program has NO detail tab
in the origin App's spreadsheet — the analyst skill stamped a row there whose "Sheet URL" points into the external App's own
spreadsheet. After SpecKit is generated for that external App, the origin row must show the SpecKit link too.

Usage: speckit_stamp_origin.py <origin_spreadsheet_id> <app_spreadsheet_id> <today> [--dry]

Matching (no guessing from names): an origin data row (row 7+) matches when its "Sheet URL" contains "/d/<app_spreadsheet_id>/".
If that URL carries a gid it is matched to the App menu whose "Sheet URL" has the same gid; otherwise, if the App has exactly
one menu with a SpecKit link, that link is used. Rows that cannot be matched are reported, never guessed.
Writes ONLY the "SpecKit" cell of the matched origin rows (+ inserts the column / updates B4 when needed). Overwrites a cell
only when its value differs. Never run concurrently for the same origin spreadsheet.
"""
import sys, os, re, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service
from sheet_speckit import MC, FIRST, HEADER, col_letter, mc_sheet_id, ensure_speckit_column, set_date


def gid_of(url):
    m = re.search(r"gid=(\d+)", url or "")
    return int(m.group(1)) if m else None


def read_mc(sheets, sid):
    vals = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A1:Z2000").execute().get("values", [])
    hdr = vals[5] if len(vals) > 5 else []
    idx = lambda name: next((i for i, h in enumerate(hdr) if str(h).strip().lower() == name.lower()), None)
    return vals, idx("Sheet URL"), idx(HEADER)


def main():
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    dry = "--dry" in sys.argv
    if len(args) != 3:
        print(__doc__); sys.exit(1)
    origin, app, today = args
    if origin == app:
        raise SystemExit("origin and app are the same spreadsheet — nothing to stamp")
    sheets = sheets_service()

    avals, a_url, a_sk = read_mc(sheets, app)
    if a_sk is None:
        print("App has no SpecKit column yet — generate SpecKit for it first"); return
    app_menus = []
    for r in avals[FIRST - 1:]:
        if len(r) > 1 and str(r[1]).strip():
            url = r[a_url] if a_url is not None and len(r) > a_url else ""
            sk = r[a_sk] if len(r) > a_sk else ""
            if sk.strip():
                app_menus.append({"gid": gid_of(url), "sk": sk.strip()})
    if not app_menus:
        print("App has no SpecKit link yet — nothing to stamp"); return

    ovals, o_url, o_sk = read_mc(sheets, origin)
    if o_url is None:
        raise SystemExit("origin Menu Contents has no 'Sheet URL' header")
    rows = [(i, ovals[i][o_url]) for i in range(FIRST - 1, len(ovals))
            if len(ovals[i]) > o_url and f"/d/{app}/" in ovals[i][o_url]]
    if not rows:
        print(f"no row in origin links to app {app} — nothing to stamp"); return

    created_col = False
    if o_sk is None and not dry:
        o_id = mc_sheet_id(sheets, origin)
        o_sk, created_col = ensure_speckit_column(sheets, origin, o_id)
        ovals, o_url, o_sk = read_mc(sheets, origin)
    data = []
    for i, url in rows:
        g = gid_of(url)
        sk = next((m["sk"] for m in app_menus if g is not None and m["gid"] == g), None)
        if sk is None and len(app_menus) == 1:
            sk = app_menus[0]["sk"]
        if sk is None:
            print(f"row {i + 1}: cannot match gid {g} to an App menu with SpecKit — skipped"); continue
        cur = ovals[i][o_sk] if o_sk is not None and len(ovals[i]) > o_sk else ""
        if cur.strip() == sk:
            print(f"row {i + 1}: unchanged"); continue
        print(f"row {i + 1}: {'would set' if dry else 'set'} SpecKit" + (f" (was: {cur[:40]})" if cur.strip() else ""))
        if o_sk is not None:
            data.append({"range": f"'{MC}'!{col_letter(o_sk)}{i + 1}", "values": [[sk]]})
    if data and not dry:
        sheets.spreadsheets().values().batchUpdate(spreadsheetId=origin, body={"valueInputOption": "USER_ENTERED", "data": data}).execute()
        set_date(sheets, origin, today)
    print(json.dumps({"origin": origin, "app": app, "rows_matched": len(rows), "rows_written": 0 if dry else len(data),
                      "column_inserted": created_col, "speckit_column": col_letter(o_sk) if o_sk is not None else None}))


if __name__ == "__main__":
    main()
