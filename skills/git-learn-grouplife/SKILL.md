---
installer: create-shortcut
name: git-learn-grouplife
description: 'อ่าน source code ของ App เดียวจาก Gitblit กลุ่ม delphi แบบ remote (ไม่ clone ลงเครื่อง) โดยดูข้อมูล repo/path จากชีตติดตามเดียวกับ /git-clone-grouplife (spreadsheet 18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0). Use when user says "/git-learn-grouplife", ต้องการอ่าน/ศึกษา source code ของโปรแกรมกลุ่มประกันกลุ่มโดยไม่ต้องการ clone ลงเครื่อง.'
created_at: 2026-09-01T00:00:00+07:00
argument-hint: "[ชื่อ App หรือบางส่วนของชื่อ]"
---

# /git-learn-grouplife — อ่าน source code ของ App เดียวจาก Gitblit แบบไม่ clone

Sibling ของ [[reference-gitclone-grouplife-skill]] — หา App ตัวเดียวกันจากชีตติดตาม
เดียวกันทุกประการ (repo + Sub Folder) ต่างกันที่ skill นี้**ไม่ clone**อะไรลงเครื่อง
เลย แต่อ่าน source ตรง ๆ ผ่าน Gitblit web UI (endpoint `tree/` สำหรับ list โฟลเดอร์
และ `raw/` สำหรับดึงเนื้อไฟล์ดิบ) — เหมาะกับกรณีแค่อยากอ่าน/ทำความเข้าใจโค้ด ไม่ได้
จะแก้ไขหรือ push อะไรกลับ (ถ้าต้องแก้ไขจริงต้องใช้ `/git-clone-grouplife` แทน เพราะ
ต้องมี `.git` ในเครื่องถึงจะ commit/push ได้)

skill นี้เป็น read-only ทั้งต่อชีตติดตามและต่อ repo บน Gitblit — ไม่เคยเขียนอะไรกลับ
ทั้งสองที่

## Step 1 — ถามชื่อ App แล้วหา repo/path จากชีต

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife/scripts/search_app.py "<คำค้น>"
```
- **0 ผลลัพธ์**: แจ้งผู้ใช้ไม่เจอ ถามชื่ออื่น หรือแนะนำให้เช็คว่า App นี้เคยถูก
  บันทึกไว้ในชีตหรือยัง (ถ้ายังไม่มี ต้องไปใช้ `/git-clone-grouplife-update` ก่อน
  ไม่ใช่หน้าที่ของ skill นี้ที่จะไป scan Gitblit เอง)
- **1 ผลลัพธ์**: ยืนยันชื่อเต็มกับผู้ใช้สั้น ๆ ก่อนไป Step 2
- **มากกว่า 1 ผลลัพธ์**: โชว์ชื่อ App เต็มทั้งหมด (พร้อม Group/repo ที่สังกัด เผื่อชื่อ
  ซ้ำกันคนละ repo) ให้ผู้ใช้เลือกเจาะจง 1 ตัว — **ห้ามเดาว่าอันไหนที่ต้องการ**

**ระวัง**: field `repo` ในผลลัพธ์เป็นสตริงเต็มแบบ `git clone
ssh://<gitblit_user>@10.100.2.187:29418/delphi/<repo>.git` (ค่าเดียวกับที่
`/git-clone-grouplife` ใช้ต่อ SSH) — แต่ `browse_repo.py` (Step 2/3 ด้านล่าง)
ต้องการแค่**ชื่อ repo สั้น ๆ** (`<repo>` ในแพทเทิร์นข้างบน เช่น `apprunjobs`,
`groupwork`) เพราะมันต่อ URL ของ Gitblit web UI เอง ไม่ผ่าน SSH เลย — ต้องตัดเอา
เฉพาะ segment ระหว่าง `/delphi/` กับ `.git` ออกมาก่อนใช้เสมอ ห้ามส่งสตริง
`git clone ssh://...` ทั้งก้อนเข้า `browse_repo.py` ตรง ๆ

