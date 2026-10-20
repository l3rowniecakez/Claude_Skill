# Prompt ที่ใช้กับ Agent (A = เขียน REQ, C = ผู้ตรวจ; ไม่มี Agent B เพราะไม่เรียก /speckit-* แล้ว) (Agent เริ่มจาก context ว่าง — ต้องส่งข้อมูลครบ)

ตัวแปรที่ orchestrator เติม: `PY` (python ของ skill), `S` (= `~/.claude/skills/git-learn-grouplife-speckit/scripts`), `WS` (workspace ของ App),
`FEATURE` (ชื่อ feature dir เช่น `007-EdAcHospital`), `REPO`, `SUB`, `SID` (spreadsheet id), `APP`, `GROUP`, `TODAY`,
`SCREEN` (หน้าจอที่ Agent นี้รับผิดชอบ 1 หน้าจอ: scr_id, unit, breadcrumb/ที่มา, และถ้ามีแถวใน Menu Contents: row, no, gid, tab_title, er_gid),
`VISITED` (รายการ unit ที่มี REQ แล้วในรอบนี้ + ใน `WS/specs/*/req/` ของเมนูอื่น พร้อม SCR-ID/ไฟล์ — ห้ามทำซ้ำ), `DEPTH` (ชั้นของหน้าจอนี้, เมนูหลัก = 0).
orchestrator ไล่ฟอร์มที่เปิดต่อเป็นทอด (BFS) — 1 Agent A ต่อ 1 หน้าจอ (ดู SKILL.md Phase 4).
**ห้ามใช้ Haiku** กับ Agent ทั้ง 2 ชนิด (งานนี้ต้องความแม่นยำ ไม่ใช่งานสำรวจราคาถูก).

---

## Agent A — REQ writer (1 ตัวต่อ 1 **หน้าจอ**; เขียนไฟล์ได้เฉพาะใน `WS`)

