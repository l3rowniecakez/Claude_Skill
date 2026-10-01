---
installer: create-shortcut
name: git-learn-grouplife-er-diagram
description: 'สร้าง ER-Diagram ของเมนูงานโปรแกรมกลุ่มประกันกลุ่ม (Delphi) ต่อยอดจาก Google Sheet ที่ /git-learn-grouplife-system-analyst วิเคราะห์ไว้ — ผู้ใช้ระบุชื่อ App แล้วเลือกเมนูเป็น checkbox, skill อ่านคอลัมน์ DB + Call Store, ดูโครงสร้าง Table/View/Store จริงจาก DB .52/.139 (+ /datadic-grouplife), สรุปความสัมพันธ์ one-to-one / one-to-many / many-to-many แล้วเพิ่ม tab "[ER] <ชื่อ tab เมนู>" + ลิงก์ในคอลัมน์ "ER-Diagram" ของ Menu Contents. Use when user says "/git-learn-grouplife-er-diagram", ต้องการทำ ER-Diagram / ดูว่าเมนูงานเก็บข้อมูลลง Table ไหนบ้างและสัมพันธ์กันอย่างไร.'
created_at: 2026-09-30T00:00:00+07:00
argument-hint: "[ชื่อ App]"
---

# /git-learn-grouplife-er-diagram — ER-Diagram ของเมนูงาน

ต่อยอดจาก `reference-gitlearn-grouplife-system-analyst-skill` (`/git-learn-grouplife-system-analyst`):
skill นั้นวิเคราะห์เมนูแล้วเขียน Google Sheet ต่อ App (โฟลเดอร์ Drive "GroupLife by Claude AI",
id `1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ`) ส่วน skill นี้**อ่านผลนั้น**มาสร้าง ER-Diagram ของแต่ละเมนู
เพื่อศึกษาว่าเมนูเก็บข้อมูลลง Table ไหน และแต่ละ Table สัมพันธ์กันแบบ 1:1 / 1:N / N:M อย่างไร

**Skill นี้ไม่อ่าน source Delphi เลย** — ข้อมูลเริ่มต้นทั้งหมดมาจาก tab วิเคราะห์เมนู (คอลัมน์ `DB`,
`Call Store`) แล้วไปอ่านโครงสร้างจริงจาก DB. งานหนักคือ**อ่านโค้ด Store/View** เพื่อรู้ว่า join/insert/update
ตารางไหน ไม่ใช่แค่ดูรายชื่อ Table

Python: `~/.config/redmine-summary-to-email/venv/bin/python3` (มี google-api + pymssql). Scripts อยู่ที่
`~/.claude/skills/git-learn-grouplife-er-diagram/scripts/` (ย่อเป็น `$S` ด้านล่าง). Google auth = token เดิม
`~/.config/claude-google-access/token.json` (ดู `reference-claude-google-access-oauth`).
DB login อยู่ที่ `~/.config/grouplife-db/credentials.json` (SIT `.52`, Mirror Prod `.139`, UAT `.22` — ตาม
`reference-db-credentials-sit-139-uat`; **ห้าม**ถามผู้ใช้ซ้ำ และ **SIT=.52, UAT=.22, .139=Mirror Prod** ห้ามเรียก .139 ว่า UAT)

ตัวแปรที่ใช้ในคำสั่งด้านล่าง: `PY` = python ที่ติดตั้งครบตาม `requirements.txt` (บนเครื่องเจ้าของ skill = `~/.config/redmine-summary-to-email/venv/bin/python3`;
เครื่องอื่น/Windows = python ใน venv ของตัวเอง เช่น `%USERPROFILE%\\er-venv\\Scripts\\python.exe`), `S` = โฟลเดอร์ `scripts/` ของ skill นี้
(`~/.claude/skills/git-learn-grouplife-er-diagram/scripts`) — ตั้งใน Bash ทุกครั้งที่เรียก เพราะ shell state ไม่ค้างข้ามคำสั่ง.
**ก่อนใช้ครั้งแรกบนเครื่องใด ให้รัน `$PY $S/check_setup.py`** (ตรวจ package/ฟอนต์/Google token/DB credentials แล้วบอกวิธีแก้ทุกข้อที่ขาด)

