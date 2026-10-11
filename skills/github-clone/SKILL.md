---
installer: create-shortcut
name: github-clone
description: Clone repo จาก GitHub ผ่าน `gh` CLI ที่ login ไว้แล้วด้วย SSH protocol (ไม่ต้องจัดการ password/credential เองแบบ GitBlit) แล้วถามหา repo (owner/repo หรือ URL) + ตำแหน่ง folder ปลายทางก่อน clone จริง. Use when user says "/github-clone" หรือต้องการ clone repo จาก GitHub.
created_at: 2026-10-11T09:29:39+07:00
argument-hint: "[owner/repo หรือ repo URL] [ตำแหน่ง folder ปลายทาง]"
---

# /github-clone — Clone repo จาก GitHub ผ่าน SSH (gh CLI)

Sibling ของ [[git-clone]] แต่สำหรับ GitHub แทน GitBlit — ต่างจาก GitBlit
ตรงที่ GitHub auth ผ่าน `gh` CLI ที่ login ไว้แล้ว (ยืนยันแล้ว 2026-10-11:
`gh auth status` → logged in, `git_protocol: ssh`) **ไม่ต้องจำหรือจัดการ
password เองเลย** ไม่มีเรื่อง rotate รายเดือนแบบ GitBlit host เดิม

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — ตรวจสอบ gh auth ก่อนเสมอ

```bash
gh auth status
```

- ถ้ายังไม่ login หรือ token หมดอายุ → แจ้ง user ให้รัน `gh auth login` เอง
  (เป็น interactive login ผ่าน browser/device code ทำแทนไม่ได้) ห้ามเดา credential
  หรือพยายาม auth เอง
- ถ้า login อยู่แล้วแต่ `git_protocol` ไม่ใช่ `ssh` → แจ้ง user ว่าปกติ setup นี้ใช้
  SSH แต่เครื่องนี้ตั้งเป็น protocol อื่น ถามว่าจะดำเนินการต่อด้วย protocol ปัจจุบัน
  หรือจะเปลี่ยนก่อน (`gh config set git_protocol ssh`)

---

## Step 2 — ขอ parameter 2 ตัว

ถามให้ครบก่อน clone จริงเสมอ ห้ามเดาแทน user:

1. **repo** — รับได้ 2 แบบ:
   - `owner/repo` (เช่น `anthropics/claude-code`)
   - URL เต็ม (`https://github.com/owner/repo` หรือ `git@github.com:owner/repo.git`)
2. **ตำแหน่ง folder ที่จะ clone ไปวาง** — path ปลายทางในเครื่อง

ตรวจสอบก่อนว่า path ปลายทางยังไม่มีอยู่ หรือถ้ามีอยู่แล้วต้องเป็น empty directory —
ถ้ามีไฟล์อยู่แล้วให้เตือน user และถามยืนยันก่อน ห้าม clone ทับโดยไม่ถาม:

```bash
ls -A "<ตำแหน่ง folder ปลายทาง>" 2>/dev/null
```

---

## Step 3 — Clone ด้วย `gh repo clone`

```bash
gh repo clone <repo> "<ตำแหน่ง folder ปลายทาง>"
```

`gh repo clone` ใช้ auth + protocol ที่ login ไว้อัตโนมัติ (ไม่ต้อง pexpect ขับ
password prompt เหมือน [[git-clone]])

- Exit code `0` → clone สำเร็จ แจ้ง user พร้อม path ที่ clone มาลง
- Error ว่า `could not find <repo>` หรือ `HTTP 404` → repo ไม่มีจริง หรือ account
  ที่ login อยู่ไม่มีสิทธิ์เข้า (private repo ที่ไม่ได้เป็นสมาชิก) แจ้ง user ตรง ๆ
  ห้ามเดาสาเหตุเอง
- Error อื่น (path ปลายทางมีปัญหา ฯลฯ) → แจ้ง user ตรง ๆ
