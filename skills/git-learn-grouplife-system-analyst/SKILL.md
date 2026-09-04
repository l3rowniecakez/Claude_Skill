---
installer: create-shortcut
name: git-learn-grouplife-system-analyst
description: 'วิเคราะห์เมนูงานของโปรแกรมกลุ่มประกันกลุ่ม (Delphi) แบบละเอียดถึงระดับ event/store/DB โดยผู้ใช้เลือกเมนูที่ต้องการเป็น checkbox แล้วสรุปเป็นคู่มือ+เอกสารเชิงเทคนิคลง Google Sheet ต่อ App (ใต้โฟลเดอร์ Drive "GroupLife by Claude AI", id 1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ). Use when user says "/git-learn-grouplife-system-analyst", ต้องการวิเคราะห์เมนู/ทำเอกสารระบบงานของโปรแกรมกลุ่มประกันกลุ่มเพื่อเตรียม spec ทำระบบใหม่.'
created_at: 2026-09-04T00:00:00+07:00
argument-hint: "[ชื่อ App หรือ Path เก็บโปรแกรม]"
---

# /git-learn-grouplife-system-analyst — วิเคราะห์เมนูงาน + จัดทำเอกสารระบบลง Sheet

Sibling ของ [[reference-git-learn-grouplife-skill]] — ใช้วิธีอ่าน source แบบ**ไม่ clone**
เดียวกันทุกประการ (Gitblit web `tree/`/`raw/` ผ่าน `browse_repo.py`) และหา repo/path
ของ App จากชีตติดตามเดียวกัน (spreadsheet `18zoUG8L_a5pmg-4_TD0g2ZLjzgpIMlKM0IcVN07_2u0`)
แต่จุดประสงค์ต่างกัน: skill นี้ไม่ได้อ่านโค้ดเพื่อทำความเข้าใจเฉย ๆ แต่วิเคราะห์**เมนูงาน**
ของโปรแกรมทีละเมนูอย่างละเอียด (ปุ่มไหนเรียก event อะไร, event นั้นไป query/insert/update/
delete ข้อมูลผ่าน Store อะไรใน DB ไหน) แล้วสรุปเป็นเอกสารคู่มือ+ข้อมูลเชิงเทคนิคลง
Google Sheet 1 ไฟล์ต่อ 1 App — เป้าหมายปลายทางคือให้เอกสารนี้เอาไปใช้สร้างระบบใหม่ได้

**รูปแบบเอกสาร (ล็อกกับผู้ใช้แล้ว 2026-09-04)**: ดู `scripts/drive_ops.py` และ
`scripts/sheet_write.py` docstring สำหรับ schema เต็ม — สรุปสั้น ๆ:
- โครงสร้าง Drive: `<Root>/<Group>/<AppName>` (1 spreadsheet ต่อ 1 App, ไม่ใช่ 1 spreadsheet
  ต่อเมนู) — `<Group>` = คอลัมน์ Group ในชีตติดตาม (ชื่อ repo สั้น ๆ), `<AppName>` = คอลัมน์
  AppName (โฟลเดอร์ก่อน `/trunk`)
- Tab "Menu Contents": สารบัญของ App นั้น, header 4 แถว (โปรแกรม/Repo URL/Sub Folder/
  วันที่อัพเดท) + แถวว่าง + header ตาราง (No/เมนูงาน/รายละเอียดเมนูงาน/Delphi Path File/
  Sheet URL) + 1 แถวต่อเมนูที่เคยวิเคราะห์แล้ว
- Tab รายละเอียดต่อเมนู (ตั้งชื่อ tab ตาม unit/form หลักของเมนูนั้น เช่น `ListAcDeathWaitPay`):
  header 6 แถว (โปรแกรม/Repo URL/Sub Folder/เมนูงาน/รายละเอียดเมนูงาน/วันที่อัพเดท) + แถวว่าง
  2 แถว + ตาราง 6 คอลัมน์ (Component Name/Description/Component Caption/Event Name/DB/
  Call Store) + ส่วนเพิ่มท้ายตาราง "ขั้นตอนการใช้งาน (User Manual Steps)" เป็น step
  เรียงลำดับแบบคู่มือผู้ใช้ (ส่วนนี้เพิ่มขึ้นจากไฟล์ตัวอย่างเดิม เพื่อให้ครบตามวัตถุประสงค์ที่
  ผู้ใช้ระบุไว้ตอนสั่งสร้าง skill — ไม่ใช่ hallucinate โครงสร้างเอง)
