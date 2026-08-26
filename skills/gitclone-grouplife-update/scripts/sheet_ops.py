#!/usr/bin/env python3
"""Find / upsert rows in the "gitclone-grouplife" tracking sheet
(spreadsheet 18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0, tab resolved live
— it was renamed "Sheet1" -> "Main" once already, so this never hardcodes
the tab name).

Columns: A=Group (repo short name), B=AppName (folder right before trunk),
C=repo (a ready-to-copy "git clone ssh://..." command), D=Sub Folder (App
path relative to repo root, ending in "/trunk"), E=Full Path (a formula
replicating row 2's example: =C{row} & "/" & D{row}). Row 1 is the header,
row 2 is a fixed "Example" row — never touched, never included in matching.

Upsert semantics: a row is matched by AppName first, then by Sub Folder if
AppName didn't match (case-insensitive exact match either way). If matched,
the row's Group/AppName/repo/Sub Folder/formula are OVERWRITTEN with the new
values (this is a deliberate update, not a skip) — the previous values are
returned in the result so the caller can flag a surprising overwrite (e.g.
same AppName suddenly pointing at a very different Sub Folder, which usually
means two distinct programs share a name rather than one program that moved
— see SKILL.md). If no match, a new row is inserted. Never sorts, filters,
or deletes a row.

Usage:
  sheet_ops.py find <app_name_or_sub_folder>
      Case-insensitive exact match against column B (AppName) or column D
      (Sub Folder). Prints JSON {"found": true, "row_number": N, "group":
      ..., "app_name": ..., "sub_folder": ...} or {"found": false}.

  echo '{"Group": "...", "AppName": "...", "repo": "...", "Sub Folder": "..."}' | \
    sheet_ops.py upsert
      Upserts ONE row. Prints JSON {"action": "inserted"|"updated",
      "row_number": N, "previous": {...} (only present for "updated")}.

  echo '[{...}, {...}, ...]' | sheet_ops.py upsert-batch
      Same upsert contract as above but for many items in ONE API round
      trip (one read, one batchUpdate for changed rows, one update for the
      contiguous block of new rows) — use this for a full-repo re-scan
      instead of calling upsert in a loop. NOT safe to run two of these (or
      upsert/upsert-batch together) concurrently against the same sheet —
      row-number and dup-match state is computed once up front from a
      single read, so a concurrent writer would race it. Do these
      sequentially. Prints JSON: {"inserted_count": N, "updated_count": N,
      "inserted": [...], "updated": [...]} (each "updated" entry includes
      "previous" for audit).
"""
import sys
import os
import json

sys.path.insert(0, os.path.expanduser("~/.config/claude-google-access"))
from read_sheet import get_service  # noqa: E402

SPREADSHEET_ID = "18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0"
HEADER = ["Group", "AppName", "repo", "Sub Folder", "Full Path"]
REQUIRED_FIELDS = ("Group", "AppName", "repo", "Sub Folder")


def sheet_name(service):
    """The single tab's name has already changed once (Sheet1 -> Main)
    mid-development — resolve it live instead of hardcoding, since this
    spreadsheet only ever has the one tab."""
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    return meta["sheets"][0]["properties"]["title"]


def read_values(service):
    name = sheet_name(service)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{name}!A:E",
    ).execute()
    return result.get("values", [])


def row_at(row, idx):
    return row[idx].strip() if len(row) > idx else ""


def find(service, needle):
    needle_lower = needle.strip().lower()
    values = read_values(service)
    for i, row in enumerate(values):
        row_number = i + 1
        if row_number <= 2:  # header + fixed example row
            continue
        app_name = row_at(row, 1)
        sub_folder = row_at(row, 3)
        if app_name.lower() == needle_lower or sub_folder.lower() == needle_lower:
            return {
                "found": True,
                "row_number": row_number,
                "group": row_at(row, 0),
                "app_name": app_name,
                "repo": row_at(row, 2),
                "sub_folder": sub_folder,
            }
    return {"found": False}


def build_index(values):
    """Returns (app_name_index, sub_folder_index, next_row) where the two
    indexes map lowercased value -> (row_number, row_values), and next_row
    is the first blank row after the last used one (search starts at row 3,
    past header + fixed example)."""
    app_index = {}
    sub_index = {}
    next_row = 3
    for i, row in enumerate(values):
        rn = i + 1
        if rn <= 2:
            continue
        app_name = row_at(row, 1)
        sub_folder = row_at(row, 3)
        if app_name:
            app_index[app_name.lower()] = (rn, row)
        if sub_folder:
            sub_index[sub_folder.lower()] = (rn, row)
        if row_at(row, 0):
            next_row = rn + 1
    return app_index, sub_index, next_row


