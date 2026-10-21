# Prompt ที่ใช้กับ Agent (A = เขียน REQ, C = ผู้ตรวจ; ไม่มี Agent B เพราะไม่เรียก /speckit-* แล้ว) (Agent เริ่มจาก context ว่าง — ต้องส่งข้อมูลครบ)

ตัวแปรที่ orchestrator เติม: `PY` (python ของ skill), `S` (= `~/.claude/skills/git-learn-grouplife-speckit/scripts`), `WS` (workspace ของ App),
`FEATURE` (ชื่อ feature dir เช่น `007-EdAcHospital`), `REPO`, `SUB`, `SID` (spreadsheet id), `APP`, `GROUP`, `TODAY`,
`SCREEN` (หน้าจอที่ Agent นี้รับผิดชอบ 1 หน้าจอ: scr_id, unit, breadcrumb/ที่มา, และถ้ามีแถวใน Menu Contents: row, no, gid, tab_title, er_gid),
`VISITED` (รายการ unit ที่มี REQ แล้วในรอบนี้ + ใน `WS/specs/*/req/` ของเมนูอื่น พร้อม SCR-ID/ไฟล์ — ห้ามทำซ้ำ), `DEPTH` (ชั้นของหน้าจอนี้, เมนูหลัก = 0).
orchestrator ไล่ฟอร์มที่เปิดต่อเป็นทอด (BFS) — โดยปกติ 1 Agent A ต่อ 1 หน้าจอ; หน้าจอลูกเล็ก ๆ (< ~600 บรรทัด .pas ทั้งคู่) ที่แม่/พี่น้องใช้ unit ร่วมกันให้รวมเป็น Agent A ตัวเดียว (ส่ง `SCREEN` เป็นรายการ) ได้ — ผลลัพธ์ยังต้องเป็น REQ 1 ไฟล์ต่อ 1 หน้าจอ (ดู SKILL.md Phase 4).
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
>    (ได้ทั้ง .pas+.dfm, `*.dfm.decoded.txt` และ `*.dfm.digest.txt`). **วิธีอ่าน (ประหยัด token แต่ครบเท่าเดิม):**
>    - `.dfm`: อ่าน **`X.dfm.digest.txt`** (ตัด layout/font/สี/รูป blob ออก ที่เหลือคือทุก property ที่อาจมีผลต่อ requirement; รูปแบบ `<เลขบรรทัดจริง>|<บรรทัด>`) — เลขบรรทัดคือเลขของ `.dfm.decoded.txt` ใช้อ้าง evidence ได้ตรง ๆ. ห้ามอ่าน `.decoded.txt` ทั้งไฟล์ (ใช้ Read offset/limit เฉพาะช่วงที่ต้องคัด/ตรวจเมื่อสงสัยว่า digest ตัดอะไรไป).
>    - `.pas`: รัน `{{PY}} {{S}}/scan_form.py pas <ไฟล์>` เพื่อดูรายการ method + ช่วงบรรทัด, `scan_form.py events <X.dfm.decoded.txt>` เพื่อรู้ว่าปุ่ม/เมนูใดเรียก handler ใด,
>      แล้วอ่านเนื้อ handler ด้วย `scan_form.py body <ไฟล์> <Method…>` หรือ Read offset/limit. ส่วนที่ไม่ใช่ handler (type/var/uses/initialization/FormCreate/FormShow) อ่านด้วย Read ตามช่วงบรรทัด — **ห้ามข้าม method ใดที่ตัวควบคุมบนหน้าจอเรียกถึง**. ไฟล์เล็ก (< ~400 บรรทัด) อ่านทั้งไฟล์ได้.
>    - unit กลางที่ใช้ร่วม (`Utility.pas`, `MainUnit.pas OpenFormMenu`, DataModule): ถ้ามี `{{WS}}/_shared.md` ให้อ่านแทนการอ่าน unit เหล่านั้นซ้ำ (มีเนื้อ method ตรงตัว + เลขบรรทัดจริง); ใช้อ้าง evidence ได้เหมือนไฟล์ต้นทาง ให้ระบุ path ต้นทาง ไม่ใช่ `_shared.md`.
>    unit ที่หน้าจอเรียกแล้วพฤติกรรมสำคัญอยู่ในนั้น (DataModule, unit ค้นหา, unit ตรวจสอบ) ต้องดึงมาอ่านด้วย; ที่ไม่ได้อ่าน → ลง Section 9/14 ว่าไม่ได้อ่าน.
>    ถ้ารายงาน `missing`/`ambiguous` → ใช้ `{{PY}} ~/.claude/skills/git-learn-grouplife/scripts/browse_repo.py list` หาไฟล์จริง แล้วดึงใหม่; ห้ามเลือกไฟล์เองเมื่อกำกวม.
> 3. ดึง DB object ที่เกี่ยวข้อง: `{{PY}} {{S}}/fetch_source.py db {{WS}} 10.100.2.52 <DB> <object...>` สำหรับทุก stored proc/view/ตาราง ที่หน้าจอเรียก/อ่าน/เขียน
>    (DB = ชื่อ database จริง เช่น OGL/OceanLife/DataOne — ถ้า `not_found` ลอง DB อื่นที่เกี่ยวข้อง; ไม่เจอจริง → Section 9). proc ที่เรียกซ้อน (`EXEC other`) ตามไปอ่านได้ลึก ≤ 3 ชั้น.
>    ได้ไฟล์ใน `{{WS}}/source/_db/<DB>/`. อ่าน `.sql` ทั้งไฟล์เพื่อรู้กฎใน proc (WHERE/IF/คำนวณ/INSERT/UPDATE/RAISERROR).
> 3.5 **ไล่หาฟอร์ม/โปรแกรมที่ถูกเปิดต่อจากหน้าจอนี้ (บังคับ — ห้ามข้าม)**: **เริ่มด้วยสแกนอัตโนมัติ** `{{PY}} {{S}}/scan_form.py opens <trunk ใน {{WS}}/source/...> <.pas ของหน้าจอ และ unit ย่อยที่มันเรียกจริง…>` — ได้ `child_forms` / `external_programs` / `generic_open_calls` พร้อมบรรทัด, method ที่ครอบ, ปุ่ม/คอมโพเนนต์ที่ยิง handler นั้น (จาก .dfm) และ `target_member_opens_modal` (Edit/ShowMe ของปลายทางเปิด modal เองหรือไม่). สแกนตัด comment/string แล้ว และรู้ตัวแปรฟอร์มทุกตัวจาก `.dpr` (ตรวจแล้วตรงกับผลไล่มือของ 4 เมนูแรก). **ผลสแกนคือจุดที่ต้องไปอ่าน body แล้วยืนยัน ไม่ใช่คำตอบสุดท้าย** — ผลที่ไม่ใช่การเปิดฟอร์มจริง (เช่น ตัวแปรถูกกล่าวถึงเฉยๆ) ให้ตัดออกพร้อมเหตุผล; ถ้าเห็นรูปแบบเปิดฟอร์มที่สแกนไม่รู้จัก (ฟังก์ชันห่อ/TAction/ตัวแปรชื่อต่างจาก .dpr) ให้ grep เพิ่มเอง. ข้อความเดิมต่อไปนี้ยังใช้เป็นเกณฑ์ตัดสินว่าอะไรนับว่าเปิดฟอร์ม: **อย่าพึ่งแค่ `.Create`/`.Show`** — บทเรียนจาก Benefits: ฟอร์มรายการ (List*) เปิดฟอร์มแก้ไข (Ed*) ด้วย `<ตัวแปรฟอร์ม>.Edit(Sender, key)` /
>    `<ตัวแปรฟอร์ม>.ShowMe`, ซึ่งภายในเรียก `MainForm.OpenModalForm` → `FindShowModalForm` → `Application.CreateForm` + `ShowModal` (Utility.pas) — จึงต้อง grep **ตัวแปรฟอร์มของทุกฟอร์มใน `.dpr`** (รูป `{FormVar}` หลังชื่อ unit) ว่าถูกอ้างใน `.pas` นี้หรือไม่
>    (ตัดคอมเมนต์ก่อน) แล้วอ่าน body ของเมธอดที่เรียก (`Edit`/`ShowMe`) ในฟอร์มปลายทางด้วย. ค้นทั้ง `.pas` และ `.dfm` ของหน้าจอ (และ unit ย่อยที่มันเรียกใช้จริง) ทุกจุดที่เปิดฟอร์ม/โปรแกรมอื่น:
>    ปุ่ม/เมนู/popup/`TAction`/`OnDblClick` ที่ handler เรียก `TfrmX.Create`, `Application.CreateForm`, `.ShowModal`, `.Show`, `.Execute`, `FindShowForm(...)`,
>    ฟังก์ชันห่อที่ภายในเปิดฟอร์ม (ตามเข้าไปอ่าน body — ดึง unit นั้นมาด้วย `fetch_source.py`), `WinExec`/`ShellExecute`/`CreateProcess` (โปรแกรมภายนอก).
>    ใช้ grep บน `{{WS}}/source/` เช่น `grep -nEi "\.create\b|createform|showmodal|\.show\b|\.execute\b|FindShowForm|OpenModalForm|FindShowModalForm|winexec|shellexecute|createprocess|<FormVar1>\.|<FormVar2>\." <ไฟล์>` (`.Execute` ของ TMSSQL/query ไม่ใช่การเปิดฟอร์ม) แล้วไล่ดูผลทีละจุด (อย่าเชื่อ Sheet analyst ว่าไม่มี).
>    - ฟอร์มปลายทางในโปรแกรมเดียวกัน → ใส่ใน `child_forms` (button/component, caption, event, unit, form_class, open_mode, condition, `evidence` path:บรรทัด+quote) และใน REQ: ปุ่มนั้นอยู่ที่ 3.3 BTN-/4.3 ACT- พร้อมระบุ "เปิดหน้าจอ <SCR-ID ของลูก>" (ถ้ายังไม่มี SCR-ID ให้ใช้กฎใน req-mapping.md); ลูกที่อยู่ใน VISITED → ลิงก์ไปไฟล์เดิม ไม่ทำซ้ำ.
>    - โปรแกรมภายนอก (คนละ `.dpr`/exe) → ใส่ใน `external_programs` (ปุ่ม, path/exe, evidence) และเขียนใน REQ เท่านั้นว่าเรียกอะไร — **ไม่วิเคราะห์ต่อ**.
>    - ถ้าหน้าจอเป็นเมนูหลัก (DEPTH 0) ให้อ่านวิธีที่เมนูหลักเปิดฟอร์มนี้ด้วย (เช่น `OpenFormMenu` → `FindShowForm`; ตามไปอ่าน implementation จริง ดึง unit มา) แล้วบันทึกที่ Section 7.1/8 (opener) พร้อมหลักฐาน — ไม่ทราบ/อ่านไม่ได้ → Section 9.
>    - ไม่พบจุดใดเลย → `child_forms: []` และเขียนใน REQ (Section 1.3/9) ว่า "ตรวจ grep แล้วไม่พบการเปิดฟอร์มอื่น" พร้อมคำสั่ง/รูปแบบที่ใช้ค้น.
> 4. เขียน `REQ_<SCR-ID>_<unit>.md` ตาม template + req-mapping.md: ครบ 14 section (ที่ไม่มีใน code = บรรทัด N/A ตามกฎ), ID ในเซลล์แรกของตาราง, และ `APPENDIX A — EVIDENCE MAP`. **ใน Evidence Map เขียนแค่ `<ID> :: <path>:<บรรทัดเริ่ม[-จบ]>` (ช่วงแคบ 1–3 บรรทัดที่มี statement/property นั้นจริง) — ไม่ต้องพิมพ์คำพูด** `fill_evidence.py` จะคัดลอกคำพูดตรงตัวจากไฟล์จริงให้ (ถ้าเขียนคำพูดเองก็ได้ ระบบไม่ทับ).
> 4.5 **เกณฑ์ความละเอียด (ประหยัด token ที่ขั้นอ่าน/พิมพ์ ไม่ใช่ที่ความครบ — บทเรียนจากการเทียบเมนู 014: ผู้ตรวจพบของที่เขียนกระชับเกินไป)** ก่อนปิดไฟล์ ตรวจรายการนี้และเพิ่มให้ครบ (ทุกข้อต้องมี evidence path:บรรทัด):
>    a. **ทุกคอลัมน์ที่ nullable** (ดูจาก `source/_db/**/*.table.txt`) ที่ถูกใช้ใน JOIN / WHERE / การเทียบค่า / การแสดงผล → ทำเป็น `EC-` ของตัวเอง ระบุผลเมื่อเป็น NULL (แถวหลุดจาก join, เทียบแล้วเป็นเท็จ/จริง, แสดงว่าง ฯลฯ).
>    b. **JOIN ที่ key ไม่ครอบ PK/unique ของตารางปลายทาง** → `EC-` ความเสี่ยงแถวซ้ำ/คูณ และผลต่อ Footer/ผลรวม/จำนวนราย (อ้าง PK จาก `.table.txt`).
>    c. **การเปรียบเทียบ/การคำนวณบนค่าที่แสดง** (DisplayText, format, ส่วนเวลาของ datetime, BETWEEN ปลายช่วง) → `BR-` บอกว่าเทียบอะไรกับอะไร + `EC-` ผลเมื่อ format/ส่วนเวลาต่างกัน.
>    d. **ปุ่ม/เมนู/คอมโพเนนต์ที่ซ่อนหรือไม่มี handler** (`Visible = ivNever/False`, ไม่มี `OnClick`), **handler ที่ประกาศแต่ไม่ถูกผูก**, **คอมโพเนนต์ว่าง/ไม่ผูกกับ code** (เช่น ProgressBar, PageControl เปล่า) → แถวของตัวเองใน 3.3 (`BTN-`) หรือ `BR-` (+ Open Issue ถ้าไม่ทราบเจตนา) ไม่ใช่แค่ย่อหน้าใน Section 2.
>    e. **ทุก handler ของหน้าจอ** (จาก `scan_form.py pas`) ต้องถูกอ้างใน REQ อย่างน้อยหนึ่งแห่ง (BTN/ACT/BR/ALT/EC) หรืออยู่ใน Open Issue ว่า "ว่าง/ไม่ได้ผูก" — รวม `FormShow`/`FormActivate`/`FormClose`/`FormCreate` และลำดับการตั้ง-คืน `Screen.Cursor`.
>    f. **property ของฟอร์ม/grid ที่ code อ่านผลได้จริง** (`FormStyle`, `WindowState`, `Position`, `DataController.KeyFieldNames`, `SortOrder`, `Options*` ที่กระทบพฤติกรรม) → ลง Section 2/3/4 ที่เกี่ยวข้อง (ข้ามสี/ฟอนต์/ตำแหน่ง/ขนาด).
>    g. แถวใน 3.3 และตารางอื่นเขียนสั้น 1–2 ประโยคต่อแถวได้ — ความละเอียดอยู่ที่ "ครบทุกข้อเท็จจริง" ไม่ใช่ "ยาว".
> 5. เขียน `req/README.md` (สารบัญหน้าจอ).
> 6. รัน `{{PY}} {{S}}/fill_evidence.py {{WS}} {{FEATURE}}` (เติมคำพูด; รายการ `unresolved` = path/บรรทัดผิด ต้องแก้ให้ชี้ถูกที่) แล้ว `{{PY}} {{S}}/verify_evidence.py {{WS}} {{FEATURE}}` และแก้จน `fail_count = 0` (แก้ไฟล์ REQ เท่านั้น; วนได้สูงสุด 4 รอบ). ตอนแก้ผลที่ fail ให้อ่านเฉพาะรายการ fail ใน JSON — ห้ามอ่านไฟล์ REQ ทั้งไฟล์กลับเข้ามาถ้าแก้ได้ด้วย Edit ตรงจุด.
>
> ส่งกลับ (final message เป็น JSON เดียว): `{"screens":[{"scr_id","unit","req_file","open_questions":n,"unread_units":[...]}], "child_forms":[{"button","caption","event","unit","form_class","open_mode","condition","evidence"}], "external_programs":[{"button","target","evidence"}], "opener":"...", "sheet_vs_code_diffs":[...], "unresolved":[...], "verify": {"fail_count":n,"warn_count":n}}`.
> `unresolved` = สิ่งที่ทำไม่ได้/ไม่ครบ (บอกตรง ๆ ห้ามอ้างว่าครบถ้าไม่ครบ).

