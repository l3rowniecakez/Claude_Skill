#!/usr/bin/env python3
"""delphi_build_run.py - build (dcc32) and run a Delphi 7 program from Windows or WSL.

Standard library only. Bundled with the /delphi-build-run skill so it works on any
machine that has Delphi 7 installed (native Windows Python, or Python inside WSL).

Sub-commands (all print JSON unless noted):
  detect                         find Delphi 7 install + dcc32, show platform
  set-delphi <root>              remember the Delphi 7 root folder for this machine
  scan <dpr|folder>              locate the .dpr, list ParamStr/ParamCount usage, saved params
  params-save <dpr> --set N=V..  remember ParamStr(N)=V for that project
  params-clear <dpr>             forget saved params for that project
  build <dpr> [--rebuild]        compile with dcc32 (text output, ends with BUILD_RESULT line)
  run <dpr> [--set N=V ...]      start the built exe (saved params are used unless overridden)
  recent                         list projects used before on this machine (for /delphi-build-run with no path)
  configs <dpr>                  show Config.ini the exe reads + its Data_Source + template inis
  use-config <dpr> --server 52|139|22 [--allow-derived]   point Config.ini at that DB server

Per-machine settings live in ~/.config/delphi-build-run/config.json (outside the skill).
"""
import argparse
import json
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

IS_WIN = os.name == "nt"
IS_WSL = (not IS_WIN) and (
    "microsoft" in platform.release().lower() or bool(os.environ.get("WSL_DISTRO_NAME"))
)
CONFIG_PATH = Path.home() / ".config" / "delphi-build-run" / "config.json"
WIN_PATH_RE = re.compile(r"^[A-Za-z]:[\\/]")


def die(msg, code=2):
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(code)


def require_windows_host():
    if not (IS_WIN or IS_WSL):
        die("Delphi 7 produces Win32 programs: run this on Windows (or WSL on Windows). "
            "On macOS/Linux use a Windows VM or remote Windows machine.")


# ---------------------------------------------------------------- paths
def run_capture(cmd, **kw):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, **kw)
    return r.returncode, decode(r.stdout)


def decode(b):
    for enc in ("utf-8", "cp874"):
        try:
            return b.decode(enc)
        except UnicodeDecodeError:
            pass
    return b.decode("utf-8", "replace")


def to_host(p):
    """Any user-supplied path (Windows or Linux style) -> path usable by this Python."""
    p = str(p).strip().strip('"')
    if IS_WSL and WIN_PATH_RE.match(p):
        rc, out = run_capture(["wslpath", "-u", p])
        if rc == 0:
            return Path(out.strip())
    return Path(p).expanduser()


def to_win(p):
    """Host path -> Windows-style path string (what dcc32 / the exe understand)."""
    p = str(p)
    if IS_WIN or WIN_PATH_RE.match(p):
        return p
    if IS_WSL:
        rc, out = run_capture(["wslpath", "-w", p])
        if rc == 0:
            return out.strip()
    return p


# ---------------------------------------------------------------- config
def load_config():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def project_key(dpr):
    return to_win(dpr).lower()


# ---------------------------------------------------------------- registry
def reg_read(hive, key, name, view32):
    if IS_WIN:
        import winreg
        h = {"HKLM": winreg.HKEY_LOCAL_MACHINE, "HKCU": winreg.HKEY_CURRENT_USER}[hive]
        flags = winreg.KEY_READ | (winreg.KEY_WOW64_32KEY if view32 else 0)
        try:
            with winreg.OpenKey(h, key, 0, flags) as k:
                return winreg.QueryValueEx(k, name)[0]
        except OSError:
            return None
    cmd = ["reg.exe", "query", hive + "\\" + key, "/v", name]
    if view32:
        cmd.append("/reg:32")
    try:
        rc, out = run_capture(cmd)
    except OSError:
        return None
    if rc != 0:
        return None
    m = re.search(r"^\s*" + re.escape(name) + r"\s+REG_\w+\s+(.*?)\s*$", out, re.M | re.I)
    return m.group(1) if m else None


