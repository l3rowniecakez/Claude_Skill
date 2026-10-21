# กฎการกรอก STANDARD_REQ_TEMPLATE_v1_1 สำหรับหน้าจอ Delphi ที่เขียนเสร็จแล้ว (as-built)

Template ต้นฉบับ: `~/.claude/skills/STANDARD_REQ_TEMPLATE_v1_1/STANDARD_REQ_TEMPLATE_v1_1.md` (อ่านด้วย Read ทุกครั้ง — ห้ามเขียนทับ
ต้นฉบับ). Template เขียนมาสำหรับเว็บที่ยังไม่ได้สร้าง; ที่นี่เรา**ถอด requirement จากระบบที่สร้างเสร็จแล้ว**
ดังนั้นทุกข้อความต้องมาจาก code จริง. เอกสารต่อ 1 หน้าจอ = 1 ไฟล์ `REQ_<SCR-ID>_<ชื่อ form/unit>.md` ใน `specs/<feature>/req/`.

## 1. หน้าจอ = ไฟล์ REQ

- หน้าจอ = form ของเมนู 1 แถวใน "Menu Contents" (tab วิเคราะห์ของเมนูนั้น) **รวม**แถวลูกที่ breadcrumb ขึ้นต้นด้วย
  `<breadcrumb เมนู> => [ปุ่ม: ...]` (ฟอร์มลูกที่เปิดจากปุ่ม — `read_menus.py list` คืนเป็น `descendant_rows`) — ทุกฟอร์มเป็นหน้าจอแยก
  ไฟล์แยก. Popup เล็ก ๆ ที่เป็น `MessageDlg`/`InputBox` ไม่ใช่หน้าจอ (บันทึกเป็น Error Message/Process Flow ของหน้าจอที่เปิดมัน).
- `SCR-ID` = `SCR-<APPCODE>-<NNN>`: `APPCODE` = AppName ตัด prefix `GroupLifeInsuranceSystem_` (ถ้ามี) → ตัวพิมพ์ใหญ่ เอาเฉพาะ A-Z0-9
  สูงสุด 12 ตัว (เช่น `AcHospital_P` → `ACHOSPITALP`, `GroupLifeInsuranceSystem_Benefits` → `BENEFITS`); `NNN` = คอลัมน์ `No` ของ
  **แถวของหน้าจอนั้นเอง** ใน Menu Contents (3 หลัก) — คงที่ ไม่เปลี่ยนเมื่อรันซ้ำ.
- **ฟอร์มที่ไล่พบจาก code แต่ไม่มีแถวใน Menu Contents** (เช่น ฟอร์มลูกที่ analyst ไม่ได้บันทึก): `SCR-ID` = `SCR-<APPCODE>-<NNN ของหน้าจอแม่>-<k>` โดย `k` = ลำดับที่พบ (1,2,…) ตามลำดับ handler ใน `.pas` ของแม่ (คงที่เมื่อ source ไม่เปลี่ยน).
  ไล่ต่อเป็นทอดได้ลึกสุด 5 ชั้น; unit ที่มี REQ แล้ว (ในเมนูเดียวกันหรือเมนูอื่นใน `specs/*/req/` — หาจากบรรทัด `unit:` ใน META) **ห้ามทำซ้ำ** ให้ลิงก์ไปไฟล์เดิม; ฟอร์มของโปรแกรมภายนอก (WinExec) ไม่ทำ REQ ที่นี่ (บันทึกว่าเรียกอะไรเท่านั้น).
- ชื่อไฟล์: `REQ_<SCR-ID>_<ชื่อ unit ของ form>.md` เช่น `REQ_SCR-ACHOSPITALP-001_ACHospital_U.md`.
- ท้ายสุดสร้าง `req/README.md` = ตารางสารบัญ (SCR-ID | ชื่อหน้าจอ | unit .pas/.dfm | เปิดจาก (เมนู หรือ ปุ่มของ SCR-ID ไหน) | ไฟล์ REQ).

## 2. กฎเหล็ก (ผิดข้อใดข้อหนึ่ง = verify_evidence.py ไม่ผ่าน หรือผู้ตรวจ reject)

1. **ทุกข้อเท็จจริงมีหลักฐาน** ใน `APPENDIX A — EVIDENCE MAP` (รูปแบบข้อ 4). ไม่มีหลักฐาน = ห้ามเขียน.
2. **อ่านจาก snapshot ใน `source/` เท่านั้น** (ดึงด้วย `fetch_source.py`) — ไม่อ่านสดจาก Gitblit, ไม่เชื่อ Sheet analyst ลอย ๆ.
   Sheet analyst ใช้เป็น "แผนที่" (หา unit/store/ตาราง) เท่านั้น; ถ้า Sheet ขัดกับ code → **code ชนะ** แล้วจดความต่างไว้ใน
   Section 9 เป็น `Q-xxx` ชนิด "Sheet analyst ไม่ตรง code: …" (ให้ผู้ใช้รู้ว่า Sheet ควรอัพเดท).
