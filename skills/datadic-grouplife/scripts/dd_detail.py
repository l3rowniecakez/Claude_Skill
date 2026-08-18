#!/usr/bin/env python3
"""Read the full column/field structure of one table from its own
per-table Data Dictionary spreadsheet (the URL in the "Link" column of the
master index sheet).

Usage:
  dd_detail.py <spreadsheet_url_or_id>

Looks for a tab named "Data dictionary" (falls back to the first tab if not
found). Prints one JSON object: {table_name, description, last_update,
fields: [{field, description, type, size, null, key, validation, value,
min_value, max_value, example, save_condition, note}]}.
"""
import sys
import os
import re
import json

sys.path.insert(0, os.path.expanduser("~/.config/claude-google-access"))
from read_sheet import get_service  # noqa: E402

FIELD_COLS = [
    "field", "description", "type", "size", "null", "key", "validation",
    "value", "min_value", "max_value", "example", "save_condition", "note",
]


def extract_id(url_or_id):
    m = re.search(r"/d/([a-zA-Z0-9_-]+)", url_or_id)
    return m.group(1) if m else url_or_id


def main():
    spreadsheet_id = extract_id(sys.argv[1])
    service = get_service()

    meta = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
    titles = [s["properties"]["title"] for s in meta.get("sheets", [])]
    sheet_name = "Data dictionary" if "Data dictionary" in titles else titles[0]

    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"'{sheet_name}'",
        valueRenderOption="FORMULA",
    ).execute()
    values = [[str(c) for c in row] for row in result.get("values", [])]

    table_name = ""
    description = ""
    last_update = ""
    header_idx = None

    for i, row in enumerate(values):
        joined = [c.strip() for c in row]
        if "Field#" in joined:
            header_idx = i
            break
        elif "ชื่อตาราง" in joined:
            j = joined.index("ชื่อตาราง")
            table_name = row[j + 1].strip() if j + 1 < len(row) else ""
        elif any(c.strip().startswith("Description") for c in row):
            j = next(k for k, c in enumerate(row) if c.strip().startswith("Description"))
            description = row[j + 1].strip() if j + 1 < len(row) else ""
        elif "LastUpdate" in joined:
            j = joined.index("LastUpdate")
            last_update = row[j + 1].strip() if j + 1 < len(row) else ""

    fields = []
    if header_idx is not None:
        header_row = [c.strip() for c in values[header_idx]]
        start = next((k for k, c in enumerate(header_row) if c == "Field#"), 0)
        for row in values[header_idx + 1:]:
            cells = row[start:start + len(FIELD_COLS)]
            if not any(c.strip() for c in cells):
                continue
            cells += [""] * (len(FIELD_COLS) - len(cells))
            fields.append(dict(zip(FIELD_COLS, [c.strip() for c in cells])))

    print(json.dumps({
        "table_name": table_name,
        "description": description,
        "last_update": last_update,
        "sheet_used": sheet_name,
        "fields": fields,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
