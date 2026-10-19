# STANDARD REQUIREMENT TEMPLATE
## Ocean Life Web Portal — Input สำหรับ /speckit.specify

<!--
วิธีใช้:
  1. Copy ไฟล์นี้ → rename เป็น  REQ_[SCR-ID]_[ชื่อหน้าจอ].md
  2. กรอกข้อมูลทุก [PLACEHOLDER] — section ไหนไม่มีให้ใส่ "N/A"
  3. ตรวจ Pre-Check ด้านล่างให้ครบก่อน run command
  4. รัน: /speckit.specify พร้อมแนบชื่อไฟล์นี้ใน Claude Code Chat

mapping กับ spec.md output:
  Section 1  → User Stories (US-xxx)
  Section 2  → Functional Requirements: Screen & Navigation
  Section 3  → Functional Requirements: Input (FR-xxx)
  Section 4  → Functional Requirements: Result & Actions (FR-xxx)
  Section 5  → Business Rules (BR-xxx)
  Section 6  → Error Messages (MSG-xxx)
  Section 7  → Pre-condition / Post-condition
  Section 8  → Process Flow (Happy Path + Alt Flows)
  Section 9  → Open Issues → Clarifications (Q-xxx)
  Section 10 → NFR
  Section 11 → Success Criteria (SC-xxx)
  Section 12 → Key Entities
  Section 13 → Edge Cases
  Section 14 → Assumptions
-->

---

## META

| รายการ | ค่า |
|--------|-----|
| Screen ID | `SCR-XXX-000` |
| ชื่อหน้าจอ | [ชื่อภาษาไทย / English] |
| Module | [ชื่อ Module] |
| URL | `/[module]/[path]` |
| Version | v1.0 |
| วันที่จัดทำ | DD/MM/YYYY |
| SA | [ชื่อ SA] |
| Feature Branch | `[NNN]-[feature-slug]` |
| สถานะ | Draft |

---

## SECTION 1 — OVERVIEW
> spec-kit ใช้ส่วนนี้สร้าง **User Stories** และ **Business Context**

### 1.1 วัตถุประสงค์
<!-- อธิบาย: หน้าจอนี้ทำอะไร / ใครใช้ / แก้ปัญหาอะไร (2–4 ประโยค) -->
[อธิบายวัตถุประสงค์]

### 1.2 Roles & Permissions

| Role | ชื่อตำแหน่ง | สิทธิ์ | ขอบเขตข้อมูล |
|------|-----------|-------|------------|
| `[role1]` | [ชื่อ] | View / View+Edit / Full | [ทั้งหมด / เฉพาะ branch ตัวเอง / ระบุ] |
| `[role2]` | [ชื่อ] | View | [ขอบเขต] |

### 1.3 Scope
**ใน scope:** [รายการ feature ที่พัฒนาในเวอร์ชันนี้]
**นอก scope:** [รายการที่ไม่รวม]

### 1.4 User Stories
<!--
กรอก 1 block ต่อ 1 Story — ห้ามข้าม "ตัวอย่างข้อมูลจริง"
ถ้าไม่มีตัวอย่าง → ใส่ "TBD" แล้วเปิด Q ใน Section 9
-->

**User Story [N]: [ชื่อ Story]**

- **As a** [Role]
- **I want to** [action ที่ต้องการ]
- **So that** [ประโยชน์ที่ได้รับ]

**ตัวอย่างข้อมูลจริง (Example Data):**
<!-- ❗ บังคับ — ระบุตัวอย่างที่จะนำไปใช้ใน Acceptance Scenario จริง -->
<!-- เช่น: ชื่อของรางวัล = "OCHI COIN 500 เหรียญ", ช่วงวัน = "01/07/2568–31/07/2568", ข้อความ SMS = "สวัสดีคุณ[ชื่อ] ขอมอบ OCHI COIN 500 เหรียญ สมัครได้ที่ [shortlink]" -->
- [ตัวอย่างค่าจริงที่ใช้ในระบบ]

**Acceptance Scenario:**
- **Given** [เงื่อนไขเริ่มต้น พร้อมค่าตัวอย่างจริง]
- **When** [action]
- **Then** [ผลลัพธ์ พร้อมค่าที่คาดหวังจริง]

---

