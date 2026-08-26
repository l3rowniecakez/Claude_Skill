---
installer: create-shortcut
name: gitclone-grouplife
description: 'Clone source code เฉพาะ App เดียว (ไม่ใช่ทั้ง repo) จาก Gitblit กลุ่ม delphi ลงเครื่อง โดยดูข้อมูล repo/path จากชีตติดตาม (spreadsheet 18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0). Use when user says "/gitclone-grouplife", ต้องการ clone/ดึง source code ของโปรแกรมกลุ่มประกันกลุ่มลงเครื่อง.'
created_at: 2026-08-26T00:00:00+07:00
argument-hint: "[ชื่อ App หรือบางส่วนของชื่อ] [folder ปลายทาง]"
---

# /gitclone-grouplife — Clone เฉพาะ App เดียวจาก Gitblit

Sibling ของ [[reference-gitclone-grouplife-update-skill]] — skill นั้นหา path แล้ว
บันทึกลงชีต ส่วน skill นี้**อ่าน**ชีตนั้นเพื่อเอา path ไป `git clone` ลงเครื่องจริง
skill นี้เป็น read-only ต่อชีต ไม่เคยเขียนอะไรกลับเข้าไป

**กฎเหล็ก**: **ห้าม sync/checkout ทั้ง repo ลงเครื่องเด็ดขาด** ต้องใช้
`git sparse-checkout` (cone mode) จำกัด working tree ให้เหลือแค่โฟลเดอร์ `trunk`
ของ App ที่ระบุเท่านั้น — วิธีการอยู่ใน `scripts/clone_app.py` แล้ว ห้ามรัน
`git clone` ธรรมดาโดยไม่ผ่าน script นี้เด็ดขาด

**Path ที่ได้ยังคงซ้อนอยู่ที่ `dest_dir/<Sub Folder>`** (เช่น
`dest_dir\Cashier_Program\CHPro002_P\trunk\...`) ไม่ flatten ขึ้นมาที่ root —
เคยลอง flatten (ย้ายไฟล์ขึ้น root + ลบ `.git`) ไปแล้วเมื่อ 2026-08-26 ตามคำขอแรก
ของผู้ใช้ แต่ผู้ใช้กลับมาตัดสินใจใหม่หลังรู้ว่า **ไม่มี `.git` แปลว่า push
ไม่ได้** — จึงยืนยันให้เก็บ `.git` และ path ซ้อนไว้แทน (ทางเลือก A) **ห้าม
flatten/ลบ `.git` อีกเด็ดขาด แม้ผู้ใช้จะบ่นว่า path ลึกอีกครั้งก็ตาม** ให้อธิบาย
trade-off นี้ซ้ำแทนการแก้ script เงียบ ๆ

## Step 1 — ถามชื่อ App

รับคำค้น (พิมพ์แค่บางส่วนได้) แล้วค้นหา:
```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/gitclone-grouplife/scripts/search_app.py "<คำค้น>"
```
- **0 ผลลัพธ์**: แจ้งผู้ใช้ไม่เจอ ถามชื่ออื่น หรือแนะนำให้เช็คว่า App นี้เคยถูก
  บันทึกไว้ในชีตหรือยัง (ถ้ายังไม่มี ต้องไปใช้ `/gitclone-grouplife-update` ก่อน
  ไม่ใช่หน้าที่ของ skill นี้ที่จะไป scan Gitblit เอง)
- **1 ผลลัพธ์**: ยืนยันชื่อเต็มกับผู้ใช้สั้น ๆ ก่อนไป Step 2
- **มากกว่า 1 ผลลัพธ์**: โชว์ชื่อ App เต็มทั้งหมด (พร้อม Group/repo ที่สังกัด เผื่อชื่อ
  ซ้ำกันคนละ repo) ให้ผู้ใช้เลือกเจาะจง 1 ตัว — **ห้ามเดาว่าอันไหนที่ต้องการ**

## Step 2 — ถาม Folder ปลายทาง

ถามผู้ใช้ว่าจะ clone ไปไว้ที่ไหน (path เต็ม) — ต้องเป็น folder ที่ **ยังไม่มีอยู่
หรือว่างเปล่า** (`clone_app.py` จะปฏิเสธเองถ้า path มีอยู่แล้วและไม่ว่าง — ห้ามลบ
ของเดิมทิ้งให้เอง ถ้าเจอ error นี้ให้ถามผู้ใช้ว่าจะเปลี่ยน path หรือจัดการโฟลเดอร์
เดิมเองก่อน)

## Step 3 — Clone

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/gitclone-grouplife/scripts/clone_app.py \
  "<repo field จาก search_app.py>" "<sub_folder จาก search_app.py>" "<dest_dir>"
```

- `clone_app.py` ทำ `git clone --no-checkout --filter=blob:none` แล้วตามด้วย
  `git sparse-checkout init --cone` + `git sparse-checkout set "<sub_folder>"` +
  `git checkout <default branch>` — จบแล้ว working tree จะมีแค่ path ของ App นั้น
  เท่านั้น (เช็คได้ด้วย `git sparse-checkout list` ใน dest_dir) `dest_dir` ยังเป็น
  git repo ปกติ ใช้ `git add`/`commit`/`push` จาก dest_dir ได้เลย
- Auth SSH ใช้ credential จาก `~/.config/gitblit-web/credentials.json` (บัญชี
  เดียวกับที่ `/gitclone-grouplife-update` ใช้ login เว็บ) แทนที่ placeholder
  `<gitblit_user>` ใน "repo" field ด้วย username จริงจากไฟล์นี้อัตโนมัติ — ถ้าไฟล์
  นี้ไม่มี (เครื่องใหม่) ให้ขอ username/password จากผู้ใช้แล้วสร้างไฟล์รูปแบบ
  `{"base_url": "https://10.100.2.187:8443/", "username": "...", "password":
  "..."}` เอง (ดู [[reference-gitclone-grouplife-update-skill]] — credential เดียวกับ
  [[reference-gitblit-credentials]], password rotate รายเดือน)
- ถ้าคืน `{"error": ...}` ให้หยุดและแจ้งผู้ใช้ทันที (script ลบ dest_dir
  ที่สร้างค้างไว้ให้เองถ้า clone ล้มเหลวกลางคัน เพราะเป็นแค่ผลลัพธ์ที่ทำไม่สำเร็จ
  ไม่ใช่งานของผู้ใช้ — แต่ห้ามลบ dest_dir เองถ้า error เป็น "already exists and is
  not empty" เพราะนั่นคือของเดิมที่มีอยู่ก่อนแล้ว ไม่ใช่ของที่ script สร้าง)

## Step 4 — สรุปผล

บอกผู้ใช้ว่า row เท่าไหร่ App อะไร path อะไร (`checked_out_path` จากผลลัพธ์) และ
branch ที่ checkout ไว้ พร้อมเตือนสั้น ๆ ว่า working tree นี้จำกัดแค่ App เดียว
(`git sparse-checkout list`) ถ้าต้องการเพิ่ม App อื่นในเครื่องเดียวกันทีหลัง ต้องเรียก
skill นี้ใหม่คนละ dest_dir หรือใช้ `git sparse-checkout add "<sub_folder อื่น>"` เองใน
dest_dir เดิม (skill นี้ไม่รองรับ multi-app ในโฟลเดอร์เดียวอัตโนมัติ) — `dest_dir`
ยังเป็น git repo ปกติ แก้โค้ดแล้ว `git add`/`commit`/`push` ได้จากตรงนั้นเลย
