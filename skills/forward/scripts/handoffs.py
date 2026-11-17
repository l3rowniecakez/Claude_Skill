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
  handoffs.py session NAME [--exclude UUID]            Session ID เต็ม + ชื่อ + เวลาใช้ล่าสุด + cwd ของงาน (สำหรับ /recap <ชื่องาน>)
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


_SESSION_NAMES = None


def session_names() -> dict:
    """session uuid -> ชื่อที่ผู้ใช้ตั้งด้วย /rename (custom-title ล่าสุด, ไม่มีใช้ agent-name)"""
    global _SESSION_NAMES
    if _SESSION_NAMES is None:
        _SESSION_NAMES = {}
        files = sorted(Path.home().glob(".claude/projects/*/*.jsonl"), key=lambda f: f.stat().st_mtime)
        for f in files:
            try:
                for line in f.open(encoding="utf-8", errors="replace"):
                    if '"custom-title"' in line or '"agent-name"' in line:
                        try:
                            o = json.loads(line)
                        except ValueError:
                            continue
                        n = o.get("customTitle") or o.get("agentName")
                        if n and o.get("sessionId"):
                            _SESSION_NAMES[o["sessionId"]] = n
            except OSError:
                pass
    return _SESSION_NAMES


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
    meta["session_name"] = session_names().get(meta.get("session", ""), "")
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
            if d.get("session_name"):
                print(f"    session: {d['session_name']}")
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
    if not hist:  # ชื่อ session ที่ตั้งด้วย /rename
        hist = [d for d in all_handoffs() if d.get("session_name") and key in d["session_name"].lower()]
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


UUID_RX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


def transcript_of(uuid):
    """path ของ transcript jsonl ของ session (glob เฉพาะ ~/.claude/projects/*/ ห้าม find /)"""
    if not UUID_RX.match(uuid or ""):
        return None
    hits = list(Path.home().glob(f".claude/projects/*/{uuid}.jsonl"))
    return hits[0] if hits else None


def transcript_cwd(path):
    try:
        for line in path.open(encoding="utf-8", errors="replace"):
            m = re.search(r'"cwd":"([^"]*)"', line)
            if m:
                return m.group(1)
    except OSError:
        pass
    return ""


def bkk(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ts + 7 * 3600))


def match_for_session(query):
    """หา handoff ที่ตรงกับ 'ชื่องาน' ที่ผู้ใช้พิมพ์: key / เลข RM / ชื่อไฟล์ / ชื่อ session / title (ทุกคำต้องอยู่ใน title)"""
    hist = find_key(query)
    if hist:
        return hist
    words = [w for w in re.split(r"\s+", query.lower().strip()) if w]
    return [d for d in all_handoffs()
            if words and all(w in (d["title"] + " " + d.get("key", "") + " " + d.get("session_name", "")).lower() for w in words)]


def scan_transcripts(query, limit=5, exclude=()):
    """fallback เมื่อ handoff ไม่มี session id: grep ข้อความในฟีลด์ transcript (fixed-string, เฉพาะ ~/.claude/projects/*/)"""
    needles = [query]
    if query.lstrip("#").isdigit():
        needles = [f"#{query.lstrip('#')}", f"RM {query.lstrip('#')}", f"rm{query.lstrip('#')}"]
    files = list(Path.home().glob(".claude/projects/*/*.jsonl"))
    hits = []
    for f in files:
        if f.stem in exclude:
            continue
        try:
            blob = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        n = sum(blob.count(x) for x in needles)
        if n >= 3:
            hits.append((n, f))
    hits.sort(key=lambda t: (t[0], t[1].stat().st_mtime), reverse=True)  # เรียงตามจำนวนที่เจอ (session ที่ทำงานนั้นจริงจะเจอเยอะสุด)
    return hits[:limit]


def cmd_session(args):
    """/recap <ชื่องาน> -> ปริ้น Session ID เต็ม + ชื่อ + เวลาใช้ล่าสุด + cwd + คำสั่ง resume ของงานนั้น"""
    if not args:
        print("usage: handoffs.py session <ชื่องาน|RM|key|ชื่อ session>"); return
    exclude = set()
    while "--exclude" in args:  # session ปัจจุบัน (กันเจอตัวเองใน fallback)
        i = args.index("--exclude")
        exclude.add(args[i + 1]); del args[i:i + 2]
    query = " ".join(args)
    hist = match_for_session(query)
    if not hist:
        print(f"ไม่พบ handoff ที่ตรงกับ '{query}' — ลองสแกน transcript (เดา):")
        for n, f in scan_transcripts(query, exclude=exclude):
            print(f"GUESS | uuid={f.stem} | hits={n} | last_used={bkk(f.stat().st_mtime)} | cwd={transcript_cwd(f) or '?'} | name={session_names().get(f.stem, '-')}")
        return
    keys = []
    for d in hist:
        if d["key"] not in keys:
            keys.append(d["key"])
    print(f"MATCHED_KEYS={len(keys)}")
    for k in keys:
        chain = [d for d in hist if d["key"] == k]  # newest first
        latest = chain[0]
        print(f"\n== key={k} | RM={latest.get('rm') or '-'} | status={latest['status']} | title={latest['title'][:90]}")
        sessions, seen = [], set()
        for d in chain:
            s = d.get("session", "")
            if s and s not in seen:
                seen.add(s); sessions.append(d)
        if not sessions:
            print("  ⚠️ NO_SESSION_ID: handoff ของ key นี้ไม่ได้บันทึก session id ไว้ (handoff เก่า/legacy)")
            for n, f in scan_transcripts(latest.get("rm") or k, exclude=exclude):
                print(f"  GUESS | uuid={f.stem} | hits={n} | last_used={bkk(f.stat().st_mtime)} | cwd={transcript_cwd(f) or '?'} | name={session_names().get(f.stem, '-')}")
            continue
        for i, d in enumerate(sessions):
            u = d["session"]
            tp = transcript_of(u)
            if tp:
                used, src, cwd = bkk(tp.stat().st_mtime), "transcript mtime", transcript_cwd(tp)
            else:
                used, src, cwd = bkk(d["mtime"]), "เวลา handoff (ไม่ใช่เวลาใช้งานจริง — ไม่พบ transcript ในเครื่องนี้)", d.get("cwd", "")
            tag = "LATEST" if i == 0 else "EARLIER"
            print(f"  [{tag}] session_id={u}")
            print(f"    name={d.get('session_name') or '-'} | last_used={used} ({src}) | cwd={cwd or '?'}")
            print(f"    resume: /resume {u}    (หรือ cd '{cwd}' && claude --resume {u})" if cwd else f"    resume: /resume {u}")
            print(f"    handoff: {d['file']}")
            if not tp:
                print("    ⚠️ TRANSCRIPT_MISSING: resume อาจไม่ได้บนเครื่องนี้")
    dup = {}
    for k in keys:
        s = next((d.get("session") for d in hist if d["key"] == k and d.get("session")), "")
        if s:
            dup.setdefault(s, []).append(k)
    for s, ks in dup.items():
        if len(ks) > 1:
            print(f"\nNOTE: session {s} ใช้ร่วมกันหลาย key ({', '.join(ks)}) — resume แล้ว context จะรวมหลายงาน")


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
    elif cmd == "sessions":  # ตารางชื่อ session -> key (ใช้ตรวจว่า /rename ตรงกับงาน)
        for d in latest_per_key(all_handoffs()):
            if d.get("session_name"):
                print(f"{d['session_name']}\t{d['key']}\t{d.get('session', '')}")
    elif cmd == "session":
        cmd_session(args)
    elif cmd == "verify":
        cmd_verify(args)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
