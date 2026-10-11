---
installer: create-shortcut
name: github-merge-master
description: 'เตรียม + เปิด Pull Request บน GitHub จาก branch `issue/<N>` เข้า default branch (main/master) ผ่าน `gh pr create` แล้ว merge จริงผ่าน `gh pr merge` หลัง user confirm (ต่างจาก /git-merge-master ที่ทำ merge commit ตรงบน local แล้ว push — ตัวนี้ใช้ flow Pull Request มาตรฐานของ GitHub แทน). Use when user says "/github-merge-master" หรือต้องการรวมงานจาก branch issue เข้า default branch บน GitHub.'
created_at: 2026-10-11T09:29:39+07:00
argument-hint: "[owner/repo] [Path code ในเครื่อง] [เลข GitHub issue]"
---

# /github-merge-master — เปิด + merge Pull Request เข้า default branch (GitHub)

Sibling ของ [[github-new-branch]] (ใช้สร้าง branch `issue/<N>` ไว้ก่อนหน้านี้),
[[github-commit-push]] (ใช้ push commit ขึ้น branch `issue/<N>` ก่อนเปิด PR) —
**ต่างจาก [[git-merge-master]] (GitBlit) ตรงที่ GitHub ใช้ flow Pull Request
มาตรฐาน** ไม่ใช่การทำ merge commit ตรงบน local แล้ว push master เหมือน Gitblit
convention เดิม งานของ skill นี้คือ: เปิด PR จาก `issue/<N>` เข้า default branch,
ให้ user ตรวจสอบ/confirm แล้วค่อย merge จริงผ่าน `gh pr merge`

**กฎเหล็ก**: skill นี้**ไม่ merge อัตโนมัติทันทีที่เปิด PR** — ต้องโชว์ลิงก์ PR +
สถานะ (mergeable, review, CI check) ให้ user ดูก่อนเสมอ แล้วถาม confirm แยกต่างหาก
ก่อน `gh pr merge` จริงทุกครั้ง แม้ PR จะพร้อม merge แล้วก็ตาม (merge เข้า default
branch มีผลกระทบเทียบเท่า push master ใน Gitblit — ต้องมี confirm สองชั้นเหมือนกัน)

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — รับข้อมูล + ตรวจสอบ path local + ตรวจสอบ gh auth

```bash
gh auth status
```

ถ้ายังไม่ login/หมดอายุ → แจ้ง user ให้รัน `gh auth login` เอง ห้ามเดา credential

รับ argument ตามลำดับ `<owner/repo> <Path code ในเครื่อง> <เลข GitHub issue>` —
ข้อไหนขาดให้ถามเพิ่ม ห้ามเดาแทน:

1. **owner/repo** — ถ้า user ให้ URL มาแทน ให้ตัดเอาเฉพาะ `owner/repo` ออกมาเอง
2. **Path code ในเครื่อง** — path ที่มีการแก้ไข/commit+push ค้างอยู่บน branch
   `issue/<N>` แล้ว (ปกติมาจาก [[github-clone]] + [[github-new-branch]] +
   [[github-commit-push]] ทำไว้ก่อนหน้าในงานเดียวกัน) **ต้องตรวจสอบก่อนแตะอะไร
   เสมอ**:
   ```bash
   git -C "<path>" rev-parse --is-inside-work-tree
   git -C "<path>" branch --show-current
   git -C "<path>" remote get-url origin
   ```
   - ถ้า path ไม่มีอยู่จริง หรือไม่ใช่ git repo จริง หรือ remote ไม่ตรงกับ
     `<owner>/<repo>` ให้หยุดแจ้ง user ทันที ห้ามเดาต่อ
   - ถ้า current branch ไม่ใช่ `issue/<N>` (N จากข้อ 3) ให้เตือน user และถามยืนยัน
     ก่อนว่าจะดำเนินการต่อกับ branch ปัจจุบันนี้จริงไหม
3. **เลข GitHub issue** ที่งานนี้แก้ (เช่น `42`) — ต้องได้มาจาก user ตรง ๆ ห้ามเดา
   ใช้ประกอบ PR title/body (`Closes #<N>`) ใน Step 3

---

## Step 2 — เช็คว่า branch `issue/<N>` push ขึ้น remote แล้วหรือยัง

```bash
git -C "<path>" fetch origin
git -C "<path>" log "origin/issue/<N>..issue/<N>" 2>&1
```

- ถ้า `origin/issue/<N>` ยังไม่มีเลย หรือมี commit ค้างที่ยังไม่ push → แจ้ง user
  ว่าต้อง push ให้ครบก่อนเปิด PR ได้ (แนะนำ [[github-commit-push]] ถ้า user ยังไม่
  ได้ทำ) **ห้ามเปิด PR จาก branch ที่ไม่ sync กับ remote**
- ถ้า sync กันแล้ว (ไม่มี commit ค้าง) ไปต่อ Step 3

---

## Step 3 — เช็คว่ามี PR อยู่แล้วหรือยัง / เปิด PR ใหม่

```bash
gh pr list --repo "<owner>/<repo>" --head "issue/<N>" --json number,url,state
```

