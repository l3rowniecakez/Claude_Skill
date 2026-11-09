#!/usr/bin/env python3
"""ขอ OAuth token สำหรับ Gmail (gmail.modify = อ่าน Sent + สร้าง Draft) เก็บที่ ~/.config/redmine-draft-mail-uat/token.json
ต้องมี OAuth client (Desktop app) ไฟล์ client_secret.json ที่ใดที่หนึ่งต่อไปนี้ หรือส่ง --client-secret <path>:
  ~/.config/redmine-draft-mail-uat/client_secret.json | ~/.config/claude-google-access/client_secret.json
หมายเหตุ: flow นี้ยังไม่ได้ทดสอบบนเครื่องที่เขียน skill (เครื่องนั้นมี token อยู่แล้ว)
"""
import argparse, os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
ap = argparse.ArgumentParser(); ap.add_argument("--client-secret"); a = ap.parse_args()
cands = [a.client_secret, os.path.join(common.CONF_DIR, "client_secret.json"),
         os.path.expanduser("~/.config/claude-google-access/client_secret.json")]
cs = next((c for c in cands if c and os.path.exists(c)), None)
if not cs: sys.exit("ไม่พบ client_secret.json — ขอไฟล์ OAuth client (Desktop) จากผู้ดูแล แล้ววางที่ %s" % os.path.join(common.CONF_DIR, "client_secret.json"))
from google_auth_oauthlib.flow import InstalledAppFlow
flow = InstalledAppFlow.from_client_secrets_file(cs, ["https://www.googleapis.com/auth/gmail.modify"])
creds = flow.run_local_server(port=0, open_browser=common.IS_WIN)
os.makedirs(common.CONF_DIR, exist_ok=True)
out = os.path.join(common.CONF_DIR, "token.json"); open(out, "w").write(creds.to_json()); os.chmod(out, 0o600)
print("บันทึก token แล้ว:", out)
