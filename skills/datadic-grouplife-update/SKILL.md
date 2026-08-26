---
installer: create-shortcut
name: datadic-grouplife-update
description: 'สร้างใหม่/อัพเดท Data Dictionary ของระบบประกันกลุ่ม/เดี่ยว (Data One / OceanLife / OGL) ให้ตรงกับโครงสร้างจริงใน DB — เพิ่มแถวในหน้าแรกของ Google Sheet และสร้าง/แก้ไข Link Sheet รายละเอียดคอลัมน์ของ table นั้น. Use when user says "/datadic-grouplife-update", ต้องการ create/update Data Dictionary ของ table ใหม่หรือ table ที่เปลี่ยนโครงสร้าง.'
created_at: 2026-08-26T00:00:00+07:00
argument-hint: "[ip server DB] [db: dataone|oceanlife|ogl] [table name หนึ่งหรือหลายชื่อ คั่นด้วย comma/space]"
---

# /datadic-grouplife-update — Group/Individual Life Data Dictionary Create/Update

สร้างแถวใหม่ + Link Sheet ใหม่ในหน้าแรกของ Data Dictionary (spreadsheet ID
`1qHeg391cRNrGA1HC3cWxsv9HcJZS0POuI94uaR27cqU`) เมื่อ table ยังไม่มีในดัชนี
หรืออัพเดท Link Sheet ของ table ที่มีอยู่แล้วให้ตรงกับโครงสร้างจริงใน DB
(query สด ผ่าน `db_columns.py`, ไม่เดา ไม่อ่านจาก doc เก่า)

ใช้คู่กับ (แต่แยกจาก) `/datadic-grouplife` ซึ่งเป็น read-only viewer — skill
นี้เป็นตัวเดียวที่เขียนลง Google Sheet ได้

## กฎเหล็ก — ต้องยึดตลอดทั้ง flow

1. **ห้ามยุ่ง แก้ไข อัพเดท หรือลบแถว/ไฟล์ที่ไม่เกี่ยวข้องกับ Table ที่ได้รับ
   คำสั่งโดยเด็ดขาด** — ทุกการเขียนต้องเจาะจงแค่แถวเดียว/ไฟล์เดียวของ table
   นั้น ห้าม sort, ห้าม filter ทั้งชีต, ห้ามลบแถวใด ๆ แม้แต่ของ table เดียวกัน
   (มีแต่ appen/update เท่านั้น ไม่มี delete)
2. **ตรวจดูชื่อ table ก่อนเสมอ** (`dic_index.py find` แบบ exact match) — ถ้า
   ไม่มีค่อยสร้างใหม่ ถ้ามีอยู่แล้วให้อัพเดท ห้ามสร้างซ้ำโดยไม่เช็คก่อน
3. **หลาย table พร้อมกันต้องทำทีละตัวตามลำดับ (sequential) ห้าม parallel** —
   `dic_index.py append` คำนวณแถวถัดไปจากสถานะปัจจุบันของ sheet ถ้ารันพร้อม
   กันหลาย table ในดัชนีเดียวกันจะชนกันคำนวณแถวผิด/เขียนทับกันได้ ทำเสร็จ
   ทีละ table ให้ครบ (append/update index สำเร็จแล้ว) ก่อนเริ่ม table ถัดไป
4. Scripts ในนี้ทุกตัวมี safety check ในตัว (verify แถวก่อนเขียน, เขียนแค่
   cell ที่ระบุ) แต่ก็ยังต้องอ่านผลลัพธ์ทุกครั้งและถ้า script คืน `{"error":
   ...}` ให้หยุดและแจ้งผู้ใช้ทันที ห้าม retry มั่ว ๆ

## Step 0 — เช็ค OAuth scope (ทำครั้งแรกที่ใช้ก่อน create table ใหม่)

`create` ใช้ Drive API `files.copy` เพื่อสร้างสเปรดชีตใหม่ต่อ table ซึ่ง
ต้องการ scope **`https://www.googleapis.com/auth/drive`** (เขียนเต็ม) —
token OAuth ที่ใช้กับ Google Sheets/Drive ของคุณอาจตั้งไว้แค่
`drive.readonly` เดิม (พอสำหรับ read-only ของ `/datadic-grouplife` แต่ไม่พอ
สำหรับ `create` ของ skill นี้)

