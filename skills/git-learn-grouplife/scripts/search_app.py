#!/usr/bin/env python3
"""Search the git-clone-grouplife tracking sheet
(spreadsheet 18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0, tab resolved live)
for Apps whose AppName contains a keyword — read-only, this skill never
writes to the sheet (that's /git-clone-grouplife-update's job). Shared
lookup logic with the sibling /git-clone-grouplife skill, which uses the
same sheet to do a real `git clone` instead of reading the source remotely.

Usage:
  search_app.py <keyword>
      Case-insensitive substring match against column B (AppName). Prints
      JSON list of matches: [{"group": "...", "app_name": "...", "repo":
      "...", "sub_folder": "..."}, ...] (empty list if none). Row 1 (header)
      and row 2 (fixed "Example" row) are never matched.

  search_app.py --exact <app_name>
      Case-insensitive EXACT match only. Prints a single JSON object (same
      shape as one list entry) or {"error": "not found"} if no exact match.
"""
import sys
import os
import json

sys.path.insert(0, os.path.expanduser("~/.config/claude-google-access"))
from read_sheet import get_service  # noqa: E402

SPREADSHEET_ID = "18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0"


def sheet_name(service):
    meta = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    return meta["sheets"][0]["properties"]["title"]


def read_values(service):
    name = sheet_name(service)
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{name}!A:D",
    ).execute()
    return result.get("values", [])


def row_at(row, idx):
    return row[idx].strip() if len(row) > idx else ""


def all_apps(service):
    values = read_values(service)
    apps = []
    for i, row in enumerate(values):
        rn = i + 1
        if rn <= 2:  # header + fixed example row
            continue
        app_name = row_at(row, 1)
        if not app_name:
            continue
        apps.append({
            "group": row_at(row, 0),
            "app_name": app_name,
            "repo": row_at(row, 2),
            "sub_folder": row_at(row, 3),
        })
    return apps


def search(service, keyword):
    keyword_lower = keyword.strip().lower()
    return [a for a in all_apps(service) if keyword_lower in a["app_name"].lower()]


def search_exact(service, app_name):
    needle = app_name.strip().lower()
    for a in all_apps(service):
        if a["app_name"].lower() == needle:
            return a
    return None


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "usage: search_app.py <keyword> | --exact <app_name>"}), file=sys.stderr)
        sys.exit(1)
    service = get_service()
    try:
        if sys.argv[1] == "--exact":
            if len(sys.argv) < 3:
                raise ValueError("usage: search_app.py --exact <app_name>")
            result = search_exact(service, sys.argv[2])
            if result is None:
                result = {"error": "not found"}
        else:
            result = search(service, sys.argv[1])
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