## SECTION 2 — SCREEN STRUCTURE
> spec-kit ใช้ส่วนนี้สร้าง **FR: Navigation และ Layout**

### 2.1 Navigation Tabs ใน Module

| # | Tab | Screen ID | หมายเหตุ |
|---|-----|-----------|---------|
| 1 | [Tab 1] | SCR-XXX-001 | |
| 2 | [Tab 2] | SCR-XXX-002 | |
| N | **[หน้าจอนี้]** | **SCR-XXX-00N** | **← active** |

### 2.2 Layout Sections
<!-- ระบุ section หลักบนหน้าจอ เช่น Search Form / Result Grid / Detail Panel -->
1. [ส่วนที่ 1 เช่น "เงื่อนไขค้นหา"]
2. [ส่วนที่ 2 เช่น "ผลลัพธ์การค้นหา"]

---

## SECTION 3 — INPUT FIELDS
> spec-kit ใช้ส่วนนี้สร้าง **FR: Validation, Default Values, Cascade**

<!-- Type options: Date Picker | Dropdown | Multi-select Dropdown | Text Input | Checkbox | Radio -->
<!-- Required: Y = บังคับกรอก, N = ไม่บังคับ -->

| # | ชื่อ Field (TH) | Field Name (EN) | Type | Required | Default | Validation |
|---|----------------|----------------|------|----------|---------|------------|
| 1 | [ชื่อ TH] | [Field EN] | Date Picker | Y | วันปัจจุบัน | DD/MM/YYYY ไม่เกินวันปัจจุบัน |
| 2 | [ชื่อ TH] | [Field EN] | Date Picker | Y | วันปัจจุบัน | ≥ Field #1 |
| 3 | [ชื่อ TH] | [Field EN] | Dropdown | N | ทั้งหมด | Master Data: [ชื่อ list] |
| 4 | [ชื่อ TH] | [Field EN] | Dropdown | N | [ตาม role] | Cascade จาก Field #3 |
| 5 | [ชื่อ TH] | [Field EN] | Text Input | N | (ว่าง) | ตัวเลข [N] หลัก |
| 6 | [ชื่อ TH] | [Field EN] | Text Input | N | (ว่าง) | Format: [PATTERN] |

### 3.1 Cascade Dependencies

| เมื่อเปลี่ยน (Parent) | ผลกับ (Child) | พฤติกรรม |
|---------------------|--------------|---------|
| [Field A] | [Field B] | Filter list ของ B ตาม A + Reset ค่า B |

### 3.2 Default ตาม Role / Context

| Field | เงื่อนไข | Default Value |
|-------|---------|--------------|
| [Field] | ผู้ใช้มีสาขาประจำ | สาขาประจำของ user |
| [Field] | ผู้ใช้ไม่มีสาขาประจำ | [fallback เช่น "0001"] |

### 3.3 Action Buttons

| ปุ่ม | Action | พฤติกรรม |
|------|--------|---------|
| [ชื่อปุ่ม Primary] | [เช่น ค้นหา] | Validate → Call API → แสดงผล |
| [ชื่อปุ่ม Secondary] | [เช่น ล้างเงื่อนไข] | Reset ทุก field → default value [ล้าง/คง result] |

---

## SECTION 4 — RESULT & ROW ACTIONS
> spec-kit ใช้ส่วนนี้สร้าง **FR: Result Grid, Pagination, Row Actions**

### 4.1 Result Grid Columns

<!-- Sortable: Y/N | Format: DD/MM/YYYY | Text | Badge | CCCC:ชื่อ | Link | Icon -->

| # | ชื่อคอลัมน์ (TH) | Column (EN) | Format | Sortable |
|---|-----------------|------------|--------|----------|
| 1 | ดำเนินการ | Actions | Icons | N |
| 2 | [ชื่อ TH] | [EN] | DD/MM/YYYY | Y |
| 3 | [ชื่อ TH] | [EN] | Text | Y |
| 4 | [ชื่อ TH] | [EN] | Badge | N |

### 4.2 Display Rules

| รายการ | ค่า |
|--------|-----|
| Sort default | [ชื่อคอลัมน์] — [ล่าสุดก่อน / น้อยไปมาก] |
| Pagination | [N] รายการต่อหน้า |
| Result label | "แสดง X–Y จากทั้งหมด Z รายการ" |
| No result | แสดงข้อความแทนตาราง — ไม่แสดงตารางเปล่า |
| Max records | [N] รายการ (ถ้าเกิน → [บล็อก / แจ้งเตือน]) |

