#!/usr/bin/env python3
"""Write ONE analyzed menu's results into an App's spreadsheet (created by
drive_ops.py): adds/overwrites a detail tab and upserts the matching row in
the "Menu Contents" tab.

**Never run this concurrently for the same spreadsheet_id** — row numbers in
"Menu Contents" are computed from a single read, same caveat as
/git-clone-grouplife-update's sheet_ops.py. Call this once per selected menu,
sequentially, from the orchestrating session — not from parallel analysis
agents themselves (see SKILL.md Phase 4).

Column schema locked with the user on 2026-09-04:
  Menu Contents tab: No | เมนูงาน | รายละเอียดเมนูงาน | Delphi Path File | Sheet URL
  Detail tab table:  Component Name | Description | Component Caption | Event Name | DB | Call Store
  (6 columns — the duplicated "Event Name" column seen in the hand-built
  example spreadsheet 1wI9_Q-Zw50vLMNbtozKhCpb7ebsLYtmyHUC_1gBnLnY was a
  typo, not the standard to replicate.)

Re-running for a menu whose tab already exists REPLACES that tab's content
(clears then rewrites) rather than duplicating a second tab or appending
below old content — analysis is meant to be re-run as source code changes.

Usage: pass one JSON object on stdin:
{
  "spreadsheet_id": "...",
  "program_name": "OGL_Benefits.exe",
  "repo_url": "git clone ssh://...",
  "sub_folder": "GroupLifeInsuranceSystem_Benefits/trunk",
  "breadcrumb": "\"เมนูงาน...\" => \"...\" => \"...\"",
  "description": "one-line description of the menu",
  "delphi_path_file": "ListForm\\ListAcDeathWaitPay.*",
  "tab_title": "ListAcDeathWaitPay",
  "today": "2026-09-04",
  "component_rows": [
    ["FormShow", "โหลดข้อมูลแสดงในกริดตอนเปิดฟอร์ม", "", "FormShow", "oceanlife", "sp_gl_ListAC_TransferMoney"],
    ["btnSearch", "ปุ่มค้นหารายการ", "Search", "btnSearchClick", "oceanlife", "sp_gl_ListAC_TransferMoney"]
  ],
  "manual_steps": ["1. ผู้ใช้เปิดเมนู ... แล้วเลือกช่วงวันที่", "2. กด Search ระบบจะ ..."]
}
Prints JSON {"tab_gid", "tab_url", "menu_contents_row", "menu_contents_action"}.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service  # noqa: E402

DETAIL_HEADER = ["Component Name", "Description", "Component Caption", "Event Name", "DB", "Call Store"]
MENU_CONTENTS_TITLE = "Menu Contents"
MENU_CONTENTS_FIRST_DATA_ROW = 7  # row 6 is the header

# Same palette as drive_ops.py's Menu Contents tab — matched to the user's
# hand-built example spreadsheet (added 2026-09-04).
LABEL_BG = {"red": 0.812, "green": 0.886, "blue": 0.953}
TABLE_HEADER_BG = {"red": 0.106, "green": 0.267, "blue": 0.471}
WHITE = {"red": 1, "green": 1, "blue": 1}


def get_sheet_id_by_title(meta, title):
    for s in meta["sheets"]:
        if s["properties"]["title"] == title:
            return s["properties"]["sheetId"]
    return None


def ensure_detail_tab(sheets, spreadsheet_id, tab_title):
    meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    sheet_id = get_sheet_id_by_title(meta, tab_title)
    if sheet_id is not None:
        sheets.spreadsheets().values().clear(
            spreadsheetId=spreadsheet_id, range=f"'{tab_title}'!A1:Z2000", body={},
        ).execute()
        return sheet_id
    resp = sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id,
        body={"requests": [{"addSheet": {"properties": {"title": tab_title}}}]},
    ).execute()
    return resp["replies"][0]["addSheet"]["properties"]["sheetId"]


def write_detail_tab(sheets, spreadsheet_id, sheet_id, payload):
    values = [
        ["โปรแกรม", payload["program_name"]],
        ["Repo URL", payload["repo_url"]],
        ["Sub Folder", payload["sub_folder"]],
        ["เมนูงาน", payload["breadcrumb"]],
        ["รายละเอียดเมนูงาน", payload["description"]],
        ["วันที่อัพเดท Sheet ล่าสุด", payload["today"]],
        [],
        [],
        DETAIL_HEADER,
    ]
    header_row_count = len(values)  # 9, matches template layout exactly
    values.extend(payload["component_rows"])

    manual_steps = payload.get("manual_steps") or []
    manual_header_row = None
    if manual_steps:
        manual_header_row = len(values) + 2  # 1-indexed row of the "ขั้นตอนการใช้งาน" label
        values.append([])
        values.append(["ขั้นตอนการใช้งาน (User Manual Steps)"])
        for step in manual_steps:
            values.append([step])

    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{payload['tab_title']}'!A1",
        valueInputOption="USER_ENTERED",
        body={"values": values},
    ).execute()

    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id, "startRowIndex": 0, "endRowIndex": 6,
                    "startColumnIndex": 0, "endColumnIndex": 1,
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
                    "startRowIndex": header_row_count - 1, "endRowIndex": header_row_count,
                    "startColumnIndex": 0, "endColumnIndex": len(DETAIL_HEADER),
                },
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": WHITE},
                    "backgroundColor": TABLE_HEADER_BG,
                    "horizontalAlignment": "CENTER",
                }},
                "fields": "userEnteredFormat.textFormat,userEnteredFormat.backgroundColor,userEnteredFormat.horizontalAlignment",
            }
        },
    ]
    if manual_header_row:
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": manual_header_row - 1, "endRowIndex": manual_header_row,
                    "startColumnIndex": 0, "endColumnIndex": len(DETAIL_HEADER),
                },
                "cell": {"userEnteredFormat": {
                    "textFormat": {"bold": True, "foregroundColor": WHITE},
                    "backgroundColor": TABLE_HEADER_BG,
                }},
                "fields": "userEnteredFormat.textFormat,userEnteredFormat.backgroundColor",
            }
        })
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests},
    ).execute()


def upsert_menu_contents_row(sheets, spreadsheet_id, payload, tab_url):
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{MENU_CONTENTS_TITLE}'!A{MENU_CONTENTS_FIRST_DATA_ROW}:E2000",
    ).execute()
    rows = result.get("values", [])
    breadcrumb = payload["breadcrumb"].strip()

    match_row = None
    next_row = MENU_CONTENTS_FIRST_DATA_ROW
    for i, row in enumerate(rows):
        row_number = i + MENU_CONTENTS_FIRST_DATA_ROW
        existing_breadcrumb = row[1].strip() if len(row) > 1 else ""
        if existing_breadcrumb == breadcrumb:
            match_row = row_number
        if row and (row[0] if len(row) > 0 else ""):
            next_row = row_number + 1

    row_number = match_row or next_row
    row_values = [
        row_number - MENU_CONTENTS_FIRST_DATA_ROW + 1,
        breadcrumb,
        payload["description"],
        payload["delphi_path_file"],
        tab_url,
    ]
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{MENU_CONTENTS_TITLE}'!A{row_number}:E{row_number}",
        valueInputOption="USER_ENTERED",
        body={"values": [row_values]},
    ).execute()
    return row_number, ("updated" if match_row else "inserted")


def touch_menu_contents_date(sheets, spreadsheet_id, today):
    sheets.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=f"'{MENU_CONTENTS_TITLE}'!B4",
        valueInputOption="USER_ENTERED",
        body={"values": [[today]]},
    ).execute()


def main():
    payload = json.load(sys.stdin)
    try:
        sheets = sheets_service()
        spreadsheet_id = payload["spreadsheet_id"]
        sheet_id = ensure_detail_tab(sheets, spreadsheet_id, payload["tab_title"])
        write_detail_tab(sheets, spreadsheet_id, sheet_id, payload)
        tab_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={sheet_id}#gid={sheet_id}"
        row_number, action = upsert_menu_contents_row(sheets, spreadsheet_id, payload, tab_url)
        touch_menu_contents_date(sheets, spreadsheet_id, payload["today"])
        result = {
            "tab_gid": sheet_id,
            "tab_url": tab_url,
            "menu_contents_row": row_number,
            "menu_contents_action": action,
        }
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
