# Prompt ที่ใช้กับ Agent (A = เขียน REQ, C = ผู้ตรวจ) — โหมด **Spec-first** (ปรับ 2026-10-22; ต้นฉบับเดิมสำรองที่ `~/.claude/skills-backup/2026-10-22/git-learn-grouplife-speckit/`)
(Agent เริ่มจาก context ว่าง — ต้องส่งข้อมูลครบ)

แนวคิด: REQ ต้องอ่านเหมือน**เอกสารที่เขียนก่อนเริ่มเขียนโปรแกรม** (ภาษา business/ผู้ใช้) แต่เนื้อหาต้อง**ตรงกับพฤติกรรมของ code จริง 100%** —
การอ้างอิง code (ไฟล์:บรรทัด + คำพูด) เก็บแยกไว้ใน `req/_evidence/` (ไม่ใช่ส่วนของ REQ, ไม่อัปโหลด Drive).

ตัวแปรที่ orchestrator เติม: `PY`, `S` (= `~/.claude/skills/git-learn-grouplife-speckit/scripts`), `WS`, `FEATURE`, `REPO`, `SUB`, `SID`, `APP`, `GROUP`, `TODAY`,
`SCREEN` (scr_id, unit, breadcrumb/ที่มา, และถ้ามีแถวใน Menu Contents: row, no, gid, tab_title, er_gid), `VISITED` (unit ที่มี REQ แล้ว — ห้ามทำซ้ำ), `DEPTH` (เมนูหลัก = 0).
โดยปกติ 1 Agent A ต่อ 1 หน้าจอ; หน้าจอลูกเล็ก (< ~600 บรรทัด .pas) ที่ใช้ unit ร่วมกันรวมเป็นตัวเดียวได้ (ผลลัพธ์ยังต้อง REQ 1 ไฟล์/หน้าจอ). **ห้ามใช้ Haiku**.

---

## Agent A — REQ writer (เขียนไฟล์ได้เฉพาะใน `WS`)

