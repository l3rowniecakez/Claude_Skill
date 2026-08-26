#!/usr/bin/env python3
"""Create / read / update ONE per-table Data Dictionary spreadsheet (the file
linked from the "Link" column of the master index sheet — a separate Google
Sheet per table, with tabs "Data dictionary" and "HistoryLog").

SAFETY: `create` only ever touches the brand-new spreadsheet it just copied
(never the master index, never another table's file). `update` only rewrites
the field-rows block (row 8 downward) and the 3 header cells (ชื่อตาราง /
Description / LastUpdate) of the SAME file resolved from the given link, plus
appends one new row to HistoryLog — it never deletes existing HistoryLog
entries and never touches any other table's file.

Usage:
  dic_table.py create <db: DataOne|OceanLife|OGL> <table_name>
      stdin JSON: {"table_description": "...", "columns": [{"field","type",
      "size","nullable","description"}, ...], "history_note": "..."}
      Copies this DB's template spreadsheet into this DB's Drive folder,
      clears the copied field/history rows, writes the real table name /
      description / LastUpdate / column list, adds HistoryLog row #1.
      Prints JSON: {"spreadsheet_id": "...", "url": "..."}
      REQUIRES the OAuth token to have full Drive write scope
      (https://www.googleapis.com/auth/drive) — files.copy needs it, and the
      token currently only has drive.readonly. See SKILL.md Step 0.

  dic_table.py read <link_or_id>
      Prints JSON: {"table_name", "description", "last_update", "fields":
      [{"field","description","type","size","null", "row_number"}]}

  dic_table.py update <link_or_id>
      stdin JSON: {"table_description": "..." (optional), "columns": [...],
      "history_note": "..."}
      Merges live DB columns into the existing field list (see merge rule
      below) and rewrites ONLY the field-rows block, then appends one
      HistoryLog row. Never silently drops a field that exists in the sheet
      but not in the live DB — it's kept and reported back so the caller can
      tell the user.
      Prints JSON: {"added": [...], "changed": [...], "kept_not_in_db": [...]}
"""
import sys
import os
import re
import json
import datetime

sys.path.insert(0, os.path.expanduser("~/.config/claude-google-access"))
from read_sheet import get_service  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

# Defaults below point at the original author's own Data Dictionary
# (per-table template spreadsheet + its Drive folder) for each DB — they only
# work if you have access to those exact Drive files, which you won't unless
# you're in the same organization. To use this skill with YOUR OWN Data
# Dictionary spreadsheet, either edit these values directly, or override them
# per-DB with environment variables DD_TEMPLATE_<DB> / DD_FOLDER_<DB> (DB in
# UPPERCASE, e.g. DD_TEMPLATE_DATAONE, DD_FOLDER_DATAONE) — no code change
# needed. See SKILL.md "การตั้งค่าก่อนใช้งาน" for what the template file must
# look like (2 tabs: "Data dictionary" + "HistoryLog", same layout as an
# existing per-table file in your own index sheet).
TEMPLATES = {
    "DataOne": {
        "template_id": os.environ.get("DD_TEMPLATE_DATAONE", "1D0uAjNBmpBbsSTRpZ3VxAVsiM2Q6ZjiylBLzjkGnwFY"),
        "folder_id": os.environ.get("DD_FOLDER_DATAONE", "1oItX3Xedax5Hd4EvssYgn6eJMIyGEx_o"),
    },
    "OceanLife": {
        "template_id": os.environ.get("DD_TEMPLATE_OCEANLIFE", "1m12q5zUN-CKvEDvpdvjLiDN77YEn5jFkHR34NKT54no"),
        "folder_id": os.environ.get("DD_FOLDER_OCEANLIFE", "13kn0tJTwVmU2fIW70ThtRKV5SoR7wZQw"),
    },
    "OGL": {
        "template_id": os.environ.get("DD_TEMPLATE_OGL", "1KfoLoeuTpaFh4JYlsm3c1n0pd6w-5fincewlb_X27W8"),
        "folder_id": os.environ.get("DD_FOLDER_OGL", "13BN6jihGRrHBCRBxYWG3VupMVfpxkv9V"),
    },
}

