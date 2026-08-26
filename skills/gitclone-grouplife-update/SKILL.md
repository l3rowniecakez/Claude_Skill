---
installer: create-shortcut
name: gitclone-grouplife-update
description: 'ค้นหา App (โฟลเดอร์ที่มี "trunk" อยู่ข้างใน) ใน repo กลุ่ม delphi บน Gitblit แล้วเพิ่มแถวใหม่ในชีตติดตาม path สำหรับ git clone รายแอพ (spreadsheet 18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0). Use when user says "/gitclone-grouplife-update", มี app ใหม่ต้องการ path เต็มสำหรับ sparse-checkout, หรือถามหา trunk path ของโปรแกรมใน repo กลุ่ม delphi.'
created_at: 2026-08-26T00:00:00+07:00
argument-hint: "[repo name ใน delphi group] [app name หรือคำค้น]"
---

# /gitclone-grouplife-update — Delphi Group App Path Finder + Sheet Recorder

Repo แต่ละตัวใน Gitblit กลุ่ม `delphi` เป็นการ import โครงสร้าง SVN เก่าเข้ามาทั้งยวง
เก็บหลาย ๆ โปรแกรม (App) ไว้ในที่เดียว — โครงสร้างเดิมคือ `<App>/trunk` (บาง repo มี
ชั้น category คั่นกลางด้วย เช่น `AccountSystem/GLPRO001_P/trunk`) เป้าหมายของ skill นี้
คือหา path เต็มไปจนถึงโฟลเดอร์ `trunk` ของ App ที่ต้องการ แล้วบันทึกไว้ในชีตกลาง
เพื่อให้ทำ `git clone` + sparse-checkout เฉพาะ App นั้นได้ ไม่ต้องโคลนทั้ง repo

**กฎเหล็ก**: skill นี้เขียนชีตแบบ **upsert เท่านั้น** — App ที่มีอยู่แล้ว (match ด้วย
AppName หรือ Sub Folder แบบ case-insensitive) จะถูก **update ทับแถวเดิม** (ไม่ insert
แถวใหม่ซ้ำ), App ที่ยังไม่มีจะถูก **insert** เป็นแถวใหม่ — **ห้าม sort/filter/ลบแถว
เดิมเด็ดขาด** แม้แต่แถว "Example" (row 2) การ update เป็นแค่เขียนทับ 5 คอลัมน์ของ
row นั้นเท่านั้น ไม่แตะ row อื่น — เหมือนกับ [[feedback-no-adhoc-queries]] philosophy
ของ `/datadic-grouplife-update` (ที่ต่างกันคือฝั่งนั้นมี separate find→create/update
step ให้ผู้ใช้ยืนยัน diff ก่อนเขียน ส่วน skill นี้ upsert อัตโนมัติเพราะข้อมูลมีแค่
4 field ธรรมดา ไม่มี field ที่มนุษย์กรอกเพิ่มแบบ Data Dictionary)

## ภาพรวม infra ที่ใช้

