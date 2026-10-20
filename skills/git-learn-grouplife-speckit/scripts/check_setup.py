#!/usr/bin/env python3
"""Pre-flight check for /git-learn-grouplife-speckit on ANY machine. Run with the python you will use for the other scripts.
Reports each requirement as OK / MISSING with the exact fix. Read-only; exit code 1 if anything is missing.
When /STANDARD_REQ_TEMPLATE_v1_1 (or another dependent skill) is missing it prints the /ocean-skill-update command that installs them.
"""
import sys, os, json, shutil, importlib
from pathlib import Path
for _s in (sys.stdout, sys.stderr):
    _s.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
SKILLS = HERE.parents[1]
HOME = Path.home()
TOKEN = Path(os.environ.get("GROUPLIFE_GOOGLE_TOKEN") or HOME / ".config" / "claude-google-access" / "token.json")
GITBLIT = HOME / ".config" / "gitblit-web" / "credentials.json"
DBCRED = Path(os.environ.get("GROUPLIFE_DB_CREDENTIALS") or HOME / ".config" / "grouplife-db" / "credentials.json")
problems, missing_skills = [], []


def report(ok, what, fix=""):
    print(("OK      " if ok else "MISSING ") + what + ("" if ok else f"\n         -> {fix}"))
    if not ok:
        problems.append(what)


print(f"python: {sys.executable} ({sys.version.split()[0]})   skills dir: {SKILLS}")
for mod, pip in [("googleapiclient", "google-api-python-client"), ("google.oauth2", "google-auth"), ("pymssql", "pymssql")]:
    try:
        importlib.import_module(mod); report(True, f"python package {pip}")
    except Exception:
        report(False, f"python package {pip}", f"{sys.executable} -m pip install -r \"{HERE.parent / 'requirements.txt'}\"")

# --- skills this one builds on / calls
need = ["git-learn-grouplife", "git-learn-grouplife-system-analyst", "git-learn-grouplife-er-diagram",
        "STANDARD_REQ_TEMPLATE_v1_1"]
for n in need:
    ok = (SKILLS / n / "SKILL.md").exists()
    report(ok, f"skill /{n}", "install with /ocean-skill-update")
    if not ok:
        missing_skills.append(n)
for f in ("git-learn-grouplife/scripts/browse_repo.py", "git-learn-grouplife-er-diagram/scripts/db_schema.py"):
    report((SKILLS / f).exists(), f"file {f}", "re-install the owning skill with /ocean-skill-update")
report((SKILLS / "STANDARD_REQ_TEMPLATE_v1_1" / "STANDARD_REQ_TEMPLATE_v1_1.md").exists(), "REQ template file STANDARD_REQ_TEMPLATE_v1_1.md",
       "re-install /STANDARD_REQ_TEMPLATE_v1_1 with /ocean-skill-update")

# --- credentials
ok = TOKEN.exists()
report(ok, f"Google token ({TOKEN})", "create it with the team's OAuth setup; account needs Editor on the Drive folders "
       "'GroupLife by Claude AI' and 'GroupLife SpecKit by Claude AI'")
if ok:
    try:
        sc = set(json.load(open(TOKEN, encoding="utf-8")).get("scopes", []))
        report({"https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"} <= sc,
               "Google token scopes (spreadsheets + drive)", "re-authorize with those scopes")
    except Exception as e:
        report(False, "Google token readable", str(e))
report(GITBLIT.exists(), f"Gitblit web credentials ({GITBLIT})",
       'create JSON {"base_url": "https://10.100.2.187:8443/", "username": "...", "password": "..."} (see /git-learn-grouplife)')
report(DBCRED.exists(), f"DB credentials ({DBCRED})",
       'create JSON {"10.100.2.52": {"user": "...", "password": "..."}, ...} — ask the DB owner; never commit it')

if missing_skills:
    only = ",".join(missing_skills)
    print(f"\nTo install the missing skills run:  /ocean-skill-update  -> choose 'เลือกเฉพาะบาง Skill' -> {only}\n"
          f"(or non-interactively: bash <ocean-skill-update dir>/scripts/update.sh --only {only})")
print("\nAll good." if not problems else f"\n{len(problems)} item(s) missing.")
sys.exit(1 if problems else 0)
