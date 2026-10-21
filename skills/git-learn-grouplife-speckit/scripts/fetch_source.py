#!/usr/bin/env python3
"""Build the READ-ONLY source snapshot that every SpecKit document of an App is derived from and verified against.

Why: the specs must match the real code 100%. Reading the code remotely every time (browse_repo.py) leaves nothing to
re-check later (verify_evidence.py, /speckit-analyze, /speckit-converge all need files on disk). So the exact files read
are mirrored once into  <workspace>/source/  and every evidence reference points into that tree.

  <workspace>/source/<repo>/<full repo path>      Delphi .pas/.dfm/.dpr read from Gitblit master (same endpoint as /git-learn-grouplife);
                                                   Thai text is restored from Gitblit's mojibake (see fix_thai) so quotes are real Thai
  <workspace>/source/.../X.dfm.digest.txt          READING AID: decoded .dfm minus layout/font/colour/blob props, `<orig line>|<line>` (scan_form.py)
  <workspace>/source/.../X.dfm.decoded.txt         .dfm with #3650#3619-style char codes turned into real Thai, SAME line numbers as the .dfm
  <workspace>/source/_db/<db>/<object>.sql         stored proc / view / function definition (OBJECT_DEFINITION, raw)
  <workspace>/source/_db/<db>/<table>.table.txt    table structure, ONE fact per line (columns / PK / FK / unique)

Everything is read-only against the origin: Gitblit web GET only, DB catalog SELECT only (via the ER skill's db_schema.py,
which never executes the analysed procs). Local copies are chmod 444. Nothing is ever pushed anywhere and the snapshot is
never uploaded to Drive (only the generated documents are).

Usage:
  fetch_source.py tree  <repo> <sub_folder> <workspace>
      -> lists every file under sub_folder (cached in source/.tree_<repo>.json); {files:[...], truncated}
  fetch_source.py files <repo> <sub_folder> <workspace> <name> [<name> ...] [--max-bytes N]
      (default limit 2,000,000 bytes per file; a bigger file such as a 6 MB MainUnit.dfm is reported in `errors` — re-run with
       --max-bytes 12000000 and then GREP it (don't Read it whole))
      <name> = "EdForm\\EdAcHospital.pas" (as in the Sheet's "Delphi Path File", relative to sub_folder) | a full repo path |
               a bare unit name "EdAcHospital" (-> its .pas AND .dfm). A .pas also pulls its sibling .dfm and vice versa.
      -> {fetched:[{path,local,lines,thai}], missing:[...], ambiguous:[{name,candidates}], matched_by_name:[...], errors:[...]}
         ambiguous / missing names are REPORTED, never guessed — resolve them by hand (browse_repo.py list) and re-run.
  fetch_source.py db    <workspace> <ip> <db> <object> [<object> ...]
      -> {saved:[{object,type,local}], not_found:[...]}    (ip = 10.100.2.52 = SIT by default; db = OGL|OceanLife|DataOne|...)
"""
import sys, os, re, json, stat, subprocess
from pathlib import Path
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")

SKILLS = Path(__file__).resolve().parents[2]          # .../skills (sibling skills live next to this one)
BROWSE_DIR = Path(os.environ.get("GROUPLIFE_BROWSE_DIR") or SKILLS / "git-learn-grouplife" / "scripts")
DBSCHEMA = Path(os.environ.get("GROUPLIFE_DB_SCHEMA") or SKILLS / "git-learn-grouplife-er-diagram" / "scripts" / "db_schema.py")


def write_ro(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(stat.S_IRUSR | stat.S_IWUSR)
    with open(path, "w", encoding="utf-8", newline="") as f:     # newline="" keeps the original CRLF
        f.write(text)
    path.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)


def load_browse():
    if not (BROWSE_DIR / "browse_repo.py").exists():
        raise SystemExit(f"git-learn-grouplife skill not found at {BROWSE_DIR} — install it (/ocean-skill-update --only git-learn-grouplife)")
    sys.path.insert(0, str(BROWSE_DIR))
    import browse_repo, gitblit_client
    return browse_repo, gitblit_client


def fix_thai(text):
    """Gitblit's raw endpoint serves the legacy cp874 (Thai) bytes of Delphi 7 sources as if they were ISO-8859-1 and
    re-encodes them as UTF-8, so every Thai string arrives as mojibake (e.g. 'ºÑ¹·Ö¡' instead of 'บันทึก'). The damage is
    exactly reversible: latin-1 -> bytes -> cp874. Applied only when every char is <= U+00FF (a file that already holds real
    Unicode is left alone) and the strict cp874 decode yields Thai letters. Returns (text, status) with status one of
    "repaired" | "not_needed" | "unrepaired" (high-latin chars present but not a clean cp874 round trip — reported, never guessed)."""
    if any(ord(c) > 0xFF for c in text):
        return text, "not_needed"
    if not any(0xA1 <= ord(c) <= 0xFF for c in text):
        return text, "not_needed"
    try:
        fixed = text.encode("latin-1").decode("cp874")
    except UnicodeDecodeError:
        return text, "unrepaired"
    if any("\u0e00" <= c <= "\u0e7f" for c in fixed):
        return fixed, "repaired"
    return text, "unrepaired"