ก่อนรัน `dic_table.py create` ครั้งแรก ให้เช็ค scope ของ token ที่ใช้อยู่
(path ขึ้นกับวิธีตั้งค่า Google OAuth ของคุณเอง เช่นถ้าเก็บไว้ที่
`~/.config/claude-google-access/token.json`):
```bash
python3 -c "import json; print(json.load(open('<path ไป token.json ของคุณ>'))['scopes'])"
```
ถ้าไม่มี `https://www.googleapis.com/auth/drive` เต็ม (มีแค่ `.readonly`) ให้
แจ้งผู้ใช้ว่าต้อง **ขยาย scope ก่อน** (นี่คือการเปลี่ยนสิทธิ์เข้าถึง Google
Drive ทั้งบัญชี ต้องขอความยินยอมจากผู้ใช้ก่อนเสมอ ห้ามทำเองเงียบ ๆ):
1. แก้ scope list ในสคริปต์ authorize ของคุณให้มี
   `https://www.googleapis.com/auth/drive` แทน `drive.readonly`
2. ลบ token เก่าทิ้ง
3. ให้ผู้ใช้รันสคริปต์ authorize เองใหม่ (ต้องเปิด browser ยืนยัน consent)

ถ้า flow ที่กำลังทำเป็น **update** table ที่มีอยู่แล้ว (ไม่ได้ create ใหม่)
ไม่จำเป็นต้องขยาย scope เพราะ `dic_table.py update`/`dic_index.py
update-row` ใช้แค่ Sheets API (`spreadsheets` scope ที่มีอยู่แล้วพอ) — เช็ค
scope เฉพาะตอนจะต้อง `create` เท่านั้น

## Step 1 — รับ Input ให้ครบ 3 อย่างเสมอ

ต้องมีครบทั้ง 3 อย่างก่อนเริ่มทำงาน ถ้าขาดอย่างใดอย่างหนึ่งให้ถามผู้ใช้ก่อน
เสมอ (ห้ามเดา):
1. **IP server DB** — ต้องเป็น IP ของ SQL Server ที่มี credential ตั้งไว้แล้ว
   ใน `scripts/db_columns.py` (`DB_CREDENTIALS` dict) หรือ environment
   variable `DD_DB_USER`/`DD_DB_PASSWORD` — ถ้าเป็น IP อื่นที่ยังไม่เคยตั้งค่า
   ต้องขอ user/password จากผู้ใช้ก่อนเสมอ ห้ามเดา
2. **ชื่อ DB** — ต้องเป็นหนึ่งใน `Data One` (=database `DataOne`) /
   `OceanLife` (=database `OceanLife`) / `OGL` (=database `OGL`) — รับได้ทั้ง
   แบบมีช่องว่างหรือไม่มี ไม่สนตัวพิมพ์
3. **ชื่อ Table** — รับได้ **หลายชื่อพร้อมกัน** (คั่นด้วย comma/ช่องว่าง/
   ขึ้นบรรทัดใหม่) ต้องเป็นชื่อเต็ม ไม่ใช่คำค้นบางส่วน (skill นี้ต่างจาก
   `/datadic-grouplife` ตรงที่ไม่รับ substring search)

ถ้าผู้ใช้ระบุ IP/DB มาแล้วแต่ไม่บอกชื่อ Table (หรือกลับกัน) ให้ถามส่วนที่
ขาดก่อนเสมอ อย่าเดาหรือ list table ทั้งหมด

## Step 2 — ทำทีละ Table (sequential loop ถ้ามีหลายชื่อ)

Sheet ดัชนี (index) ที่ตรงกับแต่ละ DB:

| ชื่อ DB (arg) | Sheet tab ในดัชนี | database จริงบน SQL Server |
|---|---|---|
| `dataone` / `data one` | `Data One` | `DataOne` |
| `oceanlife` | `OceanLife` | `OceanLife` |
| `ogl` | `OGL` | `OGL` |

Header ของแต่ละ index sheet ต่างกันเล็กน้อย (ใช้ชื่อ header ตรงตัวเป๊ะเวลา
ส่ง JSON เข้า `dic_index.py append`/`update-row`):

- **Data One**: `ต้องส่ง marking`, `ตรวจเช็คการมี ข้อมูลsencetive แล้ว? `,
  `No.`, `Table Name`, `Max_Column_id_used`, `ความสำคัญ`, `SQL Claim`,
  `Web Claim`, `Web Member`, `Web HR`, `Assign`, `รอตรวจสอบ`, `Review`,
  `คำอธิบายตาราง`, `Link`
- **OceanLife**: เหมือน Data One แต่ column DB-flag ชื่อ `GroupLife` (ไม่ใช่
  `SQL Claim`) และมี `CIS` เพิ่มหลัง `Web HR`, `รอตรวจสอบ` header
- **OGL**: เหมือน Data One แต่ column DB-flag ชื่อ `GroupLife / OGL`, ไม่มี
  `CIS`, และ header ใช้ `รอตรวจ` (ไม่ใช่ `รอตรวจสอบ`)

