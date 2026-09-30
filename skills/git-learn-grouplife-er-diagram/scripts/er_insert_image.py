#!/usr/bin/env python3
"""Put an ER PNG into a Google Sheet as a FLOATING image over cells — fully automatic, private
(no public sharing, no Apps Script scope).

How: Sheets/Drive APIs cannot insert images directly, but Drive's xlsx->Google Sheets conversion keeps
images anchored to cells. So: (1) build a 1-tab .xlsx with the PNG anchored at A1 (openpyxl),
(2) upload it converted to a temporary Google Sheet, (3) spreadsheets.sheets.copyTo that tab into the
target spreadsheet, (4) rename it, (5) trash the temp file.

Usage: er_insert_image.py <spreadsheet_id> <tab_title> <png_path> [--width 1100] [--anchor-row 9]
  If a tab called <tab_title> already exists it is REPLACED (deleted, then the copy is renamed to it);
  new gid is returned — er_write.py finds the tab again by title and rewrites the link.
Prints JSON {tab_gid, tab_title, rows_reserved}.  rows_reserved = how many rows the picture covers at
default row height (21px) so later writers can start their tables below/right of it.
"""
import sys, os, json, math, tempfile
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service, drive_service
from googleapiclient.http import MediaFileUpload
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XImage
from PIL import Image


def main():
    argv = sys.argv[1:]
    opts = {}
    for k in ("--width", "--anchor-row"):
        if k in argv:
            i = argv.index(k); opts[k] = int(argv[i + 1]); del argv[i:i + 2]
    args = argv
    width = opts.get("--width", 1100)
    anchor_row = opts.get("--anchor-row", 9)
    sid, title, png = args[0], args[1], args[2]
    im = Image.open(png)
    w = min(width, im.width)
    h = int(im.height * w / im.width)

    tmpdir = tempfile.mkdtemp()
    xlsx = os.path.join(tmpdir, "er_img.xlsx")
    wb = Workbook(); ws = wb.active; ws.title = "img"
    xi = XImage(png); xi.width, xi.height = w, h
    ws.add_image(xi, f"A{anchor_row}")
    wb.save(xlsx)

    drive, sheets = drive_service(), sheets_service()
    tmp = drive.files().create(
        body={"name": "ZZ_tmp_er_image (auto-delete)", "mimeType": "application/vnd.google-apps.spreadsheet"},
        media_body=MediaFileUpload(xlsx, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
        fields="id").execute()["id"]
    try:
        src_gid = sheets.spreadsheets().get(spreadsheetId=tmp).execute()["sheets"][0]["properties"]["sheetId"]
        new = sheets.spreadsheets().sheets().copyTo(
            spreadsheetId=tmp, sheetId=src_gid, body={"destinationSpreadsheetId": sid}).execute()
        new_gid = new["sheetId"]
        meta = sheets.spreadsheets().get(spreadsheetId=sid).execute()
        reqs = []
        for s in meta["sheets"]:
            if s["properties"]["title"] == title and s["properties"]["sheetId"] != new_gid:
                reqs.append({"deleteSheet": {"sheetId": s["properties"]["sheetId"]}})
        reqs.append({"updateSheetProperties": {"properties": {"sheetId": new_gid, "title": title},
                                               "fields": "title"}})
        sheets.spreadsheets().batchUpdate(spreadsheetId=sid, body={"requests": reqs}).execute()
    finally:
        drive.files().update(fileId=tmp, body={"trashed": True}).execute()
    print(json.dumps({"tab_gid": new_gid, "tab_title": title, "rows_reserved": math.ceil(h / 21) + 2,
                      "image_px": [w, h]}))


if __name__ == "__main__":
    main()