def upsert(service, payload):
    missing = [k for k in REQUIRED_FIELDS if not payload.get(k)]
    if missing:
        return {"error": f"missing required field(s): {missing}"}

    values = read_values(service)
    app_index, sub_index, next_row = build_index(values)

    match = app_index.get(payload["AppName"].strip().lower()) or \
        sub_index.get(payload["Sub Folder"].strip().lower())

    if match:
        row_number, old_row = match
        row_values = [
            payload["Group"], payload["AppName"], payload["repo"], payload["Sub Folder"],
            f'=C{row_number} & "/" & D{row_number}',
        ]
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name(service)}!A{row_number}:E{row_number}",
            valueInputOption="USER_ENTERED",
            body={"values": [row_values]},
        ).execute()
        return {
            "action": "updated",
            "row_number": row_number,
            "previous": {
                "Group": row_at(old_row, 0),
                "AppName": row_at(old_row, 1),
                "repo": row_at(old_row, 2),
                "Sub Folder": row_at(old_row, 3),
            },
        }

    row_values = [
        payload["Group"], payload["AppName"], payload["repo"], payload["Sub Folder"],
        f'=C{next_row} & "/" & D{next_row}',
    ]
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{sheet_name(service)}!A{next_row}:E{next_row}",
        valueInputOption="USER_ENTERED",
        body={"values": [row_values]},
    ).execute()
    return {"action": "inserted", "row_number": next_row}


def upsert_batch(service, items):
    values = read_values(service)
    app_index, sub_index, next_row = build_index(values)

    inserted = []
    updated = []
    errors = []
    update_data = []  # list of {range, values} for values().batchUpdate
    insert_rows = []  # contiguous block appended after next_row
    cur_insert_row = next_row

    for item in items:
        missing = [k for k in REQUIRED_FIELDS if not item.get(k)]
        if missing:
            errors.append({"item": item, "reason": f"missing field(s): {missing}"})
            continue

        app_key = item["AppName"].strip().lower()
        sub_key = item["Sub Folder"].strip().lower()
        match = app_index.get(app_key) or sub_index.get(sub_key)

        if match:
            row_number, old_row = match
            row_values = [
                item["Group"], item["AppName"], item["repo"], item["Sub Folder"],
                f'=C{row_number} & "/" & D{row_number}',
            ]
            update_data.append({
                "range": f"{sheet_name(service)}!A{row_number}:E{row_number}",
                "values": [row_values],
            })
            updated.append({
                "row_number": row_number,
                "AppName": item["AppName"],
                "Sub Folder": item["Sub Folder"],
                "previous": {
                    "Group": row_at(old_row, 0),
                    "AppName": row_at(old_row, 1),
                    "repo": row_at(old_row, 2),
                    "Sub Folder": row_at(old_row, 3),
                },
            })
            # keep indexes consistent in case later items in this same batch
            # reference the same AppName/Sub Folder again
            new_row_tuple = (row_number, row_values)
            app_index[item["AppName"].strip().lower()] = new_row_tuple
            sub_index[item["Sub Folder"].strip().lower()] = new_row_tuple
            continue

        row_values = [
            item["Group"], item["AppName"], item["repo"], item["Sub Folder"],
            f'=C{cur_insert_row} & "/" & D{cur_insert_row}',
        ]
        insert_rows.append(row_values)
        inserted.append({"row_number": cur_insert_row, "AppName": item["AppName"], "Sub Folder": item["Sub Folder"]})
        new_row_tuple = (cur_insert_row, row_values)
        app_index[app_key] = new_row_tuple
        sub_index[sub_key] = new_row_tuple
        cur_insert_row += 1

    if update_data:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={"valueInputOption": "USER_ENTERED", "data": update_data},
        ).execute()

    if insert_rows:
        end_row = next_row + len(insert_rows) - 1
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name(service)}!A{next_row}:E{end_row}",
            valueInputOption="USER_ENTERED",
            body={"values": insert_rows},
        ).execute()

    return {
        "inserted_count": len(inserted),
        "updated_count": len(updated),
        "error_count": len(errors),
        "inserted": inserted,
        "updated": updated,
        "errors": errors,
    }


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: sheet_ops.py find <needle> | upsert | upsert-batch"}), file=sys.stderr)
        sys.exit(1)
    cmd = sys.argv[1]
    service = get_service()
    try:
        if cmd == "find":
            if len(sys.argv) < 3:
                raise ValueError("usage: sheet_ops.py find <needle>")
            result = find(service, sys.argv[2])
        elif cmd == "upsert":
            payload = json.load(sys.stdin)
            result = upsert(service, payload)
        elif cmd == "upsert-batch":
            items = json.load(sys.stdin)
            result = upsert_batch(service, items)
        else:
            raise ValueError(f"unknown subcommand {cmd}")
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