### 4.3 Row Actions (Action Icons)

| Icon | Label | เงื่อนไขแสดง | Role ที่เห็น | ไปหน้าจอ |
|------|-------|------------|------------|---------|
| 📄 | ดู (View) | ทุกแถว | ทุก Role | [SCR-ID หน้า Detail] |
| ✏️ | แก้ไข (Edit) | [field] = "[ค่า]" | [role ที่มีสิทธิ์] | [SCR-ID หน้า Edit] |

---

## SECTION 5 — BUSINESS RULES
> spec-kit ใช้ส่วนนี้สร้าง **BR-xxx** ใน spec.md

| BR-ID | หมวด | กฎ | Trigger | ผลลัพธ์ |
|-------|------|---|---------|--------|
| BR-001 | Validation | [กฎ] | [เงื่อนไข] | [สิ่งที่ระบบทำ] |
| BR-002 | Default | Default [field] = [ค่า] | เปิดหน้าจอ / login | ระบบ set อัตโนมัติ |
| BR-003 | Permission | [action] เฉพาะ Role [X] | User กด [action] | แสดง/ซ่อน/บล็อก |
| BR-004 | Cascade | เมื่อเปลี่ยน [Field A] → filter [Field B] | Field A เปลี่ยนค่า | Reset B + filter list |
| BR-005 | Data Scope | Role [X] เห็นข้อมูล [ขอบเขต] | Load data | Filter ตาม scope |

---

## SECTION 6 — ERROR MESSAGES
> spec-kit ใช้ส่วนนี้สร้าง **MSG-xxx** ใน spec.md

| MSG-ID | เงื่อนไขที่เกิด | ข้อความ (TH) | Severity | Action |
|--------|--------------|------------|---------|--------|
| MSG-001 | [validation ไม่ผ่าน] | [ข้อความแจ้งเตือน] | Error | Highlight field + บล็อก |
| MSG-002 | [validation อื่น] | [ข้อความ] | Error | Highlight field + บล็อก |
| MSG-003 | ไม่พบข้อมูล | [ข้อความ เช่น "ไม่พบข้อมูลที่ตรงกับเงื่อนไข"] | Info | แสดงข้อความแทนตาราง |
| MSG-004 | โหลด Master Data ไม่ได้ | [ข้อความ] + retry | Error | Error banner + retry + บล็อกค้นหา |
| MSG-005 | Session หมดอายุ | [ข้อความ] | Warning | Redirect → Login |
| MSG-006 | ไม่มีสิทธิ์ | [ข้อความ] | Error | Redirect → Unauthorized |

---

## SECTION 7 — PRE-CONDITION & POST-CONDITION
> spec-kit ใช้ส่วนนี้กำหนด **เงื่อนไขก่อน/หลัง** ที่ระบบต้องตรวจสอบ

### 7.1 Pre-condition (เงื่อนไขก่อนเข้าใช้งาน)
<!-- สิ่งที่ต้องเป็นจริงก่อนที่ user จะเข้าหน้าจอนี้ได้ -->

| # | เงื่อนไข | ถ้าไม่ผ่าน → |
|---|---------|------------|
| PRE-001 | User login ด้วย SSO แล้ว (session ยังไม่หมดอายุ) | Redirect → หน้า Login |
| PRE-002 | User มี Role ที่มีสิทธิ์เข้าถึงหน้าจอนี้ | Redirect → หน้า Unauthorized |
| PRE-003 | [เงื่อนไขอื่น เช่น Master Data โหลดสำเร็จ] | [พฤติกรรม] |
| PRE-004 | [เงื่อนไขอื่น เช่น Module เปิดใช้งานแล้ว] | [พฤติกรรม] |

### 7.2 Post-condition (ผลลัพธ์หลังดำเนินการสำเร็จ)
<!-- สถานะของระบบหลังจาก Happy Path เสร็จสมบูรณ์ -->