## กฎสำคัญ

- **DB read-only เท่านั้น**: ใช้ `db_schema.py` (catalog views + `OBJECT_DEFINITION`) — ห้าม EXEC store ที่กำลังวิเคราะห์,
  ห้าม INSERT/UPDATE/DELETE, ห้ามยิง ad-hoc query แปลก ๆ ตาม `feedback-no-adhoc-queries`. ไม่แนะนำให้อ่านไฟล์
  Doc/db-schema — ให้ดูจาก DB `.52` สด ๆ ตาม `feedback-no-read-dbschema-docs-use-db52`
- **เขียนได้เฉพาะ**: (1) แทรกคอลัมน์ "ER-Diagram" ใน Menu Contents (2) tab `[ER] ...` (3) ลิงก์ใน cell ER-Diagram
  ของแถวเมนูนั้น (4) วันที่ B4 (5) ไฟล์ PNG ใน `ER-Picture` ของ repo (6) **cell "ER-Diagram" ของแถวที่ Sheet ต้นทางที่ชี้มายัง App นี้** (เฉพาะ cell นั้น — ดู Phase 4.5).
  **ห้ามแก้** tab วิเคราะห์เมนูเดิม, ห้ามแตะไฟล์ Template `1wI9_Q-Zw50vLMNbtozKhCpb7ebsLYtmyHUC_1gBnLnY`
  (มันเป็นแค่ตัวอย่างหน้าตาคอลัมน์ ER-Diagram) — ผู้ใช้เคยตอกย้ำเรื่องไม่แก้ scope อื่น `feedback-no-unrelated-scope-edits`
- **เมนูเดิมที่เคยทำ ER แล้ว = UPDATE tab เดิม + cell เดิม** ห้ามสร้าง tab ซ้ำ (`er_write.py` บังคับเอง: ดู gid ใน cell
  ER-Diagram ก่อน แล้วค่อยดูชื่อ tab) — ต้องส่ง `breadcrumb` ให้ตรงกับคอลัมน์ "เมนูงาน" เป๊ะทุกตัวอักษร
- **ห้ามเดาความสัมพันธ์แล้วอ้างว่าเป็นจริง**: DB legacy ชุดนี้มี FK constraint น้อย. ทุก relationship ต้องมี `evidence`
  ระบุที่มา 1 ใน 3 ระดับ: `FK constraint <ชื่อ>` (ชัวร์สุด) / `JOIN ใน <store/view> (ON ...)` / `inferred: ชื่อคอลัมน์ตรงกัน`
  (อ่อนสุด ต้องบอกตรง ๆ) — cardinality ที่ไม่มี PK/unique index ยืนยัน ให้เขียนใน `note` ว่า "ประมาณการ"
- ห้ามอ้างว่า ER ครบถ้ายังไม่ครบ (Store ที่ encrypted/หาไม่เจอ/dynamic SQL อ่านไม่ออก → ระบุใน Phase สรุป)

## ต้นแบบที่ล็อกแล้ว (ผู้ใช้ยืนยัน 2026-09-30: "ยึดเมนูนี้เป็นต้นแบบ ต้องให้ผลแบบนี้เป๊ะ ๆ")

ต้นแบบ = tab `[ER] MainAgentBrokerManage` ของเมนู `"Sales - Setting" => "Agent - Broker"` ใน Sheet
`GroupLifeInsuranceSystem_Center` (https://docs.google.com/spreadsheets/d/1cjtr455CKV1YRpf5p2RcHdn6DCH8M8GY7BB6FIvVGFU, gid ล่าสุดดูจากคอลัมน์
ER-Diagram แถว 9). ทุกเมนูต้องได้ผลหน้าตาเดียวกันทุกอย่าง:
- Tab ชื่อ `[ER] <ชื่อ tab วิเคราะห์เมนู>` วางท้ายสุด; แถว 1-6 = โปรแกรม / Repo URL / Sub Folder / เมนูงาน / วิเคราะห์จาก Tab / วันที่อัพเดท (label พื้นน้ำเงินเข้ม ตัวขาวหนา);
  แถว 8 = หัวข้อ "ER Diagram (รูปด้านล่าง; ...)"; **รูป ER ลอยที่แถว 9** กว้าง ~1100px; ใต้รูป = ตาราง Relationships → ตาราง Store/View → บล็อก Mermaid
