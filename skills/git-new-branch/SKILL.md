---
installer: create-shortcut
name: git-new-branch
description: 'สร้าง local branch ใหม่ชื่อ `ticket/<N>` ให้ repo ของ App ในกลุ่ม delphi group-insurance ที่ clone ไว้แล้ว โดย fetch + sync กับ base branch (default `master`) ล่าสุดจาก origin ก่อนแตกออกมาเสมอ เพื่อไม่ให้ทำงานค้างอยู่บน local master โดยไม่ตั้งใจ. Use when user says "/git-new-branch" หรือกำลังจะเริ่มแก้โค้ดสำหรับ ticket ใหม่ในโปรแกรมกลุ่มนี้.'
created_at: 2026-09-04T00:00:00+07:00
argument-hint: "[Path code ในเครื่อง] [เลข ticket] [base branch (default master)]"
---

# /git-new-branch — สร้าง local branch สำหรับเริ่มงาน ticket ใหม่

Sibling ของ [[git-clone-grouplife]] (ใช้ clone App ลงเครื่องก่อนหน้านี้แล้ว) และอยู่
คนละช่วงกับ [[git-merge-master]] (ทำตอน**จบ**งานเพื่อ merge เข้า master) — skill นี้
ทำตอน**เริ่ม**งาน: เตรียม local branch ชื่อ `ticket/<N>` ที่แตกออกมาจาก base branch
ล่าสุดจาก origin (ปกติคือ `master`) ให้พร้อมแก้โค้ด

**เหตุผลที่ต้องมี**: [[git-merge-master]] สมมติไว้เลยว่า current branch ตอนจะ merge
ต้องชื่อ `ticket/<N>` — ถ้าไม่มีขั้นตอนสร้าง branch นี้ไว้ก่อน ผู้ใช้เสี่ยงแก้โค้ดค้างอยู่
บน local `master` โดยไม่รู้ตัว แล้วไปเจอปัญหาตอน merge (local master มี commit ค้างที่
[[git-merge-master]] จะไม่ยอม reset ทับให้เงียบ ๆ)

**กฎเหล็ก**: ห้ามเดา ticket number หรือ base branch เอง ต้องได้จาก user ตรง ๆ และ
ห้าม `checkout -b` ทับ/ลบ branch เดิมที่มีอยู่แล้วโดยไม่ถามก่อนเสมอ

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — รับข้อมูล + ตรวจสอบ path local

รับ argument ตามลำดับ `<Path code ในเครื่อง> <เลข ticket> [base branch]` — ข้อไหนขาด
ให้ถามเพิ่ม ห้ามเดาแทน:

1. **Path code ในเครื่อง** — path ที่ clone ไว้แล้ว (ปกติมาจาก [[git-clone-grouplife]]
   ก่อนหน้านี้ในงานเดียวกัน) ต้องตรวจสอบก่อนแตะอะไรเสมอ:
   ```bash
   git -C "<path>" rev-parse --is-inside-work-tree
   git -C "<path>" remote get-url origin
   git -C "<path>" branch --show-current
   ```
   ถ้า path ไม่มีอยู่จริง หรือไม่ใช่ git repo จริง ให้หยุดแจ้ง user ทันที ห้ามเดาต่อ
2. **เลข ticket** (Gitblit) ที่จะเริ่มงาน (เช่น `15`) — ต้องได้มาจาก user ตรง ๆ ห้ามเดา
   — ใช้ตั้งชื่อ branch เป็น `ticket/<N>` ตาม convention เดียวกับ
   [[reference_claim_dataextraction_gitblit]]
3. **Base branch** — default `master` ถ้า user ไม่ได้ระบุ (ตรงกับ convention ที่
   [[git-merge-master]] ใช้อยู่แล้ว) ถามยืนยันเฉพาะถ้า user ต้องการ base อื่น

---

## Step 2 — เช็ค working tree สะอาดก่อนสร้าง branch

```bash
git -C "<path>" status --porcelain
```

