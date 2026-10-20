#!/usr/bin/env python3
"""Drive operations for /git-learn-grouplife-speckit.

Destination root (locked with the user 2026-10-20): Drive folder "GroupLife SpecKit by Claude AI"
(id 1MHYE71oBUdH70DwdoIP-n1CQ_nzvrSfL). Layout:

  <ROOT>/<Group>/<AppName>/                      <- App folder  ("Speckit URL" in the Sheet header, B5)
      constitution.md                            <- once per App
      <NNN>-<TabTitle>/                          <- one folder per menu ("SpecKit" column in Menu Contents)
          req/REQ_<SCR-ID>_<Form>.md             <- one file per screen
          spec.md plan.md research.md data-model.md quickstart.md tasks.md analysis.md
          contracts/ checklists/ ...

<Group> / <AppName> are the SAME names the analyst skill used for its spreadsheet (the Drive folder that holds the
App's spreadsheet, and the spreadsheet's name) so the two trees mirror each other.

Usage:
  speckit_drive.py ensure-app <group> <app_name>
      -> {group_folder_id, app_folder_id, app_folder_url, created:{group,app}}   (idempotent, creates only what is missing)
  speckit_drive.py ensure-feature <app_folder_id> <feature_dir_name>
      -> {feature_folder_id, feature_folder_url, created}                        (empty folder; reused if it exists)
  speckit_drive.py download <folder_id> <file_name> <dest_path>
      -> {found, saved_to, bytes}   (used to restore constitution.md of an App on a machine that has no workspace yet)
  speckit_drive.py upload <parent_folder_id> <local_path> [--as-folder <name>]
      local_path = a FILE  -> uploaded into <parent_folder_id> (same name => content replaced, no duplicate)
      local_path = a DIR   -> its CONTENT is mirrored into <parent_folder_id> (or into a sub folder <name> with --as-folder),
                             recursively, creating sub folders as needed; same-named files are updated in place.
      -> {folder_id, folder_url, created:[...], updated:[...], stale:[...]}
         stale = files that exist on Drive under that folder but not locally (reported ONLY, never deleted).
Never deletes anything. Never touches anything outside <ROOT>.
"""
import sys, os, json, mimetypes
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import drive_service
from googleapiclient.http import MediaFileUpload

ROOT_FOLDER_ID = "1MHYE71oBUdH70DwdoIP-n1CQ_nzvrSfL"
FOLDER = "application/vnd.google-apps.folder"
SKIP = {".DS_Store", "Thumbs.db"}
MIME = {".md": "text/markdown", ".json": "application/json", ".txt": "text/plain", ".yml": "text/plain",
        ".yaml": "text/plain", ".sql": "text/plain"}
_KW = dict(supportsAllDrives=True)


def esc(name):
    return name.replace("\\", "\\\\").replace("'", "\\'")


def folder_url(fid):
    return f"https://drive.google.com/drive/folders/{fid}"


def find_child(d, parent, name, mime=None):
    q = f"'{parent}' in parents and trashed = false and name = '{esc(name)}'"
    if mime:
        q += f" and mimeType = '{mime}'"
    r = d.files().list(q=q, fields="files(id,name,mimeType)", pageSize=10, includeItemsFromAllDrives=True, **_KW).execute()
    files = r.get("files", [])
    if mime is None:
        files = [f for f in files if f["mimeType"] != FOLDER] or files
    return files[0] if files else None


def list_children(d, parent):
    out, token = [], None
    while True:
        r = d.files().list(q=f"'{parent}' in parents and trashed = false", fields="nextPageToken, files(id,name,mimeType)",
                           pageSize=200, pageToken=token, includeItemsFromAllDrives=True, **_KW).execute()
        out += r.get("files", [])
        token = r.get("nextPageToken")
        if not token:
            return out


def ensure_folder(d, parent, name):
    f = find_child(d, parent, name, FOLDER)
    if f:
        return f["id"], False
    c = d.files().create(body={"name": name, "mimeType": FOLDER, "parents": [parent]}, fields="id", **_KW).execute()
    return c["id"], True