- รูป: กล่อง Table (หัวเข้ม + ชื่อ DB ใต้ชื่อ, คอลัมน์ Key | Column | Type, PK ขีดเส้นใต้), view = หัวเทาน้ำเงิน `«view»`, เส้น elbow crow's foot ออกจากแถวคอลัมน์ที่ join,
  ตารางที่เชื่อมมากสุดอยู่กลาง / parent ซ้าย / ลูกขวา — ทั้งหมดมาจาก `er_render.py` อัตโนมัติ
- Menu Contents: คอลัมน์ "ER-Diagram" อยู่ขวา "Sheet URL" (แถวเมนูเดียวกัน)
- **ห้ามปรับ layout/สี/ขนาดใน `er_render.py` / `er_write.py` เอง** ถ้าไม่ได้ขออนุญาตผู้ใช้ก่อน; แก้ได้เฉพาะ bug. ก่อนแก้ให้เทียบกับต้นแบบด้านบน
- ห้ามใช้ `no_image` (กล่องแบบเซลล์) ผู้ใช้ตัดสินแล้วว่าไม่สวย

## รูป ER เก็บใน folder "ER-Picture" (เพิ่ม 2026-09-30)

ไฟล์ PNG ที่ gen ขึ้นมา**ห้ามวางปนกับ Sheet** — เก็บใน Drive: `GroupLife by Claude AI / <Group repo> / ER-Picture / [ER] <tab> (<AppName>).png`
(`<Group repo>` = โฟลเดอร์ที่ spreadsheet ของ App อยู่, เช่น `groupwork-system-2016`). **ทุกโฟลเดอร์ repo ต้องมี** `ER-Picture` — `er_upload_png.py` หาตามชื่อ
ถ้าไม่มีจะสร้างให้เอง (ครั้งเดียวต่อ repo), รันซ้ำเมนูเดิม = เขียนทับไฟล์เดิม ไม่เกิดไฟล์ซ้ำ, ไฟล์เป็นส่วนตัว (ไม่แชร์). `er_write.py` เรียกให้อัตโนมัติ และคืน `picture_url`
— ใส่ลิงก์นี้ในสรุป Phase 5 ด้วย

ใช้กับ **ทุก repo** ใต้โฟลเดอร์หลัก `GroupLife by Claude AI` (id `1lAPvU0Rh5Nm5BZuOvlPrAHxDdAl81LLZ`) ไม่ใช่เฉพาะ `groupwork-system-2016` — ตอนนี้มี `groupwork`,
`claim-work-legacy`, `groupwork-system-2016` (สร้าง `ER-Picture` ครบแล้ว 2026-09-30). ถ้ามี repo ใหม่โผล่ในอนาคต `er_write.py` สร้างโฟลเดอร์ให้เองตอนเขียนเมนูแรก
หรือรัน `$PY $S/ensure_er_folders.py` เพื่อสร้างให้ทุก repo ทีเดียว (idempotent)

## Setup สำหรับคนอื่นที่จะใช้ skill นี้ (Linux / macOS / Windows)

skill แพ็กมาให้แล้ว: ฟอนต์ (`fonts/` DejaVu — รูป ER หน้าตาเหมือนกันทุกเครื่อง เทียบพิกเซลกับต้นแบบแล้วเหมือนกัน), `requirements.txt`, และสคริปต์ที่ใช้ path/encoding แบบข้าม OS
(`Path.home()`, UTF-8 ทุก stdin/stdout/ไฟล์ JSON — ภาษาไทยไม่พังบน Windows). ที่**ต้องตั้งเองต่อเครื่อง** (ห้ามข้าม/ห้ามเดา — รัน `check_setup.py` แล้วทำตามที่มันบอก):
1. **Python 3.9+ + venv**: `python -m venv <dir>` แล้ว `<dir>/bin/pip install -r requirements.txt` (Windows: `<dir>\\Scripts\\pip.exe`)
2. **Google token** `~/.config/claude-google-access/token.json` (Windows: `%USERPROFILE%\\.config\\claude-google-access\\token.json`; หรือชี้ด้วย env `GROUPLIFE_GOOGLE_TOKEN`)
   scope `spreadsheets` + `drive`; บัญชีต้องเป็น Editor ของโฟลเดอร์ Drive "GroupLife by Claude AI". สร้างตาม `reference-claude-google-access-oauth` — ขอ `client_secret.json`
   จากเจ้าของ skill (ไม่อยู่ใน skill เพราะเป็นความลับ) แล้วรัน authorize ครั้งเดียว