## Step 2 — สำรวจโครงสร้างไฟล์ก่อนอ่าน

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife/scripts/browse_repo.py tree "<repo>" "<sub_folder>"
```
- คืน `files` เป็น list path เต็มของทุกไฟล์ใต้ `sub_folder` (ค่า Sub Folder จากชีต,
  ลงท้าย `/trunk`) แบบ recursive, `requests_used`/`truncated` บอกว่าไล่ทันครบไหม —
  ถ้า `truncated: true` (ชนเพดาน `--max-requests` default 500) ให้ไล่ดูทีละโฟลเดอร์
  ย่อยด้วย `browse_repo.py list "<repo>" "<path ย่อย>"` แทน อย่าเพิ่ม
  `--max-requests` มั่ว ๆ จนกลายเป็นแครอลทั้ง repo
- ใช้ `browse_repo.py list "<repo>" "<path>"` (ไม่ระบุ path = root ของ repo) เพื่อดู
  ทีละชั้นเวลาต้องการยืนยันด้วยตาหรือ path ลึกมาก

## Step 3 — อ่านไฟล์ที่ต้องการ

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife/scripts/browse_repo.py read "<repo>" "<file path เต็มจาก tree/list>"
```
- คืน `content` เป็น text (decode utf-8 ก่อน แล้ว fallback cp874 แล้ว latin-1 แบบ
  replace ถ้าจำเป็น — โค้ด Delphi 7 เก่ามักเป็น cp874 มากกว่า utf-8) พร้อม `size`/
  `encoding` ให้เช็ค
- ไฟล์ที่เป็น binary จริง (มี NUL byte ใน 8KB แรก เช่น `.res`, `.dcu`, `.suo`, ไอคอน)
  จะได้ `{"error": "binary file..."}` แทน — **ข้ามไฟล์เหล่านี้ไปเลย ไม่ต้องพยายาม
  decode เอง** ไม่มีประโยชน์กับการอ่านโค้ด
- ไฟล์ที่ใหญ่เกิน 2MB (`--max-bytes` default) จะได้ error บอกขนาดแทนเนื้อหา — ถ้า
  จำเป็นจริง ๆ ค่อยเพิ่ม `--max-bytes` เอง แต่ปกติไฟล์ source Delphi ไม่ควรใหญ่ขนาดนี้
- อ่านทีละไฟล์ตามที่ต้องการเข้าใจ — skill นี้ไม่ได้ทำให้ grep ข้ามทั้ง App ได้ในทีเดียว
  เหมือนมี local clone ต้องไล่เปิดเองทีละไฟล์ตาม `tree`/`list` ผลลัพธ์

## ข้อจำกัดที่ต้องบอกผู้ใช้ล่วงหน้า (ถ้าเกี่ยวข้อง)

- **แก้ไข/commit/push ไม่ได้จาก skill นี้** — เป็น read-only เพียว ถ้าผู้ใช้บอกว่า
  จะแก้โค้ดหลังอ่านเสร็จ ให้แนะนำ `/git-clone-grouplife` แทนตั้งแต่ต้น
- **ไม่มี local grep ข้ามทั้ง App ในทีเดียว** — ถ้าผู้ใช้ต้องการค้นหา keyword ข้ามหลาย
  ไฟล์/ทั้ง App เป็นจำนวนมาก การ `tree` แล้วอ่านทีละไฟล์ผ่าน web อาจช้ากว่า clone จริง
  มาก ให้แจ้ง trade-off นี้และเสนอ `/git-clone-grouplife` เป็นทางเลือกถ้างานลักษณะนี้
- Auth ใช้ session login เว็บเดียวกับ `/git-clone-grouplife-update`
  (`~/.config/gitblit-web/credentials.json`) — ถ้าไฟล์นี้ไม่มี (เครื่องใหม่) ให้ขอ
  username/password จากผู้ใช้แล้วสร้างไฟล์รูปแบบ `{"base_url":
  "https://10.100.2.187:8443/", "username": "...", "password": "..."}` เอง (ดู
  [[reference-gitclone-grouplife-update-skill]] — credential เดียวกับ
  [[reference-gitblit-credentials]], password rotate รายเดือน)