_LIT = re.compile(r"(?:'(?:[^']|'')*'|#\d+|#\$[0-9A-Fa-f]+)+")
_TOK = re.compile(r"'((?:[^']|'')*)'|#(\d+)|#\$([0-9A-Fa-f]+)")


def decode_dfm_text(text):
    """Delphi writes non-ASCII string properties in .dfm as char codes (Caption = #3650#3619'xyz'). This returns the same text
    with every literal run that contains a #code replaced by the real characters, LINE FOR LINE (line numbers stay identical to
    the .dfm, so an evidence reference may cite either file). Control codes (< 32) are kept as #n."""
    def run(m):
        lit = m.group(0)
        if "#" not in lit.replace("''", ""):
            return lit
        out = []
        for t in _TOK.finditer(lit):
            if t.group(1) is not None:
                out.append(t.group(1).replace("''", "'"))
            else:
                n = int(t.group(2)) if t.group(2) else int(t.group(3), 16)
                out.append(chr(n) if n >= 32 else f"#{n}")
        return "'" + "".join(out).replace("'", "''") + "'"
    return "\n".join(_LIT.sub(run, ln) for ln in text.split("\n"))


def norm(p):
    return p.replace("\\", "/").strip("/")


def tree_cached(ws, repo, sub, browse, session):
    cache = Path(ws) / "source" / f".tree_{repo}.json"
    if cache.exists():
        d = json.loads(cache.read_text(encoding="utf-8"))
        if d.get("sub_folder") == norm(sub):
            return d
    # own BFS (not browse.tree): one folder the Gitblit web UI cannot list (HTTP 500, e.g. names with parentheses such as
    # "Script/GLF-1572(BOI)") must not abort the whole crawl — it is skipped and reported in `skipped_folders`
    from collections import deque
    queue, files, skipped, used = deque([norm(sub)]), [], [], 0
    while queue and used < 1500:
        path = queue.popleft()
        used += 1
        try:
            entries = browse.list_folder(session, repo, path)
        except Exception as e:                       # noqa: BLE001
            skipped.append({"folder": path, "error": str(e)[:120]}); continue
        for en in entries:
            (queue if en["type"] == "folder" else files).append(en["path"])
    d = {"sub_folder": norm(sub), "files": files, "truncated": bool(queue), "skipped_folders": skipped}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return d


def resolve(name, files, sub):
    """-> (paths, candidates, matched_by_name) ; paths = resolved full repo paths, candidates = list when ambiguous."""
    n = norm(name)
    low = {f: f.lower() for f in files}
    if "." in os.path.basename(n):
        hits = [f for f, l in low.items() if l == n.lower() or l == (norm(sub) + "/" + n).lower() or l.endswith("/" + n.lower())]
    else:
        base = n.lower()
        hits = [f for f, l in low.items() if os.path.basename(l) in (base + ".pas", base + ".dfm")]
    by_name = False
    if not hits and "/" in n:
        # the Sheet's "Delphi Path File" does not always mirror the real folder layout: fall back to the bare file name,
        # accepted only when it is unique (reported via matched_by_name so it is visible, never silent)
        bn = os.path.basename(n).lower()
        hits = [f for f, l in low.items() if os.path.basename(l) == bn]
        by_name = bool(hits)
    # several different folders holding the same unit name = ambiguous (a .pas + its .dfm in one folder is NOT ambiguous)
    dirs = {os.path.dirname(h).lower() for h in hits}
    if len(dirs) > 1:
        return [], sorted(hits), False
    return hits, [], by_name


def cmd_tree(repo, sub, ws):
    browse, gb = load_browse()
    d = tree_cached(ws, repo, sub, browse, gb.open_session())
    print(json.dumps({"files": d["files"], "truncated": d["truncated"], "count": len(d["files"]),
                      "skipped_folders": d.get("skipped_folders", [])}, ensure_ascii=False, indent=1))


