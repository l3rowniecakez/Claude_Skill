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

HARD RULE (2026-09-04): "same menu re-selected" is decided by the breadcrumb
string alone (the "เมนูงาน" value), matched against "Menu Contents" — NOT by
whatever tab_title the caller passes in. Before writing, this script looks up
the existing row for that breadcrumb, resolves the gid in its Sheet URL to
that tab's real current title, and forces payload tab_title to match it. This
means the caller/agent's proposed tab_title is only a suggestion used for a
genuinely new menu — it is silently overridden on a re-run so the same menu
never ends up with two tabs.

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
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from google_clients import sheets_service  # noqa: E402

DETAIL_HEADER = ["Component Name", "Description", "Component Caption", "Event Name", "DB", "Call Store"]
MENU_CONTENTS_TITLE = "Menu Contents"
MENU_CONTENTS_FIRST_DATA_ROW = 7  # row 6 is the header

# Color read directly from the Template spreadsheet's actual cell formatting via
# the Sheets API on 2026-09-04 — ONE single dark-navy color for BOTH the label
# column and the table header row, always with white bold text (see drive_ops.py
# for the fuller note — an earlier two-shade guess here was wrong).
LABEL_BG = {"red": 0.02745098, "green": 0.21568628, "blue": 0.3882353}
TABLE_HEADER_BG = LABEL_BG
WHITE = {"red": 1, "green": 1, "blue": 1}

# Word wrap + top vertical alignment on every column, and fixed-but-reasonable
# column pixel widths — re-applied on every write/overwrite of a detail tab
# (not just first creation), per user feedback 2026-09-04 (see SKILL.md).
DETAIL_COL_WIDTHS = [150, 420, 150, 150, 110, 260]
FORMATTED_ROW_COUNT = 2000


def wrap_align_request(sheet_id, end_col, end_row=FORMATTED_ROW_COUNT):
    return {
        "repeatCell": {
            "range": {
                "sheetId": sheet_id,
                "startRowIndex": 0,
                "endRowIndex": end_row,
                "startColumnIndex": 0,
                "endColumnIndex": end_col,
            },
            "cell": {"userEnteredFormat": {"wrapStrategy": "WRAP", "verticalAlignment": "TOP"}},
            "fields": "userEnteredFormat.wrapStrategy,userEnteredFormat.verticalAlignment",
        }
    }


def column_width_requests(sheet_id, widths):
    return [
        {
            "updateDimensionProperties": {
                "range": {"sheetId": sheet_id, "dimension": "COLUMNS", "startIndex": i, "endIndex": i + 1},
                "properties": {"pixelSize": w},
                "fields": "pixelSize",
            }
        }
        for i, w in enumerate(widths)
    ]


def get_sheet_id_by_title(meta, title):
    for s in meta["sheets"]:
        if s["properties"]["title"] == title:
            return s["properties"]["sheetId"]
    return None


def get_title_by_sheet_id(meta, sheet_id):
    for s in meta["sheets"]:
        if s["properties"]["sheetId"] == sheet_id:
            return s["properties"]["title"]
    return None


def read_menu_contents_rows(sheets, spreadsheet_id):
    result = sheets.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{MENU_CONTENTS_TITLE}'!A{MENU_CONTENTS_FIRST_DATA_ROW}:E2000",
    ).execute()
    return result.get("values", [])


def find_existing_tab_gid(rows, breadcrumb):
    """Same menu re-analyzed = UPDATE, never a new tab/row. Match is by the exact
    breadcrumb string in the existing 'เมนูงาน' column (same rule upsert_menu_contents_row
    uses for the Menu Contents row) — the gid embedded in that row's Sheet URL tells us
    which tab already belongs to this menu, regardless of what tab_title the caller/agent
    proposes this run."""
    breadcrumb = breadcrumb.strip()
    for row in rows:
        existing_breadcrumb = row[1].strip() if len(row) > 1 else ""
        if existing_breadcrumb == breadcrumb:
            sheet_url = row[4] if len(row) > 4 else ""
            m = re.search(r"gid=(\d+)", sheet_url)
            return int(m.group(1)) if m else None
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
                    "textFormat": {"bold": True, "foregroundColor": WHITE},
                    "backgroundColor": LABEL_BG,
                }},
                "fields": "userEnteredFormat.textFormat,userEnteredFormat.backgroundColor",
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
    requests.append(wrap_align_request(sheet_id, len(DETAIL_HEADER)))
    requests.extend(column_width_requests(sheet_id, DETAIL_COL_WIDTHS))
    if manual_header_row:
        # "ขั้นตอนการใช้งาน (User Manual Steps)" section heading — per user feedback
        # 2026-09-04, this one row must NOT wrap (stays one line, overflowing into
        # empty cells to the right like a normal section title). Must come after
        # the general wrap_align_request above so it overrides that row.
        requests.append({
            "repeatCell": {
                "range": {
                    "sheetId": sheet_id,
                    "startRowIndex": manual_header_row - 1, "endRowIndex": manual_header_row,
                    "startColumnIndex": 0, "endColumnIndex": len(DETAIL_HEADER),
                },
                "cell": {"userEnteredFormat": {"wrapStrategy": "OVERFLOW_CELL"}},
                "fields": "userEnteredFormat.wrapStrategy",
            }
        })
    sheets.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body={"requests": requests},
    ).execute()


def upsert_menu_contents_row(sheets, spreadsheet_id, payload, tab_url, rows):
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

        # RULE (2026-09-04, hard requirement — see SKILL.md "กฎสำคัญ"): if this
        # breadcrumb was already analyzed before, this run is an UPDATE of that
        # exact same menu — reuse its existing tab, never create a second tab for
        # the same menu even if the caller/agent proposed a different tab_title.
        rows = read_menu_contents_rows(sheets, spreadsheet_id)
        existing_gid = find_existing_tab_gid(rows, payload["breadcrumb"])
        if existing_gid is not None:
            meta = sheets.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            existing_title = get_title_by_sheet_id(meta, existing_gid)
            if existing_title:
                payload["tab_title"] = existing_title

        sheet_id = ensure_detail_tab(sheets, spreadsheet_id, payload["tab_title"])
        write_detail_tab(sheets, spreadsheet_id, sheet_id, payload)
        tab_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit?gid={sheet_id}#gid={sheet_id}"
        row_number, action = upsert_menu_contents_row(sheets, spreadsheet_id, payload, tab_url, rows)
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