3. **ห้ามคงแถว/ข้อความตัวอย่างของ template** ที่ code ไม่รองรับ (เช่น SSO, Role, Pagination, Browser, Audit Log — โปรแกรม Delphi
   desktop ส่วนใหญ่ไม่มี). Section/ตารางที่ไม่มีใน code → เขียนบรรทัดเดียว `N/A — ไม่พบใน code (ตรวจ: <unit ที่อ่านแล้ว>)`.
4. **ห้ามเดา** — สิ่งที่ code ตอบไม่ได้ (เจตนาธุรกิจ, ข้อมูลจริงในตาราง, พฤติกรรมของ unit ที่ไม่ได้ดึงมาอ่าน, runtime config จากไฟล์ .ini/.dat)
   ให้เปิดเป็น `Q-xxx` Status=Open ใน Section 9 (ระบุ "เกี่ยวกับ" ชัดเจน) — **ห้ามใช้คำว่า "น่าจะ/คงจะ/probably"** นอก Section 9/14.
5. **ตัวอย่างข้อมูลจริง (Section 1.4)**: ใช้ได้เฉพาะค่าที่เป็น literal/ค่าคงที่/Caption ที่เห็นใน code. ห้ามไป SELECT ข้อมูลจริงจาก DB
   (ข้อมูลลูกค้า + ห้ามยิง query แปลก ๆ). ไม่มี literal ที่ใช้เป็นตัวอย่างได้ → `TBD` + เปิด Q (template อนุญาตไว้แล้ว).
6. **ข้อความ error/คำเตือน ต้องตรงตัวอักษร** (ภาษาไทยตามที่ปรากฏใน code, รวมเครื่องหมาย). ข้อความที่ประกอบด้วย runtime value ให้เขียนเป็น
   `...'<ชื่อตัวแปร>'...` ตามโค้ดจริง.
7. ไม่แก้/ไม่เสนอให้แก้ code. ข้อบกพร่องที่พบใน code (เช่น proc ที่ไม่ถูกเรียก) → บันทึกตามจริงใน Section 14/Section 9 ไม่ "แก้" ใน spec.

## 3. การแปลง Section ของ template → สิ่งที่หาได้ใน Delphi