- **สี** (เพิ่ม 2026-09-04 ตามฟีดแบ็กผู้ใช้ — mirror สีจากไฟล์ Template ของผู้ใช้): คอลัมน์
  label ของ header info block (โปรแกรม/Repo URL/Sub Folder/ฯลฯ) พื้นฟ้าอ่อน
  `#CFE2F3`-ish (`rgb(0.812,0.886,0.953)`) ตัวหนา; แถว header ของตาราง (No/เมนูงาน/...
  หรือ Component Name/...) พื้นน้ำเงินเข้ม `rgb(0.106,0.267,0.471)` ตัวหนังสือขาวตัวหนา
  จัดกึ่งกลาง — ทำอัตโนมัติทั้งใน `drive_ops.py` (ตอนสร้าง Menu Contents ใหม่) และ
  `sheet_write.py` (ทุกครั้งที่เขียน/overwrite detail tab)
- **ไม่มีการ copy ไฟล์ "Template" (`1wI9_Q-Zw50vLMNbtozKhCpb7ebsLYtmyHUC_1gBnLnY`) เลย** —
  ผู้ใช้ยืนยันให้สร้างชีตเปล่าใหม่ทุกครั้งที่เจอ App ที่ยังไม่เคยมี ไฟล์ Template และไฟล์ที่ผู้ใช้
  ทำมือไว้ก่อนหน้า (เช่น `GroupLifeInsuranceSystem_Benefits` ที่มีอยู่แล้วในโฟลเดอร์
  `groupwork-system-2016`) เป็นแค่ตัวอย่างอ้างอิง ห้ามแก้ไข/เขียนทับ

## Phase 1 — resolve App (เหมือน git-learn-grouplife Step 1 ทุกประการ)

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife/scripts/search_app.py "<คำค้นจาก argument>"
```
- **0 ผลลัพธ์**: แจ้งผู้ใช้ไม่เจอ ถามชื่ออื่น หรือแนะนำ `/git-clone-grouplife-update` ก่อน
  ถ้า App นี้ยังไม่เคยถูกบันทึกในชีตติดตามเลย
- **1 ผลลัพธ์**: ยืนยันชื่อเต็ม (Group/AppName/Sub Folder) กับผู้ใช้สั้น ๆ ก่อนไป Phase 2
- **มากกว่า 1 ผลลัพธ์**: โชว์ทั้งหมดพร้อม Group ที่สังกัด ให้ผู้ใช้เลือกเจาะจง — ห้ามเดา

จาก field `repo` (รูปแบบ `git clone ssh://<user>@10.100.2.187:29418/delphi/<repo>.git`)
ตัดเอาเฉพาะ `<repo>` สั้น ๆ ไว้ใช้กับ `browse_repo.py` (ดู git-learn-grouplife SKILL.md
เรื่องนี้ ห้ามส่งสตริงเต็มเข้าไปตรง ๆ)