# Name written into the HistoryLog "UserUpdate" column. Set DD_USER_NAME in
# your environment (or just edit this default) to your own name/handle.
HISTORY_USER = os.environ.get("DD_USER_NAME", "<Developer Name>")

FIELD_HEADER_ROW = 6      # 0-indexed row of "Field#" header inside "Data dictionary"
FIELD_DATA_START = 7      # 0-indexed first data row
EPOCH = datetime.date(1899, 12, 30)


def extract_id(url_or_id):
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id)
    return m.group(1) if m else url_or_id


def today_serial():
    return (datetime.date.today() - EPOCH).days


def get_drive(service):
    return build("drive", "v3", credentials=service._http.credentials)


def get_sheet_id(meta, title):
    for s in meta.get("sheets", []):
        if s["properties"]["title"] == title:
            return s["properties"]["sheetId"]
    return None


def cmd_create(service, db, table_name, payload):
    tpl = TEMPLATES.get(db)
    if not tpl:
        print(json.dumps({"error": f"unknown db '{db}', expected DataOne/OceanLife/OGL"}))
        return

    drive = get_drive(service)
    new_name = f"{db}.{table_name}"

    try:
        copied = drive.files().copy(
            fileId=tpl["template_id"],
            body={"name": new_name, "parents": [tpl["folder_id"]]},
        ).execute()
    except Exception as e:
        print(json.dumps({"error": f"Drive files.copy failed (needs full 'drive' scope, not drive.readonly — see SKILL.md Step 0): {e}"}))
        return

    spreadsheet_id = copied["id"]

    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    dd_sheet_id = get_sheet_id(meta, "Data dictionary")
    hist_sheet_id = get_sheet_id(meta, "HistoryLog")
    if dd_sheet_id is None or hist_sheet_id is None:
        print(json.dumps({"error": f"copied spreadsheet {spreadsheet_id} is missing 'Data dictionary' or 'HistoryLog' tab — template may have changed"}))
        return

    # Clear only the field-data block (leaving header/labels rows 1-7 intact)
    # and only the HistoryLog data block (leaving its header rows intact).
    service.spreadsheets().values().batchClear(
        spreadsheetId=spreadsheet_id,
        body={"ranges": [
            f"'Data dictionary'!A{FIELD_DATA_START + 1}:N2000",
            "'HistoryLog'!B5:F2000",
        ]},
    ).execute()

    columns = payload.get("columns", [])
    table_description = payload.get("table_description", "")

    field_rows = []
    for col in columns:
        field_rows.append([
            col.get("field", ""),
            col.get("description", ""),
            col.get("type", ""),
            col.get("size", ""),
            col.get("nullable", ""),
        ])

    data = [
        {"range": f"'Data dictionary'!C2", "values": [[new_name]]},
        {"range": f"'Data dictionary'!C3", "values": [[table_description]]},
        {"range": f"'Data dictionary'!C5", "values": [[today_serial()]]},
    ]
    if field_rows:
        data.append({
            "range": f"'Data dictionary'!B{FIELD_DATA_START + 1}",
            "values": field_rows,
        })

    history_note = payload.get("history_note", "สร้าง Data Dictionary จากโครงสร้าง DB จริง")
    data.append({
        "range": "'HistoryLog'!B5",
        "values": [[1, "", history_note, datetime.date.today().isoformat(), HISTORY_USER]],
    })

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()

    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0"
    print(json.dumps({"spreadsheet_id": spreadsheet_id, "url": url}))


def read_fields(service, spreadsheet_id):
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range="'Data dictionary'!A1:N2000",
        valueRenderOption="FORMULA",
    ).execute()
    values = result.get("values", [])

    def cell(row, idx):
        return row[idx].strip() if idx < len(row) and isinstance(row[idx], str) else (row[idx] if idx < len(row) else "")

    table_name = cell(values[1], 2) if len(values) > 1 else ""
    description = cell(values[2], 2) if len(values) > 2 else ""
    last_update = cell(values[4], 2) if len(values) > 4 else ""

    fields = []
    for i, row in enumerate(values[FIELD_DATA_START:], start=FIELD_DATA_START + 1):
        field = cell(row, 1)
        if not field:
            continue
        fields.append({
            "field": field,
            "description": cell(row, 2),
            "type": cell(row, 3),
            "size": cell(row, 4),
            "null": cell(row, 5),
            "row_number": i,
        })

    return table_name, description, last_update, fields