| Section | ดึงจาก |
|---|---|
| META | Screen ID/ชื่อ/Module = ตามข้อ 1; `URL` = `N/A (Delphi desktop) — unit: <Unit>.pas`; Version `v1.0`; วันที่ = วันนี้ (พ.ศ./ค.ศ. ตาม template ใช้ DD/MM/YYYY ค.ศ.); `SA` = `N/A — ถอดจาก source ปัจจุบันโดย Claude Code (reverse-spec)`; Feature Branch = ชื่อ feature dir; สถานะ = `As-Built (ตรง code ณ <วันนี้>, repo <repo> master)` |
| 1.1 วัตถุประสงค์ | สรุปจาก Caption/ชื่อ form + สิ่งที่ handler ทำจริง (2–4 ประโยค) |
| 1.2 Roles | เฉพาะที่ code ตรวจจริง (user level/สิทธิ์/`Enabled := (Level …)`, ตัวแปร global ของ user). ไม่มี → `N/A` + Q ว่าสิทธิ์ควบคุมที่เมนูหลักหรือไม่ (ถ้าไม่ได้อ่าน main form) |
| 1.3 Scope | ใน scope = สิ่งที่หน้าจอทำจริง; นอก scope = ฟอร์ม/โปรแกรมที่ปุ่มเรียกต่อ (ระบุว่าอยู่ใน REQ ไหน หรือ App ไหนถ้า WinExec) |
| 1.4 User Story | 1 story ต่อ flow หลักของหน้าจอ (ดู/เพิ่ม/แก้/ลบ/พิมพ์…) จาก event handler จริง; Given/When/Then ใช้ค่า literal จริงเท่านั้น (ข้อ 2.5) |
| 2.1 Navigation | ทางเข้าเมนู = breadcrumb เต็มจาก Menu Contents; ฟอร์มลูกที่เปิดจากปุ่ม = SCR-ID ของไฟล์ REQ ลูก |
| 2.2 Layout | `TPageControl/TTabSheet/TPanel/TGroupBox` จาก `.dfm` (ใช้ `*.dfm.decoded.txt` อ่านคำไทย) |
| 3 Input Fields | ทุก `TEdit/TMaskEdit/TComboBox/TDateTimePicker/TCheckBox/TRadioGroup/TMemo/DBEdit…` ที่ผู้ใช้กรอก/เลือก: Type, Required (ดูจากโค้ด validate/`ShowMessage` ตอน Save), Default (`.dfm` property/`FormShow`/`FormCreate`), Validation (`OnExit/OnKeyPress/MaxLength/EditMask`/เช็คตอน Save). **ID ใน cell แรก = `F-001`, `F-002` …** |
| 3.1 Cascade | handler ที่ตั้ง/เคลียร์/กรอง component อื่น (`OnChange/OnExit/OnClick` ของ combo ฯลฯ) |
| 3.2 Default ตาม Role | เฉพาะที่ code มีเงื่อนไข; ไม่มี → N/A |
| 3.3 Action Buttons | ทุก `TButton/TBitBtn/TSpeedButton/TToolButton/TMenuItem/TAction` ที่มี handler — พฤติกรรมตามโค้ด. **ID = `BTN-001` …** |
| 4.1 Grid | คอลัมน์ `TDBGrid/TStringGrid/TcxGrid/TListView` (`Columns`, field ที่ผูก, `DisplayFormat`, sortable จาก `OnTitleClick`/ORDER BY). **ID = `COL-001` …** (ไม่มี grid → N/A) |
| 4.2 Display Rules | sort default (ORDER BY จริง), paging (ถ้ามี), "ไม่พบข้อมูล" (ข้อความจริง), limit — เขียนเป็นตาราง key/value ตาม template; ข้อที่ไม่มีใน code ลบแถว |
| 4.3 Row Actions | `OnDblClick/OnCellClick/popup menu` ของ grid ที่เปิดฟอร์ม/ทำงานต่อ. **ID = `ACT-001` …** |
| 5 Business Rules | เงื่อนไข/การคำนวณ/การตรวจสอบใน handler และใน stored proc/SQL ที่เรียก (อ่านจาก `source/_db/...`). **ID = `BR-001` …** (หมวด Validation/Default/Permission/Cascade/Data Scope/Calculation/Persistence) |
| 6 Error Messages | ทุก `ShowMessage/MessageDlg/Application.MessageBox/raise Exception/` ข้อความที่ proc ส่งกลับ — ข้อความตรงตัว, Severity ตามชนิด dialog (mtError/mtWarning/mtInformation/mtConfirmation), Action = สิ่งที่โค้ดทำต่อ. **ID = `MSG-001` …** |
| 7.1 Pre-condition | สิ่งที่ code ต้องการก่อนเปิดฟอร์ม (ตัวแปร global ที่ต้องตั้งค่า, connection, พารามิเตอร์ `ParamStr`, ฟอร์มที่ต้องเปิดอยู่ก่อน) **ID = `PRE-001`** — ไม่มี → N/A |
| 7.2 Post-condition | ผลลัพธ์ที่เกิดจริงในข้อมูล (INSERT/UPDATE/DELETE ตารางไหน, ไฟล์ที่สร้าง) **ID = `POST-001`** |
| 8 Process Flow | Happy Path เป็น numbered steps ตามลำดับ event จริง (`FormCreate → FormShow → …`); Alt Flows จากทางแยกใน handler. **ID Alt = `ALT-001`** |
| 9 Open Issues | ทุกอย่างที่ code ตอบไม่ได้ + ความต่าง Sheet↔code + unit ที่ไม่ได้ดึงมาอ่าน (ระบุชื่อ). Status = Open ทั้งหมด (ปิดไม่ได้เพราะไม่มีผู้ตอบในรอบนี้) |
| 10 NFR | เฉพาะที่ code ระบุ (timeout ของ connection/command, `Screen.Cursor`, จำกัดจำนวนแถว) ที่เหลือ N/A. ไม่ต้องมี ID |
| 11 Acceptance Criteria | `AC-001…` อธิบายพฤติกรรมที่ตรวจได้จริงของหน้าจอ (ผูกกับ BR/MSG/BTN) — วิธีทดสอบ = Manual. ไม่ต้องมี evidence (อนุมานได้จาก BR/MSG) |
| 12 Key Entities | ตาราง/view ที่หน้าจออ่าน-เขียน จาก snapshot `source/_db/<db>/*.table.txt` (ชื่อคอลัมน์/ชนิด/PK/FK จริง) — ใช้ ER tab ของ Sheet เป็นแผนที่ แต่ **ต้องยืนยันคอลัมน์กับ `.table.txt`** ; หมายเหตุ = "มีอยู่แล้ว (as-built)" |
| 13 Edge Cases | เฉพาะกรณีที่ code จัดการจริง (NULL, ไม่พบข้อมูล, ซ้ำ, transaction/rollback) **ID = `EC-001`**; กรณีที่ code ไม่ได้จัดการ → บันทึกเป็น "ไม่มีการจัดการใน code" + Q (ไม่ต้องคิดพฤติกรรมให้) |
| 14 Assumptions | ระบุตรง ๆ: DB schema อ่านจาก SIT `10.100.2.52` ณ วันที่สร้าง, source = master ของ repo ณ วันที่สร้าง, unit ที่ไม่ได้อ่าน, runtime config ที่อ่านไม่ได้ |
| Pre-Check 18 ข้อ | ตอบเป็น ✅/❌ + หมายเหตุสั้น ๆ; ข้อที่เป็นของงาน SA ใหม่ (ข้อ 12 ปิด Q, ข้อ 15 SMS) → `N/A (as-built)` |
| CHANGE LOG | `v1.0 | <วันนี้> | Claude Code | ถอดจาก source ปัจจุบัน (reverse-spec)` |

