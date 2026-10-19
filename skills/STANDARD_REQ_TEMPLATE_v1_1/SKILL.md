---
installer: create-shortcut
name: STANDARD_REQ_TEMPLATE_v1_1
description: 'Standard Requirement Template v1.1 (Ocean Life Web Portal) — แม่แบบเอกสาร requirement 14 section (META, User Story, Screen, Input, Result, Business Rules, Error Messages, Pre/Post-condition, Process Flow, Open Issues, NFR, Success Criteria, Key Entities, Edge Cases, Assumptions) ใช้เป็น input ของ /speckit.specify. Use when user says "/STANDARD_REQ_TEMPLATE_v1_1", ต้องการสร้างไฟล์ REQ_[SCR-ID]_[ชื่อหน้าจอ].md ใหม่จาก template มาตรฐาน หรือให้ช่วยกรอก requirement หน้าจอ.'
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
5. แจ้งผู้ใช้ว่าขั้นถัดไปคือรัน `/speckit.specify` พร้อมแนบไฟล์ REQ นี้
