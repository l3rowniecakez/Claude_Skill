#!/usr/bin/env python3
"""Fill the verbatim quotes of the Evidence Map mechanically, so Agent A only has to write WHERE the evidence is, not copy WHAT it says.

In the ```evidence block under "APPENDIX A" of a REQ file an Agent may now write a line WITHOUT the quote:
        BR-003 :: EdForm/EdAcHospital.pas:366-368
and this script rewrites it to the exact form verify_evidence.py expects:
        BR-003 :: EdForm/EdAcHospital.pas:366-368 :: `if EdHosID.Text = '' then`
The quote is copied from the real file in source/ (whitespace-collapsed, comments kept), taken from the stated line range only:
all non-empty lines of the range joined with one space; if that is longer than 220 chars the FIRST non-empty line is used.
Lines that already have a quote are left untouched. A line whose file/range cannot be resolved is reported (not guessed) and left as is,
so verify_evidence.py still fails on it. Because the quote is copied, verify_evidence can no longer fail on a mistyped quote — it still
fails on a wrong file/range (which is the real "guessing" signal) and on missing coverage.

Usage: fill_evidence.py <workspace> <feature_dir_name>     (rewrites specs/<feature>/req/REQ_*.md in place; prints JSON summary)
"""
import sys, re, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from verify_evidence import Snapshot, parse_range, collapse, EV_RE      # same path resolution as the gate

for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")

NOQUOTE_RE = re.compile(r"^(\s*)([A-Z]+-\d{3})\s*::\s*([^:]+?:\d+(?:-\d+)?)\s*$")
MAXLEN = 220


def quote_for(snap, loc):
    ref, _, rng = loc.rpartition(":")
    lr = parse_range(rng)
    f, err = snap.find(ref)
    if f is None or lr is None:
        return None, err or f"bad range '{rng}'"
    L = snap.lines(f)
    a, b = lr
    if a < 1 or a > len(L):
        return None, f"line {a} outside {ref} ({len(L)} lines)"
    rows = [collapse(x) for x in L[a - 1: min(b, len(L))] if collapse(x)]
    if not rows:
        return None, f"lines {a}-{b} of {ref} are empty"
    q = " ".join(rows)
    if len(q) > MAXLEN:
        q = rows[0]
    return q.replace("`", "'") if q.startswith("`") or q.endswith("`") else q, None


def main():
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    ws, feat = Path(sys.argv[1]), sys.argv[2]
    fdir = ws / "specs" / feat
    snap = Snapshot(ws / "source")
    rep = {"feature": feat, "filled": 0, "already_quoted": 0, "unresolved": []}
    for req in sorted((fdir / "req").glob("REQ_*.md")):
        side = req.parent / "_evidence" / (req.stem + ".evidence.md")
        target = side if side.is_file() else req
        text = target.read_text(encoding="utf-8")
        head, sep, appendix = text.partition("APPENDIX A")
        if not sep:                                   # sidecar has no APPENDIX heading: whole file is the evidence block
            head, sep, appendix = "", "", text

        def fix_block(m):
            out = []
            for ln in m.group(2).split("\n"):
                nq = NOQUOTE_RE.match(ln)
                if nq:
                    q, err = quote_for(snap, nq.group(3))
                    if q is None:
                        rep["unresolved"].append({"file": req.name, "id": nq.group(2), "loc": nq.group(3), "why": err}); out.append(ln)
                    else:
                        rep["filled"] += 1; out.append(f"{nq.group(1)}{nq.group(2)} :: {nq.group(3)} :: `{q}`")
                else:
                    if EV_RE.match(ln):
                        rep["already_quoted"] += 1
                    out.append(ln)
            return m.group(1) + "\n".join(out) + m.group(3)

        new_app = re.sub(r"(```evidence\s*\n)(.*?)(```)", fix_block, appendix, flags=re.S)
        if new_app != appendix:
            target.write_text(head + sep + new_app, encoding="utf-8")
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    sys.exit(1 if rep["unresolved"] else 0)


if __name__ == "__main__":
    main()