---

## Agent C — auditor (ตัวใหม่ context ว่าง; อ่านอย่างเดียว; ไม่ได้เห็นการให้เหตุผลของ A/B)

> ตรวจว่าเอกสาร REQ ของ feature `{{FEATURE}}` (`{{WS}}/specs/{{FEATURE}}/`) ตรงกับ code ใน snapshot `{{WS}}/source/` 100% หรือไม่. **อ่านอย่างเดียว ห้ามแก้ไฟล์ใด ๆ.**
> **รอบ: {{ROUND}}** (1 = ตรวจเต็ม; 2–3 = ตรวจเฉพาะ ID/ย่อหน้าที่แก้ใน `{{CHANGED}}` + ตรวจว่าการแก้ไม่ทำให้ข้ออื่นขัดกัน + สแกนซ้ำข้อ (5) เฉพาะถ้าแก้เกี่ยวกับฟอร์มลูก).
> **เครื่องตรวจอัตโนมัติผ่านแล้ว**: ทุกบรรทัดใน Evidence Map มี quote ที่มีอยู่จริงใน path:บรรทัดที่ระบุ (`verify_evidence.py` fail_count=0) และทุก ID ในตารางมี evidence — **ไม่ต้องเปิดไฟล์เพื่อยืนยันว่า quote มีอยู่จริง** ให้ใช้เวลาไปกับสิ่งที่เครื่องตรวจไม่ได้: (a) quote นั้น*รองรับข้อความในเอกสารจริงหรือไม่* (ข้ออ้างเกิน/ตีความผิด/เงื่อนไขตกหล่น/สลับ if-else) (b) พฤติกรรมของ code ที่ตกหล่น (c) คำเดา (d) ฟอร์มลูก.
> **ข้ออ้างที่มาจาก DB schema ต้องตรวจด้วย (บทเรียนรอบเทียบ 014: ผู้ตรวจเคยข้ามส่วนนี้ ทั้งที่ EC เรื่อง NULL/แถวซ้ำพึ่งมัน)**: ทุกข้อความใน REQ ที่อ้าง nullable / PK / unique / ชนิดคอลัมน์ / ความซ้ำของข้อมูล (Key Entities, EC-, BR- เรื่อง JOIN) ให้เปิด `{{WS}}/source/_db/**/<table>.table.txt` ของตารางนั้นยืนยันทีละข้อ และตรวจว่าคอลัมน์ที่ใช้ใน JOIN ครอบ PK/unique ของตารางปลายทางจริงตามที่เขียน — ข้อที่ยืนยันไม่ได้ = `unsupported`. ตาราง/proc ที่ไม่มีไฟล์ใน `_db` = `unsupported` (อย่าเดา).
> **ตรวจความหมายของ cross-reference ภายในเอกสาร**: `verify_evidence.py` ตรวจแล้วว่า ID ที่อ้าง (BR-/Q-/BTN- ฯลฯ) *มีอยู่จริง* — ที่ต้องตรวจเองคือ *หัวข้อของ ID ปลายทางตรงกับที่อ้างหรือไม่* (เช่น "ดู Q-006" แต่ Q-006 พูดเรื่องอื่น) และข้อความที่บอกว่า "ทำเสมอ/ทุกครั้ง" มีเงื่อนไขใน code ที่ตัดข้ออ้างนั้นหรือไม่ (เช่น `if Restore then`) — ตามเข้าไปอ่านฟังก์ชันห่อให้ครบก่อนยืนยัน.
> วิธี: ตรวจ**ทุก** ID (F/BTN/COL/ACT/BR/MSG/PRE/POST/ALT/EC) ทุก User Story/Acceptance Criteria/Key Entity (รอบ 1) โดยเปิดช่วงที่เกี่ยวข้องใน `source/` ดูเอง — อ่าน handler ผ่าน `{{PY}} {{S}}/scan_form.py body <ไฟล์> <Method>` และ .dfm ผ่าน `*.dfm.digest.txt` ได้ (ตัดเฉพาะ layout/font/สี). รายงาน: (1) ข้อที่ขัดกับ code (ยก path:บรรทัด + ข้อความของ code + ข้อความในเอกสาร) (2) ข้อที่ code ไม่รองรับ/ไม่มีหลักฐาน (3) พฤติกรรมของ code ที่เอกสารไม่ได้พูดถึงแต่สำคัญ
> (4) คำที่เป็นการคาดเดา (5) **ปุ่ม/เมนู/handler ที่เปิดฟอร์มหรือโปรแกรมอื่นแล้ว REQ ไม่ได้บันทึก/ไม่ได้ลิงก์ไปหน้าจอลูก**: รัน `{{PY}} {{S}}/scan_form.py opens <trunk> <.pas ของทุกหน้าจอ>` เทียบกับ `child_forms`/`external_programs` ใน REQ แล้ว grep เสริมเองเฉพาะรูปแบบที่สแกนไม่รู้จัก (ฟังก์ชันห่อ/TAction); ฟอร์มลูกที่พบแต่ไม่มี REQ (และไม่อยู่ใน VISITED) ให้รายงานใน `missing_behaviors`. ไม่มีข้อบกพร่อง = บอกตรง ๆ ว่าตรวจอะไรไปบ้างและไม่พบ — ห้ามเขียนว่า "น่าจะถูก".
> ส่งกลับเป็น JSON: `{"contradictions":[...],"unsupported":[...],"missing_behaviors":[...],"speculation":[...],"checked":{"fr":n,"br":n,"msg":n,"entities":n}}`.
> orchestrator แก้เอกสารตามผล (บันทึก ID ที่แก้ไว้เป็น `CHANGED`) แล้วเรียกผู้ตรวจรอบถัดไป (`SendMessage` ต่อ Agent C ตัวเดิมได้ — ส่งแค่ `CHANGED` + diff ไม่ต้องส่งเอกสารทั้งฉบับ ยังคงบทบาทอ่านอย่างเดียว) จนทุกรายการว่าง (สูงสุด 3 รอบ).
