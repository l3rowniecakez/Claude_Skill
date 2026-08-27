---
name: git-new-ticket
description: เปิด Ticket ใหม่บน Gitblit (title/topic/description เท่านั้น ไม่มี code) ผ่าน web login session + Wicket AJAX submit บนพอร์ต 8443 — ไม่ใช้ browser จริง ขับด้วย curl ล้วน ๆ โดยถามครบ 3 อย่างก่อนเสมอ (Repo URL แบบ http, username/password เข้า Gitblit, เลข Ref RM ที่จะเปิด ticket) แล้วสรุปให้ confirm ก่อนสร้างจริง และข้อความ ticket ต้องปิดท้ายด้วย #ai-work เสมอ
installer: create-shortcut
created_at: 2026-08-27T13:32:34+07:00
argument-hint: "[repo-url-http] [rm-ref]"
---

# /git-new-ticket — เปิด Ticket ใหม่บน Gitblit (ไม่มี code)

Skill นี้มีหน้าที่เดียว: เปิด **ticket record ใหม่** (title/topic/description) บน
Gitblit ผ่าน web UI (พอร์ต `8443`) โดยขับด้วย `curl` ล้วน ๆ ไม่ต้องเปิด browser
จริง อิง flow ที่ยืนยันแล้วใน [[reference_gitblit_web_ticket_creation]] — คนละ
เรื่องกับการ push code เข้า `ticket/N` ผ่าน SSH (พอร์ต `29418`, ดู
[[git-commit-push]] / [[reference_claim_dataextraction_gitblit]]) ซึ่งใช้ได้เฉพาะ
ticket ที่มีอยู่แล้วเท่านั้น

**กฎเหล็ก**: ห้าม submit ticket จริงจนกว่าจะถามครบ 3 อย่าง + โชว์สรุปให้ user
confirm ก่อนเสมอ แม้ข้อมูลจะมาครบใน `$ARGUMENTS` ตั้งแต่แรกก็ตาม
([[feedback_never_auto_commit_wait_for_explicit_instruction]] — logic เดียวกับ
push code: การเรียก skill ไม่เท่ากับอนุมัติให้ยิงจริงทันที)

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — ถามข้อมูลให้ครบ 3 อย่าง

ถ้ามาใน `$ARGUMENTS` แล้วครบก็ใช้เลย ข้อไหนขาดให้ถามเพิ่ม:

1. **Repo URL (http)** — เช่น `https://10.100.2.187:8443/summary/delphi/groupwork-system-2016.git`
   หรือแค่ path ของ repo เช่น `delphi/groupwork-system-2016.git` ก็ได้ ให้ parse หา
   ส่วน `{repo}` (เช่น `delphi/groupwork-system-2016.git`) และ host:port ออกมา
   (default host คือ `10.100.2.187:8443` ถ้า user ไม่ได้ระบุ host มาเอง — เป็น host
   เดียวกับที่ [[reference_gitblit_credentials]] ใช้อยู่แล้วแต่คนละพอร์ต)
2. **Username / Password เข้า Gitblit** — ถามทุกครั้งตามที่ user สั่งไว้ตรง ๆ
   สำหรับ skill นี้ (ต่างจาก default ของ [[feedback_never_store_db_credentials]] ที่
   ให้ auto-reuse ได้) — แต่เพื่อความสะดวกให้เสนอ default จาก
   [[reference_gitblit_credentials]] เป็นตัวเลือกแรกด้วย `AskUserQuestion`:
   - **ใช้ credential เดิมที่จำไว้ (Recommended)** — โชว์แค่ username ไม่ต้องโชว์
     password ทับซ้ำ
   - **ใช้ username/password อื่น** — ให้พิมพ์มาใหม่ทั้งคู่

   ถ้า login fail (ไม่ใช่ HTTP Basic — ต้องเป็น form login ตาม Step 3) ให้แจ้ง user
   ว่า auth ไม่ผ่าน (password อาจ rotate ไปแล้ว) แล้วถามรหัสใหม่ ไม่เดาซ้ำเอง
3. **Ref RM ที่จะเปิด Ticket** — เลข Redmine ticket ที่ ticket นี้เกี่ยวข้อง (เช่น
   `93857`)

---

## Step 2 — ดึงรายละเอียดจาก Redmine มาช่วยตั้ง title/description

ใช้ [[reference_redmine_api_key]] ดึง subject ของ RM ที่ได้จาก Step 1 มาช่วยร่าง
เนื้อหา ticket (ไม่บังคับต้องสำเร็จ — ถ้า fetch ไม่ได้ ให้ถาม user แทน):

```bash
curl -s -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/issues/<RM>.json"
```

ร่างค่าที่จะใช้สร้าง ticket:

- **title**: `RM #<RM>: <subject จาก Redmine>` (ถ้าดึง subject ไม่ได้ ให้ถาม user
  ว่าจะตั้ง title เองว่าอะไร)
- **topic**: `RM #<RM>`
- **description**: สรุปสั้น ๆ จาก Redmine (หรือที่ user ให้มา) ต่อท้ายด้วย
  `#ai-work` เสมอ — เช็คทุกครั้งว่ามี tag นี้ต่อท้ายจริง อย่าเชื่อว่าใส่แล้ว
  ([[feedback_tag_ai_work_comments]] — จุดที่เคยพลาดซ้ำมาแล้วในบริบทอื่น)
- ฟิลด์ที่เหลือปล่อย default: `type=2` (bug) เว้นแต่ user ระบุอย่างอื่น,
  `severity=0`, `priority:priority=2` (normal), `responsible:responsible=` ว่าง
  (unassigned)