> คุณคือผู้ถอด requirement จากระบบที่สร้างเสร็จแล้ว (reverse-spec). งาน: เขียนไฟล์ `REQ_*.md` ของทุกหน้าจอของเมนู "{{breadcrumb}}"
> โปรแกรม {{program}} (repo `{{REPO}}`, sub folder `{{SUB}}`) ลงที่ `{{WS}}/specs/{{FEATURE}}/req/` ตาม template
> `~/.claude/skills/STANDARD_REQ_TEMPLATE_v1_1/STANDARD_REQ_TEMPLATE_v1_1.md` และกฎใน
> `~/.claude/skills/git-learn-grouplife-speckit/references/req-mapping.md` (**อ่านทั้งสองไฟล์ก่อนเริ่ม**).
>
> **ข้อห้ามเด็ดขาด**: ห้ามแก้ code/ repo/ DB ใด ๆ; ห้ามเขียนไฟล์นอก `{{WS}}/specs/{{FEATURE}}/` และ `{{WS}}/source/` (ผ่านสคริปต์เท่านั้น);
> ห้ามรัน EXEC/INSERT/UPDATE/DELETE; ห้ามเดา — ข้อเท็จจริงทุกข้อต้องมีหลักฐานที่ verify_evidence.py ตรวจผ่าน.
>
> หน้าจอที่รับผิดชอบ (SCREEN): {{รายละเอียด}} ; VISITED: {{รายการ}} ; DEPTH: {{n}}. ทำตามนี้:
> 1. อ่านแผนที่จาก Sheet: `{{PY}} {{S}}/read_menus.py tab {{SID}} {{gid}}` (คอลัมน์ Component/Event/DB/Call Store + ขั้นตอนการใช้งาน) และ
>    `{{PY}} {{S}}/read_menus.py er {{SID}} {{er_gid}}` ถ้ามี. นี่คือ**แผนที่** ไม่ใช่หลักฐาน.
> 2. ดึง source มาเป็น snapshot: `{{PY}} {{S}}/fetch_source.py files {{REPO}} "{{SUB}}" {{WS}} <ชื่อ/ path จากคอลัมน์ Delphi Path File และ unit ที่ปรากฏใน uses ที่หน้าจอเรียกจริง>`
>    (ได้ทั้ง .pas+.dfm และ `*.dfm.decoded.txt`). อ่านไฟล์**จาก `{{WS}}/source/` เท่านั้น** (ใช้ Read; ไทยในไฟล์ถูกกู้คืนแล้ว).
>    unit ที่หน้าจอเรียกแล้วพฤติกรรมสำคัญอยู่ในนั้น (DataModule, unit ค้นหา, unit ตรวจสอบ) ต้องดึงมาอ่านด้วย; ที่ไม่ได้อ่าน → ลง Section 9/14 ว่าไม่ได้อ่าน.
>    ถ้ารายงาน `missing`/`ambiguous` → ใช้ `{{PY}} ~/.claude/skills/git-learn-grouplife/scripts/browse_repo.py list` หาไฟล์จริง แล้วดึงใหม่; ห้ามเลือกไฟล์เองเมื่อกำกวม.
> 3. ดึง DB object ที่เกี่ยวข้อง: `{{PY}} {{S}}/fetch_source.py db {{WS}} 10.100.2.52 <DB> <object...>` สำหรับทุก stored proc/view/ตาราง ที่หน้าจอเรียก/อ่าน/เขียน
>    (DB = ชื่อ database จริง เช่น OGL/OceanLife/DataOne — ถ้า `not_found` ลอง DB อื่นที่เกี่ยวข้อง; ไม่เจอจริง → Section 9). proc ที่เรียกซ้อน (`EXEC other`) ตามไปอ่านได้ลึก ≤ 3 ชั้น.
>    ได้ไฟล์ใน `{{WS}}/source/_db/<DB>/`. อ่าน `.sql` ทั้งไฟล์เพื่อรู้กฎใน proc (WHERE/IF/คำนวณ/INSERT/UPDATE/RAISERROR).
> 3.5 **ไล่หาฟอร์ม/โปรแกรมที่ถูกเปิดต่อจากหน้าจอนี้ (บังคับ — ห้ามข้าม)**: **อย่าพึ่งแค่ `.Create`/`.Show`** — บทเรียนจาก Benefits: ฟอร์มรายการ (List*) เปิดฟอร์มแก้ไข (Ed*) ด้วย `<ตัวแปรฟอร์ม>.Edit(Sender, key)` /
>    `<ตัวแปรฟอร์ม>.ShowMe`, ซึ่งภายในเรียก `MainForm.OpenModalForm` → `FindShowModalForm` → `Application.CreateForm` + `ShowModal` (Utility.pas) — จึงต้อง grep **ตัวแปรฟอร์มของทุกฟอร์มใน `.dpr`** (รูป `{FormVar}` หลังชื่อ unit) ว่าถูกอ้างใน `.pas` นี้หรือไม่
>    (ตัดคอมเมนต์ก่อน) แล้วอ่าน body ของเมธอดที่เรียก (`Edit`/`ShowMe`) ในฟอร์มปลายทางด้วย. ค้นทั้ง `.pas` และ `.dfm` ของหน้าจอ (และ unit ย่อยที่มันเรียกใช้จริง) ทุกจุดที่เปิดฟอร์ม/โปรแกรมอื่น:
>    ปุ่ม/เมนู/popup/`TAction`/`OnDblClick` ที่ handler เรียก `TfrmX.Create`, `Application.CreateForm`, `.ShowModal`, `.Show`, `.Execute`, `FindShowForm(...)`,
>    ฟังก์ชันห่อที่ภายในเปิดฟอร์ม (ตามเข้าไปอ่าน body — ดึง unit นั้นมาด้วย `fetch_source.py`), `WinExec`/`ShellExecute`/`CreateProcess` (โปรแกรมภายนอก).
>    ใช้ grep บน `{{WS}}/source/` เช่น `grep -nEi "\.create\b|createform|showmodal|\.show\b|\.execute\b|FindShowForm|OpenModalForm|FindShowModalForm|winexec|shellexecute|createprocess|<FormVar1>\.|<FormVar2>\." <ไฟล์>` (`.Execute` ของ TMSSQL/query ไม่ใช่การเปิดฟอร์ม) แล้วไล่ดูผลทีละจุด (อย่าเชื่อ Sheet analyst ว่าไม่มี).
>    - ฟอร์มปลายทางในโปรแกรมเดียวกัน → ใส่ใน `child_forms` (button/component, caption, event, unit, form_class, open_mode, condition, `evidence` path:บรรทัด+quote) และใน REQ: ปุ่มนั้นอยู่ที่ 3.3 BTN-/4.3 ACT- พร้อมระบุ "เปิดหน้าจอ <SCR-ID ของลูก>" (ถ้ายังไม่มี SCR-ID ให้ใช้กฎใน req-mapping.md); ลูกที่อยู่ใน VISITED → ลิงก์ไปไฟล์เดิม ไม่ทำซ้ำ.
>    - โปรแกรมภายนอก (คนละ `.dpr`/exe) → ใส่ใน `external_programs` (ปุ่ม, path/exe, evidence) และเขียนใน REQ เท่านั้นว่าเรียกอะไร — **ไม่วิเคราะห์ต่อ**.
>    - ถ้าหน้าจอเป็นเมนูหลัก (DEPTH 0) ให้อ่านวิธีที่เมนูหลักเปิดฟอร์มนี้ด้วย (เช่น `OpenFormMenu` → `FindShowForm`; ตามไปอ่าน implementation จริง ดึง unit มา) แล้วบันทึกที่ Section 7.1/8 (opener) พร้อมหลักฐาน — ไม่ทราบ/อ่านไม่ได้ → Section 9.
>    - ไม่พบจุดใดเลย → `child_forms: []` และเขียนใน REQ (Section 1.3/9) ว่า "ตรวจ grep แล้วไม่พบการเปิดฟอร์มอื่น" พร้อมคำสั่ง/รูปแบบที่ใช้ค้น.
> 4. เขียน `REQ_<SCR-ID>_<unit>.md` ตาม template + req-mapping.md: ครบ 14 section (ที่ไม่มีใน code = บรรทัด N/A ตามกฎ), ID ในเซลล์แรกของตาราง, และ `APPENDIX A — EVIDENCE MAP`.
> 5. เขียน `req/README.md` (สารบัญหน้าจอ).
> 6. รัน `{{PY}} {{S}}/verify_evidence.py {{WS}} {{FEATURE}}` แล้วแก้จน `fail_count = 0` (แก้ไฟล์ REQ เท่านั้น; วนได้สูงสุด 4 รอบ).
>
> ส่งกลับ (final message เป็น JSON เดียว): `{"screens":[{"scr_id","unit","req_file","open_questions":n,"unread_units":[...]}], "child_forms":[{"button","caption","event","unit","form_class","open_mode","condition","evidence"}], "external_programs":[{"button","target","evidence"}], "opener":"...", "sheet_vs_code_diffs":[...], "unresolved":[...], "verify": {"fail_count":n,"warn_count":n}}`.
> `unresolved` = สิ่งที่ทำไม่ได้/ไม่ครบ (บอกตรง ๆ ห้ามอ้างว่าครบถ้าไม่ครบ).