3. **DB login** `~/.config/grouplife-db/credentials.json` (หรือ env `GROUPLIFE_DB_CREDENTIALS`) รูปแบบ
   `{"10.100.2.52": {"user": "...", "password": "..."}, "10.100.3.139": {...}, "12.100.7.22": {...}}` — **ไม่อยู่ใน skill โดยตั้งใจ (ห้ามใส่รหัสผ่านลง skill/repo ที่แชร์)**
   ขอจากผู้ดูแล DB ของทีม; Linux/Mac ตั้ง `chmod 600`. ต้องต่อเครือข่ายภายใน (VPN) ถึง DB ได้; ถ้าเชื่อมไม่ได้ ให้แจ้งผู้ใช้ ห้ามสร้าง ER จากการเดาโครงสร้าง
   (บน Windows `pymssql` ติดตั้งจาก wheel ได้ ถ้าติดตั้งไม่ผ่านให้แจ้งผู้ใช้ ไม่ต้องหาทางอ้อมเอง)

## Phase 1 — resolve App → หา spreadsheet

ผู้ใช้ระบุชื่อ App (argument) — ถ้าไม่ระบุให้ถามชื่อ App ก่อน. ค้นใน Drive (ไม่ต้องผ่านชีตติดตาม repo):

```bash
$PY $S/find_app_sheet.py "<คำค้นชื่อ App>"
```
- **0 ผลลัพธ์**: แจ้งว่ายังไม่เคยวิเคราะห์ App นี้ → แนะนำ `/git-learn-grouplife-system-analyst` ก่อน (skill นี้ต้องมี
  Sheet วิเคราะห์อยู่แล้ว). **ห้ามนับไฟล์ `Template`** (อยู่ที่ root ไม่ใช่ App จริง)
- **1 ผลลัพธ์**: ยืนยันชื่อ (Group/AppName + ลิงก์) กับผู้ใช้สั้น ๆ
- **>1**: โชว์ Group+ชื่อ ให้เลือกเจาะจง (AskUserQuestion) — ห้ามเดา

## Phase 2 — list "เมนูงาน" ให้เลือกเป็น checkbox

```bash
$PY $S/read_menus.py list <spreadsheet_id>
```
ได้ `menus[]` (breadcrumb, description, sheet_url/gid/tab_title, `er_url`). **ใช้ AskUserQuestion จริง**
(checkbox `multiSelect: true` เหมือน `/git-learn-grouplife-system-analyst` Phase 4): แบ่งชุดละ ≤4 ตัวเลือก,
≤4 คำถามต่อการเรียก 1 ครั้ง (≤16 ต่อครั้ง), มากกว่านั้นเรียกหลายรอบแล้วรวมผล; `header` เช่น "เมนู 1-4";
ใส่ breadcrumb เต็มใน `label`/`description`. เมนูที่ `er_url` ไม่ว่าง (เคยทำ ER แล้ว) ให้ติดหมายเหตุ
"มี ER อยู่แล้ว — จะอัพเดททับ". ข้ามเมนูที่ไม่มี tab วิเคราะห์ (`gid` เป็น null) และแจ้งผู้ใช้.
ถ้ารายการมีมากกว่า ~16 ให้ถามเป็นรอบ ๆ แต่ไม่ต้องแยกหมวด (รายการมันแบนอยู่แล้ว).

**ถ้าเลือก ≥2 เมนู** ให้ถามโหมดรัน (AskUserQuestion, `multiSelect:false`, header "โหมดรัน") เหมือน analyst Phase 4.5:
"Break point ทีละเมนู (Recommended)" (ทำ 1 เมนู เขียน Sheet จบ แล้วหยุดรอผู้ใช้พิมพ์ `continue`; สรุปท้ายรอบต้องมีรายการ
เมนูที่เหลือ + spreadsheet_id เพื่อ resume) / "รันทุกเมนูรวดเดียว" (Agent ขนานได้ แต่เขียน Sheet ทีละเมนูตามลำดับ). ถามใหม่ทุกครั้ง.

