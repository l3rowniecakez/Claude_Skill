#!/usr/bin/env python3
"""Pre-flight check for /git-learn-grouplife-er-diagram on ANY machine (Linux / macOS / Windows).
Run it with the SAME python you will use for the other scripts:  python check_setup.py
Reports each requirement as OK / MISSING with the fix. Read-only; exit code 1 if anything is missing.
"""
import sys, os, json, importlib
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.path.expanduser("~")
TOKEN = os.environ.get("GROUPLIFE_GOOGLE_TOKEN") or os.path.join(HOME, ".config", "claude-google-access", "token.json")
CRED = os.environ.get("GROUPLIFE_DB_CREDENTIALS") or os.path.join(HOME, ".config", "grouplife-db", "credentials.json")
problems = []


def report(ok, what, fix=""):
    print(("OK      " if ok else "MISSING ") + what + ("" if ok else f"\n         -> {fix}"))
    if not ok:
        problems.append(what)


print(f"python: {sys.executable} ({sys.version.split()[0]})")
for mod, pip in [("googleapiclient", "google-api-python-client"), ("google.oauth2", "google-auth"),
                 ("pymssql", "pymssql"), ("PIL", "Pillow"), ("openpyxl", "openpyxl")]:
    try:
        importlib.import_module(mod); report(True, f"python package {pip}")
    except Exception:
        report(False, f"python package {pip}", f"{sys.executable} -m pip install -r \"{os.path.join(HERE, '..', 'requirements.txt')}\"")

for f in ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"):
    report(os.path.exists(os.path.join(HERE, "..", "fonts", f)), f"bundled font {f}", "re-install the skill (fonts/ folder is part of it)")

ok = os.path.exists(TOKEN)
report(ok, f"Google token ({TOKEN})", "create it with the team's OAuth setup (see SKILL.md 'Setup'); account needs Editor on the Drive folder 'GroupLife by Claude AI'")
if ok:
    try:
        sc = json.load(open(TOKEN, encoding="utf-8")).get("scopes", [])
        need = {"https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"}
        report(need <= set(sc), "Google token scopes (spreadsheets + drive)", "re-authorize with those scopes")
    except Exception as e:
        report(False, "Google token readable", str(e))

ok = os.path.exists(CRED)
report(ok, f"DB credentials ({CRED})", 'create JSON {"10.100.2.52": {"user": "...", "password": "..."}, "10.100.3.139": {...}, "12.100.7.22": {...}} — ask the DB owner; never commit it')
if ok:
    try:
        d = json.load(open(CRED, encoding="utf-8"))
        report(all("user" in v and "password" in v for v in d.values()) and bool(d), "DB credentials format", 'each IP needs "user" and "password"')
    except Exception as e:
        report(False, "DB credentials readable JSON", str(e))

print("\nAll good." if not problems else f"\n{len(problems)} item(s) missing.")
sys.exit(1 if problems else 0)
