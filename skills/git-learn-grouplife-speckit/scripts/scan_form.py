#!/usr/bin/env python3
"""Deterministic pre-processing of the source snapshot so Agents read LESS without losing any requirement-relevant fact.

Everything here is read-only and mechanical (no judgement): it only DROPS text that cannot carry a requirement (layout / font /
colour / image blobs) or INDEXES text so an Agent can Read just the part it needs. Original line numbers are always kept, so every
quote an Agent takes can still be cited against the real file in source/ (verify_evidence.py checks the real file, never a digest).

  scan_form.py dfm    <X.dfm.decoded.txt|X.dfm> [--out FILE]
      -> digest: `<orig line no>|<original line>` for every line EXCEPT layout/font/colour props and binary blobs (Picture.Data,
         Glyph.Data, ...) and `end` lines (indentation already shows nesting). Unknown properties are KEPT (blacklist, not whitelist).
         Written next to the source as X.dfm.digest.txt (chmod 444) unless --out. Prints {orig_bytes, digest_bytes, saved_pct}.
  scan_form.py events <X.dfm.decoded.txt>
      -> JSON {handler_name: [{component, class, caption, event, line}]} — which button/menu/grid fires which handler.
  scan_form.py pas    <X.pas>
      -> JSON index: uses lists, form class, every method with first/last line of its span (Read just that range), and a
         one-line list of referenced project-form variables.
  scan_form.py body   <X.pas> <Method> [<Method> ...]
      -> prints the method bodies with line numbers (`<line>|<text>`). <Method> = `Edit` or `TEdAcHospitalForm.Edit`.
  scan_form.py opens  <trunk_dir_with_dpr> <X.pas> [<Y.pas> ...] [--depth N]
      -> JSON {child_forms, external_programs, generic_open_calls}: every place the given .pas files open another project form
         (reference to any form variable declared in the .dpr, `TForm.Create`, Application.CreateForm), every
         WinExec/ShellExecute/CreateProcess, and every ShowModal/FindShowForm/OpenModalForm-style call. Comments and string
         literals are ignored. Each hit has line, enclosing method, quoted source line, and (via the .dfm) the component that fires
         that handler. This is a SCAN to be confirmed by reading the method; it is meant to replace hand-grepping, not judgement.
"""
import sys, os, re, json, stat
from pathlib import Path
for _s in (sys.stdin, sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")

# ---------------------------------------------------------------- dfm digest
DROP_EXACT = {
    "Left", "Top", "Width", "Height", "ClientWidth", "ClientHeight", "Color", "ParentColor", "ParentFont", "ParentBiDiMode",
    "TabOrder", "TabStop", "Align", "Anchors", "AutoSize", "Transparent", "Layout", "Alignment", "Cursor", "PixelsPerInch",
    "TextHeight", "OldCreateOrder", "ShowHint", "ParentShowHint", "BevelInner", "BevelOuter", "BevelKind", "BevelWidth",
    "BorderStyle", "BorderWidth", "Ctl3D", "ParentCtl3D", "Center", "Stretch", "Proportional", "Spacing", "Margin", "Flat",
    "ColCount", "DefaultColWidth", "DefaultRowHeight", "RowCount", "FixedCols", "FixedRows", "GridLineWidth", "ScrollBars",
    "WordWrap", "Pitch", "Position", "WindowState", "ImeName", "ImeMode", "Kind", "Glyph", "NumGlyphs", "Layout", "Indent",
    "ExplicitLeft", "ExplicitTop", "ExplicitWidth", "ExplicitHeight", "HorzScrollBar.Tracking", "VertScrollBar.Tracking",
    "Offset", "Frame.Style", "Frame.Width", "Alignment", "ParentBackground", "DoubleBuffered", "DragCursor", "DragKind",
    "DragMode", "FullRepaint", "Locked", "HeaderAlignmentHorz", "HeaderAlignmentVert", "Size", "MinWidth", "HeaderGlyphAlignmentHorz",
}
DROP_PREFIX = (
    "Font.", "Style.Font", "Style.Color", "Style.BorderColor", "Style.BorderStyle", "Style.Edges", "Style.Shadow", "Style.TextStyle",
    "Style.IsFontAssigned", "Style.LookAndFeel", "StyleFocused.", "StyleHot.", "StyleDisabled.", "LookAndFeel.", "Margins.",
    "Constraints.", "Properties.Alignment", "Properties.Buttons.Glyph", "Appearance.", "ParentFont", "Bands.Font",
    "OptionsView.Band", "HorzScrollBar.", "VertScrollBar.", "Gradient", "Header.Font", "Title.Font", "Title.Color", "Title.Alignment",
    "Styles.", "Painter", "Position.BandIndex", "Position.ColIndex", "Position.RowIndex", "Position.LineCount",
)
OPEN_MULTI = re.compile(r"=\s*[\{\(<]\s*$")          # value continues on following lines
PROP_RE = re.compile(r"^(\s*)([A-Za-z_][\w.]*)\s*=\s*(.*)$")
CLOSERS = {"{": "}", "(": ")", "<": ">"}


def _droppable(name):
    return name in DROP_EXACT or name.startswith(DROP_PREFIX)


def dfm_digest(text):
    """yield (lineno, line) for the lines worth reading"""
    out, skip_close = [], None
    for no, raw in enumerate(text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), 1):
        line = raw.rstrip()
        if skip_close:                                    # inside a dropped multi-line value
            if line.endswith(skip_close):
                skip_close = None
            continue
        s = line.strip()
        if not s or s == "end":
            continue
        m = PROP_RE.match(line)
        if m:
            name, value = m.group(2), m.group(3)
            blob = OPEN_MULTI.search(line) and line.rstrip().endswith("{")      # binary blob: always dropped
            if blob or _droppable(name):
                if OPEN_MULTI.search(line):
                    skip_close = CLOSERS[line.rstrip()[-1]]
                continue
        out.append((no, line))
    return out


