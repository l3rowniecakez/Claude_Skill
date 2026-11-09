#!/usr/bin/env python3
"""ตรวจความพร้อมของเครื่อง: python libs, Gmail token, profile รูปแบบเมล UAT ของผู้ใช้คนนี้.
exit code 0 = พร้อมทั้งหมด, 1 = ขาดบางอย่าง (อ่านข้อความที่พิมพ์)"""
import importlib, os, sys, json
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
ok = True
print("สภาพแวดล้อม: %s | python %s" % ("Windows native (CLI/Desktop)" if common.IS_WIN else ("WSL" if common.IS_WSL else "Linux/macOS"), sys.version.split()[0]))
PIPC = "py -m pip install" if common.IS_WIN else "pip install"
for mod, pip in [("googleapiclient", "google-api-python-client"), ("google.oauth2", "google-auth"), ("PIL", "Pillow")]:
    try:
        importlib.import_module(mod); print("OK   lib", mod)
    except Exception:
        ok = False; print("MISS lib %s  -> %s %s  (แนะนำ venv: python -m venv <โฟลเดอร์> แล้วใช้ python ใน venv)" % (mod, PIPC, pip))
for need in ("read", "draft"):
    p = common.find_token(need)
    if p: print("OK   gmail token (%s): %s" % (need, p))
    else:
        ok = False
        print("MISS gmail token สำหรับ %s  -> python3 auth_gmail.py  (ต้องมี client_secret.json) หรือใช้ OAuth 'Claude For Access GDrive' ที่ ~/.config/claude-google-access/" % need)
prof = common.load_profile()
if prof:
    print("OK   profile: %s (เรียนรู้จาก %s ฉบับ, บัญชี %s, เมื่อ %s)" % (common.PROFILE_PATH, prof.get("mails_analyzed"), prof.get("account"), prof.get("learned_at")))
else:
    ok = False
    print("MISS profile  -> เครื่อง/ผู้ใช้นี้ยังไม่เคยเรียนรู้พฤติกรรมการส่งเมล UAT: รัน  %s learn_style.py  (ในโฟลเดอร์ scripts) ก่อนร่างเมลครั้งแรก" % ("python" if common.IS_WIN else "python3"))
sys.exit(0 if ok else 1)