def cmd_read(service, link):
    spreadsheet_id = extract_id(link)
    table_name, description, last_update, fields = read_fields(service, spreadsheet_id)
    print(json.dumps({
        "table_name": table_name,
        "description": description,
        "last_update": last_update,
        "fields": fields,
    }, ensure_ascii=False, indent=2))


def cmd_update(service, link, payload):
    spreadsheet_id = extract_id(link)
    table_name, description, last_update, existing_fields = read_fields(service, spreadsheet_id)

    existing_by_name = {f["field"].lower(): f for f in existing_fields}
    live_columns = payload.get("columns", [])
    live_by_name = {c["field"].lower(): c for c in live_columns}

    merged = []
    added = []
    changed = []

    # Keep existing order first, updating in place from the live DB.
    for f in existing_fields:
        live = live_by_name.get(f["field"].lower())
        if live is None:
            merged.append([f["field"], f["description"], f["type"], f["size"], f["null"]])
            continue
        new_desc = live.get("description") or f["description"]
        new_row = [f["field"], new_desc, live.get("type", ""), live.get("size", ""), live.get("nullable", "")]
        if new_row[2:] != [f["type"], f["size"], f["null"]] or new_desc != f["description"]:
            changed.append(f["field"])
        merged.append(new_row)

    kept_not_in_db = [f["field"] for f in existing_fields if f["field"].lower() not in live_by_name]

    # Append genuinely new fields (in live DB, not already in the sheet).
    for c in live_columns:
        if c["field"].lower() not in existing_by_name:
            merged.append([c["field"], c.get("description", ""), c.get("type", ""), c.get("size", ""), c.get("nullable", "")])
            added.append(c["field"])

    # Clear the old field block, then write the merged block back — a single
    # contiguous rewrite of ONLY the field-rows range, nothing else on the
    # sheet is touched.
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=f"'Data dictionary'!A{FIELD_DATA_START + 1}:N2000",
    ).execute()

    data = [
        {"range": "'Data dictionary'!C5", "values": [[today_serial()]]},
    ]
    if "table_description" in payload and payload["table_description"]:
        data.append({"range": "'Data dictionary'!C3", "values": [[payload["table_description"]]]})
    if merged:
        data.append({"range": f"'Data dictionary'!B{FIELD_DATA_START + 1}", "values": merged})

    # Find next HistoryLog No. (append-only — never touches prior rows).
    hist = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range="'HistoryLog'!B4:B2000",
    ).execute().get("values", [])
    last_no = 0
    next_hist_row = 5
    for i, row in enumerate(hist[1:], start=5):
        if row and str(row[0]).strip():
            try:
                last_no = max(last_no, int(row[0]))
            except ValueError:
                pass
            next_hist_row = i + 1

    history_note = payload.get("history_note", "อัพเดท Data Dictionary ตามโครงสร้าง DB จริง")
    data.append({
        "range": f"'HistoryLog'!B{next_hist_row}",
        "values": [[last_no + 1, "", history_note, datetime.date.today().isoformat(), HISTORY_USER]],
    })

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()

    print(json.dumps({
        "added": added,
        "changed": changed,
        "kept_not_in_db": kept_not_in_db,
        "field_count": len(merged),
    }, ensure_ascii=False))


def main():
    mode = sys.argv[1]
    service = get_service()

    if mode == "create":
        db = sys.argv[2]
        table_name = sys.argv[3]
        payload = json.load(sys.stdin)
        cmd_create(service, db, table_name, payload)
    elif mode == "read":
        cmd_read(service, sys.argv[2])
    elif mode == "update":
        link = sys.argv[2]
        payload = json.load(sys.stdin)
        cmd_update(service, link, payload)
    else:
        print(json.dumps({"error": f"unknown mode '{mode}'"}))


if __name__ == "__main__":
    main()