## Phase 2 — หาไฟล์ .dpr หลัก + ชื่อโปรแกรม + main menu form

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife/scripts/browse_repo.py list "<repo>" "<sub_folder>"
```
- หาไฟล์ `.dpr` ตัวเดียวที่รากของ `sub_folder` — ชื่อไฟล์ (ตัด `.dpr`) + `.exe` คือ
  `โปรแกรม` ที่จะเขียนลง header (เช่น `OGL_Benefits.dpr` → `OGL_Benefits.exe`)
- `read` ไฟล์ `.dpr` แล้วดูบรรทัด `Application.CreateForm(TfrmXXX, frmXXX)` **แรกสุด**
  ปกติคือ main/shell form ที่มี menu bar หลักของโปรแกรม (ดูตัวอย่างภาพหน้าจอที่ผู้ใช้ให้ไว้
  ตอนสร้าง skill นี้ — แถบบนมี tab หมวดใหญ่ + ไอคอนพร้อม dropdown เมนูย่อย)
- `read` ทั้ง `.pas` และ `.dfm` ของ main form นั้น

## Phase 3 — สกัด menu tree 3 ชั้นจาก main form

จาก `.dfm` (โครงสร้าง component) + `.pas` (event handler) ของ main form ให้ไล่หา:
1. **หมวดใหญ่ระดับบนสุด** (เช่น tab/page แยกกลุ่มงาน — "เมนูงานส่วนผลประโยชน์ และ
   ติดตามผล", "Main", "เมนูงานส่วนการเงิน")
2. **กลุ่มเมนูย่อยในแต่ละหมวด** (ปุ่ม toolbar/ribbon ที่มี dropdown menu — เช่น
   "ข้อมูลทั่วไป (General-Info)", "บันทึกการจ่าย (Payment)", "พิมพ์เอกสาร (Print-Document)")
3. **เมนูปลายทาง (leaf)** ในแต่ละกลุ่ม (แต่ละ `TMenuItem`/component ปลายทางที่มี
   `OnClick` จริง — เช่น "รายละเอียดรายการจ่ายเงิน", "[AcGpPro01] ...")

สำหรับแต่ละ leaf ให้ไล่ตาม `OnClick` handler ใน `.pas` เพื่อหา**ฟอร์มปลายทาง** (มักเป็น
`TfrmXXX.Create` / `ShowForm` / ชื่อ unit ที่ปรากฏใน `uses` — บันทึกไว้เป็น candidate
"Delphi Path File" เบื้องต้น ยังไม่ต้องมั่นใจ 100% เพราะ agent วิเคราะห์เชิงลึกใน Phase 5
จะยืนยัน/แก้ไขอีกที)

ประกอบ breadcrumb string รูปแบบเดียวกับตัวอย่าง: `"หมวดใหญ่" => "กลุ่มย่อย" => "เมนูปลายทาง"`

## Phase 4 — ให้ผู้ใช้เลือกเมนู (AskUserQuestion แบบ checkbox จริง, แบ่งชุดอัตโนมัติ)

**ใช้ AskUserQuestion tool จริง** (ไม่ใช่ list ข้อความให้ผู้ใช้พิมพ์ตอบเอง — แก้ตามฟีดแบ็ก
ผู้ใช้ 2026-09-04: ต้อง copy ข้อความมาเพื่อตอบคำถามมันไม่สะดวก อยากได้ checkbox กดเลือกจริง
ใน CLI) แต่ตัว tool จำกัด**สูงสุด 4 ตัวเลือกต่อ 1 คำถาม และสูงสุด 4 คำถามต่อการเรียก 1
ครั้ง** (รวมมากสุด 16 ตัวเลือกต่อการเรียก 1 ครั้ง) ในขณะที่เมนูจริงมักมีมากกว่านั้น —
ต้อง**แบ่งชุด (chunk) อัตโนมัติ** ดังนี้:

1. แบ่ง list ที่จะให้เลือก (หมวดใหญ่ในรอบแรก / กลุ่มย่อยในรอบสอง / leaf ในรอบสาม) เป็นชุด
   ละไม่เกิน 4 รายการ
2. รวมได้สูงสุด 4 ชุดต่อการเรียก `AskUserQuestion` 1 ครั้ง (ตั้ง `multiSelect: true` ทุก
   คำถาม เพื่อให้แต่ละชุดกลายเป็น checkbox กลุ่มหนึ่งที่เลือกได้หลายข้อ) — ตั้ง `header`
   บอกลำดับชุดให้ผู้ใช้รู้ว่ากำลังเลือกช่วงไหน เช่น `"เมนู 1-4"`, `"เมนู 5-8"`
3. ถ้ารายการทั้งหมดมีมากกว่า 16 ให้เรียก `AskUserQuestion` **หลายรอบต่อเนื่องกัน** (รอบถัด
   ไปคุมชุดที่เหลือ) แล้วรวมผลลัพธ์ที่ผู้ใช้เลือกจากทุกรอบเข้าด้วยกัน
4. ใช้ `option.description` ใส่ context เพิ่ม (เช่น breadcrumb เต็ม, ฟอร์มเป้าหมาย candidate,
   หมายเหตุ "ไม่มี OnClick" ถ้าเจอ) เพื่อช่วยผู้ใช้ตัดสินใจโดยไม่ต้องสลับไปดูที่อื่น

ลำดับรอบเหมือนเดิม 3 รอบ:
1. รอบแรก: ให้เลือก **หมวดใหญ่ระดับบนสุด** (top-level tabs/categories) — เลือกได้มากกว่า 1
2. รอบสอง (ต่อแต่ละหมวดที่เลือก): ให้เลือก **กลุ่มเมนูย่อย** ในหมวดนั้น
3. รอบสาม (ต่อแต่ละกลุ่มที่เลือก): ให้เลือก **เมนูปลายทาง (leaf)** จริงที่จะส่งไปวิเคราะห์ใน
   Phase 5 — นี่คือ output สุดท้ายของ phase นี้

ถ้าบางชั้นไม่มีชื่อกลุ่มย่อยจริง (เช่น bar ที่ไม่มี Caption, หรือ tab หนึ่งมี items ระดับ leaf
ตรงๆ ไม่ผ่านกลุ่มย่อย) ให้ข้ามรอบนั้นไปเลย ไม่ต้องสร้างคำถามหลอกๆ ที่ไม่มีตัวเลือกจริง

## Phase 5 — วิเคราะห์แบบขนาน (แยก Agent ต่อ 1 เมนูที่เลือก)

สำหรับ **แต่ละ leaf menu ที่ผู้ใช้เลือก** ให้เรียก `Agent` tool (subagent_type ปกติ,
ไม่ใช้ `fork` — งานนี้เป็น read-only investigation ใหม่ ไม่ต้องสืบทอด context เดิม) แบบ
**ขนานในข้อความเดียว** (หลาย Agent call พร้อมกัน ถ้าเลือกหลายเมนู)

Prompt ที่ส่งให้แต่ละ agent ต้องมีครบ (agent เริ่มจาก context ว่าง ไม่รู้อะไรมาก่อน):
- `<repo>` สั้น ๆ, `<sub_folder>`, breadcrumb เต็มของเมนูนี้, ฟอร์มเป้าหมาย candidate จาก
  Phase 3 (บอกว่ายังไม่ยืนยัน ให้ agent ตรวจสอบเองด้วย)
- คำสั่งให้ใช้ `~/.config/redmine-summary-to-email/venv/bin/python3
  ~/.claude/skills/git-learn-grouplife/scripts/browse_repo.py` (list/tree/read) เพื่อ
  หา `.pas`+`.dfm` ของฟอร์มเป้าหมายให้แน่ใจ แล้วอ่านทั้งคู่ให้ครบ
- ให้วิเคราะห์ทุก component ที่มี event จริง (ปุ่ม, grid, FormShow/FormCreate สำหรับ query
  แสดงผล ฯลฯ) — ต่อแต่ละตัวต้องตอบ: component name, คำอธิบายสั้น, caption (ถ้ามี),
  ชื่อ event/handler, DB connection ที่ใช้ (ชื่อ database จาก connection component), และ
  stored proc/query ที่ถูกเรียก (ไล่จาก `TADOStoredProc`/`TMSStoredProc`/`TQuery`/
  `ExecSQL`/SQL text ตรง ๆ — ระบุถ้า INSERT/UPDATE/DELETE ไปกระทบตารางไหนถ้าดูจาก SQL
  ได้ชัดเจน ใส่ในคำอธิบายด้วย)
- ให้เขียน "ขั้นตอนการใช้งาน" เป็น narrative แบบคู่มือผู้ใช้ (numbered steps) อธิบายลำดับ
  การทำงานจริงของหน้าจอนี้ตั้งแต่เปิดจนจบ งาน
- **ให้ agent return ผลลัพธ์เป็น JSON object เดียวตรง ๆ ใน final message** ให้ตรง schema
  ที่ `sheet_write.py` ต้องการ (ดู docstring ในไฟล์นั้น) ยกเว้น field ที่ orchestrator
  (ตัวเอง) จะเติมเอง: `spreadsheet_id`, `program_name`, `repo_url`, `sub_folder`, `today`
- **agent ห้ามเขียนอะไรลง Google Sheet เอง** — เป็น read-only investigation ล้วน ๆ
  ส่งผลกลับมาให้ orchestrator เขียนแทน (เหตุผล: ป้องกัน concurrent write ชน spreadsheet
  เดียวกัน ดู Phase 6)

## Phase 6 — เตรียม/หา spreadsheet ของ App แล้วเขียนผลตามลำดับ (ห้ามขนาน)

**ก่อน** เขียนผลจาก Phase 5 ต้อง ensure โฟลเดอร์+spreadsheet ก่อน (ทำครั้งเดียวต่อ 1 รอบ
รัน skill):

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife-system-analyst/scripts/drive_ops.py \
  ensure "<Group>" "<AppName>" "<program_name เช่น OGL_Benefits.exe>" \
  "<repo_url เต็มจากชีตติดตาม>" "<sub_folder>" "<วันนี้ YYYY-MM-DD>"
```
คืน `spreadsheet_id` — ใช้ตัวนี้กับทุกเมนูของ App เดียวกันในรอบนี้

