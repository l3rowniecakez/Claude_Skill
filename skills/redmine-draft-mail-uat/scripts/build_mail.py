#!/usr/bin/env python3
"""สร้าง body.html / body.txt ของเมล [แจ้ง UAT] จากไฟล์เนื้อหา JSON โดยใช้ "สไตล์ของผู้ใช้คนนี้" จาก profile.json
(ที่ learn_style.py เรียนรู้จาก Sent ของบัญชีนั้น) — ไม่มีค่าเฉพาะคน/เฉพาะเครื่องฝังในสคริปต์นี้

ใช้: python3 build_mail.py content.json --out-dir <dir>
content.json (ฟิลด์ที่ไม่ใช้ใส่ null/ตัดทิ้งได้):
{
 "subject": "[แจ้ง UAT] Task #N UR YYYYNNNN - ชื่อเรื่อง",     # ถ้าไม่ใส่ prefix ระบบเติม [แจ้ง UAT] ให้
 "salutation": "เรียน ...",
 "title": "ชื่อเรื่อง (บรรทัด เรื่อง ...)",
 "redmine": "Task #N UR YYYYNNNN - ชื่อเรื่อง",              # ข้อความสีน้ำเงินในประโยค 'เนื่องจากได้รับแจ้งตาม Redmine หมายเลข ...'
 "path_blocks": [{"label": "ฝ่าย...", "path": "\\\\server\\...", "program": "OGL_Benefits.exe"}],
 "objectives": ["..."], "before": ["..."], "after": ["..."],
 "details": [{"title": "1. ...", "bullets": ["..."]}],
 "reply_request": "แต่ละฝ่ายหาก UAT เสร็จ กรุณา Reply Email ฉบับนี้...",   # ไม่บังคับ
 "table": {"title": "...", "headers": ["..."], "rows": [["...", "{{ต้องกรอก}}"]]},
 "steps": [{"title": "ขั้นตอน", "text": "...", "expect": "ผลที่คาดหวัง", "image": "cidname|null",
            "image_caption": "...", "image_placeholder": "รอแทรกภาพ: ..."}],
 "image_width": 640
}
ข้อความที่ครอบด้วย {{...}} จะถูกไฮไลต์เหลือง = จุดที่ผู้ใช้ต้องกรอก/แทรกภาพเองก่อนส่ง
"""
import argparse, html, json, os, re, sys
try:
    sys.stdout.reconfigure(encoding="utf-8"); sys.stderr.reconfigure(encoding="utf-8")  # Windows console เป็น cp874/cp1252 → ภาษาไทยจะ error ถ้าไม่ตั้ง
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

ap = argparse.ArgumentParser(); ap.add_argument("content"); ap.add_argument("--out-dir", required=True)
a = ap.parse_args()
c = json.load(open(a.content, encoding="utf-8"))
prof = common.load_profile() or {}
st = prof.get("html_style", {})
RED = st.get("before_color") or "#ff0000"
GREEN = st.get("after_color") or "#38761d"
BLUE = "#0000ff"
SEP = (prof.get("separator_top") or [["=" * 60, 0]])[0][0]
CONTACT = (prof.get("contact_line_top") or [["กรณีติดปัญหา แจ้งทาง Chat หรือแจ้งทาง loop mail นี้ได้เลยครับ", 0]])[0][0]
CLOSING = (prof.get("closing_top") or [["จึงเรียนมาเพื่อทดสอบระบบ", 0]])[0][0]
SIG = prof.get("signature")
IMGW = int(c.get("image_width") or 640)
HL = "background-color:#ffff00"


def esc(t):
    t = html.escape(t or "")
    return re.sub(r"\{\{(.+?)\}\}", lambda m: '<span style="%s">%s</span>' % (HL, m.group(1)), t)


def plain(t):
    return re.sub(r"\{\{(.+?)\}\}", r"<<\1>>", t or "")


H, T = [], []  # html / text parts


def line(t, color=None, u=False, i=False, size=None, br_after=False):
    s = esc(t)
    if size: s = '<font size="%s">%s</font>' % (size, s)
    if u: s = "<u>%s</u>" % s
    if i: s = "<i>%s</i>" % s
    if color: s = '<font color="%s">%s</font>' % (color, s)
    H.append("<div><b>%s</b></div>" % s)
    T.append(plain(t))
    if br_after: H.append("<div><br></div>"); T.append("")


def blank():
    H.append("<div><br></div>"); T.append("")


def sep():
    H.append("<div><b>%s</b></div>" % SEP); T.append(SEP)


def bullets(items, color=None):
    for it in items:
        line(("- " + it) if not re.match(r"^\s*(\d+[\.\)]|-)\s", it) else it, color=color)


