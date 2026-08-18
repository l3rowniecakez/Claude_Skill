---
installer: create-shortcut
name: datadic-grouplife
description: 'เปิดดู Data Dictionary ของระบบประกันกลุ่ม/เดี่ยว (Data One / OceanLife / OGL) จาก Google Sheet — ค้นหาชื่อ Table แล้วแสดงโครงสร้างคอลัมน์ทั้งหมด. Use when user says "/datadic-grouplife", ถาม "table นี้มี field อะไรบ้าง", หรือต้องการดู Data Dictionary ของ DB dataone/oceanlife/ogl.'
created_at: 2026-08-18T00:00:00+07:00
argument-hint: "[db: dataone|oceanlife|ogl] [table name หรือคำค้นบางส่วน]"
---

# /datadic-grouplife — Group/Individual Life Data Dictionary Viewer

อ่านรายชื่อ Table และโครงสร้างคอลัมน์จาก Google Sheet กลาง (spreadsheet ID
`1qHeg391cRNrGA1HC3cWxsv9HcJZS0POuI94uaR27cqU`) ซึ่งมี 3 sheet (tab) ที่เป็น
ดัชนีรายชื่อ table ของแต่ละ DB:

| DB argument | Sheet name (tab) |
|---|---|
| `dataone` | `Data One` |
| `oceanlife` | `OceanLife` |
| `ogl` | `OGL` |

แต่ละแถวในดัชนีมีคอลัมน์ `Table Name`, `คำอธิบายตาราง` และ `Link` — ค่าใน
`Link` คือ URL ไปยัง **Google Spreadsheet แยกต่างหากของแต่ละ table** (คนละไฟล์
ต่อ 1 table ไม่ใช่ gid เดียวกัน) ซึ่งมี tab ชื่อ `Data dictionary` เก็บ
โครงสร้างคอลัมน์แบบเต็ม (Field#, Description, Type, Size, Null, Key,
Validation, Value, Min/Max Value, Example, เงื่อนไขในการบันทึก, หมายเหตุ)

Auth: ใช้ token เดิมที่ตั้งไว้แล้วใน memory `reference-claude-google-access-oauth`
(`~/.config/claude-google-access/token.json`, scope `spreadsheets`) — ไม่ต้อง
ขอ auth ใหม่ ยกเว้น token หมดอายุ/refresh fail จริง ๆ ค่อย fallback ตามที่
memory นั้นบอกไว้

Python env: `~/.config/redmine-summary-to-email/venv/bin/python3` (มี
google-api-python-client ติดตั้งแล้ว)

Scripts ของ skill นี้เอง (แก้ bug str-cast ของ `read_sheet.py` เดิม +
resolve header column แบบ dynamic แล้ว ไม่ต้อง reuse ตัวเดิม):
- `scripts/dd_index.py <sheet_name> [search_substring]` → list/ค้นหาแถวใน
  ดัชนี พิมพ์ JSONL บรรทัดละ 1 table: `{no, table_name, description, link}`
- `scripts/dd_detail.py <link_url>` → เปิด spreadsheet ของ table นั้น อ่าน
  tab `Data dictionary` คืน JSON: `{table_name, description, last_update,
  fields: [...]}`

---

## Step 1 — หา DB และคำค้น table

รับ `$ARGUMENTS` เป็น `[db] [คำค้น]` แบบไหนก็ได้ (อาจมีแค่ db, แค่คำค้น,
ทั้งคู่ หรือไม่มีเลย)

- ถ้าไม่มี argument เลย และดูจากบทสนทนาแล้วยังไม่รู้ทั้ง db และคำค้น ให้ถาม
  ผู้ใช้เป็นภาษาไทยว่า "จะดู DB ตัวไหน (dataone / oceanlife / ogl) และต้องการ
  ดู Table ชื่ออะไร (พิมพ์ชื่อเต็มหรือบางส่วนก็ได้)" — ใช้ AskUserQuestion ถ้า
  ต้องการให้เลือก DB จาก list, ปล่อยให้พิมพ์อิสระได้สำหรับชื่อ table
- **ถ้าระบุ DB มาแล้วแต่ยังไม่ระบุชื่อ table**: ต้องถามชื่อ Table ก่อนเสมอ
  ตามที่ผู้ใช้กำหนดไว้ ("ต้องถามว่าต้องการดู Table Name ชื่ออะไร") — อย่าเดา
  หรือ list table ทั้งหมดโดยไม่ถามก่อน
- **ถ้าไม่ระบุ DB**: ให้ค้นหาคำค้นนั้นไล่ทีละ sheet ทั้ง 3 (`Data One`,
  `OceanLife`, `OGL`) ไม่ต้องถามว่าจะดู DB ไหนก่อน — ค้นหาแล้วรวมผลจากทุก DB

## Step 2 — รันค้นหา

