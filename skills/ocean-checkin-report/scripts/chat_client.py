#!/usr/bin/env python3
"""Google Chat read-only client + OAuth setup for /ocean-checkin-report.

Secrets never live inside the skill folder. Lookup order:
  token.json / client_secret.json:
    1. $OCEAN_CHAT_CONFIG_DIR (if set)
    2. ~/.config/ocean-google-chat/
    3. ~/.config/claude-google-access/   (legacy, only if its token already has Chat scopes)

Usage:
  chat_client.py check        # JSON status: deps / client_secret / token / scopes / API reachable
  chat_client.py authorize    # loopback OAuth on localhost:8766, prints consent URL, writes token.json
  chat_client.py spaces       # list spaces the user is in
"""
import json
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

CHAT_SCOPES = [
    "https://www.googleapis.com/auth/chat.spaces.readonly",
    "https://www.googleapis.com/auth/chat.messages.readonly",
    "https://www.googleapis.com/auth/chat.memberships.readonly",
]
PRIMARY_DIR = os.environ.get("OCEAN_CHAT_CONFIG_DIR") or os.path.expanduser("~/.config/ocean-google-chat")
LEGACY_DIR = os.path.expanduser("~/.config/claude-google-access")
AUTH_PORT = 8766


def _token_scopes(path):
    try:
        with open(path) as f:
            return json.load(f).get("scopes") or []
    except (OSError, ValueError):
        return []


def find_token():
    for d in (PRIMARY_DIR, LEGACY_DIR):
        p = os.path.join(d, "token.json")
        if os.path.exists(p) and all(s in _token_scopes(p) for s in CHAT_SCOPES[:2]):
            return p
    return None


def find_client_secret():
    for d in (PRIMARY_DIR, LEGACY_DIR):
        p = os.path.join(d, "client_secret.json")
        if os.path.exists(p):
            return p
    return None


def get_service():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    path = find_token()
    if not path:
        sys.exit("NO_CHAT_TOKEN: ยังไม่ได้เปิดสิทธิ์ Google Chat — รัน `chat_client.py check` แล้วทำตามขั้นตอน setup ใน SKILL.md")
    creds = Credentials.from_authorized_user_file(path)
    if not creds.valid:
        creds.refresh(Request())
        with open(path, "w") as f:
            f.write(creds.to_json())
    return build("chat", "v1", credentials=creds, cache_discovery=False)


def list_spaces(svc):
    out, token = [], None
    while True:
        r = svc.spaces().list(pageSize=1000, pageToken=token).execute()
        out += r.get("spaces", [])
        token = r.get("nextPageToken")
        if not token:
            return out


def resolve_space(svc, space):
    """Accept 'spaces/ID', bare ID, or a display-name substring."""
    if space.startswith("spaces/"):
        return space, space
    hits = [s for s in list_spaces(svc) if space.lower() in s.get("displayName", "").lower()]
    if len(hits) == 1:
        return hits[0]["name"], hits[0]["displayName"]
    if not hits:
        return f"spaces/{space}", space
    sys.exit("พบหลายห้อง: " + "; ".join(f'{s["displayName"]} ({s["name"]})' for s in hits))


def list_messages(svc, space, since=None, until=None):
    parts = []
    if since:
        parts.append(f'createTime > "{since}T00:00:00+07:00"')
    if until:
        parts.append(f'createTime < "{until}T23:59:59+07:00"')
    out, token = [], None
    while True:
        kw = dict(parent=space, pageSize=1000, pageToken=token, orderBy="createTime ASC")
        if parts:
            kw["filter"] = " AND ".join(parts)
        r = svc.spaces().messages().list(**kw).execute()
        out += r.get("messages", [])
        token = r.get("nextPageToken")
        if not token:
            return out


def check():
    st = {"config_dir": PRIMARY_DIR}
    try:
        import google_auth_oauthlib  # noqa: F401
        import googleapiclient  # noqa: F401
        st["deps"] = True
    except ImportError:
        st["deps"] = False
    st["client_secret"] = find_client_secret()
    st["token"] = find_token()
    st["api_ok"] = False
    if st["deps"] and st["token"]:
        try:
            svc = get_service()
            svc.spaces().list(pageSize=1).execute()
            st["api_ok"] = True
        except Exception as e:  # report the Google error text verbatim
            st["api_error"] = str(e)[:400]
    st["ready"] = st["api_ok"]
    print(json.dumps(st, ensure_ascii=False, indent=1))


def authorize():
    from google_auth_oauthlib.flow import InstalledAppFlow

    secret = find_client_secret()
    if not secret:
        sys.exit(f"ไม่พบ client_secret.json — วางไฟล์ไว้ที่ {PRIMARY_DIR}/client_secret.json ก่อน")
    os.makedirs(PRIMARY_DIR, mode=0o700, exist_ok=True)
    flow = InstalledAppFlow.from_client_secrets_file(secret, CHAT_SCOPES)
    creds = flow.run_local_server(
        port=AUTH_PORT,
        open_browser=False,
        authorization_prompt_message="เปิดลิงก์นี้ในเบราว์เซอร์เพื่อยืนยันสิทธิ์:\n{url}",
        success_message="ยืนยันสิทธิ์สำเร็จ ปิดแท็บนี้ได้เลย",
        timeout_seconds=900,
    )
    path = os.path.join(PRIMARY_DIR, "token.json")
    with open(path, "w") as f:
        f.write(creds.to_json())
    os.chmod(path, 0o600)
    print(f"\nSaved token to {path}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "check"
    if cmd == "check":
        check()
    elif cmd == "authorize":
        authorize()
    elif cmd == "spaces":
        for s in list_spaces(get_service()):
            print(f'{s["name"]}\t{s.get("spaceType", "")}\t{s.get("displayName", "(DM)")}')
    else:
        sys.exit(__doc__)
