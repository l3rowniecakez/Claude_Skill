---
installer: create-shortcut
name: git-learn-grouplife-speckit
description: 'ทำเอกสาร requirement ราย "หน้าจอ" (/STANDARD_REQ_TEMPLATE_v1_1) ย้อนหลังจากโปรแกรมกลุ่มประกันกลุ่ม (Delphi) ที่พัฒนาเสร็จแล้ว ต่อยอดจาก Google Sheet ที่ /git-learn-grouplife-system-analyst และ /git-learn-grouplife-er-diagram ทำไว้ — ผู้ใช้ระบุ App แล้วเลือกเมนูเป็น checkbox, skill สร้างโฟลเดอร์ต่อ repo/App/เมนูใน Drive "GroupLife SpecKit by Claude AI" (id 1MHYE71oBUdH70DwdoIP-n1CQ_nzvrSfL), แปะ URL ลง Sheet (คอลัมน์ "SpecKit" ต่อจาก "ER-Diagram" + แถว "Speckit URL" ในหัว Sheet) แล้วถอด REQ 1 ไฟล์ต่อ 1 หน้าจอจาก code จริง 100% (ห้ามเดา ห้ามแก้ code). ไม่เรียก /speckit-*. Use when user says "/git-learn-grouplife-speckit", ต้องการทำ REQ/เอกสาร requirement ของเมนูงานโปรแกรมกลุ่มประกันกลุ่มที่เขียนเสร็จแล้ว.'
created_at: 2026-10-20T00:00:00+07:00
argument-hint: "[ชื่อ App]"
---

# /git-learn-grouplife-speckit — ทำ REQ ราย "หน้าจอ" ย้อนหลังจากระบบที่เขียนเสร็จแล้ว

ต่อยอดจาก `/git-learn-grouplife-system-analyst` (Sheet วิเคราะห์เมนูต่อ App) และ `/git-learn-grouplife-er-diagram` (แท็บ `[ER]`):
ต่อเมนูที่เลือก skill นี้ถอด **requirement เป็นไฟล์ `REQ_<SCR-ID>_<unit>.md` 1 ไฟล์ต่อ 1 หน้าจอ** ตาม `/STANDARD_REQ_TEMPLATE_v1_1`
แล้วเก็บลง Drive. **ไม่เรียก `/speckit-*` ใด ๆ** (ผู้ใช้ตัดออก 2026-10-20 เพราะมากเกินความต้องการ).

ระบบนี้เขียนเสร็จแล้ว — เป็นการถอดระบบที่มีอยู่ (as-built) ไม่ใช่การวางแผนระบบใหม่. กฎที่ผู้ใช้ล็อกไว้:
**เอกสารต้องตรงกับ code ปัจจุบัน 100% — ห้ามคาดเดา — ห้ามแก้ไข code ใด ๆ ทั้งสิ้น**

อ่านก่อนลงมือ: `references/agent-prompts.md` (prompt ของ Agent A เขียน REQ / Agent C ผู้ตรวจ — orchestrator ต้องใช้ส่งต่อ).
**orchestrator ไม่ต้อง Read `references/req-mapping.md`** (วิธีกรอก template ราย Section + Evidence Map) — Agent A เป็นคนอ่านเอง (prompt สั่งไว้แล้ว) ยกเว้นต้องตัดสินใจเรื่อง SCR-ID/รูปแบบเอง.

ตัวแปร: `PY` = python ที่ติดตั้ง `requirements.txt` (เครื่องเจ้าของ skill = `~/.config/redmine-summary-to-email/venv/bin/python3`; เครื่องอื่น = venv ของตัวเอง),
`S` = `~/.claude/skills/git-learn-grouplife-speckit/scripts` — ตั้งใหม่ทุกคำสั่ง Bash. Workspace ในเครื่อง = `<WORKDIR>/<Group>/<AppName>`
(`WORKDIR` = `$GROUPLIFE_SPECKIT_WORKDIR` หรือ `~/grouplife-speckit`).

## กฎเหล็ก