- **Gitblit web UI** ที่ `https://10.100.2.187:8443/` — repo กลุ่ม `delphi` **ต้อง
  login ถึงจะเห็น** (anonymous เห็นแค่กลุ่ม `forks`) — session login ทำผ่าน
  `scripts/gitblit_client.py` โดยอ่าน credential จาก
  `~/.config/gitblit-web/credentials.json` (เก็บนอกโฟลเดอร์ skill เพราะโฟลเดอร์นี้
  sync ขึ้น public GitHub repo ตาม [[reference-claude-skill-github-repo]] — ถ้าไฟล์
  credential นี้หายไปในเครื่องใหม่ ให้ขอ username/password จากผู้ใช้แล้วสร้างไฟล์
  รูปแบบ `{"base_url": "https://10.100.2.187:8443/", "username": "...", "password":
  "..."}` เอง ไม่ต้องถามซ้ำถ้ามีอยู่แล้ว — credential เดียวกับที่ใช้ SSH push/pull
  ใน [[reference-gitblit-credentials]] (password rotate รายเดือน ถ้า login fail
  ให้ขอรหัสใหม่จากผู้ใช้แล้วอัพเดทไฟล์นี้)
- **Python venv**: ทุก script รันด้วย
  `~/.config/redmine-summary-to-email/venv/bin/python3` (มี `requests` ใช้งานได้ —
  `requests` ใน system python3 ของเครื่องนี้เสีย/stub เปล่า อย่าใช้ system python3)
- **Google Sheet**: `18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0` — ชื่อ tab เคยถูก
  เปลี่ยนจาก "Sheet1" เป็น "Main" มาแล้วครั้งหนึ่งระหว่างพัฒนา skill นี้ —
  `scripts/sheet_ops.py` resolve ชื่อ tab จาก sheet ตัวแรกของ spreadsheet แบบสด
  ทุกครั้ง ไม่ hardcode ชื่อ ไม่ต้องกังวลเรื่องนี้

## Step 1 — รับ input

ต้องรู้ 2 อย่างก่อนเริ่ม (ถามผู้ใช้ถ้าขาด อย่าเดา):
1. **Repo name** ใน delphi group — เช็ค list ปัจจุบันได้ด้วย:
   ```bash
   ~/.config/redmine-summary-to-email/venv/bin/python3 \
     ~/.claude/skills/gitclone-grouplife-update/scripts/scan_repo.py list-repos
   ```
   (ปัจจุบัน 6 ตัว: `apprunjobs`, `claim-work-legacy`, `claim-work`, `faxclaim-prog`,
   `groupwork-system-2016`, `groupwork` — ถ้ามี repo ใหม่ในกลุ่มจะโผล่ในนี้อัตโนมัติ)
2. **ชื่อ App หรือคำค้น** — ชื่อโฟลเดอร์ที่อยู่ **ก่อนหน้า** `trunk` เป๊ะ ๆ (ผู้ใช้ย้ำ
   จุดนี้ไว้: "ชื่อ App จะอยู่ก่อนถึง Folder Trunk") ไม่ใช่ชื่อ category ที่ครอบอยู่
   ข้างบน (เช่น App คือ `GLPRO001_P` ไม่ใช่ `AccountSystem` ที่เป็นแค่ folder จัด
   หมวดหมู่)
   - ถ้าผู้ใช้รู้ category/parent folder คร่าว ๆ ด้วย (เช่นเห็นจากภาพหน้าจอ) ให้ขอมา
     เป็น `--start` hint — ช่วยลดจำนวน request ไปเยอะมากสำหรับ repo ใหญ่ (ดู Step 2)

## โหมด Bulk — scan ทั้ง repo ทีเดียว (ใช้ครั้งแรกไปแล้ว 2026-08-26)

ถ้าผู้ใช้ขอ "auto scan" ทั้ง repo (ไม่ระบุชื่อ App เจาะจง) ให้ใช้โหมดนี้แทน Step
1-4 ด้านล่าง — **ต้อง confirm กับผู้ใช้ก่อนเขียนจริงเสมอ** เพราะเขียนทีเดียวเป็น
ร้อย ๆ แถวและ `sheet_ops.py` ไม่มีคำสั่งลบ (ครั้งแรกที่ทำ 2026-08-26 เจอ 833 App
จาก 6 repo, เขียนสำเร็จ 827 แถว ซ้ำชื่อ AppName ในตัวเอง 7 ตัว — ดู
[[project_gitclone_grouplife_bulk_populate_2026_08_26]]):

1. Scan ทีละ repo (เร็ว เพราะ Gitblit auto-collapse ให้เยอะแล้ว — ทั้ง 6 repo รวม
   ใช้เวลาไม่กี่นาที ไม่ต้องรัน background ก็ได้ถ้าทำทีละ repo):
   ```bash
   ~/.config/redmine-summary-to-email/venv/bin/python3 \
     ~/.claude/skills/gitclone-grouplife-update/scripts/scan_repo.py scan-all "<repo>" \
     > /tmp/.../scan/<repo>.json
   ```
   เช็ค `truncated` ในผลลัพธ์เสมอ — ถ้า `true` แปลว่าชน `--max-requests` (default
   20000, ปกติไม่มีทางชนเว้นแต่ repo ใหญ่ผิดปกติ) ให้รันซ้ำพร้อมเพิ่มค่านี้
2. **โชว์สรุปจำนวน App ต่อ repo ให้ผู้ใช้ดูก่อนเขียนจริงเสมอ** แล้วขอ confirm — ห้าม
   เขียนเข้าชีตทันทีโดยไม่ถาม แม้ผู้ใช้จะสั่ง "auto scan" มาแล้วก็ตาม เพราะขนาด
   จริงมักเกินคาดมาก (repo ที่มี category folder ซ้อนลึกอาจมี App เป็นร้อยตัว)
3. เมื่อ confirm แล้ว รวมผลทุก repo เป็น list เดียว (`Group`=ชื่อ repo, `AppName`/
   `Sub Folder` จากผลลัพธ์ scan, `repo`=`git clone
   ssh://<gitblit_user>@10.100.2.187:29418/delphi/<repo>.git` — **username ต้องเป็น
   placeholder `<gitblit_user>` ตัวอักษรเป๊ะ ๆ ห้าม fix เป็น username ของใครคนใด
   คนหนึ่ง เด็ดขาด** เพราะชีตนี้จะถูก skill อื่นในอนาคตดึงไปใช้
   clone จริง คนละคนกับที่ทำ skill นี้ก็ต้องแทนที่ placeholder ด้วย username ของ
   ตัวเองได้) แล้วเขียนทีเดียวด้วย:
   ```bash
   echo '[{...}, {...}, ...]' | ~/.config/redmine-summary-to-email/venv/bin/python3 \
     ~/.claude/skills/gitclone-grouplife-update/scripts/sheet_ops.py upsert-batch
   ```
   (เขียน 1 ครั้งต่อ 1 batch — เร็วกว่าและปลอดภัยกว่าเรียก `upsert` ทีละแถวเป็น
   ร้อยครั้ง คำนวณ match/row number จากสถานะชีตครั้งเดียวตอนเริ่ม จึงห้ามรันซ้อนกัน
   หลาย batch พร้อมกัน) รายงาน `inserted_count`/`updated_count`/`inserted`/`updated`
   ให้ผู้ใช้ทราบ — **ตรวจ `updated` list ให้ดี**: ถ้า `previous.Sub Folder` กับ
   `Sub Folder` ใหม่ต่างกันแบบไม่ใช่แค่ path เดิมย้ายที่ (เช่นคนละ category folder
   คนละความหมายกันเลย) ให้เตือนผู้ใช้ไว้ เพราะอาจเป็นกรณี App คนละตัวชื่อชนกัน
   (พบ 7 เคสแบบนี้ตอน bulk populate ครั้งแรก 2026-08-26 — ตอนนั้นถูก skip ไปเพราะ
   ยังไม่มี upsert ตอนนี้จะกลายเป็น "updated" แทน ต้องเช็คด้วยตาว่าเขียนทับถูกต้อง
   หรือควรเก็บทั้ง 2 แถวแยกกัน)

## โหมดทีละ App (ใช้ตอนมี App ใหม่มาเพิ่มทีหลัง)

### Step 2 — หา trunk path ด้วย `scan_repo.py find`

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/gitclone-grouplife-update/scripts/scan_repo.py find \
  "<repo>" "<คำค้น>" [--start "<parent folder path ถ้ารู้>"] [--max-requests N]
```

- ค้นหาแบบ breadth-first ใน tree ของ repo หาโฟลเดอร์ที่มี segment ชื่อ `trunk` แล้ว
  เช็คว่าชื่อ App (segment ก่อนหน้า `trunk`) มีคำค้นเป็น substring หรือไม่
  (case-insensitive) — เจอ exact match ปุ๊บหยุดค้นทันที ไม่ต้องไล่ทั้ง repo
- Gitblit auto-collapse โฟลเดอร์ลูกเดี่ยวเข้าด้วยกัน (เช่น
  `GroupLifeInsuranceSystem_Benefits/trunk` โชว์เป็นแถวเดียว) และบางทีก็ collapse
  เลยจุด `trunk` ไปอีก (เช่น `.../trunk/Claim_Prog`) — script ตัด path ให้จบที่
  `trunk` เป๊ะเสมอ ไม่ต้องกังวลเรื่องนี้
- **repo บางตัวใหญ่มาก** (`claim-work-legacy`, `claim-work`, `faxclaim-prog`,
  `groupwork` มี category folder ที่มี App ข้างในเป็นสิบ-เป็นร้อยตัว) ถ้าคำค้นไม่
  ตรงกับชื่อ folder ระดับบนเลย จะต้องไล่เปิดทุก folder ทีละชั้น — ถ้า `truncated:
  true` กลับมา (ชนเพดาน `--max-requests` ค่า default 150) ให้ขอ parent
  folder/category เพิ่มจากผู้ใช้แล้วใส่ `--start` ให้แคบลง อย่าเพิ่ม
  `--max-requests` มั่ว ๆ จนกลายเป็นแครอลทั้ง repo

ผลลัพธ์ `matches` อาจมีได้หลายรายการ (เช่นค้น "Operation" เจอทั้ง
`GroupLifeInsuranceSystem_Operation` และ `GroupLifeInsuranceSystem_Operation_GrayColor`)
— **ถ้ามีมากกว่า 1 match ให้โชว์ให้ผู้ใช้เลือกก่อนเสมอ ห้ามเดาว่าอันไหนที่ต้องการ**
ถ้าไม่เจอเลยและ `truncated: false` (ไล่จนสุดจริง ๆ ไม่ใช่ชนเพดาน) แปลว่าไม่มี App
ชื่อนี้ใน repo/parent folder นั้นจริง ๆ — แจ้งผู้ใช้ ไม่ต้องเดาไปหา repo อื่นเอง
(อาจถามว่าอยู่ repo ไหน)

ถ้าต้องการไล่ดูเองทีละชั้น (กรณีคำค้นกำกวมหรืออยากยืนยันด้วยตา) ใช้:
```bash
scan_repo.py list "<repo>" ["<path>"]
```
ได้ list ของลูกโฟลเดอร์/ไฟล์ชั้นเดียว ตรงกับที่เห็นตอน browse เว็บด้วยตาเอง

## Step 3 — เช็คสถานะในชีตก่อนเขียน (เพื่อรู้ล่วงหน้าว่าจะ insert หรือ update)

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/gitclone-grouplife-update/scripts/sheet_ops.py find "<AppName>"
```

ถ้า `found: true` แปลว่ามีอยู่แล้วที่ row นั้น — Step 4 จะ **update ทับแถวนี้**
(ไม่ใช่สร้างแถวใหม่) แจ้งผู้ใช้ล่วงหน้าว่ากำลังจะอัพเดท row ไหนจาก path เดิมอะไร
เป็น path ใหม่อะไร ถ้า path เดิมกับใหม่ต่างกันแบบดูไม่เหมือนแค่ "ย้ายที่" (เช่น
คนละ repo กันเลย) ให้ถามผู้ใช้ยืนยันก่อนว่าตั้งใจเขียนทับจริง เพราะอาจเป็น App
คนละตัวที่ชื่อชนกัน (ดู Step 4 หมายเหตุ) ถ้า `found: false` แปลว่าจะ insert แถวใหม่

## Step 4 — Upsert (insert ถ้ายังไม่มี / update ถ้ามีแล้ว)

Repo URL pattern คงที่เสมอ: `ssh://<gitblit_user>@10.100.2.187:29418/delphi/<repo>.git`
(host+port+group prefix เดียวกับ [[reference-gitblit-credentials]]) — **เขียน
`<gitblit_user>` เป็น literal placeholder ตรง ๆ ห้าม fix เป็น username จริงของใคร
คนใดคนหนึ่งเด็ดขาด** (ดูหมายเหตุด้านบนในโหมด Bulk — คอลัมน์นี้ถูกออกแบบให้ skill
อื่นในอนาคตดึงไปใช้ clone จริงโดยแทน placeholder ด้วย username ของผู้ใช้ตอนนั้นเอง)

```bash
echo '{
  "Group": "<repo>",
  "AppName": "<App Name จาก match>",
  "repo": "git clone ssh://<gitblit_user>@10.100.2.187:29418/delphi/<repo>.git",
  "Sub Folder": "<path จาก match, ลงท้าย /trunk>"
}' | ~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/gitclone-grouplife-update/scripts/sheet_ops.py upsert
```

- Match ด้วย AppName ก่อน ถ้าไม่ตรงค่อย fallback ไป match ด้วย Sub Folder
  (case-insensitive ทั้งคู่) — เจอ match ไหนก็ตาม **update 5 คอลัมน์ของแถวนั้นทับ
  เลย** ไม่เจอเลยค่อย insert แถวใหม่ (คำนวณแถวว่างถัดไปเอง ไม่ใช้ Sheets
  auto-detect) ผลลัพธ์บอก `"action": "updated"` หรือ `"inserted"` พร้อม
  `row_number`, ถ้า updated จะมี `"previous"` แนบมาด้วยให้เทียบ
- ถ้าคืน `{"error": ...}` ให้หยุดและแจ้งผู้ใช้ทันที ห้าม retry เดา row เอง
- คอลัมน์ `Full Path` (E) เป็นสูตรก็อปแบบเดียวกับแถว Example (`=C{row} & "/" &
  D{row}`) เขียนเป็น formula จริง ไม่ใช่ข้อความ
- **ระวังเคส AppName ชนกันเองในคนละ Sub Folder** (โปรแกรมชื่อเดียวกัน อยู่คนละ
  category folder ในคนละ repo หรือแม้แต่ repo เดียวกัน) — upsert จะ match ด้วย
  AppName ก่อนแล้ว "update" ทับ path เดิมด้วย path ใหม่ทันที ถ้า Step 3 เผยว่า
  path เดิม/ใหม่ต่างกันมาก (ไม่ใช่แค่ rename เล็กน้อย) ให้ถามผู้ใช้ก่อนว่าต้องการ
  เขียนทับจริงหรือเก็บทั้งคู่ไว้แยกกัน (ถ้าอยากเก็บแยก ต้องตั้งชื่อ AppName ให้ไม่
  ชนกัน เช่นเติม suffix ชื่อ category — script ไม่ auto-disambiguate ให้)

## Step 5 — สรุปผล

บอกผู้ใช้ว่า row เท่าไหร่ App อะไร path อะไร พร้อมคำสั่ง `git clone` ที่ก็อปวางได้เลย
(sparse-checkout เฉพาะ Sub Folder นั้นถ้าผู้ใช้ต้องการ ดูตัวอย่างที่
[[reference-groupwork-system-2016-repo]] เคยทำไว้)

## หลายคำขอพร้อมกัน

ถ้าผู้ใช้ขอหลาย App พร้อมกัน ให้ทำทีละตัวตามลำดับ (sequential) เหมือน
`/datadic-grouplife-update` — `sheet_ops.py append` คำนวณแถวถัดไปจากสถานะปัจจุบัน
ของชีต ถ้ารันพร้อมกันจะชนกันคำนวณแถวผิด/เขียนทับกันได้
