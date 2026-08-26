#!/usr/bin/env python3
"""Find / append / update-row in one Data Dictionary INDEX sheet (the first
page — "Data One" / "OceanLife" / "OGL" tab of the master spreadsheet
1qHeg391cRNrGA1HC3cWxsv9HcJZS0POuI94uaR27cqU).

SAFETY: every write here touches at most ONE row, and only the specific
columns given — never a full column, never a sort, never a delete. `append`
and `update-row` both re-verify the target row before writing (append checks
the target row's Table Name cell is truly blank; update-row checks it matches
the expected table name) so a stale row-number never clobbers someone else's
table.

Usage:
  dic_index.py find <sheet_name> <table_name>
      Exact (case-insensitive) match on Table Name. Prints JSON:
      {"found": true, "row_number": <1-indexed sheet row>, "link": "...",
       "max_column_id_used": ..., "assign": "...", "description": "..."}
      or {"found": false}

  echo '{"Table Name": "...", "...": ...}' | dic_index.py append <sheet_name>
      Appends ONE new row right after the last row that has a Table Name,
      using an explicit row number (never Sheets' auto-detect). Keys in the
      JSON must match this sheet's header text exactly (see SKILL.md for the
      header list per sheet — it differs slightly between Data One /
      OceanLife / OGL). "No." is computed automatically, do not pass it.
      Prints JSON: {"row_number": ..., "no": ...}

  echo '{"Max_Column_id_used": 12}' | dic_index.py update-row <sheet_name> <row_number> <expected_table_name>
      Updates only the given header->value cells on an EXISTING row. Refuses
      (prints {"error": ...}, writes nothing) if the row's current Table Name
      does not exactly match <expected_table_name>.
"""
import sys
import os
import json

sys.path.insert(0, os.path.expanduser("~/.config/claude-google-access"))
from read_sheet import get_service  # noqa: E402

# Default is the original author's own Data Dictionary master spreadsheet —
# override with your own via the DD_MASTER_SPREADSHEET_ID environment
# variable (or just edit this constant) to point at your own index sheet.
MASTER_SPREADSHEET_ID = os.environ.get("DD_MASTER_SPREADSHEET_ID", "1qHeg391cRNrGA1HC3cWxsv9HcJZS0POuI94uaR27cqU")


def find_header_row(values):
    for i, row in enumerate(values):
        for cell in row:
            if str(cell).strip() == "Table Name":
                return i
    return None


def col_letter(idx):
    """0-based column index -> A1 column letter."""
    letters = ""
    idx += 1
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


def header_index_map(header_row):
    m = {}
    for j, cell in enumerate(header_row):
        name = str(cell).strip()
        if name and name not in m:
            m[name] = j
    return m


def get_cell(row, idx):
    if idx is None or idx >= len(row):
        return ""
    return row[idx]


def load_sheet(service, sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=MASTER_SPREADSHEET_ID,
        range=f"'{sheet_name}'",
        valueRenderOption="FORMULA",
    ).execute()
    return result.get("values", [])


def cmd_find(service, sheet_name, table_name):
    values = load_sheet(service, sheet_name)
    header_idx = find_header_row(values)
    if header_idx is None:
        print(json.dumps({"error": f"header row not found in sheet '{sheet_name}'"}))
        return
    hmap = header_index_map(values[header_idx])
    name_idx = hmap.get("Table Name")
    link_idx = hmap.get("Link")
    max_col_idx = hmap.get("Max_Column_id_used")
    assign_idx = hmap.get("Assign")
    desc_idx = hmap.get("คำอธิบายตาราง")

    target = table_name.strip().lower()
    for i, row in enumerate(values[header_idx + 1:], start=header_idx + 2):
        name = str(get_cell(row, name_idx)).strip()
        if name.lower() == target:
            link = str(get_cell(row, link_idx)).strip()
            # `link` not starting with http means one of two things — the
            # caller must ask the user which, never assume:
            #   (a) no Link Sheet was ever created — the cell is just a bare
            #       placeholder label (e.g. literally the text "Link") with
            #       nothing behind it, or
            #   (b) a Link Sheet exists but is attached via a Google Sheets
            #       "smart chip" (Insert > Link, shown as a preview card)
            #       instead of a plain URL / HYPERLINK() formula — the Sheets
            #       API cannot read a smart chip's target URL at all
            #       (values.get returns just the chip's label text).
            link_is_chip = bool(link) and not link.lower().startswith("http")
            print(json.dumps({
                "found": True,
                "row_number": i,
                "link": link,
                "link_is_chip": link_is_chip,
                "max_column_id_used": get_cell(row, max_col_idx),
                "assign": str(get_cell(row, assign_idx)).strip(),
                "description": str(get_cell(row, desc_idx)).strip(),
            }, ensure_ascii=False))
            return
    print(json.dumps({"found": False}))