1. **อ่านอย่างเดียวกับ source/DB/Gitblit** (Gitblit web GET, DB catalog SELECT ผ่าน `db_schema.py`; ไม่ EXEC proc, ไม่ INSERT/UPDATE/DELETE, ไม่ยิง query แปลก ๆ).
   ห้าม clone/commit/push/แก้ repo; ห้ามรันโปรแกรม Delphi. `source/` ใน workspace = snapshot `chmod 444` ไม่อัปโหลดขึ้น Drive.
2. **เขียนได้เฉพาะ**: workspace ในเครื่อง; Drive ใต้ "GroupLife SpecKit by Claude AI"; Sheet ของ App = คอลัมน์ `SpecKit`, `A5/B5` ("Speckit URL"), `B4` (วันที่)
   — ห้ามแตะ tab วิเคราะห์/tab [ER]/คอลัมน์ ER-Diagram/ไฟล์ Template. ห้ามลบอะไรบน Drive เว้นแต่ผู้ใช้สั่ง.
3. **ห้ามเดา — บังคับด้วยเครื่องตรวจ**: REQ ทุกไฟล์มี Evidence Map (คำพูดตรงตัวจากไฟล์ใน `source/` + บรรทัด) และ `scripts/verify_evidence.py` ต้อง `fail_count = 0`
   ก่อนอัปโหลด. สิ่งที่ code ตอบไม่ได้ = Open Issue (Section 9) ไม่ใช่ค่าที่คิดเอง; ข้อเท็จจริงนอก source (ความหมายมาตรฐาน T-SQL/VCL ฯลฯ) ต้องติดป้ายบอกที่มา.
4. **Sheet analyst เป็นแผนที่ ไม่ใช่หลักฐาน** — ขัดกับ code เมื่อไหร่ code ชนะ + แจ้งความต่างให้ผู้ใช้.
5. **เมนูเดิม = UPDATE ทับ** (โฟลเดอร์/ไฟล์ชื่อเดิมบน Drive ถูกอัปเดต ไม่สร้างซ้ำ; ไฟล์ที่ไม่มีในรอบนี้รายงานเป็น `stale` ไม่ลบเอง) — ผู้ใช้ที่เลือกเมนูที่ "มี SpecKit แล้ว" ถือว่ายอมรับการ regenerate.
6. ห้ามใช้ Haiku กับ Agent ของ skill นี้ — งานต้องแม่นยำ.

## Phase 0 — Preflight

```bash
PY=...; S=~/.claude/skills/git-learn-grouplife-speckit/scripts
$PY $S/check_setup.py
```
ตรวจ python package, skill ที่พึ่ง (`git-learn-grouplife`, `…-system-analyst`, `…-er-diagram`, `STANDARD_REQ_TEMPLATE_v1_1`), Google token (spreadsheets+drive; Editor ของโฟลเดอร์
"GroupLife by Claude AI" และ "GroupLife SpecKit by Claude AI"), Gitblit credentials, DB credentials.
- **ขาด skill** → ติดตั้งด้วย `/ocean-skill-update` (เลือก "เลือกเฉพาะบาง Skill" ตามชื่อที่ check_setup.py พิมพ์). ไม่มีใน repo → หยุดแจ้งผู้ใช้ — ห้ามหาทางอื่นดาวน์โหลดเอง.
- **ขาด credentials/token** → บอกวิธีตามที่ check_setup.py พิมพ์ ห้ามเดา/สร้างเอง. มีข้อ MISSING ที่ยังไม่แก้ → หยุด.

## Phase 1 — หา Sheet ของ App