(header มีช่องว่างท้ายบางตัว — script `dic_index.py` trim ให้อัตโนมัติแล้ว
ไม่ต้องกังวลเรื่อง whitespace ตอนส่ง key)

สำหรับ table แต่ละตัว วนทำตามนี้จนครบ (**ห้ามข้ามลำดับ**):

### 2.1 ดึงโครงสร้างจริงจาก DB

```bash
python3 \
  ~/.claude/skills/datadic-grouplife-update/scripts/db_columns.py "<ip>" "<db>" "<table_name>"
```

ถ้าคืน `{"error": ...}` (เช่นหา table ไม่เจอใน DB นั้นจริง ๆ) ให้หยุดสำหรับ
table นี้ทันที แจ้งผู้ใช้ว่าหา table ไม่เจอใน DB/IP ที่ระบุ **ห้ามเดาแล้วไป
ต่อ** — table อาจสะกดผิดหรืออยู่คนละ DB

### 2.2 เช็คว่ามีอยู่ในดัชนีแล้วหรือยัง (exact match)

```bash
python3 \
  ~/.claude/skills/datadic-grouplife-update/scripts/dic_index.py find "<Sheet name>" "<table_name>"
```

### 2.3a ถ้ายังไม่มี (`found: false`) → Create

1. ถ้า `db_columns.py` คืน `table_description` ว่าง ให้ถามผู้ใช้สั้น ๆ ว่า
   table นี้ใช้เก็บข้อมูลอะไร (คำอธิบายตาราง 1 บรรทัด) — ถ้ามีอยู่แล้วจาก
   MS_Description ใน DB ใช้ค่านั้นได้เลยไม่ต้องถามซ้ำ
2. ถามผู้ใช้ว่า table นี้ถูกใช้งานโดยระบบไหนบ้าง (ตัวเลือกตาม column ของ
   sheet นั้น เช่น Web Claim / Web Member / Web HR / CIS ถ้ามี) — DB-flag
   column หลัก (SQL Claim / GroupLife / GroupLife-OGL ตามตาราง header ด้านบน)
   ให้ตั้ง `TRUE` อัตโนมัติเสมอเพราะมาจาก DB นั้นแน่นอนอยู่แล้ว ส่วนที่เหลือ
   default `FALSE` ถ้าผู้ใช้ไม่ระบุ
3. เช็ค Step 0 ก่อน (scope ต้องมี `drive` เต็ม) แล้วสร้างสเปรดชีตใหม่:
   ```bash
   echo '{"table_description": "...", "columns": <columns จาก 2.1>, "history_note": "สร้าง Data Dictionary จากโครงสร้าง DB จริง"}' | \
     python3 \
     ~/.claude/skills/datadic-grouplife-update/scripts/dic_table.py create "<DB จริงตาม mapping>" "<table_name>"
   ```
   เก็บ `url` ที่คืนมา
4. เพิ่มแถวใหม่ในดัชนี — **`Assign` ต้องเป็น local-part ของอีเมลผู้ใช้เอง
   (ไม่มี domain)**: เช่นถ้าอีเมลคือ `somchai.jm@ocean.co.th` ให้ใช้
   `somchai.jm` — ไม่ใช่ชื่อเต็มภาษาไทยแบบแถวเก่า:
   ```bash
   echo '{
     "Table Name": "<table_name>",
     "Max_Column_id_used": <จำนวน column จริง>,
     "ความสำคัญ": "เพิ่มใหม่",
     "<DB-flag header>": true,
     "Web Claim": false, "Web Member": false, "Web HR": false,
     "Assign": "<local-part อีเมลผู้ใช้เอง>",
     "<รอตรวจสอบ|รอตรวจ header>": true,
     "คำอธิบายตาราง": "<คำอธิบาย>",
     "Link": "<url จากขั้นตอนก่อนหน้า>"
   }' | python3 \
     ~/.claude/skills/datadic-grouplife-update/scripts/dic_index.py append "<Sheet name>"
   ```
   ถ้าคืน `{"error": ...}` (เช่น row ปลายตารางไม่ว่างจริง หรือชื่อซ้ำ) ให้
   หยุดและแจ้งผู้ใช้ ห้าม retry แบบสุ่มเดา row

### 2.3b ถ้ามีอยู่แล้ว (`found: true`) → Update