def cmd_dfm(args):
    out = None
    if "--out" in args:
        i = args.index("--out"); out = Path(args[i + 1]); del args[i:i + 2]
    src = Path(args[0])
    text = src.read_text(encoding="utf-8", errors="replace")
    rows = dfm_digest(text)
    digest = "\n".join(f"{n}|{l}" for n, l in rows) + "\n"
    dest = out or src.with_name(src.name.replace(".decoded.txt", "") + ".digest.txt")
    if dest.exists():
        dest.chmod(stat.S_IRUSR | stat.S_IWUSR)
    dest.write_text(digest, encoding="utf-8")
    dest.chmod(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
    ob, db = len(text.encode("utf-8")), len(digest.encode("utf-8"))
    print(json.dumps({"digest": str(dest), "orig_bytes": ob, "digest_bytes": db, "saved_pct": round(100 * (1 - db / max(ob, 1)), 1)}, ensure_ascii=False))


# ---------------------------------------------------------------- dfm events
OBJ_RE = re.compile(r"^(\s*)(?:object|inherited|inline)\s+(\w+)\s*:\s*(\w+)")
EVT_RE = re.compile(r"^\s*((?:\w+\.)*On[A-Z]\w*)\s*=\s*(?!(?:True|False)\s*$)(\w+)\s*$")   # real events only: OnXxx = Handler (not OneOnRow = True)
CAP_RE = re.compile(r"^(\s*)Caption\s*=\s*(.*)$")


def dfm_events(text):
    stack, ev = [], {}
    for no, raw in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        m = OBJ_RE.match(raw)
        if m:
            ind = len(m.group(1))
            while stack and stack[-1]["indent"] >= ind:
                stack.pop()
            stack.append({"indent": ind, "name": m.group(2), "class": m.group(3), "caption": None})
            continue
        if not stack:
            continue
        c = CAP_RE.match(raw)
        if c and len(c.group(1)) == stack[-1]["indent"] + 2:
            stack[-1]["caption"] = c.group(2).strip().strip("'")
            continue
        e = EVT_RE.match(raw)
        if e:
            o = stack[-1]
            ev.setdefault(e.group(2), []).append({"component": o["name"], "class": o["class"], "caption": o["caption"], "event": e.group(1), "line": no})
    return ev


def cmd_events(args):
    print(json.dumps(dfm_events(Path(args[0]).read_text(encoding="utf-8", errors="replace")), ensure_ascii=False, indent=1))


# ---------------------------------------------------------------- pascal helpers
def strip_comments(src):
    """blank out comments AND string literals' content, keeping every newline so line numbers stay identical"""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == "'":
            j = i + 1
            while j < n:
                if src[j] == "'":
                    if j + 1 < n and src[j + 1] == "'":
                        j += 2; continue
                    break
                if src[j] == "\n":
                    break
                j += 1
            seg = src[i:j + 1]
            out.append("'" + re.sub(r"[^\n]", " ", seg[1:-1]) + "'" if len(seg) >= 2 else seg)
            i = j + 1
        elif c == "/" and src.startswith("//", i):
            j = src.find("\n", i); j = n if j < 0 else j
            out.append(" " * (j - i)); i = j
        elif c == "{":
            j = src.find("}", i); j = n - 1 if j < 0 else j
            out.append(re.sub(r"[^\n]", " ", src[i:j + 1])); i = j + 1
        elif c == "(" and src.startswith("(*", i):
            j = src.find("*)", i); j = n - 2 if j < 0 else j
            out.append(re.sub(r"[^\n]", " ", src[i:j + 2])); i = j + 2
        else:
            out.append(c); i += 1
    return "".join(out)


METH_RE = re.compile(r"^\s*(?:class\s+)?(procedure|function|constructor|destructor)\s+([A-Za-z_][\w.]*)", re.I)


def read_pas(p):
    raw = Path(p).read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    return raw, strip_comments(raw)


def method_index(clean):
    lines = clean.split("\n")
    impl = next((i for i, l in enumerate(lines) if re.match(r"^\s*implementation\b", l, re.I)), None)
    if impl is None:
        return []
    starts = []
    for i in range(impl, len(lines)):
        m = METH_RE.match(lines[i])
        # real definitions in the implementation section are `procedure TX.Name(` at column 0
        if m and not lines[i].startswith((" ", "\t")):
            starts.append((i + 1, m.group(1).lower(), m.group(2)))
    tail = next((i + 1 for i in range(len(lines) - 1, -1, -1) if re.match(r"^\s*(initialization|finalization|end\.)", lines[i], re.I)), len(lines))
    res = []
    for k, (ln, kind, name) in enumerate(starts):
        end = (starts[k + 1][0] - 1) if k + 1 < len(starts) else tail - 1
        while end > ln and not lines[end - 1].strip():
            end -= 1
        res.append({"method": name, "kind": kind, "first_line": ln, "last_line": end})
    return res


def enclosing(idx, line):
    for m in idx:
        if m["first_line"] <= line <= m["last_line"]:
            return m["method"]
    return None


def cmd_pas(args):
    raw, clean = read_pas(args[0])
    uses = []
    for m in re.finditer(r"\buses\b(.*?);", clean, re.S | re.I):
        uses.append([u.strip() for u in m.group(1).split(",") if u.strip() and not re.match(r"^(dx|cx|Dev|Vcl\.)", u.strip())])
    cls = re.findall(r"^\s*(T\w+)\s*=\s*class\s*\(", clean, re.M)
    idx = method_index(clean)
    print(json.dumps({"file": args[0], "lines": raw.count("\n") + 1, "classes": cls, "uses_interface_then_implementation": uses,
                      "methods": idx}, ensure_ascii=False, indent=1))


def cmd_body(args):
    raw, clean = read_pas(args[0])
    idx = method_index(clean)
    L = raw.split("\n")
    for want in args[1:]:
        hits = [m for m in idx if m["method"].lower() == want.lower() or m["method"].lower().endswith("." + want.lower())]
        if not hits:
            print(f"### {want}: NOT FOUND"); continue
        for m in hits:
            print(f"### {m['method']}  lines {m['first_line']}-{m['last_line']}")
            for n in range(m["first_line"], m["last_line"] + 1):
                print(f"{n}|{L[n - 1]}")


# ---------------------------------------------------------------- child-form scan
DPR_UNIT = re.compile(r"^\s*(\w+)\s+in\s+'([^']+)'\s*(?:\{([^}]*)\})?", re.M)
OPEN_PATTERNS = re.compile(r"\b(ShowModal|FindShowForm|OpenModalForm|FindShowModalForm|OpenFormMenu|ShowMe|CreateForm)\b", re.I)
EXT_PATTERNS = re.compile(r"\b(WinExec|ShellExecute\w*|CreateProcess\w*)\b", re.I)


def dpr_forms(trunk):
    dprs = sorted(Path(trunk).glob("*.dpr"))
    if not dprs:
        raise SystemExit(f"no .dpr in {trunk}")
    forms = {}                                              # form var -> {unit, path}
    for m in DPR_UNIT.finditer(dprs[0].read_text(encoding="utf-8", errors="replace")):
        unit, path, tag = m.group(1), m.group(2), (m.group(3) or "").strip()
        if tag and ":" not in tag:                          # {FormVar} ; `{DM: TDataModule}` is a data module
            forms[tag] = {"unit": unit, "path": path.replace("\\", "/")}
    return dprs[0].name, forms


def cmd_opens(args):
    depth = 0
    if "--depth" in args:
        i = args.index("--depth"); depth = int(args[i + 1]); del args[i:i + 2]
    trunk, files = Path(args[0]), args[1:]
    dpr, forms = dpr_forms(trunk)
    var_re = re.compile(r"\b(" + "|".join(re.escape(v) for v in sorted(forms, key=len, reverse=True)) + r")\b(?:\s*\.\s*(\w+))?") if forms else None
    cls_re = re.compile(r"\b(T(?:" + "|".join(re.escape(v) for v in forms) + r"))\s*\.\s*Create\b") if forms else None
    result = {"dpr": dpr, "forms_in_dpr": len(forms), "child_forms": [], "external_programs": [], "generic_open_calls": []}
    for f in files:
        fp = Path(f)
        raw, clean = read_pas(fp)
        own_units = {fp.stem.lower()}
        idx = method_index(clean)
        dfm = fp.with_suffix(".dfm.decoded.txt")
        if not dfm.exists():
            dfm = fp.with_suffix(".dfm")
        evmap = dfm_events(dfm.read_text(encoding="utf-8", errors="replace")) if dfm.exists() else {}
        R, C = raw.split("\n"), clean.split("\n")
        impl = next((i for i, l in enumerate(C) if re.match(r"^\s*implementation\b", l, re.I)), 0)
        for i in range(impl, len(C)):
            line, no = C[i], i + 1
            meth = enclosing(idx, no)
            handler = meth.split(".")[-1] if meth else None
            fired_by = evmap.get(handler, []) if handler else []
            base = {"file": fp.name, "line": no, "in_method": meth, "quote": R[i].strip(), "fired_by": fired_by}
            if var_re:
                for m in var_re.finditer(line):
                    var, member = m.group(1), m.group(2)
                    if forms[var]["unit"].lower() in own_units or var == "MainForm":
                        continue                              # MainForm = the opener infrastructure (OpenFormMenu), see generic_open_calls
                    if member is None and not re.search(r"Application\s*\.\s*CreateForm\s*\([^)]*\b" + re.escape(var) + r"\b", line, re.I):
                        continue                              # a bare mention (type name etc.) is not an open
                    result["child_forms"].append({**base, "form_var": var, "unit": forms[var]["unit"], "path": forms[var]["path"], "member": member})
                for m in (cls_re.finditer(line) if cls_re else []):
                    var = m.group(1)[1:]
                    if forms[var]["unit"].lower() not in own_units:
                        result["child_forms"].append({**base, "form_var": var, "unit": forms[var]["unit"], "path": forms[var]["path"], "member": "Create(class)"})
            if EXT_PATTERNS.search(line):
                result["external_programs"].append({**base, "call": EXT_PATTERNS.search(line).group(1)})
            if OPEN_PATTERNS.search(line):
                result["generic_open_calls"].append({**base, "call": OPEN_PATTERNS.search(line).group(1)})
    # one level of wrapper resolution: does the target's Edit/ShowMe body itself open a modal form?
    cache = {}
    for ch in result["child_forms"]:
        tgt = trunk / ch["path"]
        if ch["member"] and tgt.exists():
            if tgt not in cache:
                _, c = read_pas(tgt); cache[tgt] = (c.split("\n"), method_index(c))
            lines, tidx = cache[tgt]
            for m in tidx:
                if m["method"].lower().endswith("." + ch["member"].lower()):
                    body = "\n".join(lines[m["first_line"] - 1: m["last_line"]])
                    ch["target_member_lines"] = f"{tgt.name}:{m['first_line']}-{m['last_line']}"
                    ch["target_member_opens_modal"] = bool(OPEN_PATTERNS.search(body))
                    break
    result["summary"] = {k: len(result[k]) for k in ("child_forms", "external_programs", "generic_open_calls")}
    print(json.dumps(result, ensure_ascii=False, indent=1))


CMDS = {"dfm": cmd_dfm, "events": cmd_events, "pas": cmd_pas, "body": cmd_body, "opens": cmd_opens}

if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] not in CMDS:
        print(__doc__); sys.exit(1)
    CMDS[sys.argv[1]](sys.argv[2:])
