---
installer: create-shortcut
name: STANDARD_REQ_TEMPLATE_v1_1
description: 'Standard Requirement Template v1.1 (Ocean Life Web Portal) — แม่แบบเอกสาร requirement 14 section (META, User Story, Screen, Input, Result, Business Rules, Error Messages, Pre/Post-condition, Process Flow, Open Issues, NFR, Success Criteria, Key Entities, Edge Cases, Assumptions) ใช้เป็น input ของ /speckit-specify. Use when user says "/STANDARD_REQ_TEMPLATE_v1_1", ต้องการสร้างไฟล์ REQ_[SCR-ID]_[ชื่อหน้าจอ].md ใหม่จาก template มาตรฐาน หรือให้ช่วยกรอก requirement หน้าจอ.'
created_at: 2026-10-19T00:00:00+07:00
argument-hint: "[SCR-ID] [ชื่อหน้าจอ]"
---

# /STANDARD_REQ_TEMPLATE_v1_1

แม่แบบเต็มอยู่ที่ `STANDARD_REQ_TEMPLATE_v1_1.md` ในโฟลเดอร์เดียวกับ SKILL.md นี้ (อ่านด้วย Read ก่อนใช้ทุกครั้ง)

## ขั้นตอน
1. ถามผู้ใช้: Screen ID (`SCR-XXX-000`), ชื่อหน้าจอ, Module, URL (ถ้าส่งมาเป็น args ให้ใช้เลย)
2. อ่าน template แล้ว copy ไปเป็น `REQ_[SCR-ID]_[ชื่อหน้าจอ].md` ในโฟลเดอร์ที่ผู้ใช้ระบุ (ถ้าไม่ระบุ ให้ถามก่อน — ห้ามเขียนทับ template ต้นฉบับ)
3. กรอก `[PLACEHOLDER]` เท่าที่ผู้ใช้ให้ข้อมูลมา section ไหนไม่มีข้อมูลให้ใส่ `N/A` — ห้ามเดาเนื้อหาธุรกิจเอง
4. ไล่ตรวจ Pre-Check ท้ายไฟล์ให้ครบ แล้วสรุปรายการที่ยังขาด
5. แจ้งผู้ใช้ว่าขั้นถัดไปคือรัน `/speckit-specify` พร้อมแนบไฟล์ REQ นี้ (ชื่อ command ใน template ต้นฉบับเขียน `/speckit.specify` ให้ใช้ `/speckit-specify` ตาม skill ที่ติดตั้ง)

## ลำดับการใช้งานร่วมกับ Spec Kit (โปรเจกต์ใหม่)

ครั้งเดียวต่อโปรเจกต์:

| # | คำสั่ง | หมายเหตุ |
|---|---|---|
| 0 | `specify init` | หลัง init ลบ `<project>/.claude/skills` ทิ้ง เพราะ skill speckit ติดตั้งแบบ global แล้ว เก็บ `.specify/` และ `specs/` |
| 1 | `/speckit-constitution` | กำหนดหลักการ มาตรฐานโค้ด ข้อห้ามของโปรเจกต์ |

วนซ้ำต่อหน้าจอ/feature:

| # | คำสั่ง | หมายเหตุ |
|---|---|---|
| 2 | `/STANDARD_REQ_TEMPLATE_v1_1` | สร้าง `REQ_[SCR-ID]_[ชื่อ].md` กรอกให้ครบ ตรวจ Pre-Check 18 ข้อ ปิด Q ใน Section 9 |
| 3 | `/speckit-specify` + แนบไฟล์ REQ | ได้ `spec.md` |
| 4 | `/speckit-clarify` | ถามไม่เกิน 5 ข้อ ไม่ควรข้ามแม้ Section 9 ปิดครบแล้ว |
| 5 | `/speckit-plan` | ระบุ tech stack ที่ขั้นนี้ |
| 6 | `/speckit-tasks` | ได้ `tasks.md` |
| 7 | `/speckit-analyze` | ตรวจความสอดคล้อง spec/plan/tasks (อ่านอย่างเดียว) |
| 8 | `/speckit-checklist` | ข้ามได้ |
| 9 | `/speckit-implement` | ลงมือเขียนโค้ดตาม `tasks.md` |
| 10 | `/speckit-converge` | หลัง implement เทียบโค้ดกับ spec แล้วเพิ่ม task ที่ยังขาด |

`/speckit-taskstoissues` เลิกใช้แล้ว ไม่ต้องรัน

กฎ: เดินตามลำดับนี้เสมอ ถ้าจะข้ามขั้น (เช่นไป plan ก่อน specify) ต้องแจ้งผู้ใช้ก่อน และเมื่อ skill นี้ทำขั้น 2 เสร็จ ให้บอกผู้ใช้ว่าขั้นถัดไปคือขั้น 3