---

## Step 3 — สรุปให้ confirm ก่อนสร้างจริง

**ต้องรอให้ข้อมูลครบทุกฟิลด์ก่อน** (รวมค่าที่ดึง/ร่างมาจาก Redmine ใน Step 2 —
title, topic, description พร้อม `#ai-work`, type/severity/priority) แล้วค่อยสรุป
เป็นก้อนเดียวให้ user confirm ทีเดียว **ห้ามสรุปทีละส่วนหรือแยกถามเป็นหลายรอบ**
และห้ามข้ามขั้นนี้ไม่ว่ากรณีใด แม้ `$ARGUMENTS` จะมาครบตั้งแต่แรกก็ตาม:

```
สรุปก่อนเปิด Ticket บน Gitblit
=======================================
Host           : <host:8443>
Repo           : <{repo}>
Ref RM         : #<RM>
Title          : <title>
Topic          : <topic>
Description    : <description พร้อม #ai-work>
Type/Severity  : <...>
Priority       : <...>
Responsible    : <...>
Username       : <username> (password จะไม่โชว์)
=======================================
```

ใช้ `AskUserQuestion` ถาม **Confirm สร้าง ticket / ยกเลิก** ในขั้นตอนเดียวหลังจากที่
ข้อมูลทุกฟิลด์ครบแล้วเท่านั้น

---

## Step 4 — ลงมือสร้าง ticket จริง (curl, ตาม [[reference_gitblit_web_ticket_creation]])

หลัง confirm แล้วเท่านั้น:

```bash
JAR=$(mktemp)
BASE="https://<host:8443>"
REPO="<{repo}>"           # เช่น delphi/groupwork-system-2016.git
REPO_2F="$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(urllib.parse.quote(sys.argv[1], safe=''), safe=''))" "$REPO")"

# 1) GET root — ตั้ง JSESSIONID เริ่มต้น
curl -s -k -c "$JAR" -b "$JAR" "$BASE/" -o /dev/null

# 2) POST form login (ต้องเป็น form login จริง ไม่ใช่ Basic Auth)
curl -s -k -c "$JAR" -b "$JAR" -D - -o /dev/null \
  -X POST "$BASE/?wicket:interface=:0:userPanel:loginForm::IFormSubmitListener::" \
  --data-urlencode "username=<username>" \
  --data-urlencode "password=<password>"

# 3) GET new-ticket page — repo ต้อง double-percent-encode (%252F)
NEWPAGE=$(curl -s -k -c "$JAR" -b "$JAR" "$BASE/tickets/new/$REPO_2F")

# 4) parse form id="idc": ดึง hidden field idc_hf_0 และเลข {N} จาก onclick ของปุ่ม create
#    (wicketSubmitFormById('idc', '../../?wicket:interface=:{N}:editForm:create::...', ...))

# 5) POST AJAX submit ไปที่ wicket:interface ที่ parse ได้ พร้อม header Wicket-Ajax
curl -s -k -c "$JAR" -b "$JAR" \
  -H "Wicket-Ajax: true" -H "X-Requested-With: XMLHttpRequest" \
  -H "Accept: application/xml, text/xml, */*; q=0.01" \
  --data-urlencode "title=<title>" \
  --data-urlencode "topic=<topic>" \
  --data-urlencode "description=<description พร้อม #ai-work>" \
  --data-urlencode "type=<type>" \
  --data-urlencode "severity=<severity>" \
  --data-urlencode "priority:priority=<priority>" \
  --data-urlencode "mergeto:mergeto=" \
  --data-urlencode "idc_hf_0=" \
  --data-urlencode "create=create" \
  "$BASE/?wicket:interface=:<N>:editForm:create::IActivePageBehaviorListener:0:2&wicket:ignoreIfNotActive=true"

rm -f "$JAR"
```

- `{N}` ต้อง parse ใหม่ทุกครั้งจากหน้าที่เพิ่ง GET มาใน Step ก่อนหน้า (ไม่ stable
  ข้าม request)
- response สำเร็จจะเป็น `<ajax-response><redirect><![CDATA[.../tickets/{repo}/{เลข ticket ใหม่}]]></redirect></ajax-response>`
- **ห้าม** log/echo password ออกมาในเทอร์มินัลหรือใน output ใด ๆ

---

## Step 5 — รายงานผล

หลังสร้างสำเร็จ สรุปให้ user:

- เลข ticket ใหม่ + URL เต็ม (จาก `<redirect>`)
- Ref RM ที่ผูกไว้
- เตือนว่า nี่เป็นแค่ ticket record (title/description) ยังไม่มี code ผูก — ถ้าจะ
  push code เข้า ticket นี้ต้องใช้ [[git-commit-push]] หรือ SSH push ไปที่
  `ticket/<เลขใหม่>` แยกต่างหาก

ถ้า submit fail (auth error, form field เปลี่ยนไปจากที่คาด, repo ไม่พบ) ให้รายงาน
error ตรง ๆ กับ user พร้อม response ที่ได้ ห้ามลองซ้ำเดา ๆ เอง

---

## Notes

- Skill นี้จบงานที่เปิด ticket เท่านั้น — ไม่ merge, ไม่ push code, ไม่ log time
  กลับ Redmine อัตโนมัติ (ใช้ `/redmine-logtime` แยกถ้าต้องการ)
- ถ้า auth ผ่านไม่ได้ด้วย credential จาก memory (password rotate รายเดือน) ให้ถาม
  user รหัสใหม่แล้วอัปเดต [[reference_gitblit_credentials]] ให้ตรง

---

ARGUMENTS: $ARGUMENTS