- **มี PR เปิดอยู่แล้ว** → ใช้ PR นั้นต่อ ข้าม `gh pr create` ไป Step 4 เลย
- **ยังไม่มี PR** → ถาม user หัวข้อ/รายละเอียด PR (หรือเสนอร่างจาก commit message
  ล่าสุดบน branch ให้ดูก่อน ห้ามเดาเนื้อหาเองทั้งหมดโดยไม่ให้ user เห็น) แล้วเปิด:
  ```bash
  gh pr create --repo "<owner>/<repo>" \
    --base "<default branch>" --head "issue/<N>" \
    --title "<หัวข้อ>" \
    --body "Closes #<N>

<รายละเอียด>"
  ```
  หา default branch ก่อนด้วย `gh repo view "<owner>/<repo>" --json
  defaultBranchRef --jq '.defaultBranchRef.name'` ถ้า user ไม่ได้ระบุ base อื่น

---

## Step 4 — โชว์สถานะ PR ให้ user ดูก่อน confirm merge

```bash
gh pr view <PR number> --repo "<owner>/<repo>" \
  --json url,mergeable,mergeStateStatus,reviewDecision,statusCheckRollup
```

แสดงให้ user เห็นชัดเจน: ลิงก์ PR, `mergeable` (CONFLICTING/MERGEABLE/UNKNOWN),
`reviewDecision` (ต้องการ approve ไหม), สถานะ CI check (`statusCheckRollup`)

- **`mergeable: CONFLICTING`** → หยุดแจ้ง user ว่า PR นี้ conflict กับ default
  branch ต้องไปแก้ conflict ก่อน (ปกติ rebase/merge default branch เข้า
  `issue/<N>` แล้ว push ใหม่) **ห้ามพยายามแก้ conflict เดาเอง**
- **`reviewDecision: REVIEW_REQUIRED`** (ถ้า repo ตั้ง branch protection ไว้) →
  แจ้ง user ว่า repo นี้ต้องมี approve ก่อนถึงจะ merge ได้ ห้ามพยายาม merge ทั้ง
  ที่ยังไม่ผ่าน
- CI check ยังรันไม่เสร็จ/fail → แจ้ง user สถานะตรง ๆ ถามว่าจะรอ หรือจะ merge
  ต่อทั้งที่ check ไม่ผ่าน (เฉพาะกรณี user ยืนยันเองเท่านั้น ห้ามข้ามให้อัตโนมัติ)

---

## Step 5 — Confirm สองชั้นก่อน merge จริง (เทียบเท่า warning master ของ Gitblit)

ถ้าทุกอย่างพร้อม (`MERGEABLE`, ผ่าน review requirement ถ้ามี) ให้แสดง warning
เด่นชัดก่อนถาม confirm รอบสุดท้าย — merge PR เข้า default branch มีผลเทียบเท่า
push ตรงเข้า master ใน Gitblit convention:

```bash
printf '\033[1;41;37m %s \033[0m\n' "!!! WARNING: กำลังจะ MERGE PR #<N> เข้า DEFAULT BRANCH (<base>) !!!"
```

ถามยืนยันแยกต่างหาก ("ยืนยันจริง ๆ ว่าจะ merge PR นี้เข้า <default branch>
ใช่ไหม?") — ตอบ "ไม่" ให้หยุดไว้แค่นี้ (PR เปิดไว้รอ merge ทีหลังได้ ไม่มีอะไร
เสียหาย)

ถามด้วยว่าจะ merge ด้วยวิธีไหน (ถ้า user ไม่ได้ระบุมาก่อน และ repo ไม่ได้บังคับ
วิธีเดียวไว้ผ่าน branch protection):

- **Merge commit** (`--merge`) — เก็บ history ของทุก commit บน branch ไว้ครบ
- **Squash** (`--squash`) — รวมเป็น 1 commit บน default branch
- **Rebase** (`--rebase`) — เรียง commit ต่อท้าย default branch ตรง ๆ ไม่มี merge
  commit

---

## Step 6 — Merge จริง

```bash
gh pr merge <PR number> --repo "<owner>/<repo>" --<merge|squash|rebase>
```

- ถามด้วยว่าจะลบ branch `issue/<N>` บน remote หลัง merge เลยไหม (เพิ่ม
  `--delete-branch`) — ถ้า user ไม่ตอบชัดเจน ให้ **ไม่ลบ** ไว้ก่อน (ปลอดภัยกว่า
  เก็บ branch ไว้เป็นประวัติ เหมือน [[git-merge-master]] ที่ไม่ลบ `ticket/<N>`)
- ถ้า merge fail (เช่น branch protection กันไว้, ไม่ผ่าน required check) ให้
  รายงาน error กับ user ตรง ๆ ห้ามลองวิธีอื่นแทนโดยไม่ถาม
- หลัง merge สำเร็จ สรุปผลสั้น ๆ ให้ user: PR number, merge method, default
  branch ปลายทาง, ลิงก์ PR

---

## Notes

- Skill นี้ไม่ log time หรือ comment กลับ Redmine อัตโนมัติ
- ไม่ลบ local branch `issue/<N>` หลัง merge (แม้จะลบบน remote ไปแล้วก็ตาม) เว้นแต่
  user สั่งเอง
- ถ้า repo ไหนไม่ได้ใช้ pattern `issue/N` (เช่น branch ตั้งชื่ออื่นตาม
  [[github-new-branch]] ที่ user เลือกไว้) ให้ใช้ชื่อ branch จริงที่ user ระบุแทน
  ไม่ใช่เดาว่าต้องเป็น `issue/<N>` เสมอ

---

ARGUMENTS: $ARGUMENTS
