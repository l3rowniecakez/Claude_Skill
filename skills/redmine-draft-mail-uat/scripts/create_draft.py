#!/usr/bin/env python3
"""สร้าง Gmail Draft จาก subject + body (HTML) พร้อมภาพ inline — ไม่ใส่ To/Cc/Bcc (ผู้ใช้เติมเอง) และไม่ส่งเมลเด็ดขาด

ใช้: python3 create_draft.py --subject "..." --html body.html [--text body.txt] [--image NAME=path.png ...]
     [--to a@x --cc b@x]   # ไม่บังคับ; ปกติปล่อยว่าง
ใน body.html อ้างภาพด้วย <img src="cid:NAME" width="542">  (NAME ตรงกับ --image NAME=path)
พิมพ์ draft id + ลิงก์ ออกมา
"""
import argparse, base64, hashlib, json, os, re, sys, html as htmlmod
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass
from email.message import EmailMessage
from email.utils import make_msgid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = argparse.ArgumentParser()
ap.add_argument("--subject"); ap.add_argument("--subject-file"); ap.add_argument("--html", required=True); ap.add_argument("--text")
ap.add_argument("--allow-unmasked-image", action="store_true", help="ข้ามการตรวจ PDPA manifest (ห้ามใช้กับภาพ screenshot ดิบ)"); ap.add_argument("--update", help="draft id ที่มีอยู่แล้ว: แก้ draft เดิมแทนการสร้างใหม่"); ap.add_argument("--image", action="append", default=[]); ap.add_argument("--to", action="append", default=[]); ap.add_argument("--cc", action="append", default=[])
a = ap.parse_args()

if a.subject_file:
    a.subject = open(a.subject_file, encoding="utf-8").read().strip()
if not a.subject:
    sys.exit("ต้องระบุ --subject หรือ --subject-file")
html = open(a.html, encoding="utf-8").read()
if a.text:
    text = open(a.text, encoding="utf-8").read()
else:
    t = re.sub(r"<br\s*/?>|</(div|p|li|h\d)>", "\n", html, flags=re.I)
    t = re.sub(r"<img[^>]*alt=\"([^\"]*)\"[^>]*>", r"[ภาพ: \1]", t)
    text = htmlmod.unescape(re.sub(r"<[^>]+>", "", t)); text = re.sub(r"\n{3,}", "\n\n", text).strip()

msg = EmailMessage()
msg["Subject"] = a.subject
if a.to: msg["To"] = ", ".join(a.to)
if a.cc: msg["Cc"] = ", ".join(a.cc)
msg.set_content(text)
msg.add_alternative(html, subtype="html")
html_part = msg.get_payload()[1]
def _check_masked(path):
    """ภาพที่แนบต้องผ่าน blur_images.py (อยู่ใน manifest .pdpa_processed.json ของโฟลเดอร์เดียวกัน เทียบ sha256) — กันภาพ screenshot ดิบหลุดเข้าเมล"""
    mf = os.path.join(os.path.dirname(os.path.abspath(path)), ".pdpa_processed.json")
    h = hashlib.sha256(open(path, "rb").read()).hexdigest()
    ok = os.path.exists(mf) and h in json.load(open(mf, encoding="utf-8")).get("files", {})
    if not ok and not a.allow_unmasked_image:
        sys.exit("หยุด: ภาพ %s ไม่ได้ผ่าน blur_images.py (ไม่อยู่ใน .pdpa_processed.json) — ภาพที่ยังไม่ปิดข้อมูลส่วนบุคคลห้ามเข้าเมล UAT" % path)


for spec in a.image:
    name, path = spec.split("=", 1)
    _check_masked(path)
    if 'cid:%s"' % name not in html:
        print("เตือน: ไม่พบ cid:%s ใน HTML (ภาพนี้จะไม่แสดง)" % name, file=sys.stderr)
    data = open(path, "rb").read()
    sub = "png" if path.lower().endswith(".png") else "jpeg"
    html_part.add_related(data, maintype="image", subtype=sub, cid="<%s>" % name, filename=os.path.basename(path), disposition="inline")
for cid in re.findall(r'cid:([A-Za-z0-9_\-]+)', html):
    if cid not in [s.split("=", 1)[0] for s in a.image]:
        print("เตือน: HTML อ้าง cid:%s แต่ไม่ได้ส่ง --image %s=..." % (cid, cid), file=sys.stderr)

svc, tok = common.gmail_service("draft")
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
if a.update:
    d = svc.users().drafts().update(userId="me", id=a.update, body={"message": {"raw": raw}}).execute()
else:
    d = svc.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
print("%s Draft แล้ว (ไม่ได้ส่ง) id=%s  ขนาดข้อความ ~%d KB" % ("แก้ไข" if a.update else "สร้าง", d["id"], len(raw) * 3 // 4 // 1024))
print("เปิดดู: https://mail.google.com/mail/u/0/#drafts  (หาเมลที่ subject: %s)" % a.subject[:60])
