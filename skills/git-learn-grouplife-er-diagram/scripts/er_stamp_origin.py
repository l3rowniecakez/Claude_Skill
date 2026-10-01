#!/usr/bin/env python3
"""Stamp the ER link of an App back onto the ORIGIN App's "Menu Contents" (column "ER-Diagram").

Why: an external-program menu (WinExec -> another exe) has NO detail tab in the origin App's spreadsheet. The analyst
skill already stamps a row there whose "Sheet URL" points to the external App's own spreadsheet. After this ER skill
writes the ER tab into that external App's spreadsheet (er_write.py), the origin row must also show the ER link, so
whoever opens the origin Menu Contents can reach the ER without hunting through the other file.

Usage:
  er_stamp_origin.py <origin_spreadsheet_id> <app_spreadsheet_id> [--dry]

How rows are matched (no guessing from names):
  An origin data row (row 7+) matches when its "Sheet URL" cell contains "/d/<app_spreadsheet_id>/".
  If that URL carries a gid, it is matched to the App menu whose "Sheet URL" has the same gid; otherwise, if the App has
  exactly one menu with an ER link, that link is used. Rows that cannot be matched are reported, never guessed.

What it writes: ONLY the "ER-Diagram" cell of the matched origin rows (same style as er_write.py: URL text + hyperlink).
  - Inserts the "ER-Diagram" column in the origin sheet if it does not exist yet (same helper as er_write.py).
  - Overwrites a cell only when its value differs (er_write.py replaces the ER tab, so the gid changes on a re-run and an
    old link goes stale — re-run this script after every er_write.py of an external App).
  - Never touches any other cell or tab. Prints one line per row; exit code 0 even when nothing matched (it says so).
Never run concurrently for the same origin spreadsheet.
"""
import sys, os, re, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service
from er_write import ensure_er_column, col_letter, MC, FIRST


def gid_of(url):
    m = re.search(r"gid=(\d+)", url or "")
    return int(m.group(1)) if m else None


def read_mc(sheets, sid):
    meta = sheets.spreadsheets().get(spreadsheetId=sid, fields="sheets.properties(sheetId,title)").execute()
    mc_id = next((s["properties"]["sheetId"] for s in meta["sheets"] if s["properties"]["title"] == MC), None)
    if mc_id is None:
        raise SystemExit(f"no '{MC}' tab in {sid}")
    vals = sheets.spreadsheets().values().get(spreadsheetId=sid, range=f"'{MC}'!A1:Z2000").execute().get("values", [])
    hdr = vals[5] if len(vals) > 5 else []
    idx = lambda name: next((i for i, h in enumerate(hdr) if str(h).strip() == name), None)
    return mc_id, vals, idx("Sheet URL"), idx("ER-Diagram")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv
    if len(args) != 2:
        print(__doc__); sys.exit(1)
    origin, app = args
    if origin == app:
        raise SystemExit("origin and app are the same spreadsheet — nothing to stamp")
    sheets = sheets_service()

    # 1) ER links available in the external App
    _, avals, a_url, a_er = read_mc(sheets, app)
    if a_er is None:
        print("App has no ER-Diagram column yet — run er_write.py for it first"); return
    app_menus = []
    for r in avals[FIRST - 1:]:
        if len(r) > 1 and str(r[1]).strip():
            url = r[a_url] if a_url is not None and len(r) > a_url else ""
            er = r[a_er] if len(r) > a_er else ""
            if er.strip():
                app_menus.append({"gid": gid_of(url), "er": er.strip()})
    if not app_menus:
        print("App has no ER link yet — nothing to stamp"); return

    # 2) matching rows in the origin
    o_id, ovals, o_url, o_er = read_mc(sheets, origin)
    if o_url is None:
        raise SystemExit("origin Menu Contents has no 'Sheet URL' header")
    rows = []
    for i in range(FIRST - 1, len(ovals)):
        r = ovals[i]
        url = r[o_url] if len(r) > o_url else ""
        if f"/d/{app}/" in url:
            rows.append((i, url))
    if not rows:
        print(f"no row in origin links to app {app} — nothing to stamp"); return

    created_col = False
    if o_er is None and not dry:
        o_er, created_col = ensure_er_column(sheets, origin, o_id)
        # column inserted to the right of "Sheet URL" => re-read so values line up
        _, ovals, o_url, o_er = read_mc(sheets, origin)
    reqs = []
    for i, url in rows:
        g = gid_of(url)
        er = next((m["er"] for m in app_menus if g is not None and m["gid"] == g), None)
        if er is None and len(app_menus) == 1:
            er = app_menus[0]["er"]
        if er is None:
            print(f"row {i + 1}: cannot match gid {g} to an App menu with ER — skipped"); continue
        cur = ovals[i][o_er] if o_er is not None and len(ovals[i]) > o_er else ""
        if cur.strip() == er:
            print(f"row {i + 1}: unchanged"); continue
        print(f"row {i + 1}: {'would set' if dry else 'set'} ER-Diagram" + (f" (was: {cur[:40]})" if cur.strip() else ""))
        if o_er is not None:
            reqs.append({"updateCells": {
                "range": {"sheetId": o_id, "startRowIndex": i, "endRowIndex": i + 1,
                          "startColumnIndex": o_er, "endColumnIndex": o_er + 1},
                "rows": [{"values": [{"userEnteredValue": {"stringValue": er},
                                      "userEnteredFormat": {"textFormat": {"link": {"uri": er}}}}]}],
                "fields": "userEnteredValue,userEnteredFormat.textFormat.link"}})
    if reqs and not dry:
        sheets.spreadsheets().batchUpdate(spreadsheetId=origin, body={"requests": reqs}).execute()
    print(json.dumps({"origin": origin, "app": app, "rows_matched": len(rows), "rows_written": len(reqs) if not dry else 0,
                      "column_inserted": created_col, "er_column": col_letter(o_er) if o_er is not None else None}))


if __name__ == "__main__":
    main()