# ---------------------------------------------------------------- delphi location
def delphi_candidates():
    cfg = load_config()
    if cfg.get("delphi_root"):
        yield cfg["delphi_root"]
    root = reg_read("HKLM", r"SOFTWARE\Borland\Delphi\7.0", "RootDir", True)
    if root:
        yield root
    for sub in (r"Program Files (x86)\Borland\Delphi7", r"Program Files\Borland\Delphi7",
                r"Borland\Delphi7", r"Delphi7"):
        for drv in "CDEFG":
            yield "%s:\\%s" % (drv, sub)


def find_delphi():
    seen = set()
    for c in delphi_candidates():
        c = c.rstrip("\\/")
        if c.lower() in seen:
            continue
        seen.add(c.lower())
        if (to_host(c) / "Bin" / "dcc32.exe").exists():
            return c
    return None


def need_delphi():
    root = find_delphi()
    if not root:
        die("Delphi 7 not found. Ask the user for the install folder (the one containing "
            "Bin\\dcc32.exe) and run: set-delphi <folder>")
    return root


# ---------------------------------------------------------------- project files
def _resolve_project(arg):
    p = to_host(arg)
    if p.is_dir():
        found = sorted(p.glob("*.dpr"))
        if not found:
            die("No .dpr file in folder: %s" % arg)
        if len(found) > 1:
            die("Several .dpr files, pick one: " + ", ".join(f.name for f in found))
        return found[0]
    if p.suffix.lower() != ".dpr":
        cand = p.with_suffix(".dpr")
        if cand.exists():
            return cand
        die("Not a .dpr file: %s" % arg)
    if not p.exists():
        die("File not found: %s" % arg)
    return p


def remember_project(dpr):
    """Keep the most recently used projects (newest first, max 8) in the per-machine config."""
    try:
        cfg = load_config()
        w = to_win(dpr)
        rec = [x for x in cfg.get("recent", []) if x.lower() != w.lower()]
        cfg["recent"] = ([w] + rec)[:8]
        save_config(cfg)
    except OSError:
        pass


def resolve_project(arg):
    dpr = _resolve_project(arg)
    if not to_win(dpr).startswith("\\\\"):
        remember_project(dpr)
    return dpr


def cmd_recent(a):
    """Projects used before on this machine (+ a .dpr found in the current folder) - no args needed."""
    items = []
    for w in load_config().get("recent", []):
        try:
            ok = to_host(w).exists()
        except OSError:
            ok = False
        if ok:
            items.append({"dpr": w, "name": Path(w.replace("\\", "/")).stem})
    cwd = []
    try:
        here = Path.cwd()
        cwd = [to_win(f) for f in sorted(here.glob("*.dpr"))]
    except OSError:
        pass
    print(json.dumps({"recent": items, "cwd_dpr": [c for c in cwd if not c.startswith("\\\\")]},
                     ensure_ascii=False, indent=1))


def read_dof_directories(dpr):
    dof = dpr.with_suffix(".dof")
    out = {}
    if not dof.exists():
        return out
    section = None
    for line in decode(dof.read_bytes()).splitlines():
        line = line.strip()
        if line.startswith("["):
            section = line.lower()
        elif section == "[directories]" and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def project_unit_files(dpr):
    text = decode(dpr.read_bytes())
    files = [dpr]
    for m in re.finditer(r"\bin\s+'([^']+)'", text, re.I):
        f = dpr.parent / m.group(1).replace("\\", "/")
        if f.exists():
            files.append(f)
    return files


def scan_params(dpr):
    hits, indices = [], {}
    pat = re.compile(r"Param(Str\s*\(\s*(\d+)\s*\)|Count)", re.I)
    for f in project_unit_files(dpr):
        try:
            lines = decode(f.read_bytes()).splitlines()
        except OSError:
            continue
        for no, line in enumerate(lines, 1):
            for m in pat.finditer(line):
                if m.group(2):
                    idx = int(m.group(2))
                    if idx == 0:  # ParamStr(0) is the exe path, not a user param
                        continue
                    hint = "password" if re.search(r"pass|pwd", line, re.I) else (
                        "user" if re.search(r"user|login|name", line, re.I) else None)
                    cur = indices.setdefault(idx, hint)
                    if cur is None and hint:
                        indices[idx] = hint
                hits.append({"file": str(f.relative_to(dpr.parent)), "line": no,
                             "text": line.strip()[:160]})
                break
    return hits, indices