```bash
$PY $S/find_app_sheet.py "<คำค้น>"     # ต้องมีคำค้นเสมอ — ห้ามส่ง "" (จะลิสต์ทุก App หลายร้อยรายการ)
```
0 ผลลัพธ์ → แนะนำ `/git-learn-grouplife-system-analyst` ก่อน (ไม่นับไฟล์ `Template`); 1 → ยืนยันสั้น ๆ; >1 → AskUserQuestion ให้เลือก (ห้ามเดา).
จากนั้น `read_menus.py list <spreadsheet_id>` → `program_name`, `repo_url` (ตัด `<repo>` ระหว่าง `/delphi/` กับ `.git`), `sub_folder`, `menus[]`.
(Sheets API จำกัด 60 read/นาที — ถ้าต้องอ่านหลาย tab พร้อมกัน ใช้ `values.batchGet` ไม่ใช่เรียก `read_menus.py tab` วนทีละ tab.)

## Phase 2 — เลือกเมนู

AskUserQuestion แบบ `multiSelect: true` (≤ 4 ตัวเลือก/คำถาม, ≤ 4 คำถาม/ครั้ง, >16 → หลายรอบ; `header` เช่น "เมนู 1-4").
- ตัวเลือก = เมนูระดับบน (`is_child = false`) ที่มี tab วิเคราะห์ (`gid` ไม่ null) และไม่ใช่แถว WinExec (`external_spreadsheet_id` ว่าง) และเป็นหน้าจอจริง
  (ตัดแถวที่ analyst บันทึกว่า "ไม่มีฟอร์มปลายทาง/ไม่พบ handler"). แถวลูก (`descendant_rows`) ถือเป็นหน้าจอเพิ่มของเมนูแม่อัตโนมัติ.
- ติดหมายเหตุ: `speckit_url` ไม่ว่าง → "มี SpecKit แล้ว — จะ regenerate ทับ"; `er_url` ว่าง → "ยังไม่มี [ER]". ใส่ขนาด (จำนวน component/store/ขั้นตอนใน tab วิเคราะห์) ช่วยผู้ใช้เลือกเมนูเล็ก.
- เลือก ≥ 2 เมนู → ถามโหมดรัน (`multiSelect:false`, ถามใหม่ทุกครั้ง): **Break point ทีละเมนู (Recommended)** (จบ 1 เมนูหยุดรอ `continue`; สรุปท้ายรอบมีรายการเมนูที่เหลือ + spreadsheet_id/Group/AppName/repo/sub_folder เพื่อ resume) / **รันรวดเดียว**.

## Phase 3 — สร้างโฟลเดอร์ Drive แล้ว**แปะ URL ลง Sheet ก่อนเริ่มทำเอกสาร**

Drive: `GroupLife SpecKit by Claude AI / <Group repo> / <AppName> / <NNN>-<TabTitle> / req/…` — `FEATURE` = `<No 3 หลัก>-<tab_title>` (อักขระนอก `A-Za-z0-9._-` → `_`).
```bash
$PY $S/speckit_drive.py ensure-app "<Group>" "<AppName>"            # -> app_folder_id/url
$PY $S/speckit_drive.py ensure-feature <app_folder_id> "<FEATURE>"   # ต่อเมนู -> feature_folder_id/url
echo '[{"breadcrumb":"<เมนูงาน เป๊ะ>","url":"<feature_folder_url>"}, ...]' | $PY $S/sheet_speckit.py menus <spreadsheet_id> <YYYY-MM-DD>
$PY $S/sheet_speckit.py header <spreadsheet_id> "<app_folder_url>" <YYYY-MM-DD>
```
- `menus` แทรกคอลัมน์ **"SpecKit" ทางขวาของ "ER-Diagram"** (ครั้งเดียว) แล้วใส่ URL โฟลเดอร์เมนู — แถวหน้าจอลูก (`descendant_rows`) ใส่ URL เดียวกัน; breadcrumb ต้องตรงคอลัมน์ "เมนูงาน" เป๊ะ.
- `header` เขียน "Speckit URL" + URL โฟลเดอร์ App ที่ **แถว 5 (A5/B5)** — แถวที่ว่างอยู่ เพราะ skill พี่น้องทุกตัวผูก "หัวตาราง = แถว 6, ข้อมูลเริ่มแถว 7" (แทรกแถวใหม่ = ตารางเลื่อน แล้วพังหมด). A5 มีข้อความอื่น → สคริปต์หยุดไม่เขียน.
- แจ้งผู้ใช้ลิงก์โฟลเดอร์ก่อนเริ่มทำเอกสาร.

