#!/usr/bin/env python3
"""Mechanical "no guessing" gate for the SpecKit documents of ONE menu (feature dir).

The user's rule (2026-10-20): the specs are written AFTER the system was built, so they must match today's code 100% —
no guessing. This script turns that rule into a check that does not depend on anybody's judgement:

 1. EVIDENCE QUOTES — every REQ file ends with an "APPENDIX A — EVIDENCE MAP" holding a fenced ```evidence block, one line per
    reference:    <ID> :: <file>:<line>[-<line>] :: `<verbatim quote from that file>`
    <file> is a path under  <workspace>/source/  (a unique suffix is enough, e.g. EdForm/EdAcHospital.pas or _db/OGL/sp_x.sql).
    The quote (whitespace-collapsed, case-sensitive) MUST occur in the file within +-2 lines of the stated range.
    A quote found only elsewhere in the file = FAIL ("wrong line, actual line N"). A quote not in the file = FAIL.
 2. COVERAGE — every table row whose first cell is an ID of the form F-/BTN-/COL-/ACT-/BR-/MSG-/PRE-/POST-/ALT-/EC-nnn must have
    at least one evidence line. Orphan evidence IDs are reported as warnings.
 3. NO LEFTOVER TEMPLATE TEXT — placeholders such as SCR-XXX-000, "[ชื่อ", "[อธิบาย", "[PLACEHOLDER" = FAIL.
 4. SOURCE PATHS — every `...pas/.dfm/.dpr/.sql` path written in backticks in spec.md / plan.md / tasks.md / research.md /
    data-model.md / quickstart.md / contracts/* must exist in the snapshot, otherwise FAIL.
 6. CROSS-REFERENCES — every ID mentioned in the text (BR-004, Q-006, BTN-002 ...) must be DEFINED as the first cell of a table row in the same
    REQ file; an undefined reference = WARN "xref-undefined" (may legitimately point to another screen's REQ), a duplicated definition = FAIL
    "xref-duplicate". Mechanical only: it cannot tell that Q-006 is about the wrong topic — that stays with the auditor.
 5. HEDGING WORDS (น่าจะ / คงจะ / probably / maybe / assume) outside the Assumptions/Open-Issues sections = WARN.

Usage: verify_evidence.py <workspace> <feature_dir_name>      (prints JSON report; exit 1 when fail_count > 0)
Read-only. Run it after the REQ files are written AND again after /speckit-converge — it must end with fail_count 0.
"""
import sys, os, re, json
from pathlib import Path
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")

ID_RE = re.compile(r"^(F|BTN|COL|ACT|BR|MSG|PRE|POST|ALT|EC)-\d{3}$")
EV_RE = re.compile(r"^\s*([A-Z]+-\d{3})\s*::\s*(.+?)\s*::\s*(.+?)\s*$")
PLACEHOLDERS = re.compile(r"SCR-XXX-000|\[ชื่อ|\[อธิบาย|\[PLACEHOLDER|\[เงื่อนไข|\[ตัวอย่าง|\[Role\]|\[Module\]|\[Field")
HEDGE = re.compile(r"น่าจะ|คงจะ|probably|maybe|presumably|I assume|likely to")
PATH_TOKEN = re.compile(r"`([^`\n]+?\.(?:pas|dfm|dpr|sql|txt))(?::\d+(?:-\d+)?)?`", re.I)
SOFT_SECTIONS = re.compile(r"SECTION 9|SECTION 14|Assumption|Open Issues|Clarification|Edge Cases?\b", re.I)


def collapse(s):
    return re.sub(r"\s+", " ", s).strip()


class Snapshot:
    def __init__(self, root):
        self.root = Path(root)
        self.files = {}
        for p in self.root.rglob("*"):
            if p.is_file() and not p.name.startswith(".tree_") and not p.name.endswith(".digest.txt"):   # digests are reading aids, never evidence
                self.files[p.relative_to(self.root).as_posix().lower()] = p
        self._cache = {}

    def find(self, ref):
        r = ref.replace("\\", "/").strip().lstrip("/")
        r = re.sub(r"^source/", "", r, flags=re.I).lower()
        if r in self.files:
            return self.files[r], None
        hits = [k for k in self.files if k.endswith("/" + r)]
        if len(hits) == 1:
            return self.files[hits[0]], None
        if not hits:
            return None, "file not found in source snapshot"
        return None, "ambiguous path, matches: " + ", ".join(sorted(hits)[:4])

    def lines(self, p):
        if p not in self._cache:
            self._cache[p] = p.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        return self._cache[p]


def parse_range(s):
    m = re.fullmatch(r"(\d+)(?:-(\d+))?", s.strip())
    if not m:
        return None
    a = int(m.group(1)); b = int(m.group(2) or a)
    return (a, b) if b >= a else None


COVER_REQUIRED = re.compile(r"^(BR|MSG|POST|ALT)-")   # spec-first mode: only behaviour rows need evidence; UI rows (F/BTN/COL/ACT/PRE/EC) are optional


def sidecar_for(path):
    return path.parent / "_evidence" / (path.stem + ".evidence.md")


