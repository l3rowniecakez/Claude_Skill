#!/usr/bin/env python3
"""Read-only SQL Server introspection for ER analysis (tables / views / stored procs).
Credentials come from ~/.config/grouplife-db/credentials.json (SIT .52, Mirror Prod .139, UAT .22).
Only SELECTs against catalog views / OBJECT_DEFINITION — NEVER executes the analysed procs.

Usage: db_schema.py <ip> <db: OGL|OceanLife|DataOne|...> <object_name> [<object_name> ...]
Per object prints (one JSON list):
  table -> {object, type:"table", columns:[{name,type,size,nullable,pk_order,identity,description}],
            primary_key:[...], foreign_keys:[{name,columns:[..],ref_table,ref_columns:[..]}],
            referenced_by:[{table,columns,ref_columns}], unique_indexes:[[cols],...], table_description}
  view/proc/function -> {object, type:"view"|"proc"|"function", definition:"<full source text>",
            depends_on:[{name,type}]}   (sys.sql_expression_dependencies + the source)
  missing -> {object, type:"not_found"}
Name may be "schema.name" (default schema dbo). A "db.schema.name" cross-db ref is NOT resolved here —
pass the right <db> instead.
"""
import sys, os, json
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")   # Thai text on Windows consoles (cp874/cp1252)
import pymssql

CRED = os.environ.get("GROUPLIFE_DB_CREDENTIALS") or os.path.join(
    os.path.expanduser("~"), ".config", "grouplife-db", "credentials.json")


def txt(v):
    if v is None:
        return ""
    return v.decode("utf-8", "replace") if isinstance(v, bytes) else str(v)


def main():
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    ip, db, names = sys.argv[1], sys.argv[2], sys.argv[3:]
    cred = json.load(open(CRED, encoding="utf-8")).get(ip)
    if not cred:
        print(json.dumps({"error": f"no credentials for {ip} in {CRED} — ask the user"})); sys.exit(1)
    conn = pymssql.connect(server=ip, user=cred["user"], password=cred["password"], database=db,
                           charset="UTF-8", tds_version="7.3", login_timeout=10, timeout=30)
    cur = conn.cursor(as_dict=True)
    out = []
    for name in names:
        full = name if "." in name else f"dbo.{name}"
        cur.execute("SELECT OBJECT_ID(%s) oid, (SELECT type FROM sys.objects WHERE object_id=OBJECT_ID(%s)) t", (full, full))
        r = cur.fetchone()
        if not r or not r["oid"]:
            out.append({"object": name, "type": "not_found"}); continue
        oid, t = r["oid"], (r["t"] or "").strip()
        if t == "U":
            cur.execute("""SELECT c.name, ty.name type, CASE WHEN ty.name IN ('nvarchar','nchar') THEN c.max_length/2 ELSE c.max_length END size,
                                  c.is_nullable, c.is_identity, ep.value descr,
                                  ic.key_ordinal pk_order
                           FROM sys.columns c JOIN sys.types ty ON ty.user_type_id=c.user_type_id
                           LEFT JOIN sys.extended_properties ep ON ep.major_id=c.object_id AND ep.minor_id=c.column_id AND ep.name='MS_Description'
                           LEFT JOIN sys.indexes pk ON pk.object_id=c.object_id AND pk.is_primary_key=1
                           LEFT JOIN sys.index_columns ic ON ic.object_id=pk.object_id AND ic.index_id=pk.index_id AND ic.column_id=c.column_id
                           WHERE c.object_id=%s ORDER BY c.column_id""", (oid,))
            cols = [{"name": x["name"], "type": x["type"], "size": "" if x["size"] in (None, -1) else x["size"],
                     "nullable": bool(x["is_nullable"]), "identity": bool(x["is_identity"]),
                     "pk_order": x["pk_order"] or 0, "description": txt(x["descr"]).strip()} for x in cur.fetchall()]
            cur.execute("""SELECT fk.name, OBJECT_NAME(fk.referenced_object_id) ref_table, pc.name col, rc.name ref_col, fkc.constraint_column_id o
                           FROM sys.foreign_keys fk JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id=fk.object_id
                           JOIN sys.columns pc ON pc.object_id=fkc.parent_object_id AND pc.column_id=fkc.parent_column_id
                           JOIN sys.columns rc ON rc.object_id=fkc.referenced_object_id AND rc.column_id=fkc.referenced_column_id
                           WHERE fk.parent_object_id=%s ORDER BY fk.name, fkc.constraint_column_id""", (oid,))
            fks = {}
            for x in cur.fetchall():
                f = fks.setdefault(x["name"], {"name": x["name"], "columns": [], "ref_table": x["ref_table"], "ref_columns": []})
                f["columns"].append(x["col"]); f["ref_columns"].append(x["ref_col"])
            cur.execute("""SELECT fk.name, OBJECT_NAME(fk.parent_object_id) tbl, pc.name col, rc.name ref_col
                           FROM sys.foreign_keys fk JOIN sys.foreign_key_columns fkc ON fkc.constraint_object_id=fk.object_id
                           JOIN sys.columns pc ON pc.object_id=fkc.parent_object_id AND pc.column_id=fkc.parent_column_id
                           JOIN sys.columns rc ON rc.object_id=fkc.referenced_object_id AND rc.column_id=fkc.referenced_column_id
                           WHERE fk.referenced_object_id=%s""", (oid,))
            refby = {}
            for x in cur.fetchall():
                f = refby.setdefault(x["name"], {"table": x["tbl"], "columns": [], "ref_columns": []})
                f["columns"].append(x["col"]); f["ref_columns"].append(x["ref_col"])
            cur.execute("""SELECT i.index_id, c.name FROM sys.indexes i JOIN sys.index_columns ic ON ic.object_id=i.object_id AND ic.index_id=i.index_id
                           JOIN sys.columns c ON c.object_id=ic.object_id AND c.column_id=ic.column_id
                           WHERE i.object_id=%s AND (i.is_unique=1 OR i.is_primary_key=1) AND ic.is_included_column=0 ORDER BY i.index_id, ic.key_ordinal""", (oid,))
            uq = {}
            for x in cur.fetchall():
                uq.setdefault(x["index_id"], []).append(x["name"])
            cur.execute("SELECT value FROM sys.extended_properties WHERE major_id=%s AND minor_id=0 AND name='MS_Description'", (oid,))
            d = cur.fetchone()
            out.append({"object": name, "type": "table", "table_description": txt(d["value"]).strip() if d else "",
                        "columns": cols, "primary_key": [c["name"] for c in sorted(cols, key=lambda c: c["pk_order"]) if c["pk_order"]],
                        "foreign_keys": list(fks.values()), "referenced_by": list(refby.values()),
                        "unique_indexes": list(uq.values())})
        else:
            kind = {"V": "view", "P": "proc", "FN": "function", "IF": "function", "TF": "function"}.get(t, t)
            cur.execute("SELECT OBJECT_DEFINITION(%s) d", (oid,))
            d = cur.fetchone()
            cur.execute("""SELECT DISTINCT referenced_entity_name n, o.type_desc td FROM sys.sql_expression_dependencies e
                           LEFT JOIN sys.objects o ON o.object_id=e.referenced_id
                           WHERE e.referencing_id=%s AND referenced_entity_name IS NOT NULL""", (oid,))
            deps = [{"name": x["n"], "type": x["td"] or "unresolved"} for x in cur.fetchall()]
            out.append({"object": name, "type": kind, "definition": txt(d["d"]) if d else "(encrypted/none)", "depends_on": deps})
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
