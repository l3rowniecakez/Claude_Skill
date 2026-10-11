---
installer: create-shortcut
name: github-new-branch
description: 'สร้าง local branch ใหม่ชื่อ `issue/<N>` ให้ repo ที่ clone จาก GitHub ไว้แล้ว (ผ่าน /github-clone) โดย fetch + sync กับ base branch (default branch จริงของ repo บน GitHub) ล่าสุดจาก origin ก่อนแตกออกมาเสมอ เพื่อไม่ให้ทำงานค้างอยู่บน local default branch โดยไม่ตั้งใจ. Use when user says "/github-new-branch" หรือกำลังจะเริ่มแก้โค้ดสำหรับ GitHub issue ใหม่.'
created_at: 2026-10-11T09:29:39+07:00
argument-hint: "[Path code ในเครื่อง] [เลข GitHub issue] [base branch (default = default branch ของ repo)]"
---

# /github-new-branch — สร้าง local branch สำหรับเริ่มงาน GitHub issue ใหม่

Sibling ของ [[github-clone]] (ใช้ clone repo ลงเครื่องก่อนหน้านี้แล้ว) และอยู่คนละ
ช่วงกับ [[github-merge-master]] (ทำตอน**จบ**งานเพื่อเปิด PR เข้า default branch) —
skill นี้ทำตอน**เริ่ม**งาน: เตรียม local branch ชื่อ `issue/<N>` ที่แตกออกมาจาก
base branch ล่าสุดจาก origin ให้พร้อมแก้โค้ด

ต่างจาก [[git-new-branch]] (GitBlit) ตรงที่ GitHub **ไม่มีเลข ticket
auto-increment ที่ server กำหนดให้แบบ Gitblit** — เลขที่ใช้ตั้งชื่อ branch คือ
**เลข GitHub Issue** แทน ซึ่งก็ยังต้องเป็น issue ที่เปิดจริงบน remote แล้วเท่านั้น
เหตุผลเดียวกันกับ Gitblit: กันไม่ให้ชนกับเลขที่คนอื่นเปิด issue คนละใบพร้อมกัน และ
กันไม่ให้ branch ชื่อหลุดจากงานที่ track ได้จริงบน GitHub

**กฎเหล็ก**: ห้ามเดาเลข issue หรือ base branch เอง ต้องได้จาก user ตรง ๆ และ
**ต้องมี issue นั้นเปิดอยู่จริงบน GitHub แล้วเท่านั้น** (เช็คด้วย `gh issue view`
ใน Step 1) ห้าม `checkout -b` ทับ/ลบ branch เดิมที่มีอยู่แล้วโดยไม่ถามก่อนเสมอ —
ถ้า user ยังไม่มี issue จริง ให้แนะนำเปิดก่อนด้วย `gh issue create` (ถามหัวข้อ/
รายละเอียดจาก user ก่อนเสมอ ห้ามเดาเนื้อหา issue เอง)

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — รับข้อมูล + ตรวจสอบ path local + ตรวจสอบ issue จริง

รับ argument ตามลำดับ `<Path code ในเครื่อง> <เลข GitHub issue> [base branch]` —
ข้อไหนขาดให้ถามเพิ่ม ห้ามเดาแทน:

1. **Path code ในเครื่อง** — path ที่ clone ไว้แล้ว (ปกติมาจาก [[github-clone]]
   ก่อนหน้านี้ในงานเดียวกัน) ต้องตรวจสอบก่อนแตะอะไรเสมอ:
   ```bash
   git -C "<path>" rev-parse --is-inside-work-tree
   git -C "<path>" remote get-url origin
   git -C "<path>" branch --show-current
   ```
   ถ้า path ไม่มีอยู่จริง หรือไม่ใช่ git repo จริง ให้หยุดแจ้ง user ทันที ห้ามเดาต่อ
2. **เลข GitHub issue** (เช่น `42`) — **ต้องเป็น issue ที่เปิดอยู่จริงบน remote
   แล้วเท่านั้น** เช็คก่อนใช้งานทุกครั้ง:
   ```bash
   gh issue view <N> --repo "<owner>/<repo>"
   ```
   ถ้า error ว่าไม่พบ issue → แจ้ง user ว่ายังไม่มี issue นี้จริง ถามว่าจะเปิดใหม่
   ด้วย `gh issue create --repo "<owner>/<repo>"` ไหม (ถามหัวข้อ/รายละเอียดจาก
   user ก่อนเสมอ ห้ามเดาเนื้อหาเอง) แล้วใช้เลขที่ได้จริงจากคำสั่งนั้นมาทำ Step ถัดไป