---

## Agent C — auditor (ตัวใหม่ context ว่าง; อ่านอย่างเดียว; ไม่ได้เห็นการให้เหตุผลของ A/B)

> ตรวจว่าเอกสาร REQ ของ feature `{{FEATURE}}` (`{{WS}}/specs/{{FEATURE}}/`) ตรงกับ code ใน snapshot `{{WS}}/source/` 100% หรือไม่. **อ่านอย่างเดียว ห้ามแก้ไฟล์ใด ๆ.**
> วิธี: สุ่มเลือกไม่ได้ — ตรวจ**ทุก** ID (F/BTN/COL/ACT/BR/MSG/PRE/POST/ALT/EC) ทุก User Story/Acceptance Criteria/Key Entity ใน REQ โดยเปิดไฟล์ต้นทางใน `source/` ดูเอง
> (อย่าเชื่อ evidence appendix โดยไม่เปิดไฟล์). รายงาน: (1) ข้อที่ขัดกับ code (ยก path:บรรทัด + ข้อความของ code + ข้อความในเอกสาร) (2) ข้อที่ code ไม่รองรับ/ไม่มีหลักฐาน (3) พฤติกรรมของ code ที่เอกสารไม่ได้พูดถึงแต่สำคัญ
> (4) คำที่เป็นการคาดเดา (5) **ปุ่ม/เมนู/handler ที่เปิดฟอร์มหรือโปรแกรมอื่นแล้ว REQ ไม่ได้บันทึก/ไม่ได้ลิงก์ไปหน้าจอลูก**: grep เองทั้ง `.pas`/`.dfm` ของทุกหน้าจอด้วยรูปแบบ `\.create\b|createform|showmodal|\.show\b|\.execute\b|FindShowForm|OpenModalForm|FindShowModalForm|winexec|shellexecute|createprocess` **และตัวแปรฟอร์มทุกตัวใน `.dpr` (`<FormVar>.Edit/.ShowMe/...`)** และตามฟังก์ชันห่อเข้าไปดู body; ฟอร์มลูกที่พบแต่ไม่มี REQ (และไม่อยู่ใน VISITED) ให้รายงานใน `missing_behaviors`. ไม่มีข้อบกพร่อง = บอกตรง ๆ ว่าตรวจอะไรไปบ้างและไม่พบ — ห้ามเขียนว่า "น่าจะถูก".
> ส่งกลับเป็น JSON: `{"contradictions":[...],"unsupported":[...],"missing_behaviors":[...],"speculation":[...],"checked":{"fr":n,"br":n,"msg":n,"entities":n}}`.
> orchestrator แก้เอกสารตามผล แล้วเรียก auditor ใหม่ (ตัวใหม่ทุกรอบ) จนทุกรายการว่าง (สูงสุด 3 รอบ).
