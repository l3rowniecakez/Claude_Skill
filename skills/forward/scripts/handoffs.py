#!/usr/bin/env python3
"""Handoff index shared by /forward and /recap.

Vault is fixed at ~/ψ/inbox/handoff (does not depend on cwd), so handoffs written
from any repo (/mnt/d/..., ~, etc.) all land in one place.

Usage:
  handoffs.py list [--all] [--stream S] [--days N]   open workstreams, latest per key
  handoffs.py show KEY                              print path of latest handoff for KEY
  handoffs.py history KEY                           all handoffs for KEY, newest first
  handoffs.py close KEY [--status closed|waiting|open]
  handoffs.py supersede KEY FILE                    mark older handoffs of KEY superseded
  handoffs.py verify KEY                            live check: git repo/branch + Redmine status
  handoffs.py dir                                   print vault dir
"""
import json, os, re, subprocess, sys, time
from pathlib import Path

VAULT = Path(os.environ.get("HANDOFF_DIR", Path.home() / "ψ" / "inbox" / "handoff"))
STREAMS = ["grouplife", "cde", "cam", "bot", "other"]
OPEN_STATES = {"open", "waiting", "legacy"}
REDMINE_URL = os.environ.get("REDMINE_URL", "https://redmine.ochi.link").rstrip("/")
# API key: env REDMINE_API_KEY, else the auto-memory note reference_redmine_api_key.md (any project dir)
MEMORY_KEYFILES = sorted(Path.home().glob(".claude/projects/*/memory/reference_redmine_api_key.md"))