## Phase 4 — ทำทีละเมนู (Break point: หยุดหลังแต่ละเมนู)

0. **Shared notes (ครั้งเดียวต่อ App, ไม่ใช้ LLM)** — ถ้ายังไม่มี `<WS>/_shared.md`: ดึง `Utility.pas`/`MainUnit.pas`/DataModule ด้วย `fetch_source.py files`, ดู `scan_form.py pas <ไฟล์>` หา method ตัวเปิดฟอร์มกลาง
   (เช่น `OpenFormMenu`, `OpenModalForm`, `FindShowForm`, `FindShowModalForm`) แล้ว `$PY $S/scan_form.py body <ไฟล์> <Method…> >> <WS>/_shared.md` (เนื้อ method ตรงตัว + เลขบรรทัดจริง; ไม่มีชื่อนั้นใน App อื่น = พิมพ์ NOT FOUND ให้ข้าม).
   Agent A อ่านไฟล์นี้แทนการอ่าน unit กลางซ้ำทุกหน้าจอ; ไฟล์นี้ไม่ใช่ evidence และไม่อัปโหลด.
1. `$PY $S/init_workspace.py init "<Group>" "<AppName>"` (ครั้งแรก) แล้ว `$PY $S/init_workspace.py feature "<Group>" "<AppName>" "<FEATURE>"` → `specs/<FEATURE>/req/`.
2. **ไล่หน้าจอแบบ BFS (ผู้ใช้กำหนด 2026-10-20: เจอฟอร์มลูก/ลิงก์ไปฟอร์มอื่นต้องทำด้วย ไม่ต้องถามเพิ่ม)**
   - คิวเริ่มต้น = หน้าจอของเมนู (แถวเมนู + `descendant_rows` จาก Sheet), `DEPTH` = 0; `VISITED` = unit (ชื่อ .pas ตัวพิมพ์เล็ก) ที่มี REQ แล้ว — รวมของเมนูอื่นใน `WS/specs/*/req/REQ_*.md` (grep บรรทัด `unit:` ใน META).
   - ต่อ 1 หน้าจอ: **Agent A (REQ writer)** 1 ตัว (`references/agent-prompts.md`; หน้าจอลูกเล็กที่ใช้ unit ร่วมกันรวมเป็นตัวเดียวได้ แต่ได้ REQ 1 ไฟล์/หน้าจอเหมือนเดิม) — ดึง source/DB เป็น snapshot, **ไล่หาทุกจุดที่เปิดฟอร์ม/โปรแกรมอื่น (บังคับ)**, เขียน `req/REQ_<SCR-ID>_<unit>.md`, วน `verify_evidence.py` จน `fail_count = 0` → ได้ `child_forms`, `external_programs`, `opener`.
   - ทุก `child_forms` ที่ unit ยังไม่อยู่ใน VISITED → ใส่คิว (`DEPTH`+1) ทำ Agent A ต่อโดยไม่ถามผู้ใช้; ที่อยู่ใน VISITED → แค่ลิงก์; หลายลูกในชั้นเดียวกันเรียก Agent ขนานได้ (เขียนไฟล์คนละไฟล์) แต่ verify/upload ทีละตัว.
   - จำกัดความลึก **5 ชั้น** — เกินแล้วหยุดและรายงานผู้ใช้ว่าชั้นไหนยังไม่ได้ไล่. `external_programs` (WinExec/คนละ exe) ไม่ไล่ต่อ รายงานผู้ใช้ (ถ้าต้องการให้รัน skill กับ App ปลายทาง).
   - เสร็จทุกหน้าจอ → เขียน/อัปเดต `req/README.md` (สารบัญ + ต้นไม้ "หน้าจอแม่ → ปุ่ม → หน้าจอลูก" + โปรแกรมภายนอก + opener).
   - **ถ้าฟอร์มลูกที่พบไม่มีแถวใน Menu Contents** → ใช้ SCR-ID ตามกฎใน `references/req-mapping.md`; แจ้งผู้ใช้ในสรุปว่า Sheet analyst ตกหล่นฟอร์มนี้ (ควรรัน analyst เติม).
