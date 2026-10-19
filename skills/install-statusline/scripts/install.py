#!/usr/bin/env python3
"""Install or update the Claude Code status line from GitHub.

Downloads statusline.py from the public Claude_Skill repo, writes it to
~/.claude/statusline.py (backing up any different existing copy) and points
the "statusLine" entry of ~/.claude/settings.json at it. Safe to re-run: when
nothing changed it just says so.

Exit codes: 0 ok / already up to date, 1 error, 3 installed but settings.json
has a different statusLine that was left alone (re-run with --force-settings).
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request

REPO = "l3rowniecakez/Claude_Skill"
BRANCH = "main"
SOURCE_URL = (
    f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
    "/skills/install-statusline/scripts/statusline.py"
)
CLAUDE_DIR = os.path.join(os.path.expanduser("~"), ".claude")
DEST = os.path.join(CLAUDE_DIR, "statusline.py")
SETTINGS = os.path.join(CLAUDE_DIR, "settings.json")
BACKUP_DIR = os.path.join(CLAUDE_DIR, "backups")
IS_WINDOWS = os.name == "nt"

SAMPLE_INPUT = {
    "model": {"display_name": "Test"},
    "workspace": {"current_dir": os.path.expanduser("~")},
    "cost": {"total_cost_usd": 1.23, "total_duration_ms": 600000},
    "context_window": {"used_percentage": 12, "total_input_tokens": 120000,
                       "context_window_size": 1000000},
}


def step(pct, msg):
    done = pct // 10
    print(f"[{'#' * done}{'.' * (10 - done)}] {pct:3d}% {msg}", flush=True)


def sha(data):
    return hashlib.sha256(data).hexdigest()[:12]


def fetch(source):
    if source.startswith(("http://", "https://")):
        req = urllib.request.Request(source, headers={"User-Agent": "install-statusline"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read()
    with open(os.path.expanduser(source), "rb") as f:
        return f.read()


def timestamp():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def backup(path, label):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    out = os.path.join(BACKUP_DIR, f"{label}.{timestamp()}.bak")
    shutil.copy2(path, out)
    return out


def write_atomic(path, data):
    d = os.path.dirname(path)
    os.makedirs(d, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=d)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    if not IS_WINDOWS:
        os.chmod(tmp, 0o755)
    os.replace(tmp, path)


def wanted_command():
    # Windows has no shebang support, so name the interpreter explicitly.
    return f'python "{DEST}"' if IS_WINDOWS else "~/.claude/statusline.py"


def is_ours(cmd):
    return isinstance(cmd, str) and cmd.replace("\\", "/").rstrip('"').endswith(".claude/statusline.py")


def update_settings(force):
    """Returns (state, detail): state in ok / unchanged / foreign / error."""
    settings = {}
    if os.path.exists(SETTINGS):
        try:
            with open(SETTINGS, encoding="utf-8") as f:
                settings = json.load(f)
        except (OSError, ValueError) as e:
            return "error", f"อ่าน settings.json ไม่ได้ ({e}) — ไม่ได้แก้ไขอะไร"
        if not isinstance(settings, dict):
            return "error", "settings.json ไม่ใช่ JSON object — ไม่ได้แก้ไขอะไร"
    want = {"type": "command", "command": wanted_command(), "padding": 0}
    cur = settings.get("statusLine")
    if cur == want:
        return "unchanged", ""
    if cur and not is_ours(cur.get("command") if isinstance(cur, dict) else None) and not force:
        return "foreign", json.dumps(cur, ensure_ascii=False)
    if os.path.exists(SETTINGS):
        backup(SETTINGS, "settings.json")
    settings["statusLine"] = want
    write_atomic(SETTINGS, (json.dumps(settings, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    return "ok", ""


def smoke_test():
    try:
        out = subprocess.run(
            [sys.executable, DEST], input=json.dumps(SAMPLE_INPUT),
            capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as e:
        return False, str(e)
    if out.returncode != 0 or not out.stdout.strip():
        return False, (out.stderr or "ไม่มี output").strip()[:300]
    return True, out.stdout.strip().splitlines()[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=SOURCE_URL, help="URL หรือ path ไฟล์ statusline.py (default: GitHub)")
    ap.add_argument("--force-settings", action="store_true",
                    help="เขียนทับ statusLine เดิมใน settings.json แม้ไม่ใช่ของ skill นี้")
    args = ap.parse_args()

    step(10, f"ดึง statusline.py จาก {args.source}")
    try:
        data = fetch(args.source)
    except Exception as e:  # network, 404, missing file
        print(f"ERROR: ดึงไฟล์ไม่สำเร็จ: {e}", file=sys.stderr)
        return 1
    if not data.startswith(b"#!") or b"def main" not in data:
        print("ERROR: ไฟล์ที่ได้ไม่ใช่ statusline.py ที่ถูกต้อง — ไม่ได้ติดตั้งอะไร", file=sys.stderr)
        return 1

    step(40, "เทียบกับไฟล์ที่ติดตั้งอยู่")
    old = None
    if os.path.exists(DEST):
        with open(DEST, "rb") as f:
            old = f.read()
    if old is None:
        status = "ติดตั้งใหม่"
    elif old == data:
        status = "เป็นเวอร์ชันล่าสุดอยู่แล้ว"
    else:
        status = "อัพเดท"
    print(f"      สถานะ: {status} (new {sha(data)}" + (f", เดิม {sha(old)})" if old else ")"))

    step(60, "เขียนไฟล์")
    bak = None
    if old is not None and old != data:
        bak = backup(DEST, "statusline.py")
    if old != data:
        write_atomic(DEST, data)

    step(80, "ตั้งค่า statusLine ใน settings.json")
    s_state, s_detail = update_settings(args.force_settings)

    step(95, "ทดสอบรันสคริปต์")
    ok, line = smoke_test()

    step(100, "เสร็จ")
    print(f"\nไฟล์:      {DEST} — {status}")
    if bak:
        print(f"สำรองเดิม:  {bak}")
    print({"ok": "settings:  เพิ่ม/แก้ statusLine แล้ว (สำรอง settings.json ไว้ใน ~/.claude/backups)",
           "unchanged": "settings:  statusLine ชี้ถูกอยู่แล้ว ไม่ได้แก้",
           "foreign": f"settings:  มี statusLine อื่นอยู่ → ไม่ได้แตะ: {s_detail}",
           "error": f"settings:  {s_detail}"}[s_state])
    print(f"ทดสอบรัน:  {'OK → ' + line if ok else 'FAILED: ' + line}")
    if s_state in ("ok", "unchanged") and ok:
        print("\nstatus line จะอัพเดทเองในรอบรีเฟรชถัดไป (ถ้าไม่เห็นการเปลี่ยนแปลงให้เริ่ม session ใหม่)")
    if s_state == "foreign":
        return 3
    return 0 if ok and s_state != "error" else 1


if __name__ == "__main__":
    sys.exit(main())