def cmd_append(service, sheet_name, payload):
    values = load_sheet(service, sheet_name)
    header_idx = find_header_row(values)
    if header_idx is None:
        print(json.dumps({"error": f"header row not found in sheet '{sheet_name}'"}))
        return
    header_row = values[header_idx]
    hmap = header_index_map(header_row)
    name_idx = hmap.get("Table Name")
    no_idx = hmap.get("No.")

    if "Table Name" not in payload or not str(payload["Table Name"]).strip():
        print(json.dumps({"error": "payload must include a non-empty 'Table Name'"}))
        return
    new_name = str(payload["Table Name"]).strip()

    # Find the true last data row (last row with a non-empty Table Name) and
    # the highest No. seen, scanning ALL rows after the header — not just
    # relying on sheet rowCount, so a fully-blank trailing block still lands
    # right after the real data.
    last_data_row = header_idx  # 0-indexed into `values`
    last_no = 0
    for i, row in enumerate(values[header_idx + 1:], start=header_idx + 1):
        name = str(get_cell(row, name_idx)).strip()
        if name:
            last_data_row = i
            no_val = get_cell(row, no_idx)
            try:
                last_no = max(last_no, int(no_val))
            except (TypeError, ValueError):
                pass
        if name.lower() == new_name.lower():
            print(json.dumps({"error": f"'{new_name}' already exists at row {i + 1} — use update-row instead, do not append a duplicate"}))
            return

    target_row_0idx = last_data_row + 1  # 0-indexed
    target_row_number = target_row_0idx + 1  # 1-indexed sheet row

    # Re-verify the target row is actually blank before writing anything —
    # never overwrite a row that might belong to someone else.
    if target_row_0idx < len(values):
        existing = values[target_row_0idx]
        existing_name = str(get_cell(existing, name_idx)).strip()
        if existing_name:
            print(json.dumps({"error": f"refusing to append: row {target_row_number} is not blank (Table Name='{existing_name}')"}))
            return

    payload = dict(payload)
    payload["No."] = last_no + 1

    # Build the row as a list of (col_letter, value) writes — one per given
    # key — instead of one wide range, so unrelated columns on this brand-new
    # row are left completely untouched (they're blank anyway, but this keeps
    # the same narrow-write discipline as update-row).
    data = []
    unknown_keys = []
    for key, value in payload.items():
        idx = hmap.get(key)
        if idx is None:
            unknown_keys.append(key)
            continue
        rng = f"'{sheet_name}'!{col_letter(idx)}{target_row_number}"
        data.append({"range": rng, "values": [[value]]})

    if unknown_keys:
        print(json.dumps({"error": f"unknown header(s) for sheet '{sheet_name}': {unknown_keys} — check exact header spelling in SKILL.md"}))
        return

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=MASTER_SPREADSHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()

    print(json.dumps({"row_number": target_row_number, "no": payload["No."]}))


def cmd_update_row(service, sheet_name, row_number, expected_table_name, payload):
    values = load_sheet(service, sheet_name)
    header_idx = find_header_row(values)
    if header_idx is None:
        print(json.dumps({"error": f"header row not found in sheet '{sheet_name}'"}))
        return
    hmap = header_index_map(values[header_idx])
    name_idx = hmap.get("Table Name")

    row_0idx = row_number - 1
    if row_0idx < 0 or row_0idx >= len(values):
        print(json.dumps({"error": f"row {row_number} is out of range"}))
        return
    actual_name = str(get_cell(values[row_0idx], name_idx)).strip()
    if actual_name.lower() != expected_table_name.strip().lower():
        print(json.dumps({"error": f"refusing to update row {row_number}: expected Table Name '{expected_table_name}' but found '{actual_name}'"}))
        return

    data = []
    unknown_keys = []
    for key, value in payload.items():
        idx = hmap.get(key)
        if idx is None:
            unknown_keys.append(key)
            continue
        rng = f"'{sheet_name}'!{col_letter(idx)}{row_number}"
        data.append({"range": rng, "values": [[value]]})

    if unknown_keys:
        print(json.dumps({"error": f"unknown header(s) for sheet '{sheet_name}': {unknown_keys}"}))
        return
    if not data:
        print(json.dumps({"error": "no recognized fields to update"}))
        return

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=MASTER_SPREADSHEET_ID,
        body={"valueInputOption": "USER_ENTERED", "data": data},
    ).execute()

    print(json.dumps({"row_number": row_number, "updated": list(payload.keys())}))


def main():
    mode = sys.argv[1]
    service = get_service()

    if mode == "find":
        cmd_find(service, sys.argv[2], sys.argv[3])
    elif mode == "append":
        sheet_name = sys.argv[2]
        payload = json.load(sys.stdin)
        cmd_append(service, sheet_name, payload)
    elif mode == "update-row":
        sheet_name = sys.argv[2]
        row_number = int(sys.argv[3])
        expected_table_name = sys.argv[4]
        payload = json.load(sys.stdin)
        cmd_update_row(service, sheet_name, row_number, expected_table_name, payload)
    else:
        print(json.dumps({"error": f"unknown mode '{mode}'"}))


if __name__ == "__main__":
    main()