3. **Gate 1** — รัน `$PY $S/fill_evidence.py <WS> <FEATURE>` แล้ว `$PY $S/verify_evidence.py <WS> <FEATURE>` เองซ้ำ (อย่าเชื่อรายงาน agent) และอ่านเฉพาะ `fail_count`/รายการ fail — ไม่ต้อง Read ไฟล์ REQ เข้า context orchestrator; ไม่ผ่าน → ส่งกลับให้ A แก้ (≤ 2 รอบ) ไม่ผ่านอีก = หยุดเมนูนั้นและรายงานตรง ๆ.
4. **Gate 2 — Agent C (ผู้ตรวจอิสระ)** เทียบ REQ **ทุกหน้าจอของเมนู** กับ `source/` ทุกข้อ **และ grep หาปุ่ม/handler ที่เปิดฟอร์มอื่นที่ REQ ไม่ได้บันทึก** (บทเรียนจริง: verify_evidence ผ่านแต่ผู้ตรวจพบเลขบรรทัดผิด/ข้ออ้างเกิน code/พฤติกรรมตกหล่น)
   → แก้ REQ ตามผล (เปิดไฟล์ยืนยันก่อนแก้ทุกข้อ; ฟอร์มลูกที่ตกหล่น = กลับไปทำ Agent A ต่อ) → จด ID ที่แก้เป็น `CHANGED` → fill+verify ซ้ำ → รอบ 2–3 ส่ง `CHANGED` ให้ C (ต่อตัวเดิมด้วย `SendMessage` หรือตัวใหม่ก็ได้ — ตรวจเฉพาะส่วนที่แก้) จนว่าง (≤ 3 รอบ; รอบ 1 ตรวจเต็มเสมอ). ไม่หมด = รายงานรายการค้างตรง ๆ — **ห้ามอ้างว่าตรง 100% ถ้ายังไม่ผ่าน**.
5. **อัปโหลด**: `$PY $S/speckit_drive.py upload <feature_folder_id> <WS>/specs/<FEATURE>` (ไม่อัป `source/`) → created/updated/stale. ฟอร์มลูกที่เพิ่งพบ: ใส่ URL โฟลเดอร์เดียวกันในคอลัมน์ SpecKit ของแถวลูกใน Sheet (ถ้ามีแถว) ผ่าน `sheet_speckit.py menus`.
6. Break point: จบ turn ด้วย `[เมนูที่ n/N] <breadcrumb> ✅` + ลิงก์ + จำนวนหน้าจอ + ต้นไม้ฟอร์มลูก + สถานะ gate + จุดค้าง + รายการเมนูที่เหลือ → รอ `continue`/`stop`. ห้ามเริ่มเมนูถัดไปเอง.

## Phase 5–6, ตารางสคริปต์, ข้อจำกัด

อ่าน `references/phase5-6-and-scripts.md` **เมื่อถึงขั้นนั้นเท่านั้น** (Phase 5 = `speckit_stamp_origin.py` แปะลิงก์กลับต้นทาง WinExec; Phase 6 = สรุปให้ผู้ใช้; ไม่ต้องอ่านตอนเริ่มงาน).
สคริปต์ช่วยประหยัด token ที่ใช้ใน Phase 4: `scan_form.py` (dfm digest / events / pas index / body / opens), `fill_evidence.py` (เติมคำพูดใน Evidence Map), `verify_evidence.py` (gate).
อ่านโค้ดจาก `source/` เสมอ ไม่ใช่ `browse_repo.py read` ตรง ๆ (ไทยเพี้ยน); `.dfm` อ่านผ่าน `*.dfm.digest.txt` แล้วคัดอ้างจาก `*.dfm.decoded.txt`; ไฟล์ > 2MB ใช้ `--max-bytes` แล้ว grep.