def cmd_files(repo, sub, ws, names, max_bytes=2_000_000):
    browse, gb = load_browse()
    session = gb.open_session()
    d = tree_cached(ws, repo, sub, browse, session)
    files = d["files"]
    out = {"fetched": [], "missing": [], "ambiguous": [], "matched_by_name": [], "errors": []}
    want = []
    for nm in names:
        hits, amb, by_name = resolve(nm, files, sub)
        if by_name:
            out["matched_by_name"].append({"name": nm, "paths": hits})
        if amb:
            out["ambiguous"].append({"name": nm, "candidates": amb}); continue
        if not hits:
            out["missing"].append(nm); continue
        for h in hits:
            for sib in (h, re.sub(r"\.(pas|dfm)$", lambda m: ".dfm" if m.group(1).lower() == "pas" else ".pas", h, flags=re.I)):
                if sib in files and sib not in want:
                    want.append(sib)
    for p in want:
        r = browse.read_file(session, repo, p, max_bytes)
        if "error" in r:
            out["errors"].append({"path": p, "error": r["error"]}); continue
        text, thai = fix_thai(r["content"])
        local = Path(ws) / "source" / repo / p
        write_ro(local, text)
        rec = {"path": p, "local": str(local), "lines": text.count("\n") + 1, "thai": thai}
        if p.lower().endswith(".dfm"):
            side = Path(str(local) + ".decoded.txt")
            decoded = decode_dfm_text(text)
            write_ro(side, decoded)
            rec["decoded_sidecar"] = str(side)
            # reading-aid: same lines minus layout/font/colour/blob props (scan_form.py dfm); Agents Read THIS, quote from the decoded file
            sys.path.insert(0, str(Path(__file__).resolve().parent))
            from scan_form import dfm_digest
            digest = Path(str(local) + ".digest.txt")
            write_ro(digest, "\n".join(f"{n}|{l}" for n, l in dfm_digest(decoded)) + "\n")
            rec["digest"] = str(digest)
            rec["digest_saved_pct"] = round(100 * (1 - digest.stat().st_size / max(len(decoded.encode("utf-8")), 1)), 1)
        out["fetched"].append(rec)
        if thai == "unrepaired":
            out["errors"].append({"path": p, "error": "high-latin characters that are not a clean cp874 round trip — Thai text in this file may be garbled; do NOT quote it"})
    print(json.dumps(out, ensure_ascii=False, indent=1))


def table_text(o):
    L = [f"TABLE {o['object']}" + (f" -- {o['table_description']}" if o.get("table_description") else "")]
    if o["primary_key"]:
        L.append("PK: " + ", ".join(o["primary_key"]))
    for c in o["columns"]:
        size = f"({c['size']})" if c["size"] != "" else ""
        L.append(f"COL {c['name']} | {c['type']}{size} | {'NULL' if c['nullable'] else 'NOT NULL'}"
                 + (" | IDENTITY" if c["identity"] else "") + (f" | {c['description']}" if c["description"] else ""))
    for f in o["foreign_keys"]:
        L.append(f"FK {f['name']}: ({', '.join(f['columns'])}) -> {f['ref_table']}({', '.join(f['ref_columns'])})")
    for u in o["unique_indexes"]:
        L.append("UQ: (" + ", ".join(u) + ")")
    for r in o["referenced_by"]:
        L.append(f"REFERENCED_BY {r['table']}({', '.join(r['columns'])}) -> ({', '.join(r['ref_columns'])})")
    return "\n".join(L) + "\n"


def cmd_db(ws, ip, db, objs):
    if not DBSCHEMA.exists():
        raise SystemExit(f"db_schema.py not found at {DBSCHEMA} — install the git-learn-grouplife-er-diagram skill")
    r = subprocess.run([sys.executable, str(DBSCHEMA), ip, db, *objs], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise SystemExit("db_schema.py failed:\n" + (r.stdout[-800:] + r.stderr[-800:]))
    res = json.loads(r.stdout)
    out = {"saved": [], "not_found": []}
    base = Path(ws) / "source" / "_db" / db
    for o in res:
        name = o["object"].split(".")[-1]
        if o["type"] == "not_found":
            out["not_found"].append(o["object"]); continue
        if o["type"] == "table":
            p = base / f"{name}.table.txt"; write_ro(p, table_text(o))
        else:
            p = base / f"{name}.sql"; write_ro(p, o["definition"])
        out["saved"].append({"object": o["object"], "type": o["type"], "local": str(p)})
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) == 4 and a[0] == "tree":
        cmd_tree(a[1], a[2], a[3])
    elif len(a) >= 5 and a[0] == "files":
        rest, mb = a[4:], 2_000_000
        if "--max-bytes" in rest:
            i = rest.index("--max-bytes"); mb = int(rest[i + 1]); rest = rest[:i] + rest[i + 2:]
        cmd_files(a[1], a[2], a[3], rest, mb)
    elif len(a) >= 5 and a[0] == "db":
        cmd_db(a[1], a[2], a[3], a[4:])
    else:
        print(__doc__); sys.exit(1)