STREAM_HINTS = [
    ("cde", r"\bcde\b|dataextraction|drugnorm|drug-?norm|\bocr\b|claim-folder-worker|gemini|gcp"),
    ("cam", r"claimautomation|\bcam\b|jenkins"),
    ("bot", r"ocean-bot|web ?bot|bot system|ur ?20260219|laravel|codeigniter"),
    ("grouplife", r"\bogl|grouplife|formedit|delphi|\.pas\b|\.dfm\b|ประกันกลุ่ม|zgl_"),
]


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {}
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end > 0:
            for line in text[4:end].splitlines():
                m = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*(#.*)?$", line)
                if m:
                    meta[m.group(1)] = m.group(2).strip().strip('"')
    legacy = "key" not in meta
    if legacy:
        name = path.stem
        m = re.search(r"rm[-_ ]?(\d{4,6})", name, re.I) or re.search(r"#(\d{5,6})", text[:400])
        meta["rm"] = m.group(1) if m else ""
        meta["key"] = f"rm{meta['rm']}" if meta["rm"] else re.sub(r"^\d{4}-\d{2}-\d{2}(_\d{2}-\d{2})?_", "", name)
        low = (name + " " + text[:1500]).lower()
        meta["stream"] = next((s for s, rx in STREAM_HINTS if re.search(rx, low)), "other")
        t = re.search(r"^# Handoff:\s*(.+)$", text, re.M)
        meta["title"] = t.group(1).strip() if t else name
        meta["status"] = "legacy"
    meta.setdefault("stream", "other")
    meta.setdefault("status", "open")
    meta.setdefault("title", path.stem)
    meta["file"] = str(path)
    meta["mtime"] = path.stat().st_mtime
    meta["legacy"] = legacy
    return meta


def all_handoffs():
    if not VAULT.is_dir():
        return []
    items = [parse(p) for p in VAULT.glob("*.md") if p.name not in ("CLAUDE.md", "README.md")]
    # newest first: filename starts with YYYY-MM-DD_HH-MM, fall back to mtime
    items.sort(key=lambda d: (Path(d["file"]).name[:16], d["mtime"]), reverse=True)
    return items


def latest_per_key(items):
    seen, out = set(), []
    for d in items:
        if d["key"] in seen:
            continue
        seen.add(d["key"])
        out.append(d)
    return out


def set_status(path: str, status: str):
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if text.startswith("---\n") and re.search(r"^status:", text, re.M):
        text = re.sub(r"^status:.*$", f"status: {status}", text, count=1, flags=re.M)
    else:
        d = parse(p)
        title = d["title"].replace("\n", " ")
        fm = f"---\nkey: {d['key']}\nstream: {d['stream']}\nrm: {d.get('rm','')}\ntitle: {title}\nstatus: {status}\n---\n"
        text = fm + text
    p.write_text(text, encoding="utf-8")


def age(d):
    days = (time.time() - d["mtime"]) / 86400
    return f"{days:.0f}d" if days >= 1 else f"{days*24:.0f}h"


def cmd_list(args):
    show_all = "--all" in args
    stream = args[args.index("--stream") + 1] if "--stream" in args else None
    days = int(args[args.index("--days") + 1]) if "--days" in args else 21
    rows = latest_per_key(all_handoffs())
    now = time.time()
    shown = 0
    for s in STREAMS:
        if stream and s != stream:
            continue
        group = [d for d in rows if d["stream"] == s and (show_all or (
            d["status"] in OPEN_STATES and not (d["legacy"] and now - d["mtime"] > days * 86400)))]
        if not group:
            continue
        print(f"## {s}")
        for d in group:
            rm = f"RM #{d['rm']}" if d.get("rm") else "-"
            nxt = f"  → {d['next']}" if d.get("next") else ""
            print(f"- [{d['status']}] {d['key']} | {rm} | {d['title'][:90]} | {age(d)} ago{nxt}")
            print(f"    {d['file']}")
            shown += 1
    if not shown:
        print("(ไม่มีงานค้างใน handoff)")


def find_key(key):
    key = key.lower().lstrip("#")
    if key.isdigit():
        key = "rm" + key
    hist = [d for d in all_handoffs() if d["key"].lower() == key]
    if not hist:
        hist = [d for d in all_handoffs() if key in d["key"].lower() or key in Path(d["file"]).name.lower()]
    return hist


def redmine_key():
    if os.environ.get("REDMINE_API_KEY"):
        return os.environ["REDMINE_API_KEY"]
    for f in MEMORY_KEYFILES:
        try:
            m = re.search(r"API key:\s*`([0-9a-f]{40})`", f.read_text())
            if m:
                return m.group(1)
        except OSError:
            pass
    return None


def run(cmd, cwd=None):
    try:
        return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return ""


def cmd_verify(args):
    hist = find_key(args[0])
    if not hist:
        print(f"ไม่พบ handoff: {args[0]}"); return
    d = hist[0]
    print(f"handoff: {d['file']} (status={d['status']}, {age(d)} ago)")
    for repo in [r.strip() for r in d.get("repo", "").split(";") if r.strip()]:
        if not Path(repo).is_dir():
            print(f"repo {repo}: ⚠️ ไม่พบ path"); continue
        br = run(["git", "-C", repo, "branch", "--show-current"])
        head = run(["git", "-C", repo, "log", "--oneline", "-1"])
        dirty = run(["git", "-C", repo, "status", "--porcelain"])
        ahead = run(["git", "-C", repo, "rev-list", "--count", "@{u}..HEAD"])
        print(f"repo {repo}: branch={br or '?'} head={head[:60]} uncommitted={len(dirty.splitlines()) if dirty else 0} ahead={ahead or 'no-upstream'}")
        if d.get("branch") and br and d["branch"] != br:
            print(f"    ⚠️ handoff บอก branch={d['branch']} แต่ตอนนี้อยู่ {br}")
    key = redmine_key()
    rms = re.findall(r"\d{4,6}", d.get("rm", ""))
    for rm in rms:
        if not key:
            print(f"RM #{rm}: ⚠️ ไม่มี API key (ตั้ง env REDMINE_API_KEY)"); break
        out = run(["curl", "-s", "-m", "15", "-H", f"X-Redmine-API-Key: {key}",
                   f"{REDMINE_URL}/issues/{rm}.json"])
        try:
            i = json.loads(out)["issue"]
            print(f"RM #{rm}: {i['status']['name']} | {i.get('done_ratio',0)}% | updated {i['updated_on'][:16]} | {i['subject'][:70]}")
        except Exception:
            print(f"RM #{rm}: ⚠️ ดึงสถานะไม่ได้")


def main():
    if len(sys.argv) < 2:
        print(__doc__); return
    cmd, args = sys.argv[1], sys.argv[2:]
    if cmd == "dir":
        print(VAULT)
    elif cmd == "list":
        cmd_list(args)
    elif cmd in ("show", "history"):
        hist = find_key(args[0])
        if not hist:
            print(f"ไม่พบ handoff: {args[0]}"); sys.exit(1)
        for d in (hist[:1] if cmd == "show" else hist):
            print(d["file"] if cmd == "show" else f"[{d['status']}] {d['file']}")
    elif cmd == "close":
        status = args[args.index("--status") + 1] if "--status" in args else "closed"
        hist = find_key(args[0])
        if not hist:
            print(f"ไม่พบ handoff: {args[0]}"); sys.exit(1)
        for d in hist:  # close whole chain so legacy siblings don't resurface
            set_status(d["file"], status if d is hist[0] else ("superseded" if status != "closed" else "closed"))
        print(f"{hist[0]['key']} → {status} ({len(hist)} file)")
    elif cmd == "supersede":
        key, keep = args[0], str(Path(args[1]).resolve())
        n = 0
        for d in find_key(key):
            if str(Path(d["file"]).resolve()) != keep and d["status"] in OPEN_STATES:
                set_status(d["file"], "superseded"); n += 1
        print(f"superseded {n} older handoff(s) of {key}")
    elif cmd == "verify":
        cmd_verify(args)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
