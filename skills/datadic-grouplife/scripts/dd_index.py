#!/usr/bin/env python3
"""List / search rows in one Data Dictionary index sheet (Data One / OceanLife / OGL).

Usage:
  dd_index.py <sheet_name> [search_substring]

Always reads from the master spreadsheet
(1qHeg391cRNrGA1HC3cWxsv9HcJZS0POuI94uaR27cqU). Header row is located
dynamically by looking for a cell equal to "Table Name", so column order
differences between sheets (e.g. OceanLife has an extra "CIS" column) don't
matter. Prints one JSON object per line (JSONL): {no, table_name,
description, link}.
"""
import sys
import os
import json
import re

sys.path.insert(0, os.path.expanduser("~/.config/claude-google-access"))
from read_sheet import get_service  # noqa: E402

MASTER_SPREADSHEET_ID = "1qHeg391cRNrGA1HC3cWxsv9HcJZS0POuI94uaR27cqU"


def find_header(values):
    for i, row in enumerate(values):
        for j, cell in enumerate(row):
            if str(cell).strip() == "Table Name":
                return i, j
    return None, None


def col_index(header_row, *names):
    for name in names:
        for j, cell in enumerate(header_row):
            if str(cell).strip() == name:
                return j
    return None


def get(row, idx):
    if idx is None or idx >= len(row):
        return ""
    return str(row[idx]).strip()


def main():
    sheet_name = sys.argv[1]
    search = sys.argv[2].lower() if len(sys.argv) > 2 else None

    service = get_service()
    result = service.spreadsheets().values().get(
        spreadsheetId=MASTER_SPREADSHEET_ID,
        range=f"'{sheet_name}'",
        valueRenderOption="FORMULA",
    ).execute()
    values = result.get("values", [])

    header_row_idx, _ = find_header(values)
    if header_row_idx is None:
        print(json.dumps({"error": f"header row not found in sheet '{sheet_name}'"}))
        return
    header_row = values[header_row_idx]

    no_idx = col_index(header_row, "No.")
    name_idx = col_index(header_row, "Table Name")
    desc_idx = col_index(header_row, "คำอธิบายตาราง")
    link_idx = col_index(header_row, "Link")

    for row in values[header_row_idx + 1:]:
        table_name = get(row, name_idx)
        if not table_name:
            continue
        if search and search not in table_name.lower():
            continue
        link_cell = get(row, link_idx)
        m = re.search(r"https://\S+", link_cell)
        link = m.group(0) if m else link_cell
        print(json.dumps({
            "no": get(row, no_idx),
            "table_name": table_name,
            "description": get(row, desc_idx),
            "link": link,
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