| # | ผลลัพธ์ที่เกิดขึ้น |
|---|-----------------|
| POST-001 | [เช่น ระบบแสดงผลการค้นหาใน Grid ถูกต้อง] |
| POST-002 | [เช่น Audit Log บันทึก action ของ user พร้อม timestamp] |
| POST-003 | [เช่น ข้อมูลใน Grid สะท้อนข้อมูล ณ เวลาที่ค้นหา] |
| POST-004 | [เงื่อนไขอื่น เช่น สถานะ record เปลี่ยนเป็น [ค่า]] |

---

## SECTION 8 — PROCESS FLOW
> spec-kit ใช้ส่วนนี้สร้าง **Happy Path + Alternative Flows** ใน spec.md

### 8.1 Happy Path

```
Step 1: User เข้า [Module] → คลิก Tab "[ชื่อหน้าจอนี้]"
Step 2: ระบบโหลด Master Data + set default values
Step 3: User กรอก/เลือกเงื่อนไข
Step 4: User กด "[ปุ่ม Primary]"
Step 5: ระบบ validate
          ├─ ผ่าน → Step 6
          └─ ไม่ผ่าน → ALT-001
Step 6: ระบบแสดงผลใน [Grid / Form]
Step 7: User คลิก [action ถัดไป เช่น View / Edit]
```

### 8.2 Alternative Flows

| ALT-ID | สถานการณ์ | ขั้นตอน |
|--------|---------|--------|
| ALT-001 | Validation ไม่ผ่าน | แสดง MSG-001/002 → บล็อก → User แก้ไข |
| ALT-002 | ไม่พบข้อมูล | แสดง MSG-003 แทน Grid |
| ALT-003 | กด "[ปุ่ม Secondary/Clear]" | Reset → default [คง/ล้าง result] |
| ALT-004 | โหลด Master Data ไม่ได้ | แสดง MSG-004 + retry |
| ALT-005 | Session หมดอายุ | แสดง MSG-005 → Redirect Login |

---

## SECTION 9 — OPEN ISSUES
> spec-kit ใช้ส่วนนี้สร้าง **Q-xxx** และ **Clarifications** ใน spec.md
> ✅ Q ที่ตอบแล้ว → กรอก "คำตอบ" + เปลี่ยน Status → **Closed**; Q ที่ยังเปิดอยู่ให้ระบุ "เกี่ยวกับ" ให้ชัด

| Q-ID | คำถาม | เกี่ยวกับ | Status | คำตอบ |
|------|-------|---------|--------|-------|
| Q-001 | [คำถามที่ยังไม่มีคำตอบ] | BR-00X / Field: [ชื่อ] | Open | |
| Q-002 | [คำถาม] | | Open | |

> ✅ Q ที่ตอบแล้ว → กรอก "คำตอบ" และเปลี่ยน Status → **Closed** ก่อน run /speckit.specify

---

## SECTION 10 — NON-FUNCTIONAL REQUIREMENTS
> spec-kit ใช้ส่วนนี้สร้าง **NFR section** ใน spec.md

| หมวด | รายการ | เป้าหมาย |
|------|--------|---------|
| Performance | Response time (ปกติ) | < [N] วินาที |
| Performance | Response time (ข้อมูลมาก) | < [N] วินาที |
| Concurrent Users | ผู้ใช้พร้อมกัน | [N] users |
| Browser | รองรับ | Chrome, Edge latest 2 versions |
| Auth | การยืนยันตัวตน | SSO ผ่าน Ocean Life Web Portal |
| Audit Log | บันทึก | user + timestamp ทุกครั้งที่ [action] |
| Session | Timeout | ตาม Portal Policy |

---

## SECTION 11 — ACCEPTANCE CRITERIA
> spec-kit ใช้ส่วนนี้สร้าง **SC-xxx (Success Criteria)** ใน spec.md

| AC-ID | Acceptance Criteria | วิธีทดสอบ |
|-------|--------------------|-----------| 
| AC-001 | หน้าจอโหลดได้พร้อม default values ถูกต้องทุก field | Manual |
| AC-002 | [happy path scenario] → แสดงผลถูกต้อง | Manual |
| AC-003 | Validation error → แสดง MSG + บล็อก | Manual |
| AC-004 | ไม่พบข้อมูล → แสดงข้อความ ไม่แสดงตารางเปล่า | Manual |
| AC-005 | [cascade] ทำงานถูกต้อง | Manual |
| AC-006 | [clear/reset] → reset form ถูกต้อง | Manual |
| AC-007 | ตาราง [N] columns + pagination + result label ครบ | Manual |
| AC-008 | Performance < [N] วินาที | Performance |
| AC-009 | Role [X] ไม่สามารถ [action] ได้ | Manual |
| AC-010 | ไม่มีสิทธิ์ → redirect Unauthorized | Manual |

