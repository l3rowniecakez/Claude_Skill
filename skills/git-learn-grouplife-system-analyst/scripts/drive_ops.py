#!/usr/bin/env python3
"""Ensure the Drive folder + per-App spreadsheet exist for
/git-learn-grouplife-system-analyst, under the fixed root folder
"GroupLife by Claude AI" (id 1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ).

Layout (locked with the user 2026-09-04):
  <ROOT>/<Group>/<AppName>              one spreadsheet per App
    tab "Menu Contents"                  table of contents, one row per analyzed menu
    tab "<primary form/unit name>"       one tab per analyzed menu (added by sheet_write.py)

<Group> = the tracking sheet's "Group" column (repo short name, e.g.
"groupwork-system-2016"). <AppName> = the tracking sheet's "AppName" column
(folder right before /trunk, e.g. "GroupLifeInsuranceSystem_Benefits") — same
values /git-learn-grouplife's search_app.py returns.

This script NEVER touches the hand-built "Template" spreadsheet
(1wI9_Q-Zw50vLMNbtozKhCpb7ebsLYtmyHUC_1gBnLnY) or any other existing file —
it only creates a blank new spreadsheet, built from scratch, the first time
a given App is analyzed. On every later run for the same App it finds the
existing spreadsheet and returns it unchanged (spreadsheet_created: false) —
new menus get added as tabs by sheet_write.py, not by recreating the file.

Usage:
  drive_ops.py ensure <group> <app_name> <program_name> <repo_url> <sub_folder> <today>
      <program_name>: e.g. "OGL_Benefits.exe" (derive from the .dpr project
      filename found under sub_folder — see SKILL.md Phase 1).
      <today>: YYYY-MM-DD, written into "วันที่อัพเดท Sheet ล่าสุด" only on
      first creation (later updates to that cell happen in sheet_write.py).
      Prints JSON: {"folder_id", "folder_created", "spreadsheet_id",
      "spreadsheet_created", "spreadsheet_url"}.
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service, drive_service  # noqa: E402

ROOT_FOLDER_ID = "1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ"
MENU_CONTENTS_TITLE = "Menu Contents"
MENU_CONTENTS_HEADER = ["No", "เมนูงาน", "รายละเอียดเมนูงาน", "Delphi Path File", "Sheet URL"]

# Colors matched to the user's hand-built example spreadsheet (added 2026-09-04,
# see screenshots referenced in that session) — light blue for the label column of
# the header info block, dark navy with white bold text for table header rows.
LABEL_BG = {"red": 0.812, "green": 0.886, "blue": 0.953}
TABLE_HEADER_BG = {"red": 0.106, "green": 0.267, "blue": 0.471}
WHITE = {"red": 1, "green": 1, "blue": 1}


def _escape(name):
    return name.replace("\\", "\\\\").replace("'", "\\'")


def find_child(drive, parent_id, name, mime_type):
    q = (
        f"'{parent_id}' in parents and trashed = false "
        f"and name = '{_escape(name)}' and mimeType = '{mime_type}'"
    )
    resp = drive.files().list(q=q, fields="files(id, name)", pageSize=5).execute()
    files = resp.get("files", [])
    return files[0]["id"] if files else None


def ensure_group_folder(drive, group_name):
    folder_id = find_child(drive, ROOT_FOLDER_ID, group_name, "application/vnd.google-apps.folder")
    if folder_id:
        return folder_id, False
    meta = {
        "name": group_name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [ROOT_FOLDER_ID],
    }
    created = drive.files().create(body=meta, fields="id").execute()
    return created["id"], True


def ensure_app_spreadsheet(drive, sheets, folder_id, app_name, program_name, repo_url, sub_folder, today):
    existing_id = find_child(drive, folder_id, app_name, "application/vnd.google-apps.spreadsheet")
    if existing_id:
        return existing_id, False

    body = {
        "properties": {"title": app_name},
        "sheets": [{"properties": {"title": MENU_CONTENTS_TITLE}}],
    }
    created = sheets.spreadsheets().create(
        body=body, fields="spreadsheetId,sheets.properties"
    ).execute()
    spreadsheet_id = created["spreadsheetId"]
    sheet_id = created["sheets"][0]["properties"]["sheetId"]

    values = [
        ["โปรแกรม", program_name],
        ["Repo URL", repo_url],
        ["Sub Folder", sub_folder],
        ["วันที่อัพเดท Sheet ล่าสุด", today],
        [],
        MENU_CONTENTS_HEADER,
    ]
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{MENU_CONTENTS_TITLE}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={
            "requests": [
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 0,
                            "endRowIndex": 4,
                            "startColumnIndex": 0,
                            "endColumnIndex": 1,
                        },
                        "cell": {"userEnteredFormat": {
                            "textFormat": {"bold": True},
                            "backgroundColor": LABEL_BG,
                        }},
                        "fields": "userEnteredFormat.textFormat.bold,userEnteredFormat.backgroundColor",
                    }
                },
                {
                    "repeatCell": {
                        "range": {
                            "sheetId": sheet_id,
                            "startRowIndex": 5,
                            "endRowIndex": 6,
                            "startColumnIndex": 0,
                            "endColumnIndex": len(MENU_CONTENTS_HEADER),
                        },
                        "cell": {"userEnteredFormat": {
                            "textFormat": {"bold": True, "foregroundColor": WHITE},
                            "backgroundColor": TABLE_HEADER_BG,
                            "horizontalAlignment": "CENTER",
                        }},
                        "fields": "userEnteredFormat.textFormat,userEnteredFormat.backgroundColor,userEnteredFormat.horizontalAlignment",
                    }
                },
                {
                    "updateSheetProperties": {
                        "properties": {"sheetId": sheet_id, "gridProperties": {"frozenRowCount": 6}},
                        "fields": "gridProperties.frozenRowCount",
                    }
                },
            ]
        },
    ).execute()

    # spreadsheets().create() always lands the file in "My Drive" root —
    # move it into the group folder.
    file = drive.files().get(fileId=spreadsheet_id, fields="parents").execute()
    prev_parents = ",".join(file.get("parents", []))
    drive.files().update(
        fileId=spreadsheet_id,
        addParents=folder_id,
        removeParents=prev_parents,
        fields="id, parents",
    ).execute()

    return spreadsheet_id, True


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    p_ensure = sub.add_parser("ensure")
    p_ensure.add_argument("group")
    p_ensure.add_argument("app_name")
    p_ensure.add_argument("program_name")
    p_ensure.add_argument("repo_url")
    p_ensure.add_argument("sub_folder")
    p_ensure.add_argument("today")

    args = parser.parse_args()
    if args.cmd != "ensure":
        print(json.dumps({"error": "usage: drive_ops.py ensure <group> <app_name> <program_name> <repo_url> <sub_folder> <today>"}), file=sys.stderr)
        sys.exit(1)

    try:
        drive = drive_service()
        sheets = sheets_service()
        folder_id, folder_created = ensure_group_folder(drive, args.group)
        spreadsheet_id, spreadsheet_created = ensure_app_spreadsheet(
            drive, sheets, folder_id, args.app_name, args.program_name,
            args.repo_url, args.sub_folder, args.today,
        )
        result = {
            "folder_id": folder_id,
            "folder_created": folder_created,
            "spreadsheet_id": spreadsheet_id,
            "spreadsheet_created": spreadsheet_created,
            "spreadsheet_url": f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit",
        }
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