# ---------- header
line(c["salutation"])
line("เรื่อง " + c["title"])
blank()
red_txt = c.get("redmine")
if red_txt:
    H.append('<div><b>    เนื่องจากได้รับแจ้งตาม Redmine หมายเลข <font color="%s">%s</font> ได้มีการปรับปรุงระบบต่างๆ ดังนี้</b></div>' % (BLUE, esc(red_txt)))
    T.append("    เนื่องจากได้รับแจ้งตาม Redmine หมายเลข %s ได้มีการปรับปรุงระบบต่างๆ ดังนี้" % red_txt)
blank(); sep(); blank()

# ---------- UAT path
line("ช่องทาง Path สำหรับ UAT", u=True)
for pb in c.get("path_blocks", []):
    if pb.get("label"): line(pb["label"])
    line(pb["path"])
    if pb.get("program"): line("**เข้าโปรแกรม %s**" % pb["program"], color=BLUE)
    blank()
line("***" + CONTACT + " ***", color=RED, i=True)
if c.get("reply_request"):
    blank(); line("*** " + c["reply_request"] + " ***", color=RED, i=True)
blank(); sep(); blank()

# ---------- objectives / before-after
if c.get("objectives"):
    line("วัตถุประสงค์", u=True, size=4)
    bullets(c["objectives"]); blank(); sep(); blank()
if c.get("before") or c.get("after"):
    if c.get("before"):
        line("เดิม", color=RED, u=True); bullets(c["before"], color=RED); blank()
    if c.get("after"):
        line("หลังแก้ไข", color=GREEN, u=True); bullets(c["after"], color=GREEN); blank()
    sep(); blank()

# ---------- program details
if c.get("details"):
    line("รายละเอียดการเพิ่มเติม/ปรับปรุงโปรแกรม", u=True, size=4)
    for d in c["details"]:
        blank(); line(d["title"])
        bullets(d.get("bullets", []))
    blank(); sep(); blank()

# ---------- test data table
tb = c.get("table")
if tb:
    line(tb["title"], u=True, size=4)
    th = "".join('<td style="border:1px solid #888;padding:4px 8px;background:#e8f0fe"><b>%s</b></td>' % esc(x) for x in tb["headers"])
    rows = ""
    for r in tb["rows"]:
        rows += "<tr>" + "".join('<td style="border:1px solid #888;padding:4px 8px">%s</td>' % esc(x) for x in r) + "</tr>"
    H.append('<table style="border-collapse:collapse;font-size:13px"><tr>%s</tr>%s</table>' % (th, rows))
    T.append(tb["title"]); T.append(" | ".join(tb["headers"]))
    for r in tb["rows"]: T.append(" | ".join(plain(x) for x in r))
    blank(); sep(); blank()

# ---------- steps
if c.get("steps"):
    line("ขั้นตอนการ UAT", u=True, size=4)
    for s in c["steps"]:
        blank(); line(s["title"])
        if s.get("text"): line(s["text"])
        for im in s.get("images", []):   # หลายภาพต่อ 1 ขั้นตอน: [{"image": "cid", "caption": "..."}]
            H.append('<div><img src="cid:%s" alt="%s" width="%d"></div>' % (im["image"], html.escape(im.get("caption") or im["image"]), IMGW))
            T.append("[ภาพ: %s]" % (im.get("caption") or im["image"]))
            if im.get("caption"): line(im["caption"], i=True)
        if s.get("image"):
            H.append('<div><img src="cid:%s" alt="%s" width="%d"></div>' % (s["image"], html.escape(s.get("image_caption") or s["image"]), IMGW))
            T.append("[ภาพ: %s]" % (s.get("image_caption") or s["image"]))
            if s.get("image_caption"): line(s["image_caption"], i=True)
        elif s.get("image_placeholder"):
            line("{{[" + s["image_placeholder"] + "]}}")
        if s.get("expect"): line("ผลที่คาดหวัง: " + s["expect"], color=GREEN)
    blank(); sep(); blank()

line(CLOSING)
blank()
if SIG:
    H.append("<div>-- <br>%s</div>" % "<br>".join(html.escape(x) for x in SIG.split("\n") if x.strip()))
    T.append("-- \n" + "\n".join(x for x in SIG.split("\n") if x.strip()))

os.makedirs(a.out_dir, exist_ok=True)
open(os.path.join(a.out_dir, "body.html"), "w", encoding="utf-8").write('<div dir="ltr">' + "\n".join(H) + "</div>")
open(os.path.join(a.out_dir, "body.txt"), "w", encoding="utf-8").write("\n".join(T))
subj = c["subject"]
if not re.match(r"^\s*\[\s*แจ้ง\s*UAT\s*\]", subj):
    subj = "[แจ้ง UAT] " + subj
open(os.path.join(a.out_dir, "subject.txt"), "w", encoding="utf-8").write(subj)
print("เขียน body.html / body.txt / subject.txt ที่", a.out_dir)
print("subject:", subj)
ph = len(re.findall(r"\{\{", json.dumps(c, ensure_ascii=False)))
print("จุดที่ต้องกรอก/แทรกภาพเอง (ไฮไลต์เหลือง): %d จุด" % ph)