---

## SECTION 12 — KEY ENTITIES
> spec-kit ใช้ส่วนนี้สร้าง **Entity definitions** และ **Data Dictionary** ใน spec.md
> กรอกทุก Entity หลักที่ feature นี้ใช้หรือสร้าง — ระบุ field สำคัญ ไม่ต้องครบทุก column

| Entity | คำอธิบาย | Field สำคัญ | หมายเหตุ |
|--------|---------|-----------|---------|
| [ชื่อ Entity 1] | [อธิบายสั้นๆ ว่าคืออะไร] | [field1], [field2], [field3 (nullable)] | [เช่น มีอยู่แล้ว / ต้องสร้างใหม่] |
| [ชื่อ Entity 2] | [อธิบาย] | [fields] | |
| [ชื่อ Entity 3] | [อธิบาย] | [fields] | |

<!--
ตัวอย่าง (SMS Birthday):
| Customer | ผู้รับ SMS | citizen_id, first_name, mobile_phone, birthdate, LINE_UID (nullable), APP_ID (nullable), consent_flag | มีอยู่ใน CSMS |
| Policy   | กรมธรรม์ของลูกค้า | policy_status, policy_type (O/I/P), position_code, unit_code | มีอยู่ |
| SMS Log  | บันทึกผลการส่ง SMS | log_id, citizen_id, mobile_phone (masked), sms_status, template_type | ต้องสร้างใหม่ |
-->

---

## SECTION 13 — EDGE CASES
> spec-kit ใช้ส่วนนี้สร้าง **Edge Cases** ใน spec.md
> ระบุสถานการณ์ที่ผิดปกติหรือ boundary condition ที่ระบบต้องรองรับ — อย่างน้อย 3 รายการ

| # | สถานการณ์ (Edge Case) | พฤติกรรมที่ถูกต้อง | เกี่ยวกับ FR/BR |
|---|---------------------|-----------------|---------------|
| EC-001 | [เงื่อนไข boundary เช่น ค่า = 0, NULL, ซ้ำ, หมดอายุ] | [ระบบต้องทำอะไร — skip / error / fallback] | FR-00X / BR-00X |
| EC-002 | [race condition เช่น 2 user บันทึกพร้อมกัน] | [พฤติกรรม] | |
| EC-003 | [ปีอธิกสุรทิน / เดือน 31 วัน / วันที่พิเศษ] | [พฤติกรรม] | |
| EC-004 | [ข้อมูลว่าง / whitespace-only / NULL] | [พฤติกรรม] | |
| EC-005 | [กรณี retry / idempotent] | [พฤติกรรม] | |

<!--
tip: ถามตัวเองว่า "ถ้า [field/ข้อมูล] เป็น NULL จะเกิดอะไร?"
     "ถ้า Job ล้มเหลวกลางคันแล้วรันใหม่ จะซ้ำไหม?"
     "ถ้า 2 คนทำพร้อมกัน ใครชนะ?"
-->

---

## SECTION 14 — ASSUMPTIONS
> spec-kit ใช้ส่วนนี้สร้าง **Assumptions** ใน spec.md
> ระบุสิ่งที่ SA สมมติ/เชื่อว่าจริง โดยไม่ได้ verify — ถ้าสมมติผิด spec จะผิดตาม

| # | Assumption | ผลกระทบถ้าผิด |
|---|-----------|--------------|
| A-001 | [สิ่งที่เชื่อว่ามีอยู่แล้ว เช่น infrastructure / master data / API] | [dev ต้องสร้างเพิ่ม / scope เปลี่ยน] |
| A-002 | [นิยามหรือ rule ที่เชื่อตาม existing system โดยไม่ redefine] | [behavior อาจต่างจาก spec] |
| A-003 | [ข้อมูลที่เชื่อว่า clean/valid โดยไม่ validate ซ้ำ] | [ต้องเพิ่ม validation step] |
| A-004 | [process ที่ไม่ enforce ในระบบ แต่ฝากไว้กับ manual process] | [risk: คนลืมทำ] |
| A-005 | [ขอบเขต scope ที่ตกลงกันว่าจะทำใน phase ถัดไป] | [ถ้า business เปลี่ยนใจ ต้อง re-spec] |

