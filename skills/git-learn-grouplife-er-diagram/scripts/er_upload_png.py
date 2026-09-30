#!/usr/bin/env python3
"""Store a generated ER PNG in the "ER-Picture" folder that lives INSIDE the repo (Group) folder
of the App's spreadsheet — never next to the spreadsheets themselves.

Drive layout:  GroupLife by Claude AI / <Group> / ER-Picture / [ER] <tab> (<AppName>).png
The <Group> folder = the parent of the App spreadsheet. "ER-Picture" is found by name inside it, or
created (once per Group folder). A file with the same name is OVERWRITTEN (new content, same file id),
so re-running a menu never piles up duplicates. The file is private (no sharing changes).

Usage: er_upload_png.py <spreadsheet_id> <tab_title> <png_path>
Prints JSON {folder_id, folder_created, file_id, file_name, url, action}.
Importable: upload(sid, tab_title, png_path) -> dict.
"""
import sys, os, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import drive_service
from googleapiclient.http import MediaFileUpload

FOLDER_NAME = "ER-Picture"
FOLDER_MIME = "application/vnd.google-apps.folder"


def _q(name):
    return name.replace("\\", "\\\\").replace("'", "\\'")


def upload(sid, tab_title, png_path):
    drive = drive_service()
    meta = drive.files().get(fileId=sid, fields="name,parents").execute()
    app_name, group_id = meta["name"], meta["parents"][0]

    r = drive.files().list(q=f"'{group_id}' in parents and trashed=false and mimeType='{FOLDER_MIME}' "
                             f"and name='{FOLDER_NAME}'", fields="files(id)").execute().get("files", [])
    created = not r
    folder_id = r[0]["id"] if r else drive.files().create(
        body={"name": FOLDER_NAME, "mimeType": FOLDER_MIME, "parents": [group_id]}, fields="id").execute()["id"]

    fname = f"{tab_title} ({app_name}).png"
    media = MediaFileUpload(png_path, mimetype="image/png")
    ex = drive.files().list(q=f"'{folder_id}' in parents and trashed=false and name='{_q(fname)}'",
                            fields="files(id)").execute().get("files", [])
    if ex:
        fid = ex[0]["id"]
        drive.files().update(fileId=fid, media_body=media).execute()
        action = "updated"
    else:
        fid = drive.files().create(body={"name": fname, "parents": [folder_id]}, media_body=media,
                                   fields="id").execute()["id"]
        action = "inserted"
    return {"folder_id": folder_id, "folder_created": created, "file_id": fid, "file_name": fname,
            "url": f"https://drive.google.com/file/d/{fid}/view", "action": action}


if __name__ == "__main__":
    print(json.dumps(upload(*sys.argv[1:4]), ensure_ascii=False, indent=2))