0. **เช็ค `link_is_chip` ในผลลัพธ์ของ `find` ก่อนเสมอ** — ถ้าเป็น `false`
   ข้ามไปข้อ 1 ได้เลย (Link เป็น URL ปกติ อ่านได้) ถ้าเป็น `true` แปลว่า
   cell คอลัมน์ Link ของแถวนี้ **ไม่ใช่ URL ที่อ่านได้ผ่าน API** ซึ่งมีได้ 2
   สาเหตุที่หน้าตาเหมือนกันจากมุมมอง script — **ต้องถามผู้ใช้ว่าเป็นกรณีไหน
   ก่อนเสมอ ห้ามเดาเอง** (เว้นแต่ผู้ใช้บอกมาก่อนแล้วในคำสั่ง):

   **(a) ยังไม่เคยสร้าง Link Sheet จริงเลย** — cell เป็นแค่ label ว่าง ๆ
   (เช่น literally คำว่า `"Link"`) ที่ยังไม่มีอะไรผูกอยู่จริง → ให้ทำ
   **เหมือน create flow ทุกขั้นตอน** (ดู 2.3a ข้อ 1-3: ถามคำอธิบายตาราง/
   flags การใช้งานถ้ายังไม่รู้, สร้างสเปรดชีตใหม่ด้วย `dic_table.py
   create`) แต่ **ห้าม append แถวใหม่ในดัชนี** เพราะแถวมีอยู่แล้ว — แทนที่
   ด้วยการ `update-row` ใส่ `"Link": "<url ใหม่จาก create>"` (และ
   `Max_Column_id_used` ถ้าต้องการอัพเดทด้วยเลย) เข้าไปที่ `row_number`
   เดิมจาก `find`:
   ```bash
   echo '{"Link": "<url>", "Max_Column_id_used": <n>}' | \
     python3 \
     ~/.claude/skills/datadic-grouplife-update/scripts/dic_index.py update-row "<Sheet name>" <row_number> "<table_name>"
   ```
   จบ flow ของ table นี้แค่นี้ (ไม่ต้องอ่าน/diff อะไรเพิ่มเพราะเพิ่งสร้างใหม่)

   **(b) มี Link Sheet จริงอยู่แล้ว แค่ผูกแบบ smart chip** ที่ API อ่าน URL
   ไม่ได้ → หยุดและขอให้ผู้ใช้เปิด cell นั้นเอง (บอก sheet name +
   row_number ให้ชัดเจน) แล้ว copy URL จริงมาให้ก่อน จากนั้นไปต่อข้อ 1
   ด้วย URL ที่ได้มา
1. อ่านโครงสร้างปัจจุบันจาก Link Sheet:
   ```bash
   python3 \
     ~/.claude/skills/datadic-grouplife-update/scripts/dic_table.py read "<link จาก find>"
   ```
2. เทียบกับ columns จริงจาก DB (2.1) ด้วยตาเอง แล้ว **แสดง diff ให้ผู้ใช้ดู
   ก่อนเขียนจริงเสมอ** (field ที่เพิ่มใหม่ / type-size เปลี่ยน / field ที่มี
   ใน sheet แต่ไม่มีใน DB แล้ว — อันหลังนี้ห้ามลบเอง ให้ถามผู้ใช้ว่าจะเก็บไว้
   หรือลบ) — รอผู้ใช้ยืนยันก่อนไปขั้นตอนถัดไป
3. เมื่อผู้ใช้ยืนยันแล้ว ให้ merge เข้าไปจริง:
   ```bash
   echo '{"table_description": "<ถ้าต้องการแก้ ไม่งั้นไม่ต้องใส่ key นี้>", "columns": <columns จาก 2.1>, "history_note": "อัพเดท field ตามโครงสร้าง DB จริง"}' | \
     python3 \
     ~/.claude/skills/datadic-grouplife-update/scripts/dic_table.py update "<link>"
   ```
   (script เก็บ description เดิมไว้ให้อัตโนมัติถ้า DB ไม่มี MS_Description
   ใหม่มาทับ — ไม่มีทางเสีย description ภาษาไทยที่คนเคยกรอกไว้)
4. บั๊พ `Max_Column_id_used` ในแถวดัชนีเดิมให้ตรงจำนวน field ล่าสุด (ใช้
   `row_number` จาก `find` ใน 2.2 — script จะ verify ชื่อ table ตรงก่อนเขียน
   ให้อัตโนมัติ):
   ```bash
   echo '{"Max_Column_id_used": <field_count จาก dic_table.py update>}' | \
     python3 \
     ~/.claude/skills/datadic-grouplife-update/scripts/dic_index.py update-row "<Sheet name>" <row_number> "<table_name>"
   ```

## Step 3 — สรุปผลรวมทุก Table ท้ายสุด