## 4. APPENDIX A — EVIDENCE MAP (ท้ายไฟล์ REQ ทุกไฟล์ ต่อจาก CHANGE LOG)

~~~markdown
## APPENDIX A — EVIDENCE MAP
```evidence
F-001 :: EdForm/EdAcHospital.pas:120-124 :: `edCode.MaxLength := 10;`
MSG-001 :: EdForm/EdAcHospital.pas:440 :: `ShowMessage('บันทึกข้อมูลเรียบร้อย!');`
BR-004 :: _db/OceanLife/sp_xxx.sql:35 :: `WHERE Hospital_Type = 6`
COL-002 :: EdForm/EdAcHospital.dfm.decoded.txt:812 :: `Title.Caption = 'ชื่อโรงพยาบาล'`
```
~~~

(ตัวอย่างข้างบนเป็นรูปแบบเท่านั้น — ค่าจริงต้องมาจากไฟล์ใน `source/` ที่อ่านจริงในรอบนี้)

- รูปแบบบรรทัด: `<ID> :: <path>:<บรรทัด หรือ บรรทัดเริ่ม-จบ> :: \`<คำพูดตรงตัว>\``; คั่นด้วย ` :: ` (เว้นวรรคสองข้าง).
  **ย่อได้**: เขียนแค่ `<ID> :: <path>:<บรรทัดเริ่ม[-จบ]>` แล้วรัน `fill_evidence.py <workspace> <feature_dir>` — สคริปต์คัดลอกคำพูดตรงตัวจากช่วงบรรทัดนั้นให้ (ช่วงแคบ 1–3 บรรทัด; ยาวเกิน 220 ตัวอักษรใช้บรรทัดแรก). ช่วงที่ชี้ผิดยังทำให้ verify ไม่ผ่านตามเดิม.
- `<path>` = path ใต้ `source/` (ใช้ท้าย path ที่ไม่ซ้ำก็พอ); `.dfm` อ้างผ่าน `*.dfm.decoded.txt` ได้ (เลขบรรทัดเท่า `.dfm`).
- คำพูด = **คัดลอกตรงตัวจากไฟล์** 1 statement/1 property, ไม่เกิน ~200 ตัวอักษร, ห้ามสรุป/แปล/ย่อ (ช่องว่าง/ขึ้นบรรทัดไม่นับ แต่ตัวอักษรต้องตรง รวมตัวพิมพ์เล็ก-ใหญ่).
  คำพูดมี `|` ในตาราง markdown ไม่เป็นปัญหา เพราะอยู่ในบล็อก fenced.
- **เซลล์แรกของแถวตารางที่มี ID ต้องมีแค่ ID ล้วน** (เช่น `BTN-001`) — ใส่ชื่อปุ่ม/คอมโพเนนต์ไว้เซลล์ถัดไป ไม่งั้น verify_evidence อ่านเป็น orphan-evidence.
- ID ที่ต้องมีหลักฐาน = ทุก ID ที่เป็นเซลล์แรกของแถวตารางใน Section 3/3.3/4.1/4.3/5/6/7/8.2/13 (`F-`, `BTN-`, `COL-`, `ACT-`, `BR-`, `MSG-`,
  `PRE-`, `POST-`, `ALT-`, `EC-`). ID เดียวมีหลักฐานได้หลายบรรทัด. `AC-`, `Q-`, `A-`, `US` ไม่ต้องมี.
- ตรวจด้วย: `python verify_evidence.py <workspace> <feature_dir>` — ต้อง `fail_count = 0`.