- ถ้ามีผลลัพธ์ (มีไฟล์แก้ไข/untracked ค้างอยู่) ให้เตือน user ว่า `checkout -b` จะพา
  ไฟล์ที่แก้ค้างเหล่านี้ติดไปอยู่บน branch ใหม่ด้วย (ไม่ใช่การ commit ทับ แค่ working
  tree จะข้ามไปด้วย) — ถามยืนยันว่าตั้งใจแบบนี้จริงไหม หรืออยากจัดการ (commit/stash)
  ไฟล์เหล่านั้นก่อน ห้ามตัดสินใจแทน
- ถ้าสะอาดอยู่แล้ว ข้ามไป Step 3 ได้เลย

---

## Step 3 — เช็คว่า local branch `ticket/<N>` มีอยู่แล้วหรือยัง

```bash
git -C "<path>" show-ref --verify --quiet refs/heads/ticket/<N>
```

ถ้ามีอยู่แล้ว (exit code 0) **ห้ามเขียนทับ/ลบเองโดยไม่ถาม** — แจ้ง user แล้วให้เลือก:

- **Checkout branch เดิมที่มีอยู่** (ไม่สร้างใหม่ ข้าม Step 4-5 ไปแค่
  `git -C "<path>" checkout ticket/<N>`)
- **ลบของเดิมแล้วสร้างใหม่จาก base ล่าสุด** (เฉพาะถ้า user ยืนยันว่าของเดิมไม่ต้องการ
  แล้ว — เช็ค `git -C "<path>" log origin/ticket/<N>..ticket/<N>` ก่อนด้วยว่ามี commit
  ค้างที่ยังไม่ push หรือเปล่า ถ้ามีให้เตือนซ้ำก่อนลบจริง)
- **ยกเลิก**

ถ้ายังไม่มี (exit code ไม่ใช่ 0) ไปต่อ Step 4 ปกติ

---

## Step 4 — Fetch base branch ล่าสุดจาก origin

```bash
git -C "<path>" fetch origin <base branch>
```

ถ้า fetch fail (network/auth) ให้รายงาน error กับ user ตรง ๆ ห้ามลองซ้ำเดา ๆ เอง — ถ้า
เป็น host ที่รู้จักว่าใช้ password auth ผ่าน SSH (เช่น `10.100.2.187:29418`) ใช้
credential จาก [[reference_gitblit_credentials]] แทนการเดา (password rotate รายเดือน
ถ้า auth fail ให้ถาม user รหัสใหม่)

---

## Step 5 — สร้าง local branch `ticket/<N>` จาก base ล่าสุด

```bash
git -C "<path>" checkout -b ticket/<N> "origin/<base branch>"
```

- Branch ใหม่นี้เป็น **local-only** ทันทีหลังสร้าง — ยังไม่มีอยู่บน remote จนกว่าจะ
  push ครั้งแรก (ผ่าน [[git-commit-push]] โดยระบุ target branch เป็น `ticket/<N>`)
- ถ้า checkout fail (เช่น base branch ไม่มีจริงบน origin) ให้รายงาน error ตรง ๆ

---

## Step 6 — สรุปผล + บอกขั้นตอนถัดไป

```bash
git -C "<path>" log -1 --oneline
git -C "<path>" branch --show-current
```

สรุปให้ user: สร้าง branch `ticket/<N>` จาก `origin/<base branch>` (commit ล่าสุดคือ
อะไร) พร้อม path ที่ใช้งานอยู่ แล้วบอกขั้นตอนถัดไปตามลำดับงานปกติของกลุ่มนี้:

1. แก้โค้ดใน path นี้ตามปกติ
2. เมื่อพร้อม commit+push ใช้ [[git-commit-push]] โดยระบุ target branch = `ticket/<N>`
3. เมื่อพร้อม merge เข้า master ใช้ [[git-merge-master]] (ต้องอยู่บน branch
   `ticket/<N>` นี้ตอนเรียก)

---

## Notes

- Skill นี้จบงานที่สร้าง local branch เท่านั้น — ไม่ push, ไม่แตะ remote เลย
- ไม่ log time หรือ comment กลับ Redmine อัตโนมัติ
- ถ้า repo ไหนไม่ได้ใช้ pattern `ticket/N` แบบ Gitblit skill นี้ไม่รองรับ — แจ้ง user
  แทนที่จะเดาชื่อ branch อื่น

---

ARGUMENTS: $ARGUMENTS
