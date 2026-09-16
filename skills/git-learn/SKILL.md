---
installer: create-shortcut
name: git-learn
description: 'อ่าน source code ของ repo ใดๆ จาก GitBlit แบบ remote (ไม่ clone ลงเครื่อง) โดยรับ repo path ตรงๆ จากผู้ใช้ ไม่ผูกกับชีตติดตามหรือกลุ่ม delphi group-insurance เหมือน /git-learn-grouplife. Use when user says "/git-learn" หรือต้องการอ่าน/ศึกษา source code repo ทั่วไปจาก GitBlit โดยไม่ต้องการ clone ลงเครื่อง (ถ้าเป็น App ในกลุ่ม delphi group-insurance ให้ใช้ /git-learn-grouplife แทน).'
created_at: 2026-09-16T15:15:36+07:00
argument-hint: "[repo path หรือ SSH clone url] [sub path ถ้ามี]"
---

# /git-learn — อ่าน source code ของ repo ใดๆ จาก GitBlit แบบไม่ clone

Sibling ของ [[git-clone]] เหมือนที่ [[git-learn-grouplife]] เป็น sibling ของ
[[git-clone-grouplife]] — ต่างจาก `/git-learn-grouplife` ตรงที่ตัวนี้**ไม่ผูกกับ
ชีตติดตาม**ของกลุ่ม delphi group-insurance และไม่จำกัดว่าต้องเป็น App ในกลุ่ม
`delphi` — รับ repo path ตรง ๆ จากผู้ใช้แล้วอ่าน source ผ่าน Gitblit web UI เลย
(endpoint `tree/` สำหรับ list โฟลเดอร์ และ `raw/` สำหรับดึงเนื้อไฟล์ดิบ) โดย
**ไม่ clone**อะไรลงเครื่องทั้งสิ้น

เหมาะกับกรณีแค่อยากอ่าน/ทำความเข้าใจโค้ด ไม่ได้จะแก้ไขหรือ push อะไรกลับ (ถ้าต้อง
แก้ไขจริงต้องใช้ `/git-clone` แทน เพราะต้องมี `.git` ในเครื่องถึงจะ commit/push ได้)

skill นี้เป็น read-only ต่อ repo บน Gitblit — ไม่เคยเขียนอะไรกลับ

## Step 1 — ขอ repo path

ถาม repo path จากผู้ใช้ก่อนเสมอ ห้ามเดา — รับได้ 2 แบบ:

1. **repo path ตรง ๆ ตามที่ Gitblit web UI ใช้** เช่น `delphi/groupwork-system-2016`
   หรือ `myrepo` (ถ้าไม่มี group folder) — คือ segment ระหว่าง host:port กับ
   `.git` ใน SSH clone url นั่นเอง
2. **SSH clone url เต็ม** เช่น `ssh://user@10.100.2.187:29418/delphi/myrepo.git`
   — ถ้าผู้ใช้ให้แบบนี้มา ให้ตัดเอาเฉพาะ segment ระหว่าง `host:port/` กับ `.git`
   ออกมาเองก่อนใช้ (เช่น `delphi/myrepo`) ห้ามส่ง SSH url ทั้งก้อนเข้า
   `browse_repo.py` ตรง ๆ

ถ้าผู้ใช้บอกแค่ชื่อ repo สั้น ๆ โดยไม่รู้ว่ามี group folder ครอบหรือไม่ ให้ลองเปล่า ๆ
ก่อน (`browse_repo.py list "<repo>"`) ถ้า error ว่าไม่พบ ให้ถามผู้ใช้ว่า repo นี้อยู่
ใต้ group/folder อะไรบน Gitblit — **ห้ามเดา group เอง** (เช่นอย่าเดาว่าเป็น `delphi`
ถ้าผู้ใช้ไม่ได้บอกและ repo ไม่ใช่โปรแกรมกลุ่ม delphi group-insurance)

ถ้า repo ใช้ default branch ไม่ใช่ `master` (เช่น `main`) ทุกคำสั่งด้านล่างรับ
`--branch <ชื่อ>` เพิ่มได้