## Phase 3 — วิเคราะห์ ER (Agent 1 ตัวต่อ 1 เมนู; read-only)

ต่อเมนูที่เลือก เรียก `Agent` (subagent_type ปกติ **ไม่ใช้ fork**; ตัวเลือกโมเดลตามที่ผู้ใช้ตั้ง — งานนี้ต้องอ่าน SQL
ซับซ้อน จึงไม่ต้องบังคับ Haiku) ส่ง prompt ที่ต้องมีครบ (agent เริ่มจาก context ว่าง): `spreadsheet_id`, `gid` ของ tab เมนู,
breadcrumb, path ของ scripts + venv python, กฎ read-only/evidence ข้างบน, และขั้นตอนต่อไปนี้ให้ทำเอง:

1. **อ่าน tab วิเคราะห์**: `$PY $S/read_menus.py tab <spreadsheet_id> <gid>` → เก็บทุกแถวที่คอลัมน์ `DB` /
   `Call Store` ระบุ object (ชื่อ Table, View, Stored Proc — Call Store เป็นข้อความอิสระ เช่น
   "UPDATE OGL_AgentBrokerHD SET STATUS=1 ...", "Stored proc: OGL_ListAgentBrokerHD_NewSW", "Query: SELECT ... FROM A LEFT JOIN B").
   คอลัมน์ `DB` เป็นชื่อฐาน (OGL / OceanLife / DataOne ฯลฯ ที่อาจมี "(ConnOGL)" หรือ "OGL + OceanLife" ต่อท้าย → หลาย DB ต้องเช็คทีละ DB).
   อ่าน description + `manual_steps` ประกอบเพื่อเข้าใจว่า object ไหนเป็นตารางหลัก/ตาราง log/ตาราง master.
2. **จัดประเภท object** ด้วย `db_schema.py` (ip = `10.100.2.52` เป็นค่าเริ่มต้น; ไม่เจอค่อยลอง `10.100.3.139`;
   DB ตามคอลัมน์ `DB`, ชื่อ DB จริงคือ `OGL`/`OceanLife`/`DataOne`):
   ```bash
   $PY $S/db_schema.py 10.100.2.52 OGL <object1> <object2> ...
   ```
   - **table** → ได้ columns/PK/FK constraint/`referenced_by`/unique indexes
   - **view / proc / function** → ได้ `definition` (source เต็ม) + `depends_on`. **ต้องอ่าน code ทั้งหมด** แล้วไล่:
     `FROM`/`JOIN ... ON` (ได้คู่คอลัมน์ที่ใช้เชื่อม), `INSERT INTO`/`UPDATE`/`DELETE FROM`/`MERGE` (Table ที่ถูกเขียน),
     temp table (`#x`) ที่เกิดจาก Table จริง, proc ที่เรียกซ้อน (`EXEC other_sp` → ดึง `definition` ของมันมาอ่านต่อ ลึกได้ ~3 ชั้น),
     view ที่ join ซ้อน (ขยาย view เป็น Table ต้นทาง). Table ที่อยู่คนละ DB (`OceanLife.dbo.X`) ให้เรียก `db_schema.py` อีกรอบด้วย DB นั้น.
   - `not_found` → ลองชื่อสะกด/schema อื่น หรือรายงานว่าหาไม่เจอ (อย่าเดาโครงสร้าง)
3. **อ่านคำอธิบายคอลัมน์เสริม (ถ้าจำเป็น)** ด้วย `/datadic-grouplife` (`Skill` tool ชื่อ `datadic-grouplife`, หรือ
   `dd_index.py`/`dd_detail.py` ใน `~/.claude/skills/datadic-grouplife/scripts/`) ให้ได้ความหมายธุรกิจของคอลัมน์ key/สถานะ
   — ใช้เมื่อชื่อคอลัมน์ไม่สื่อ (`Status`, `FlagX`) เท่านั้น ไม่ต้อง dump ทั้ง dictionary.