# ---------------------------------------------------------------- commands
def cmd_detect(a):
    require_windows_host()
    root = find_delphi()
    print(json.dumps({
        "platform": "windows" if IS_WIN else "wsl",
        "delphi_root": root,
        "dcc32": (root + "\\Bin\\dcc32.exe") if root else None,
        "config_file": str(CONFIG_PATH),
    }, ensure_ascii=False))


def cmd_set_delphi(a):
    require_windows_host()
    root = a.root.strip().strip('"').rstrip("\\/")
    if not (to_host(root) / "Bin" / "dcc32.exe").exists():
        die("Bin\\dcc32.exe not found under: %s" % root)
    cfg = load_config()
    cfg["delphi_root"] = root
    save_config(cfg)
    print(json.dumps({"delphi_root": root, "saved": True}))


def parse_sets(sets):
    out = {}
    for s in sets or []:
        if "=" not in s or not s.split("=", 1)[0].isdigit():
            die("--set expects N=VALUE (N = ParamStr index), got: %s" % s)
        k, v = s.split("=", 1)
        out[str(int(k))] = v
    return out


def mask(indices, saved):
    out = {}
    for k, v in saved.items():
        hint = indices.get(int(k))
        out[k] = "***" if hint == "password" else v
    return out


def cmd_scan(a):
    require_windows_host()
    dpr = resolve_project(a.project)
    hits, indices = scan_params(dpr)
    saved = load_config().get("projects", {}).get(project_key(dpr), {}).get("params", {})
    print(json.dumps({
        "dpr": to_win(dpr),
        "needs_params": bool(indices) or any("ParamCount" in h["text"] for h in hits),
        "param_indices": {str(k): v for k, v in sorted(indices.items())},
        "saved_params_masked": mask(indices, saved),
        "source_hits": hits[:15],
    }, ensure_ascii=False))


def cmd_params_save(a):
    require_windows_host()
    dpr = resolve_project(a.project)
    cfg = load_config()
    proj = cfg.setdefault("projects", {}).setdefault(project_key(dpr), {})
    proj.setdefault("params", {}).update(parse_sets(a.set))
    save_config(cfg)
    print(json.dumps({"saved_indices": sorted(proj["params"], key=int)}))


def cmd_params_clear(a):
    require_windows_host()
    dpr = resolve_project(a.project)
    cfg = load_config()
    cfg.get("projects", {}).pop(project_key(dpr), None)
    save_config(cfg)
    print(json.dumps({"cleared": True}))