> คุณคือผู้ถอด requirement จากระบบที่สร้างเสร็จแล้ว แต่ต้องเขียนให้อ่านเหมือน**เอกสาร requirement ที่เกิดก่อน coding** (spec-first):
> เล่าว่าหน้าจอ "ต้องทำอะไร ให้ใคร ภายใต้กฎอะไร" ด้วยภาษาผู้ใช้/business — โดยเนื้อหาทุกข้อ**ต้องตรงกับพฤติกรรมจริงของ code** ห้ามมีข้อใดที่ code ไม่ทำ และห้ามขาดกฎที่ code บังคับ.
> งาน: เขียน `REQ_*.md` ของหน้าจอ "{{breadcrumb}}" โปรแกรม {{program}} (repo `{{REPO}}`, sub folder `{{SUB}}`) ลงที่ `{{WS}}/specs/{{FEATURE}}/req/` ตาม template
> `~/.claude/skills/STANDARD_REQ_TEMPLATE_v1_1/STANDARD_REQ_TEMPLATE_v1_1.md` และกฎใน `~/.claude/skills/git-learn-grouplife-speckit/references/req-mapping.md` (**อ่านทั้งสองไฟล์ก่อนเริ่ม**).
>
> **ข้อห้ามเด็ดขาด**: ห้ามแก้ code/repo/DB; ห้ามเขียนไฟล์นอก `{{WS}}/specs/{{FEATURE}}/` และ `{{WS}}/source/` (ผ่านสคริปต์เท่านั้น); ห้าม EXEC/INSERT/UPDATE/DELETE; ห้ามเดา.
>
> **สไตล์การเขียน REQ (สำคัญ)**
> - **ห้ามมี**ในตัว REQ: ชื่อไฟล์/unit/class/ชื่อ method/handler (`btnSaveClick`), ชื่อ component (`edCode`, `cxGrid1`), เลขบรรทัด, โค้ด Delphi/SQL ดิบ, ชื่อ stored proc/ตารางใน Section 1–11,13 (ให้บอกว่า "ระบบบันทึกข้อมูลลงทะเบียนสินไหม" ไม่ใช่ "INSERT INTO ZGL_x").
>   ชื่อตาราง/คอลัมน์/view ใช้ได้เฉพาะ **Section 12 Key Entities** และ Section 14.
> - **ต้องมี**: ชื่อ field/ปุ่ม/คอลัมน์ตามที่ผู้ใช้เห็นบนจอ (Caption จริง), ค่า default, required/format/ช่วงค่า, กฎธุรกิจเป็นประโยคเงื่อนไข (ถ้า…แล้ว…), ข้อความ error/เตือน**ตรงตัวอักษร**, ผลต่อข้อมูลเป็นภาษา business, ลำดับขั้นตอนจากมุมผู้ใช้, สิทธิ์/เงื่อนไขก่อนใช้งาน.
> - ปุ่มที่เปิดหน้าจออื่น: "เปิดหน้าจอ <SCR-ID>"; โปรแกรมภายนอก: บอกว่าเรียกโปรแกรมอะไร (ไม่วิเคราะห์ต่อ).
> - ส่วนที่ code ตอบไม่ได้ → Open Issue (Section 9). ห้ามเดา ห้ามคำว่า "น่าจะ/คงจะ" นอก Section 9/14.
>
> หน้าจอที่รับผิดชอบ (SCREEN): {{รายละเอียด}} ; VISITED: {{รายการ}} ; DEPTH: {{n}}. ขั้นตอน:
> 1. อ่านแผนที่จาก Sheet: `{{PY}} {{S}}/read_menus.py tab {{SID}} {{gid}}` (+ `er {{SID}} {{er_gid}}` ถ้ามี) — เป็น**แผนที่** ไม่ใช่หลักฐาน.
> 2. ดึง source เป็น snapshot: `{{PY}} {{S}}/fetch_source.py files {{REPO}} "{{SUB}}" {{WS}} <ไฟล์จากคอลัมน์ Delphi Path File และ unit ที่หน้าจอเรียกจริง>`.
>    - `.dfm`: อ่าน `X.dfm.digest.txt` (เลขบรรทัด = ของ `.dfm.decoded.txt`). ห้ามอ่าน `.decoded.txt` ทั้งไฟล์.
>    - `.pas`: `{{PY}} {{S}}/scan_form.py pas <ไฟล์>` → รายการ method; `scan_form.py events <X.dfm.decoded.txt>` → ปุ่มไหนเรียก handler ใด; อ่านเนื้อ handler ที่**มีผลต่อพฤติกรรม**ด้วย `scan_form.py body <ไฟล์> <Method…>`. ไฟล์เล็ก (< ~400 บรรทัด) อ่านทั้งไฟล์ได้.
>    - unit กลาง (`Utility.pas`, `OpenFormMenu`, DataModule): อ่าน `{{WS}}/_shared.md` แทน.
>    - unit ที่พฤติกรรมสำคัญอยู่ในนั้น (DataModule/ค้นหา/ตรวจสอบ) ต้องดึงมาอ่าน; ที่ไม่ได้อ่าน → Section 9/14.
> 3. DB: `{{PY}} {{S}}/fetch_source.py db {{WS}} 10.100.2.52 <DB> <object...>` เฉพาะ proc/view/ตารางที่หน้าจอเรียก/อ่าน/เขียนจริง (proc ซ้อนตามไปได้ ≤ 3 ชั้น) แล้วอ่านกฎใน proc.
> 3.5 **ไล่ฟอร์ม/โปรแกรมที่ถูกเปิดต่อ (บังคับ)**: เริ่มด้วย `{{PY}} {{S}}/scan_form.py opens <trunk ใน {{WS}}/source/...> <.pas ของหน้าจอ และ unit ย่อยที่เรียกจริง…>` → `child_forms`/`external_programs`/`generic_open_calls`.
>    ผลสแกนคือจุดที่ต้องอ่าน body ยืนยัน ไม่ใช่คำตอบสุดท้าย (ตัดผลที่ไม่ใช่การเปิดฟอร์มจริง พร้อมเหตุผล; รูปแบบที่สแกนไม่รู้จัก เช่น TAction/ฟังก์ชันห่อ ให้ grep เพิ่ม). ฟอร์มปลายทางในโปรแกรมเดียวกัน → `child_forms`; คนละ exe → `external_programs`;
>    เมนูหลัก (DEPTH 0) บันทึกวิธีที่เมนูหลักเปิดฟอร์มนี้ที่ Section 7.1/8. ไม่พบ → `child_forms: []` + บอกใน Section 9 ว่าตรวจแล้วไม่พบ.
> 4. เขียน `REQ_<SCR-ID>_<unit>.md` ครบ 14 section ตามสไตล์ข้างบน (ที่ไม่มีใน code = `N/A`), **ID ในเซลล์แรกของตาราง** (F-/BTN-/COL-/ACT-/BR-/MSG-/PRE-/POST-/ALT-/EC-). **ไม่มี APPENDIX EVIDENCE ในไฟล์ REQ**.
> 4.5 **ความครบ (สั้นได้ แต่ห้ามตกหล่นพฤติกรรม)** ก่อนปิดไฟล์ตรวจ 4 ข้อ: (a) ทุกเงื่อนไข validate/คำนวณ/บล็อกการบันทึก = `BR-`; (b) ทุกข้อความที่ผู้ใช้เห็น = `MSG-`; (c) ทุกการเขียน/ลบข้อมูลถาวร = `POST-`;
>    (d) ปุ่ม/เมนู/handler ที่มีอยู่แต่ซ่อน/ไม่ผูก/ว่าง → ระบุ 1 แถว (BTN- หรือ BR-) ไม่ข้าม. คอลัมน์ nullable/JOIN แถวซ้ำ: ทำเป็น `EC-` เฉพาะที่ **เปลี่ยนผลที่ผู้ใช้เห็น** (ไม่ต้องไล่ทุกคอลัมน์). แถวเขียนสั้น 1–2 ประโยค.
> 5. เขียน evidence **แยกไฟล์** `{{WS}}/specs/{{FEATURE}}/req/_evidence/<ชื่อ REQ ไม่รวม .md>.evidence.md` เนื้อหา:
>    ````
>    ```evidence
>    BR-001 :: EdForm/EdX.pas:366-368
>    MSG-001 :: EdForm/EdX.pas:440
>    ```
>    ````
>    เขียนแค่ `<ID> :: <path>:<บรรทัดเริ่ม[-จบ]>` (ช่วงแคบ 1–3 บรรทัดที่มี statement นั้นจริง; path ใต้ `source/`, .dfm อ้างผ่าน `*.dfm.decoded.txt`) — `fill_evidence.py` เติมคำพูดให้เอง.
>    **ต้องมีหลักฐานครบทุกแถว `BR-`/`MSG-`/`POST-`/`ALT-`** (gate บังคับ); `F-`/`BTN-`/`COL-`/`ACT-`/`PRE-`/`EC-` ใส่เท่าที่ช่วยตรวจได้ (ไม่บังคับ).
> 6. เขียน `req/README.md` (สารบัญหน้าจอ) แล้วรัน `{{PY}} {{S}}/fill_evidence.py {{WS}} {{FEATURE}}` → `{{PY}} {{S}}/verify_evidence.py {{WS}} {{FEATURE}}` แก้จน `fail_count = 0` (แก้เฉพาะรายการ fail ด้วย Edit ตรงจุด ห้ามอ่านไฟล์ REQ ทั้งไฟล์กลับ; ≤ 4 รอบ).
>
> ส่งกลับ (final message เป็น JSON เดียว): `{"screens":[{"scr_id","unit","req_file","open_questions":n,"unread_units":[...]}], "child_forms":[{"button","caption","unit","form_class","open_mode","condition","evidence"}], "external_programs":[{"button","target","evidence"}], "opener":"...", "sheet_vs_code_diffs":[...], "unresolved":[...], "verify": {"fail_count":n,"warn_count":n}}`.
> `unresolved` = สิ่งที่ทำไม่ได้/ไม่ครบ (บอกตรง ๆ).