3. **Base branch** — ถ้า user ไม่ได้ระบุ ใช้ default branch จริงของ repo นั้น:
   ```bash
   gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name'
   ```
   (ตรงกับ convention ที่ [[github-merge-master]] ใช้อยู่แล้ว) ถามยืนยันเฉพาะถ้า
   user ต้องการ base อื่น

---

## Step 2 — เช็ค working tree สะอาดก่อนสร้าง branch

```bash
git -C "<path>" status --porcelain
```

- ถ้ามีผลลัพธ์ (มีไฟล์แก้ไข/untracked ค้างอยู่) ให้เตือน user ว่า `checkout -b` จะพา
  ไฟล์ที่แก้ค้างเหล่านี้ติดไปอยู่บน branch ใหม่ด้วย — ถามยืนยันว่าตั้งใจแบบนี้จริงไหม
  หรืออยากจัดการ (commit/stash) ไฟล์เหล่านั้นก่อน ห้ามตัดสินใจแทน
- ถ้าสะอาดอยู่แล้ว ข้ามไป Step 3 ได้เลย

---

## Step 3 — เช็คว่า local branch `issue/<N>` มีอยู่แล้วหรือยัง

```bash
git -C "<path>" show-ref --verify --quiet refs/heads/issue/<N>
```

ถ้ามีอยู่แล้ว (exit code 0) **ห้ามเขียนทับ/ลบเองโดยไม่ถาม** — แจ้ง user แล้วให้
เลือก:

- **Checkout branch เดิมที่มีอยู่** (ไม่สร้างใหม่ ข้าม Step 4-5 ไปแค่
  `git -C "<path>" checkout issue/<N>`)
- **ลบของเดิมแล้วสร้างใหม่จาก base ล่าสุด** (เฉพาะถ้า user ยืนยันว่าของเดิมไม่
  ต้องการแล้ว — เช็ค `git -C "<path>" log origin/issue/<N>..issue/<N>` ก่อนด้วยว่า
  มี commit ค้างที่ยังไม่ push หรือเปล่า ถ้ามีให้เตือนซ้ำก่อนลบจริง)
- **ยกเลิก**

ถ้ายังไม่มี (exit code ไม่ใช่ 0) ไปต่อ Step 4 ปกติ

---

## Step 4 — Fetch base branch ล่าสุดจาก origin

```bash
git -C "<path>" fetch origin <base branch>
```

ถ้า fetch fail (network/auth) ให้รายงาน error กับ user ตรง ๆ — ถ้าเป็นปัญหา auth
ให้เช็ค `gh auth status` ก่อน แล้วแนะนำ `gh auth login` ถ้าหมดอายุ ห้ามเดาสาเหตุเอง

---

## Step 5 — สร้าง local branch `issue/<N>` จาก base ล่าสุด

```bash
git -C "<path>" checkout -b issue/<N> "origin/<base branch>"
```

- Branch ใหม่นี้เป็น **local-only** ทันทีหลังสร้าง — ยังไม่มีอยู่บน remote จนกว่าจะ
  push ครั้งแรก (ผ่าน [[github-commit-push]] โดยระบุ target branch เป็น
  `issue/<N>`)
- ถ้า checkout fail (เช่น base branch ไม่มีจริงบน origin) ให้รายงาน error ตรง ๆ

---

## Step 6 — สรุปผล + บอกขั้นตอนถัดไป

```bash
git -C "<path>" log -1 --oneline
git -C "<path>" branch --show-current
```

สรุปให้ user: สร้าง branch `issue/<N>` จาก `origin/<base branch>` (commit ล่าสุด
คืออะไร) พร้อม path ที่ใช้งานอยู่ แล้วบอกขั้นตอนถัดไปตามลำดับงานปกติ:

1. แก้โค้ดใน path นี้ตามปกติ
2. เมื่อพร้อม commit+push ใช้ [[github-commit-push]] โดยระบุ target branch =
   `issue/<N>`
3. เมื่อพร้อมรวมงานเข้า default branch ใช้ [[github-merge-master]] (เปิด Pull
   Request จาก `issue/<N>` — ต้องอยู่บน branch นี้ตอนเรียก)

---

## Notes

- Skill นี้จบงานที่สร้าง local branch เท่านั้น — ไม่ push, ไม่แตะ remote เลย
- ไม่ log time หรือ comment กลับ Redmine อัตโนมัติ
- ถ้า user อยากได้ branch ที่ GitHub ผูกกับ issue ให้อัตโนมัติ (แสดงใน issue
  sidebar) มี native command `gh issue develop <N> --checkout` เป็นทางเลือกเสริม
  ได้เช่นกัน แต่ skill นี้ใช้ flow git ธรรมดาตามด้านบนเป็นค่า default เพื่อให้
  สอดคล้องกับ [[github-commit-push]] / [[github-merge-master]]

---

ARGUMENTS: $ARGUMENTS