<!--
tip: ทุกครั้งที่คิดว่า "น่าจะ..." หรือ "คงจะ..." → ต้องเขียนเป็น Assumption
     ถ้า Assumption นั้นยังไม่แน่ใจเลย → เปิดเป็น Q ใน Section 9 แทน
-->

---

## PRE-CHECK ก่อน run /speckit.specify

| # | รายการ | ✅ |
|---|--------|---|
| 1 | META ครบ (Screen ID, URL, Branch) | ⬜ |
| 2 | Section 1: Roles + Scope ระบุชัด | ⬜ |
| 3 | Section 3: ทุก Field มี Type / Required / Default / Validation | ⬜ |
| 4 | Section 3: Cascade dependencies ระบุครบ | ⬜ |
| 5 | Section 4: Result Grid columns + Format ครบ | ⬜ |
| 6 | Section 4: Row Actions มีเงื่อนไขแสดงชัดเจน | ⬜ |
| 7 | Section 5: Business Rules ครอบคลุม edge cases | ⬜ |
| 8 | Section 6: Error Messages มี trigger + ข้อความ TH ครบ | ⬜ |
| 9 | Section 7: Pre-condition + Post-condition ระบุครบ | ⬜ |
| 10 | Section 8: Happy Path เขียนเป็น numbered steps | ⬜ |
| 11 | Section 8: Alt Flows ครอบคลุม: validation / no result / session / master data | ⬜ |
| 12 | Section 9: Q ที่ตอบแล้ว Status = Closed | ⬜ |
| 13 | Section 11: Acceptance Criteria ครอบคลุม happy path + permission + performance | ⬜ |
| 14 | Section 1.4: ทุก User Story มี "ตัวอย่างข้อมูลจริง" อย่างน้อย 1 ชุด (ห้าม placeholder ว่าง) | ⬜ |
| 15 | [ถ้า feature เกี่ยวกับ SMS] ระบุ character limit ต่อ message และได้รับการยืนยันจาก Marketing แล้ว (UCS-2 Thai = 70 chars/credit — เกินกว่านี้คิดค่าใช้จ่าย 2x) | ⬜ |
| 16 | Section 12: Key Entities ครบทุก entity ที่ feature ใช้/สร้าง พร้อม field สำคัญ | ⬜ |
| 17 | Section 13: Edge Cases อย่างน้อย 3 รายการ ครอบคลุม NULL / boundary / retry / race condition | ⬜ |
| 18 | Section 14: Assumptions ระบุทุกสิ่งที่ SA "เชื่อว่าจริง" โดยไม่ได้ verify — Q ที่ยังไม่แน่ใจเปิดใน Section 9 | ⬜ |

**เมื่อทุกรายการเป็น ✅ → พิมพ์ใน Claude Code Chat:**
```
/speckit.specify
นำ Requirement จากไฟล์ SPEC_[SCR-ID]_[ชื่อ].md
มาจัดทำ Feature Specification ภาษาไทย
สำหรับหน้าจอ "[ชื่อหน้าจอ]"
โมดูล [Module] ระบบ Ocean Life Web Portal
```

---

## CHANGE LOG

| วันที่ | Version | ผู้แก้ไข | รายการเปลี่ยนแปลง |
|-------|---------|---------|-----------------|
| DD/MM/YYYY | v1.0 | [SA Name] | สร้างเอกสารครั้งแรก |
| 26/06/2569 | v1.1 | รสรินทร์ | เพิ่ม Section 1.4 User Stories (พร้อม Example Data บังคับ); เพิ่ม Pre-Check ข้อ 14 (Example Data) และข้อ 15 (SMS character limit) |
| 26/06/2569 | v1.2 | รสรินทร์ | เพิ่ม Section 12 Key Entities, Section 13 Edge Cases, Section 14 Assumptions; เพิ่ม Pre-Check ข้อ 16–18; อัปเดต mapping comment |