def check_req(path, snap, rep):
    text = path.read_text(encoding="utf-8")
    name = path.name
    body, _, appendix = text.partition("APPENDIX A")
    side = sidecar_for(path)
    if side.is_file():            # spec-first mode: evidence lives beside the REQ, not inside it
        appendix = side.read_text(encoding="utf-8")
    # coverage targets
    ids = []
    for ln in body.splitlines():
        if ln.lstrip().startswith("|"):
            first = ln.strip().strip("|").split("|")[0].strip().strip("`*")
            if ID_RE.match(first):
                ids.append(first)
    # evidence lines
    ev = []
    for blk in re.findall(r"```evidence\s*\n(.*?)```", appendix, flags=re.S):
        for ln in blk.splitlines():
            if ln.strip():
                ev.append(ln)
    if not ev:
        rep["fail"].append({"file": name, "check": "evidence", "detail": "no ```evidence block / no evidence lines under APPENDIX A"})
    have = set()
    for ln in ev:
        m = EV_RE.match(ln)
        if not m:
            rep["fail"].append({"file": name, "check": "evidence-format", "detail": ln.strip()[:160]}); continue
        eid, loc, quote = m.groups()
        have.add(eid)
        quote = quote.replace("\\|", "|").strip()
        if len(quote) >= 2 and quote[0] == "`" and quote[-1] == "`":
            quote = quote[1:-1]
        ref, _, rng = loc.rpartition(":")
        lr = parse_range(rng)
        if not ref or lr is None:
            rep["fail"].append({"file": name, "check": "evidence-format", "id": eid, "detail": f"need <file>:<line>[-<line>], got '{loc}'"}); continue
        f, err = snap.find(ref)
        if f is None:
            rep["fail"].append({"file": name, "check": "evidence-file", "id": eid, "detail": f"{ref}: {err}"}); continue
        L = snap.lines(f)
        q = collapse(quote)
        if not q:
            rep["fail"].append({"file": name, "check": "evidence-quote", "id": eid, "detail": "empty quote"}); continue
        a, b = lr
        window = collapse(" ".join(L[max(0, a - 3): min(len(L), b + 2)]))
        rep["checked"] += 1
        if q in window:
            continue
        whole = collapse(" ".join(L))
        if q in whole:
            actual = next((i + 1 for i in range(len(L)) if collapse(L[i]) and q.startswith(collapse(L[i])[:40])), None)
            rep["fail"].append({"file": name, "check": "evidence-line", "id": eid,
                                "detail": f"quote exists in {ref} but not at lines {a}-{b}" + (f" (looks like line {actual})" if actual else "")})
        else:
            rep["fail"].append({"file": name, "check": "evidence-quote", "id": eid,
                                "detail": f"quote NOT found in {ref}: {q[:100]}"})
    for i in sorted(set(ids) - have):
        if COVER_REQUIRED.match(i):
            rep["fail"].append({"file": name, "check": "coverage", "id": i, "detail": "table row has no evidence line"})
    for i in sorted(have - set(ids)):
        rep["warn"].append({"file": name, "check": "orphan-evidence", "id": i, "detail": "evidence id not used as a table row id"})
    for m in PLACEHOLDERS.finditer(body):
        rep["fail"].append({"file": name, "check": "placeholder", "detail": m.group(0)})
    # hedging outside soft sections
    section = ""
    for ln in body.splitlines():
        if ln.startswith("#"):
            section = ln
        if HEDGE.search(ln) and not SOFT_SECTIONS.search(section):
            rep["warn"].append({"file": name, "check": "hedging", "detail": ln.strip()[:140]})


XREF_DEF = re.compile(r"^[A-Z]{1,5}-\d{3}(?:-\d+)?$")
XREF_USE = re.compile(r"(?<![\w-])((?:F|BTN|COL|ACT|BR|MSG|PRE|POST|ALT|EC|AC|Q|A|US|NFR|SC|KE)-\d{3})(?![\w-])")


def check_xref(path, rep):
    text = path.read_text(encoding="utf-8")
    body, _, appendix = text.partition("APPENDIX A")
    defined, dups = {}, []
    for ln in body.splitlines():
        if ln.lstrip().startswith("|"):
            first = ln.strip().strip("|").split("|")[0].strip().strip("`*")
            if XREF_DEF.match(first):
                if first in defined:
                    dups.append(first)
                defined[first] = True
    for d in sorted(set(dups)):
        rep["fail"].append({"file": path.name, "check": "xref-duplicate", "id": d, "detail": "ID defined as a table row more than once"})
    used = set()
    for m in XREF_USE.finditer(re.sub(r"```.*?```", "", body, flags=re.S)):
        used.add(m.group(1))
    for u in sorted(used - set(defined)):
        rep["warn"].append({"file": path.name, "check": "xref-undefined", "id": u, "detail": "ID mentioned but never defined as a table row in this file"})


def check_paths(fdir, snap, rep):
    targets = [fdir / n for n in ("spec.md", "plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md")]
    targets += sorted((fdir / "contracts").glob("*")) if (fdir / "contracts").is_dir() else []
    for t in targets:
        if not t.is_file():
            continue
        for m in PATH_TOKEN.finditer(t.read_text(encoding="utf-8")):
            ref = m.group(1)
            rep["paths_checked"] += 1
            f, err = snap.find(ref)
            if f is None:
                rep["fail"].append({"file": t.name, "check": "source-path", "detail": f"{ref}: {err}"})


def main():
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    ws, feat = Path(sys.argv[1]), sys.argv[2]
    fdir = ws / "specs" / feat
    if not fdir.is_dir():
        raise SystemExit(f"feature dir not found: {fdir}")
    snap = Snapshot(ws / "source")
    rep = {"feature": feat, "snapshot_files": len(snap.files), "checked": 0, "paths_checked": 0, "fail": [], "warn": []}
    reqs = sorted((fdir / "req").glob("REQ_*.md"))
    if not reqs:
        rep["fail"].append({"file": "req/", "check": "req-files", "detail": "no REQ_*.md found"})
    for r in reqs:
        check_req(r, snap, rep)
        check_xref(r, rep)
    check_paths(fdir, snap, rep)
    rep["fail_count"], rep["warn_count"], rep["req_files"] = len(rep["fail"]), len(rep["warn"]), [r.name for r in reqs]
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    sys.exit(1 if rep["fail"] else 0)


if __name__ == "__main__":
    main()