จากนั้น**ทีละเมนู ตามลำดับ ห้ามขนาน** (เหตุผลอยู่ใน `sheet_write.py` docstring — row
number ของ "Menu Contents" คำนวณจาก read ครั้งเดียว ถ้าเขียนขนานจะชนกัน):

```bash
echo '<JSON payload จาก agent + spreadsheet_id/program_name/repo_url/sub_folder/today>' | \
  ~/.config/redmine-summary-to-email/venv/bin/python3 \
  ~/.claude/skills/git-learn-grouplife-system-analyst/scripts/sheet_write.py
```
คืน `tab_url` (ลิงก์ตรงไปยัง tab ที่เพิ่งเขียน) — เก็บไว้สรุปให้ผู้ใช้ตอนจบ

## Phase 7 — สรุปให้ผู้ใช้

จบงานให้แจ้ง:
- ลิงก์ spreadsheet หลักของ App (Menu Contents)
- ลิงก์ tab ของแต่ละเมนูที่เพิ่งวิเคราะห์เสร็จ
- ถ้ามีเมนูไหนที่ agent วิเคราะห์ไม่ได้ครบ (เช่น หา store ไม่เจอ, SQL ซับซ้อนเกินไป
  ต้องดูมือ) ให้ระบุตรง ๆ ว่าเมนูไหนยังไม่สมบูรณ์ — **ห้ามอ้างว่าวิเคราะห์ครบถ้ายังไม่ครบจริง**

## ข้อจำกัดที่ต้องบอกผู้ใช้ล่วงหน้า (ถ้าเกี่ยวข้อง)

- Read-only ต่อ Gitblit เหมือน git-learn-grouplife — แก้ไข/commit source ไม่ได้จาก skill นี้
- การสกัด menu tree (Phase 3) เป็น static analysis จาก `.dfm`/`.pas` — ถ้าโปรแกรมสร้างเมนู
  แบบ dynamic (เขียนโค้ด build menu ตอน runtime แทนที่จะประกาศใน `.dfm` ตรง ๆ) การไล่หา
  อาจไม่ครบ ต้องแจ้งผู้ใช้และขอให้ช่วยยืนยัน breadcrumb/target form ที่ไม่ชัดเจนเอง
- Auth ใช้ credential เดียวกับ git-learn-grouplife/git-clone-grouplife-update ทั้งหมด
  (`~/.config/gitblit-web/credentials.json` สำหรับอ่าน source, `~/.config/claude-google-access/
  token.json` สำหรับเขียน Google Sheet — ดู [[reference-claude-google-access-oauth]])