รันต่อ sheet ที่เกี่ยวข้อง (1 sheet ถ้าระบุ DB มา, ทั้ง 3 sheet ถ้าไม่ระบุ DB):

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/datadic-grouplife/scripts/dd_index.py "<Sheet name>" "<คำค้น>"
```

- ถ้าผู้ใช้พิมพ์ชื่อ table แบบเจาะจง (ไม่ใช่คำค้นบางส่วน) ก็ยังใช้คำสั่งเดียวกัน
  ได้ (substring match ครอบคลุมชื่อเต็มอยู่แล้ว) — ถ้าไม่พิมพ์คำค้นเลยจะได้
  ทุก table ใน sheet นั้น (ระวังบาง sheet มีหลายร้อยแถว อย่า dump ทั้งหมดให้
  ผู้ใช้อ่าน ให้ทำเป็น list สั้น ๆ หรือขอให้ผู้ใช้เจาะคำค้นเพิ่ม)

## Step 3 — ถ้าเจอมากกว่า 1 รายการ (ซ้ำกันหลาย DB หรือหลาย table)

List ผลลัพธ์ทั้งหมดที่เจอ (พร้อมระบุ DB/sheet ของแต่ละแถว) ให้ผู้ใช้เลือกว่า
จะดู table ไหน DB ไหน เช่น:

```
เจอ 3 รายการที่ตรงกับ "xxx":
1. [dataone] TableA — คำอธิบาย...
2. [ogl] TableA_V2 — คำอธิบาย...
3. [oceanlife] TableA — คำอธิบาย...
```

ถ้าเจอรายการเดียว ให้ไปต่อ Step 4 ได้เลยโดยไม่ต้องถามยืนยันซ้ำ

## Step 4 — ดึงโครงสร้างตารางแบบเต็ม

จาก `link` ของแถวที่เลือก รัน:

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/datadic-grouplife/scripts/dd_detail.py "<link>"
```

**Table Structure ต้องแสดงเป็นตาราง Markdown เท่านั้น ห้ามเขียนบรรยายเป็นข้อความ
(bullet list / ย่อหน้า) แทนตารางเด็ดขาด** — โครงสร้างที่ต้องแสดงเสมอ:

1. หัวเรื่อง `## Table: <table_name> (DB: <db>)` ตามด้วยบรรทัด **คำอธิบาย:**
   และ **Last update:** (แปลงจาก Google Sheets date serial number เป็นวันที่
   จริงด้วย epoch 1899-12-30 ก่อนแสดงเสมอ ห้ามโชว์เลข serial ดิบ)
2. ตาราง Markdown 1 ตารางสำหรับ column ทั้งหมด (1 แถว = 1 field) — คอลัมน์ของ
   ตาราง: `Field | Description | Type | Size | Null | Key | Validation |
   Value | Min Value | Max Value | Example | เงื่อนไขในการบันทึก | หมายเหตุ`
   — ตัดคอลัมน์ที่ว่างทั้งตารางออกได้เพื่อให้อ่านง่ายขึ้น แต่ที่เหลือต้องอยู่
   ในตารางเดียวกันเสมอ ห้ามแยกเป็น sub-bullet ต่อ field
3. ถ้ามีหลาย table ที่ต้องแสดงพร้อมกัน ให้ทำแบบนี้ซ้ำต่อ table (คนละตาราง
   Markdown ต่อ table) ห้ามรวมหลาย table ไว้ในตารางเดียว

**สำคัญมาก — กันตารางแตกเป็น list ในเทอร์มินัล**: ถ้าตาราง Markdown กว้างเกิน
เทอร์มินัล (คอลัมน์เยอะ + เนื้อหายาว) ตัว renderer จะ fallback ไปแสดงทีละ field
แบบ `Field: ... / Description: ... / Type: ...` (ไม่ใช่ตารางจริง) ซึ่งเป็น
รูปแบบที่ผู้ใช้ไม่ต้องการเด็ดขาด — เพื่อป้องกันปัญหานี้ ให้ทำทุกข้อนี้เสมอ:
   - เอาบรรทัดใหม่ (`\n`) ในเนื้อหาแต่ละ cell ออก แทนที่ด้วย ` / ` ให้อยู่บรรทัด
     เดียวเสมอ (ห้ามให้ cell มีหลายบรรทัด)
   - ตัดคอลัมน์ที่ว่างทุกแถวออกจริง ๆ (ไม่ใช่แค่ทางเลือก) — โดยทั่วไป
     `Value`, `Min Value`, `Max Value`, `เงื่อนไขในการบันทึก` มักว่างทั้งหมด
     ให้ตัดทิ้งถ้าว่างจริง
   - ถ้า `Description` ยาวเกิน ~50 ตัวอักษร ให้ย่อให้สั้นลง (สรุปใจความ) แทน
     การใส่ข้อความเต็มยาว ๆ ในตาราง
   - เป้าหมายคือให้ตารางมีคอลัมน์หลักเท่าที่จำเป็น (ปกติ Field, Description,
     Type, Size, Null, Key, Validation, Example ก็เพียงพอ) และแต่ละ cell สั้น
     กระชับ เพื่อให้ตารางแสดงเป็นตารางจริงเสมอ ไม่ใช่ fallback list

## หมายเหตุ

- ห้ามแก้ไขข้อมูลใน Google Sheet ใด ๆ — skill นี้เป็น read-only เท่านั้น
- ถ้า `dd_detail.py` หา tab `Data dictionary` ไม่เจอ จะ fallback ไปใช้ tab
  แรกของไฟล์นั้นแทน (ดูจาก `sheet_used` ใน output) — ถ้าโครงสร้างไม่ตรงตามที่
  คาดไว้ให้แจ้งผู้ใช้ว่ารูปแบบไฟล์นี้ต่างจากมาตรฐาน แทนที่จะเดาแล้วแสดงข้อมูล
  ผิด
