#!/usr/bin/env python3
"""Query the LIVE column structure of one table from a group-insurance SQL Server DB.

Usage:
  db_columns.py <ip> <db_name: dataone|oceanlife|ogl> <table_name>

Prints JSON: {db, table, table_description, columns: [{field, type, size,
nullable, description}]} on success, or {"error": "..."} if the server/db/
table isn't reachable or doesn't exist. Read-only — never writes to the DB.
"""
import os
import sys
import json

import pymssql

# Fill in your own SQL Server login(s) here (per-environment IP -> (user,
# password)) — DO NOT hardcode real passwords in a file that gets committed
# to a shared/public repo. Any IP not listed here falls back to the
# DD_DB_USER / DD_DB_PASSWORD environment variables, and if those aren't set
# either, the caller must ask the user for fresh credentials instead of
# guessing.
DB_CREDENTIALS = {
    # "<your-db-server-ip>": ("<db-user>", "<db-password>"),
}

DB_NAME_MAP = {
    "dataone": "DataOne",
    "data one": "DataOne",
    "oceanlife": "OceanLife",
    "ocean life": "OceanLife",
    "ogl": "OGL",
}


def as_text(value):
    """MS_Description comes back via sql_variant — pymssql sometimes hands
    that back as raw UTF-8 bytes instead of str. Normalize to str."""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def main():
    if len(sys.argv) < 4:
        print(json.dumps({"error": "usage: db_columns.py <ip> <db_name> <table_name>"}))
        return

    ip = sys.argv[1].strip()
    db_arg = sys.argv[2].strip()
    table_name = sys.argv[3].strip()

    db_name = DB_NAME_MAP.get(db_arg.lower())
    if not db_name:
        print(json.dumps({"error": f"unknown db '{db_arg}', expected one of: dataone, oceanlife, ogl"}))
        return

    creds = DB_CREDENTIALS.get(ip)
    if not creds and os.environ.get("DD_DB_USER") and os.environ.get("DD_DB_PASSWORD"):
        creds = (os.environ["DD_DB_USER"], os.environ["DD_DB_PASSWORD"])
    if not creds:
        print(json.dumps({"error": f"no credentials for IP '{ip}' — add it to DB_CREDENTIALS or set DD_DB_USER/DD_DB_PASSWORD, or ask the user for user/password first"}))
        return
    user, password = creds

    try:
        conn = pymssql.connect(server=ip, user=user, password=password, database=db_name,
                                charset='UTF-8', tds_version='7.3', login_timeout=10, timeout=15)
    except Exception as e:
        print(json.dumps({"error": f"connection to {ip}/{db_name} failed: {e}"}))
        return

    cur = conn.cursor(as_dict=True)
    full_name = f"dbo.{table_name}"
    cur.execute("SELECT OBJECT_ID(%s) AS oid", (full_name,))
    row = cur.fetchone()
    if not row or not row["oid"]:
        print(json.dumps({"error": f"table '{table_name}' not found in {db_name} @ {ip}"}))
        return

    cur.execute("""
        SELECT ep.value AS description
        FROM sys.extended_properties ep
        WHERE ep.major_id = OBJECT_ID(%s) AND ep.minor_id = 0 AND ep.name = 'MS_Description'
    """, (full_name,))
    trow = cur.fetchone()
    table_description = as_text(trow.get("description")) if trow else ""

    cur.execute("""
        SELECT
          c.name AS field,
          t.name AS type,
          CASE WHEN t.name IN ('nvarchar','nchar') THEN c.max_length/2 ELSE c.max_length END AS size,
          c.is_nullable,
          ep.value AS description
        FROM sys.columns c
        JOIN sys.types t ON c.user_type_id = t.user_type_id
        LEFT JOIN sys.extended_properties ep
          ON ep.major_id = c.object_id AND ep.minor_id = c.column_id AND ep.name = 'MS_Description'
        WHERE c.object_id = OBJECT_ID(%s)
        ORDER BY c.column_id
    """, (full_name,))

    columns = []
    for r in cur.fetchall():
        size = r["size"]
        columns.append({
            "field": r["field"],
            "type": r["type"],
            "size": "" if size in (None, -1) else size,
            "nullable": "Y" if r["is_nullable"] else "N",
            "description": as_text(r["description"]).strip(),
        })

    print(json.dumps({
        "db": db_name,
        "table": table_name,
        "table_description": table_description.strip(),
        "columns": columns,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