เมื่อทำครบทุก table แล้ว (ไม่ว่า create หรือ update) ให้สรุปเป็นตารางสั้น ๆ
ให้ผู้ใช้เห็นภาพรวม: table ไหน sheet ไหน ทำอะไรไป (สร้างใหม่/อัพเดท) พร้อม
ลิงก์ Link Sheet ของแต่ละ table — ถ้า table ไหน error ระหว่างทางให้บอกด้วย
ว่าติดตรงไหน ไม่ต้อง retry เองโดยไม่ถาม

## การตั้งค่าก่อนใช้งาน (Setup)

1. **Google OAuth token** — ต้องมี token ที่มี scope `spreadsheets` +
   `drive` (เขียนเต็ม ไม่ใช่ readonly) ผูกกับบัญชี Google ที่เข้าถึง Data
   Dictionary spreadsheet ของทีมคุณได้ — ดู Step 0
2. **DB credentials** — เติมใน `scripts/db_columns.py` (`DB_CREDENTIALS`
   dict, ต่อ IP) หรือตั้ง environment variable `DD_DB_USER`/`DD_DB_PASSWORD`
   ก่อนใช้งาน (ห้าม commit password ที่เติมไว้กลับเข้า git — ไฟล์นี้อยู่ใน
   repo ที่แชร์กัน)
3. **Master spreadsheet / per-DB template** — ค่า default ใน
   `scripts/dic_index.py` (`MASTER_SPREADSHEET_ID`) และ
   `scripts/dic_table.py` (`TEMPLATES` dict: template spreadsheet + Drive
   folder ต่อ DB) ชี้ไปที่ Data Dictionary ของทีมต้นทางอยู่แล้ว — ถ้าทีมคุณ
   ใช้ไฟล์เดียวกันก็ใช้ได้เลยไม่ต้องแก้ ถ้ามีสเปรดชีตชุดของตัวเองแยกต่างหาก
   ให้ override ด้วย environment variable แทนการแก้โค้ด:
   `DD_MASTER_SPREADSHEET_ID`, และต่อ DB `DD_TEMPLATE_<DB>`/`DD_FOLDER_<DB>`
   (เช่น `DD_TEMPLATE_DATAONE`, `DD_FOLDER_DATAONE` — DB name เป็นตัวพิมพ์
   ใหญ่) — ไฟล์ template ต้องมี 2 tab ชื่อ `Data dictionary` (ชื่อตาราง/
   Description/LastUpdate ที่แถว 2/3/5 คอลัมน์ C, header field ที่แถว 7,
   ข้อมูล column เริ่มแถว 8) กับ `HistoryLog` (header แถว 4, ข้อมูลเริ่ม
   แถว 5) ตาม pattern เดียวกับไฟล์ table อื่นที่มีอยู่แล้วในดัชนีของคุณ
4. **`DD_USER_NAME`** (optional) — ตั้งเป็นชื่อ/handle ของคุณเอง เพื่อให้
   คอลัมน์ `UserUpdate` ใน HistoryLog ถูกต้อง (default เป็น
   `<Developer Name>` เฉย ๆ ถ้าไม่ตั้ง)

## หมายเหตุ

- `db_columns.py` เป็น read-only ต่อ DB เสมอ (query metadata อย่างเดียว ไม่
  แตะข้อมูลจริงในตาราง)
- Field description ที่ query ได้จาก DB มาจาก extended property
  `MS_Description` — table เก่าที่ยังไม่เคยใส่ comment ไว้ตอนสร้างมักไม่มี
  ต้องถามผู้ใช้เพิ่มเอง (เฉพาะตอน create table ใหม่ทั้งตาราง — ตอน update
  ปล่อยว่างไว้เหมือนเดิมถ้า DB ไม่มีและ sheet เดิมก็ไม่มี ไม่ต้องไปเดา)
- ไฟล์ต่อ table 1 ไฟล์อยู่คนละ Google Drive folder ตาม DB (`DataOne`/
  `OceanLife`/`OGL` folder แยกกัน) — `dic_table.py create` ใส่ parent
  folder ให้ถูกต้องอัตโนมัติแล้วจาก mapping ในสคริปต์ ไม่ต้องระบุเอง
- `dic_index.py append` เขียนคอลัมน์ Link เป็น plain URL text เสมอ (ไม่ใช่
  smart chip) เพื่อให้แถวที่ skill นี้สร้างเองอ่านกลับได้ปกติในอนาคต — ปัญหา
  "อ่าน Link ไม่ได้" (ดู 2.3b ข้อ 0) เกิดกับแถวเก่าที่คนอื่นใส่ลิงก์ผ่าน UI
  แบบ smart chip เท่านั้น
