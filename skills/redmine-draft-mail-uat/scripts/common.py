"""Shared helpers for /redmine-draft-mail-uat (portable: no machine/user specific values here).

Machine/user specific data lives in  ~/.config/redmine-draft-mail-uat/  (profile.json, samples/, token.json)
"""
import os, sys, json

IS_WIN = sys.platform == "win32"
IS_WSL = (not IS_WIN) and os.path.exists("/proc/version") and "microsoft" in open("/proc/version").read().lower()
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass

CONF_DIR = os.path.expanduser(os.environ.get("RDMU_CONFIG_DIR", "~/.config/redmine-draft-mail-uat"))
PROFILE_PATH = os.path.join(CONF_DIR, "profile.json")

# Token search order. First existing token whose scopes satisfy the need wins.
TOKEN_CANDIDATES = [
    os.environ.get("RDMU_TOKEN", ""),
    os.path.join(CONF_DIR, "token.json"),
    os.path.expanduser("~/.config/claude-google-access/token.json"),       # "Claude For Access GDrive" OAuth (gmail.modify)
    os.path.join(os.environ.get("APPDATA", ""), "redmine-draft-mail-uat", "token.json") if IS_WIN else "",
    os.path.expanduser("~/.config/redmine-summary-to-email/gmail_token.json"),  # gmail.compose only (cannot read Sent)
]
READ_SCOPES = {"https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.readonly",
               "https://mail.google.com/"}
DRAFT_SCOPES = {"https://www.googleapis.com/auth/gmail.modify", "https://www.googleapis.com/auth/gmail.compose",
                "https://mail.google.com/"}


def _scopes_of(path):
    try:
        t = json.load(open(path, encoding="utf-8"))
        s = t.get("scopes") or t.get("scope") or []
        return set(s.split() if isinstance(s, str) else s)
    except Exception:
        return set()


def find_token(need):
    """need = 'read' | 'draft'. Returns path or None."""
    want = READ_SCOPES if need == "read" else DRAFT_SCOPES
    for p in TOKEN_CANDIDATES:
        if p and os.path.exists(p) and (_scopes_of(p) & want):
            return p
    return None


def gmail_service(need):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    p = find_token(need)
    if not p:
        sys.exit("ไม่พบ Gmail token ที่มีสิทธิ์ %s — รัน: python3 check_env.py (แล้วทำตามคำแนะนำ / auth_gmail.py)" % need)
    creds = Credentials.from_authorized_user_file(p)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        open(p, "w").write(creds.to_json())
    return build("gmail", "v1", credentials=creds), p


def load_profile():
    if not os.path.exists(PROFILE_PATH):
        return None
    return json.load(open(PROFILE_PATH, encoding="utf-8"))
