#!/usr/bin/env python3
"""Make sure EVERY repo (Group) folder under the Drive root "GroupLife by Claude AI"
(1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ) has an "ER-Picture" subfolder. Idempotent; creates only what's missing.
Usage: ensure_er_folders.py   -> JSON [{group, er_picture_id, created}]
(er_write.py also creates the folder lazily for the Group of the App it writes, so running this is optional —
 use it after a NEW repo folder appears, or to pre-create folders for every repo.)
"""
import sys, os, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import drive_service

ROOT = "1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ"
FOLDER = "application/vnd.google-apps.folder"


def main():
    d = drive_service()
    out = []
    groups = d.files().list(q=f"'{ROOT}' in parents and trashed=false and mimeType='{FOLDER}'",
                            fields="files(id,name)", pageSize=200).execute()["files"]
    for g in groups:
        ex = d.files().list(q=f"'{g['id']}' in parents and trashed=false and mimeType='{FOLDER}' and name='ER-Picture'",
                            fields="files(id)").execute()["files"]
        if ex:
            out.append({"group": g["name"], "er_picture_id": ex[0]["id"], "created": False})
        else:
            fid = d.files().create(body={"name": "ER-Picture", "mimeType": FOLDER, "parents": [g["id"]]}, fields="id").execute()["id"]
            out.append({"group": g["name"], "er_picture_id": fid, "created": True})
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
