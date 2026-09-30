#!/usr/bin/env python3
"""Find the per-App analysis spreadsheet(s) written by /git-learn-grouplife-system-analyst
under the Drive root "GroupLife by Claude AI" (id 1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ).
Layout there is <ROOT>/<Group>/<AppName> (one spreadsheet per App).

Usage: find_app_sheet.py <keyword>      (case-insensitive substring of AppName; "" = list all)
Prints JSON list: [{group, name, spreadsheet_id, url}]. Read-only.
"""
import sys, os, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import drive_service

ROOT_FOLDER_ID = "1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ"


def list_children(drive, parent):
    out, token = [], None
    while True:
        r = drive.files().list(q=f"'{parent}' in parents and trashed = false",
                               fields="nextPageToken, files(id,name,mimeType)", pageSize=200,
                               pageToken=token).execute()
        out += r.get("files", [])
        token = r.get("nextPageToken")
        if not token:
            return out


def main():
    kw = (sys.argv[1] if len(sys.argv) > 1 else "").strip().lower()
    drive = drive_service()
    found = []
    for grp in list_children(drive, ROOT_FOLDER_ID):
        if grp["mimeType"] == "application/vnd.google-apps.folder":
            for f in list_children(drive, grp["id"]):
                if f["mimeType"] == "application/vnd.google-apps.spreadsheet" and kw in f["name"].lower():
                    found.append({"group": grp["name"], "name": f["name"], "spreadsheet_id": f["id"],
                                  "url": f"https://docs.google.com/spreadsheets/d/{f['id']}/edit"})
        elif grp["mimeType"] == "application/vnd.google-apps.spreadsheet" and kw in grp["name"].lower():
            found.append({"group": "", "name": grp["name"], "spreadsheet_id": grp["id"],
                          "url": f"https://docs.google.com/spreadsheets/d/{grp['id']}/edit"})
    print(json.dumps(found, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