4. **ตัดสิน relationship + cardinality** (ทำเป็นคู่ ๆ):
   - แหล่งหลักฐานเรียงตามน้ำหนัก: FK constraint > `JOIN ON` ใน store/view > ชื่อคอลัมน์ตรงกัน+type เดียวกัน (inferred)
   - Cardinality แต่ละปลาย ∈ `1` | `0..1` | `1..N` | `0..N`:
     - ฝั่งที่ join ด้วย **PK ทั้งชุดหรือ unique index** ของตัวเอง = ปลาย `1` (ถ้าฝั่ง FK เป็น nullable → ปลาย parent เป็น `0..1`)
     - ฝั่งที่ถือ FK ธรรมดา (ไม่ unique) = ปลาย `0..N` (หรือ `1..N` ถ้ามีเงื่อนไขว่าต้องมีลูกอย่างน้อย 1 จากโค้ด/คำอธิบาย)
     - FK ที่ตัวเองเป็น PK/unique ของตารางลูกด้วย = **one-to-one**
     - ตารางกลาง (junction) ที่มี FK 2 ตัวไป 2 ตาราง (และ PK/unique = คู่ FK นั้น) = **many-to-many** ระหว่างสองตารางนั้น → ให้วาด
       เป็น 2 relationship 1:N เข้าตารางกลาง + ระบุใน `note` ว่าเป็น N:M ผ่านตารางกลาง
   - ระบุใน `from`=ฝั่งถือ FK (ลูก), `to`=ฝั่ง parent; `from_card` = จำนวนที่ฝั่ง from ต่อ 1 แถวของ to.
     ตัวอย่าง "หลายเอกสารต่อ 1 ตัวแทน": `from`=OGL_AgentBrokerHD, `to`=OGL_Agent, `from_card`="0..N", `to_card`="1"
5. **เลือกคอลัมน์ที่จะโชว์ในกล่อง** (ต่อ entity ≤ ~12 คอลัมน์): PK ทุกตัว + FK ทุกตัวที่เกี่ยวกับ relationship + คอลัมน์ที่เมนูนี้
   เขียน/อ่านจริงจาก store/component (Status, วันที่, จำนวนเงิน ฯลฯ). `key`: `PK`, `FK1`/`FK2`..., `PK,FK1`, หรือ `""`;
   `type` ใส่พร้อมขนาด เช่น `varchar(20)`. **เรียง entity** ให้ตารางที่สัมพันธ์กันอยู่ติดกัน (ตารางหลักก่อน → ลูก → master/lookup)
   เพราะ ตัววาดรูปจัดวางเอง (ตารางที่เชื่อมมากสุดอยู่กลาง, parent ซ้าย, ลูกขวา) — ลำดับ entity ไม่มีผลกับรูป. view ให้ `kind:"view"`. ตารางที่เมนูใช้แค่ขอบ ๆ (เช่น log) ยังใส่ได้แต่คอลัมน์น้อย ๆ
6. **objects**: สรุปทุก Store/View ที่เมนูเรียก — `name`, `kind` ("Stored Proc"/"View"/"Function"), `db`, `tables` (เช่น
   `OGL_AgentBrokerHD (R/W), Branch (R)`), `summary` 1–2 บรรทัดภาษาไทยว่าทำอะไรกับ Table ไหน

**Agent ห้ามเขียน Sheet เอง** — return JSON เดียวตรง schema ของ `er_write.py` (ดู docstring ในไฟล์นั้น; **ไม่ต้องใส่**
`spreadsheet_id`, `program_name`, `repo_url`, `sub_folder`, `today` — orchestrator เติมเอง) พร้อมรายการ "จุดที่ยังไม่แน่ใจ / วิเคราะห์ไม่ครบ"
(เช่น dynamic SQL, store encrypted, Table ที่หาไม่เจอ, relationship ที่เป็น inferred).

## Phase 4 — เขียนลง Sheet (ทีละเมนู ห้ามขนาน)

ก่อนเขียนให้ดึง `program_name`/`repo_url`/`sub_folder` จาก `read_menus.py list` (คืนมาแล้ว) แล้วเติม `today` (YYYY-MM-DD วันนี้),
`spreadsheet_id`, `breadcrumb` ให้ครบ:

```bash
echo '<JSON payload>' | $PY $S/er_write.py
```
`er_write.py` ทำให้ตามลำดับ: (1) ถ้า Menu Contents ยังไม่มีหัวคอลัมน์ "ER-Diagram" จะ **แทรกคอลัมน์ใหม่ทางขวาของ "Sheet URL"**
(คอลัมน์เดิมเช่น "การใช้งาน" ขยับไปขวา; ทำแค่ครั้งเดียว, สไตล์เหมือนหัวตารางอื่น) (2) สร้าง/เขียนทับ tab `[ER] <ชื่อ tab เมนูวิเคราะห์>`
(3) ใส่ลิงก์ tab ลง cell "ER-Diagram" **แถวเดียวกับเมนู** (4) อัพเดทวันที่ B4. คืน `tab_url` และ `picture_url` (ไฟล์ใน ER-Picture) — เก็บไว้สรุป.

หน้าตา tab `[ER] ...` (แก้ 2026-09-30 หลังผู้ใช้ดูแบบกล่องเซลล์แล้วว่าไม่สวย): แถว 1-6 = ข้อมูลหัวเรื่อง; **รูป ER (PNG) ลอยที่แถว 9**
(วาดด้วย `er_render.py` — กล่องหัวเข้ม, PK ขีดเส้นใต้, view เป็นสีเทาน้ำเงิน, เส้น crow's foot ออกจากแถวคอลัมน์ที่ join จริง);
**ใต้รูป** = ตาราง Relationships (From.col | Cardinality | To.col | Notation | หลักฐาน), ตาราง Store / View ที่เกี่ยวข้อง และบล็อก Mermaid erDiagram.
เรียงลำดับในสคริปต์อัตโนมัติ: `er_write.py` เรียก `er_render.py` (payload เดียวกัน → PNG) แล้วเรียก `er_insert_image.py` สร้าง tab ที่มีรูป
(แทนที่ tab เดิมถ้ามี — gid เปลี่ยน แต่ er_write อัพเดทลิงก์ให้เอง) แล้วเขียนตารางต่อ. ไม่ต้องให้ผู้ใช้ Insert > Image เอง

**กลไกใส่รูป (สำคัญ ห้ามเปลี่ยนไปใช้ทางอื่นโดยไม่ทดสอบ)**: Sheets/Drive API แทรกรูปตรง ๆ ไม่ได้ และ token ไม่มี scope Apps Script
(การรัน Apps Script ผ่าน API ก็ต้องผูก GCP project เองด้วยมือ) จึงใช้ทาง: สร้าง .xlsx ที่มีรูปยึดกับเซลล์ (openpyxl) → อัพโหลดแปลงเป็น Google Sheet
ชั่วคราว → `spreadsheets.sheets.copyTo` เข้า spreadsheet เป้าหมาย → rename → ลบไฟล์ชั่วคราวลง trash. ไม่ต้องแชร์ไฟล์สาธารณะ (ไม่ใช้ `=IMAGE()` /
anyone-with-link). ทดสอบแล้ว 2026-09-30 ด้วย Sheet ทดลอง + เมนู Agent - Broker ของ GroupLifeInsuranceSystem_Center.
ถ้าไม่ต้องการรูป ใส่ `"no_image": true` ใน payload จะได้กล่องแบบเซลล์เดิม (ไม่แนะนำ). ดู PNG ก่อนเขียนได้ด้วย
`$PY $S/er_render.py payload.json out.png`

## Phase 4.5 — แปะลิงก์ ER กลับที่ Sheet ต้นทาง (เพิ่ม 2026-10-01 ตามฟีดแบ็กผู้ใช้)

**เมื่อไหร่**: App ที่เพิ่งทำ ER เป็น **โปรแกรมภายนอกที่ถูกเรียกด้วย WinExec จาก App อื่น** (ต้นทาง เช่น OGL_Benefits) ซึ่ง
`/git-learn-grouplife-system-analyst` ได้ "stamp" แถวหนึ่งไว้ใน Menu Contents ของต้นทางแล้ว โดยคอลัมน์ `Sheet URL` ของแถวนั้นชี้ไปยัง
spreadsheet/tab ของ App ปลายทาง (คอลัมน์ Delphi Path File ขึ้นต้นด้วย `WinExec ->`). แถวแบบนี้ไม่มี tab รายละเอียดในไฟล์ต้นทาง
ถ้าไม่แปะลิงก์ ER กลับ คนที่เปิดสารบัญของต้นทางจะเห็นช่อง ER-Diagram ว่าง ทั้งที่ ER อยู่อีกไฟล์ — **ทำทุกครั้งหลัง `er_write.py` ของ App ปลายทาง
สำเร็จ** (ผู้ใช้สั่งให้เป็นแนวทางเดียวกันสำหรับทุกคนที่เรียก skill นี้)

```bash
$PY $S/er_stamp_origin.py <origin_spreadsheet_id> <app_spreadsheet_id> [--dry]
```
- `<origin_spreadsheet_id>` = spreadsheet ของ App ต้นทางที่เรียก exe นี้ (ถ้าไม่ทราบให้ถามผู้ใช้ หรือหาจาก Menu Contents ที่มีแถว `WinExec -> <exe>`
  ของ App ที่เป็นเมนูหลักอย่าง OGL_Benefits ด้วย `find_app_sheet.py`) — ห้ามเดา; `<app_spreadsheet_id>` = spreadsheet ที่เพิ่งเขียน ER
- สคริปต์จับคู่แถวต้นทางด้วย **ลิงก์ `Sheet URL` ที่มี `/d/<app_spreadsheet_id>/`** (ไม่เดาจากชื่อ exe) แล้วเขียน**เฉพาะ cell ER-Diagram ของแถวเหล่านั้น**
  ด้วยรูปแบบเดียวกับ er_write.py (ข้อความ URL + hyperlink). exe เดียวถูกเรียกจากหลายเมนูได้ (หลายแถว) — จะแปะทุกแถว
- เขียนทับเฉพาะเมื่อค่าต่างจากเดิม: `er_write.py` สร้าง tab `[ER]` ใหม่ทุกครั้ง gid จึงเปลี่ยน ลิงก์เก่าจะเสีย → **รันซ้ำหลังทุกครั้งที่ทำ ER ซ้ำ**
- ถ้าต้นทางยังไม่มีคอลัมน์ ER-Diagram สคริปต์แทรกให้เอง; ถ้า App ปลายทางยังไม่มี ER หรือไม่มีแถวต้นทางชี้มา จะบอกตรง ๆ และไม่เขียนอะไร
- ต้นทางหลายไฟล์ (App หลายตัวเรียก exe เดียวกัน): รันสคริปต์ทีละต้นทาง; ห้ามรันขนานกับไฟล์ต้นทางเดียวกัน
- ไม่ต้องทำขั้นนี้ถ้า App ที่ทำ ER เป็นโปรแกรมหลักเอง (ER ของเมนูภายในไฟล์เดียวกัน er_write.py ผูกลิงก์ที่แถวเมนูให้แล้ว)

## Phase 5 — สรุปให้ผู้ใช้

- ลิงก์ Menu Contents ของ App + ลิงก์ tab `[ER] ...` + ลิงก์ไฟล์รูปใน `ER-Picture` ของแต่ละเมนู (และบอกว่าแทรกคอลัมน์ ER-Diagram ใหม่หรือ update ทับ)
- ถ้ามี Phase 4.5: บอกว่าแปะลิงก์กลับที่ Sheet ต้นทางตัวไหน กี่แถว (เลขแถว) หรือเพราะอะไรจึงข้าม
- ต่อเมนู สรุป 2–4 บรรทัด: Table หลักที่ใช้เก็บข้อมูล + ความสัมพันธ์เด่น ๆ (เช่น "OGL_AgentBrokerHD 1:N …")
- ระบุตรง ๆ: relationship ไหนเป็น `inferred`, Store/View ไหนอ่านไม่ครบ, Table ไหนหาไม่เจอ — **ห้ามอ้างครบถ้ายังไม่ครบ**
- ไม่ต้อง commit/push อะไร (skill นี้ไม่เกี่ยวกับ git)