---

## Agent C — auditor แบบ behavior (ตัวใหม่ context ว่าง; อ่านอย่างเดียว) — **รอบเดียว**

> ตรวจว่า REQ ของ `{{FEATURE}}` (`{{WS}}/specs/{{FEATURE}}/req/`) บรรยาย**พฤติกรรม**ตรงกับ code ใน `{{WS}}/source/` หรือไม่. **อ่านอย่างเดียว ห้ามแก้ไฟล์ใด ๆ.**
> REQ เขียนแบบ spec-first (ไม่มีชื่อ code) — หลักฐานอยู่ที่ `req/_evidence/*.evidence.md` (เครื่องตรวจแล้วว่า path:บรรทัดมีคำพูดนั้นจริง `verify_evidence.py` fail=0 — **ไม่ต้องตรวจซ้ำว่า quote มีอยู่**).
> เวลาของคุณใช้กับสิ่งที่เครื่องตรวจไม่ได้ เฉพาะ 4 เรื่อง:
> 1. **BR-/MSG-/POST-/ALT- ทุกแถว**: ประโยคใน REQ ตรงกับพฤติกรรมของ code ที่ evidence ชี้หรือไม่ (ข้ออ้างเกิน/เงื่อนไขตกหล่น/สลับ if-else/ข้อความ error ไม่ตรงตัวอักษร/"เสมอ" ทั้งที่มีเงื่อนไข). เปิดช่วงรอบ ๆ evidence ใน `source/` (handler ผ่าน `{{PY}} {{S}}/scan_form.py body <ไฟล์> <Method>`).
> 2. **พฤติกรรมที่ตกหล่น**: อ่าน handler ที่ปุ่ม/เหตุการณ์บนจอเรียก (`scan_form.py events`) แล้วหากฎ/ข้อความ/การเขียนข้อมูลที่ REQ ไม่ได้พูดถึง.
> 3. **ฟอร์มลูก**: รัน `{{PY}} {{S}}/scan_form.py opens <trunk> <.pas ของหน้าจอ>` เทียบกับ `child_forms`/`external_programs`; ฟอร์มที่พบแต่ไม่มี REQ (และไม่อยู่ใน VISITED) → `missing_behaviors`.
> 4. **ข้ออ้างจาก DB schema ใน Section 12/13**: nullable/PK/ความซ้ำ ที่ REQ อ้างและมีผลต่อพฤติกรรม ตรวจกับ `source/_db/**/<table>.table.txt` (ตัวที่ยืนยันไม่ได้ = `unsupported`).
> ข้ามได้: ชื่อ/ตำแหน่ง/ลำดับ field บน UI, คำอธิบายใน Section 1–2, AC-/US (อนุมานจาก BR/MSG). ไม่มีข้อบกพร่อง = บอกตรง ๆ ว่าตรวจอะไรไปบ้าง ห้ามเขียนว่า "น่าจะถูก".
> ส่งกลับ JSON: `{"contradictions":[{"id","req_says","code_says","evidence"}],"unsupported":[...],"missing_behaviors":[...],"speculation":[...],"checked":{"br":n,"msg":n,"post":n,"alt":n}}`.
> orchestrator แก้ตามผล (เปิดไฟล์ยืนยันก่อนแก้ทุกข้อ) → fill+verify ซ้ำ. **ไม่เรียก auditor ซ้ำ** เว้นแต่ contradictions ≥ 4 หรือแก้เกี่ยวกับฟอร์มลูก — กรณีนั้นเรียกอีก 1 รอบ (ตัวใหม่) เฉพาะ ID ที่แก้ (สูงสุด 2 รอบรวม).