def win_env(name):
    """Value of a Windows environment variable (works natively and from WSL)."""
    if IS_WIN:
        return os.environ.get(name)
    try:
        r = subprocess.run(["cmd.exe", "/c", "echo %" + name + "%"], cwd="/mnt/c",
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except OSError:
        return None
    v = decode(r.stdout).strip()
    return None if (not v or v == "%" + name + "%") else v


def lib_search_path(root):
    reg = reg_read("HKCU", r"Software\Borland\Delphi\7.0\Library", "Search Path", False) or ""
    reg = re.sub(r"\$\(DELPHI\)", lambda m: root, reg, flags=re.I)
    # other IDE macros, e.g. $(DXVCL), are Windows environment variables
    reg = re.sub(r"\$\(([A-Za-z0-9_]+)\)", lambda m: win_env(m.group(1)) or m.group(0), reg)
    base = [root + r"\Lib", root + r"\Lib\Debug", root + r"\Bin", root + r"\Imports"]
    return [p for p in reg.split(";") if p] + base


def output_dir(dpr):
    d = read_dof_directories(dpr).get("OutputDir", "")
    if d:
        return to_host(d) if WIN_PATH_RE.match(d) else (dpr.parent / d.replace("\\", "/"))
    return dpr.parent


def cmd_build(a):
    require_windows_host()
    root = need_delphi()
    dpr = resolve_project(a.project)
    dof = read_dof_directories(dpr)
    paths = [p for p in dof.get("SearchPath", "").split(";") if p] + lib_search_path(root)
    paths = [p.rstrip("\\/") or p for p in paths]
    if to_win(dpr).startswith("\\\\"):
        die("Project is on a WSL/UNC path (%s). Windows tools cannot use it as a working "
            "folder - keep the project on a Windows drive (C:, D:, ...)." % to_win(dpr))
    dcc = str(to_host(root + "\\Bin\\dcc32.exe"))
    cmd = [dcc, "-Q"] + (["-B"] if a.rebuild else [])
    out_dir = dof.get("OutputDir", "")
    if out_dir:
        cmd.append("-E" + out_dir.rstrip("\\/"))
    cmd += ["-U" + ";".join(paths), "-I" + ";".join(paths), "-R" + ";".join(paths),
            dpr.name]
    started = time.time()
    try:
        r = subprocess.run(cmd, cwd=str(dpr.parent), stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT)
    except OSError as e:
        die("Cannot start dcc32: %s" % e)
    text = decode(r.stdout)
    lines = [l for l in text.splitlines() if l.strip()]
    errs = [l for l in lines if re.search(r"\b(Error|Fatal):", l)]
    warns = [l for l in lines if re.search(r"\bWarning:", l)]
    exe = output_dir(dpr) / (dpr.stem + ".exe")
    fresh = exe.exists() and exe.stat().st_mtime >= started - 2
    ok = r.returncode == 0 and fresh
    print("\n".join(lines[-60:]))
    print("\nerrors=%d warnings=%d" % (len(errs), len(warns)))
    if any("Could not create output file" in l or "F2039" in l for l in errs):
        print("HINT: the exe is probably still running - close it, then build again.")
    if any("File not found" in l for l in errs):
        print("HINT: a unit/component is missing from the library path. Check "
              "HKCU\\Software\\Borland\\Delphi\\7.0\\Library or add folders to the .dof SearchPath.")
    print("BUILD_RESULT: %s exe=%s" % ("OK" if ok else "FAILED", to_win(exe)))
    sys.exit(0 if ok else 1)


def cmd_run(a):
    require_windows_host()
    dpr = resolve_project(a.project)
    exe = output_dir(dpr) / (dpr.stem + ".exe")
    if not exe.exists():
        die("Exe not found (build first): %s" % to_win(exe))
    params = dict(load_config().get("projects", {}).get(project_key(dpr), {}).get("params", {}))
    params.update(parse_sets(a.set))
    argv = []
    if params:
        for i in range(1, max(int(k) for k in params) + 1):
            argv.append(params.get(str(i), ""))
    kw = dict(cwd=str(exe.parent), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL)
    if IS_WIN:
        kw["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kw["start_new_session"] = True
    try:
        proc = subprocess.Popen([str(exe)] + argv, **kw)
    except OSError as e:
        die("Cannot start exe: %s" % e)
    time.sleep(a.wait)
    rc = proc.poll()
    print(json.dumps({
        "exe": to_win(exe), "args_count": len(argv), "pid": proc.pid,
        "status": "running" if rc is None else "exited_early",
        "exit_code": rc,
    }))


# ---------------------------------------------------------------- DB server config (Config.ini)
DEFAULT_SERVERS = {"52": "10.100.2.52", "139": "10.100.3.139", "22": "12.100.7.22"}
DS_RE = re.compile(rb"^(\s*Data_Source\s*=\s*)(.*?)(\r?)$", re.M | re.I)


def servers():
    return load_config().get("servers") or DEFAULT_SERVERS


def ini_server(path):
    try:
        m = DS_RE.search(Path(path).read_bytes())
    except OSError:
        return None
    return m.group(2).decode("ascii", "replace").strip() if m else None


def ini_candidates(exe_dir):
    """Config*.ini beside the exe and in up to 3 parent folders, that have a Data_Source."""
    out, seen = [], set()
    d = exe_dir
    for _ in range(4):
        for f in sorted(d.glob("Config*.ini")):
            if f in seen or f == exe_dir / "Config.ini":
                continue
            seen.add(f)
            ds = ini_server(f)
            if ds:
                out.append({"file": to_win(f), "server": ds, "_p": f})
        if d.parent == d:
            break
        d = d.parent
    return out


def cmd_configs(a):
    dpr = resolve_project(a.project)
    exe_dir = output_dir(dpr)
    cur = exe_dir / "Config.ini"
    print(json.dumps({
        "config_used_by_exe": to_win(cur),
        "exists": cur.exists(),
        "current_server": ini_server(cur) if cur.exists() else None,
        "server_choices": servers(),
        "candidates": [{k: v for k, v in c.items() if k != "_p"} for c in ini_candidates(exe_dir)],
    }, ensure_ascii=False, indent=1))


def cmd_use_config(a):
    """Make <exe folder>\\Config.ini point at the chosen DB server (the app reads only that file)."""
    dpr = resolve_project(a.project)
    exe_dir = output_dir(dpr)
    cur = exe_dir / "Config.ini"
    ip = servers().get(a.server, a.server)
    if cur.exists() and ini_server(cur) == ip:
        print(json.dumps({"status": "already", "server": ip, "config": to_win(cur)}))
        return
    cands = ini_candidates(exe_dir)
    exact = [c for c in cands if c["server"] == ip]
    derived = False
    if exact:
        src = exact[0]["_p"]
        data = src.read_bytes()
    else:
        base = [c for c in cands if c["server"] == servers().get("52", "")] or cands[:1]
        if not base:
            die("No Config*.ini template with Data_Source found near %s" % to_win(exe_dir))
        src = base[0]["_p"]
        data = DS_RE.sub(lambda m: m.group(1) + ip.encode() + m.group(3), src.read_bytes(), 1)
        derived = True
        if not a.allow_derived:
            die("No template ini for %s. Re-run with --allow-derived to copy %s and only change "
                "Data_Source (login names/passwords inside are NOT verified for this server)."
                % (ip, to_win(src)))
    backup = None
    if cur.exists():
        backup = exe_dir / "Config.ini.before-delphi-build-run"
        if not backup.exists():  # keep the very first original
            backup.write_bytes(cur.read_bytes())
    cur.write_bytes(data)
    print(json.dumps({"status": "switched", "server": ip, "config": to_win(cur),
                      "from_template": to_win(src), "derived": derived,
                      "backup": to_win(backup) if backup else None}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("detect").set_defaults(fn=cmd_detect)
    p = sub.add_parser("set-delphi"); p.add_argument("root"); p.set_defaults(fn=cmd_set_delphi)
    p = sub.add_parser("scan"); p.add_argument("project"); p.set_defaults(fn=cmd_scan)
    p = sub.add_parser("params-save"); p.add_argument("project")
    p.add_argument("--set", action="append"); p.set_defaults(fn=cmd_params_save)
    p = sub.add_parser("params-clear"); p.add_argument("project"); p.set_defaults(fn=cmd_params_clear)
    p = sub.add_parser("build"); p.add_argument("project")
    p.add_argument("--rebuild", action="store_true"); p.set_defaults(fn=cmd_build)
    p = sub.add_parser("run"); p.add_argument("project")
    p.add_argument("--set", action="append")
    p.add_argument("--wait", type=float, default=3.0); p.set_defaults(fn=cmd_run)
    sub.add_parser("recent").set_defaults(fn=cmd_recent)
    p = sub.add_parser("configs"); p.add_argument("project"); p.set_defaults(fn=cmd_configs)
    p = sub.add_parser("use-config"); p.add_argument("project")
    p.add_argument("--server", required=True, help="52 | 139 | 22 or an IP")
    p.add_argument("--allow-derived", action="store_true"); p.set_defaults(fn=cmd_use_config)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