## Step 2 — สำรวจโครงสร้างไฟล์ก่อนอ่าน

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn/scripts/browse_repo.py tree "<repo>" "<path เริ่มต้น>"
```
- `<path เริ่มต้น>` เว้นว่างได้ถ้าต้องการเริ่มจาก root ของ repo
- คืน `files` เป็น list path เต็มของทุกไฟล์ใต้ path นั้นแบบ recursive,
  `requests_used`/`truncated` บอกว่าไล่ทันครบไหม — ถ้า `truncated: true` (ชนเพดาน
  `--max-requests` default 500) ให้ไล่ดูทีละโฟลเดอร์ย่อยด้วย `browse_repo.py list
  "<repo>" "<path ย่อย>"` แทน อย่าเพิ่ม `--max-requests` มั่ว ๆ จนกลายเป็นแครอลทั้ง
  repo
- ใช้ `browse_repo.py list "<repo>" "<path>"` (ไม่ระบุ path = root ของ repo) เพื่อดู
  ทีละชั้นเวลาต้องการยืนยันด้วยตาหรือ path ลึกมาก

## Step 3 — อ่านไฟล์ที่ต้องการ

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn/scripts/browse_repo.py read "<repo>" "<file path เต็มจาก tree/list>"
```
- คืน `content` เป็น text (decode utf-8 ก่อน แล้ว fallback cp874 แล้ว latin-1 แบบ
  replace ถ้าจำเป็น) พร้อม `size`/`encoding` ให้เช็ค
- ไฟล์ที่เป็น binary จริง (มี NUL byte ใน 8KB แรก) จะได้ `{"error": "binary
  file..."}` แทน — **ข้ามไฟล์เหล่านี้ไปเลย ไม่ต้องพยายาม decode เอง**
- ไฟล์ที่ใหญ่เกิน 2MB (`--max-bytes` default) จะได้ error บอกขนาดแทนเนื้อหา —
  ถ้าจำเป็นจริง ๆ ค่อยเพิ่ม `--max-bytes` เอง
- อ่านทีละไฟล์ตามที่ต้องการเข้าใจ — skill นี้ไม่ได้ทำให้ grep ข้ามทั้ง repo ได้ใน
  ทีเดียวเหมือนมี local clone ต้องไล่เปิดเองทีละไฟล์ตาม `tree`/`list` ผลลัพธ์

## ข้อจำกัดที่ต้องบอกผู้ใช้ล่วงหน้า (ถ้าเกี่ยวข้อง)

- **แก้ไข/commit/push ไม่ได้จาก skill นี้** — เป็น read-only เพียว ถ้าผู้ใช้บอกว่า
  จะแก้โค้ดหลังอ่านเสร็จ ให้แนะนำ `/git-clone` แทนตั้งแต่ต้น
- **ไม่มี local grep ข้ามทั้ง repo ในทีเดียว** — ถ้าผู้ใช้ต้องการค้นหา keyword ข้าม
  หลายไฟล์/ทั้ง repo เป็นจำนวนมาก การ `tree` แล้วอ่านทีละไฟล์ผ่าน web อาจช้ากว่า
  clone จริงมาก ให้แจ้ง trade-off นี้และเสนอ `/git-clone` เป็นทางเลือกถ้างานลักษณะนี้
- Auth ใช้ session login เว็บเดียวกับ `/git-learn-grouplife` และ
  `/git-clone-grouplife-update` (`~/.config/gitblit-web/credentials.json`, host
  เดียวกัน `10.100.2.187:8443`) — ถ้าไฟล์นี้ไม่มี (เครื่องใหม่) ให้ขอ
  username/password จากผู้ใช้แล้วสร้างไฟล์รูปแบบ `{"base_url":
  "https://10.100.2.187:8443/", "username": "...", "password": "..."}` เอง (ดู
  [[reference-gitblit-credentials]], password rotate รายเดือน)
- ถ้า repo ที่ผู้ใช้ต้องการอ่านอยู่บน Gitblit host อื่นที่ไม่ใช่ `10.100.2.187`
  (ไม่มี credentials.json นี้รองรับ) ให้แจ้งผู้ใช้ตรง ๆ ว่า skill นี้ตั้งค่าไว้สำหรับ
  host เดิมเท่านั้น ยังไม่รองรับหลาย host พร้อมกัน