def upload_file(d, parent, path):
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    mime = MIME.get(ext) or mimetypes.guess_type(name)[0] or "application/octet-stream"
    media = MediaFileUpload(path, mimetype=mime, resumable=False)
    ex = find_child(d, parent, name)
    if ex and ex["mimeType"] != FOLDER:
        d.files().update(fileId=ex["id"], media_body=media, fields="id", **_KW).execute()
        return ex["id"], False
    c = d.files().create(body={"name": name, "parents": [parent]}, media_body=media, fields="id", **_KW).execute()
    return c["id"], True


def mirror_dir(d, parent, local_dir, rel="", res=None):
    res = res if res is not None else {"created": [], "updated": [], "seen": set()}
    names = sorted(os.listdir(local_dir))
    for n in names:
        p = os.path.join(local_dir, n)
        if n in SKIP:
            continue
        r = f"{rel}{n}"
        if os.path.isdir(p):
            fid, _ = ensure_folder(d, parent, n)
            mirror_dir(d, fid, p, r + "/", res)
        else:
            _, made = upload_file(d, parent, p)
            (res["created"] if made else res["updated"]).append(r)
            res["seen"].add(r)
    return res


def list_all(d, parent, rel=""):
    out = []
    for c in list_children(d, parent):
        if c["mimeType"] == FOLDER:
            out += list_all(d, c["id"], f"{rel}{c['name']}/")
        else:
            out.append(f"{rel}{c['name']}")
    return out


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); sys.exit(1)
    d = drive_service()
    cmd = a[0]
    if cmd == "ensure-app" and len(a) == 3:
        gid, g_new = ensure_folder(d, ROOT_FOLDER_ID, a[1])
        aid, a_new = ensure_folder(d, gid, a[2])
        print(json.dumps({"group_folder_id": gid, "app_folder_id": aid, "app_folder_url": folder_url(aid),
                          "created": {"group": g_new, "app": a_new}}, ensure_ascii=False, indent=2))
    elif cmd == "ensure-feature" and len(a) == 3:
        fid, new = ensure_folder(d, a[1], a[2])
        print(json.dumps({"feature_folder_id": fid, "feature_folder_url": folder_url(fid), "created": new},
                         ensure_ascii=False, indent=2))
    elif cmd == "download" and len(a) == 4:
        f = find_child(d, a[1], a[2])
        if not f or f["mimeType"] == FOLDER:
            print(json.dumps({"found": False}))
        else:
            data = d.files().get_media(fileId=f["id"], supportsAllDrives=True).execute()
            os.makedirs(os.path.dirname(os.path.abspath(a[3])), exist_ok=True)
            with open(a[3], "wb") as fh:
                fh.write(data)
            print(json.dumps({"found": True, "file_id": f["id"], "saved_to": a[3], "bytes": len(data)}))
    elif cmd == "upload" and len(a) >= 3:
        parent, local = a[1], a[2]
        as_folder = a[a.index("--as-folder") + 1] if "--as-folder" in a else None
        if os.path.isdir(local):
            target = parent
            if as_folder:
                target, _ = ensure_folder(d, parent, as_folder)
            res = mirror_dir(d, target, local)
            stale = sorted(set(list_all(d, target)) - res["seen"])
            print(json.dumps({"folder_id": target, "folder_url": folder_url(target), "created": res["created"],
                              "updated": res["updated"], "stale": stale}, ensure_ascii=False, indent=2))
        else:
            fid, made = upload_file(d, parent, local)
            print(json.dumps({"folder_id": parent, "folder_url": folder_url(parent), "file_id": fid,
                              "created": [os.path.basename(local)] if made else [],
                              "updated": [] if made else [os.path.basename(local)], "stale": []}, ensure_ascii=False, indent=2))
    else:
        print(__doc__); sys.exit(1)


if __name__ == "__main__":
    main()
