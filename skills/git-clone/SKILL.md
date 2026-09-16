---
installer: create-shortcut
name: git-clone
description: Clone repo จาก GitBlit ผ่าน SSH username/password — จำรหัสผ่านข้ามเซสชันไว้ใน memory (เพราะรหัสผ่านของ Gitblit hostนี้ rotate ทุกเดือน) แล้วถามหา repo url + ตำแหน่ง folder ปลายทางก่อน clone จริง. Use when user says "/git-clone" หรือต้องการ clone repo ทั่วไปจาก GitBlit (ไม่ผูกกับ tracking sheet ของกลุ่ม delphi — ถ้าเป็น App ในกลุ่มนั้นให้ใช้ /git-clone-grouplife แทน).
created_at: 2026-09-16T13:25:58+07:00
argument-hint: "[repo url] [ตำแหน่ง folder ปลายทาง]"
---

# /git-clone — Clone repo จาก GitBlit ผ่าน SSH (username/password)

Skill ทั่วไปสำหรับ clone repo ใด ๆ จาก GitBlit ผ่าน SSH — ต่างจาก
[[git-clone-grouplife]] ตรงที่ตัวนี้**ไม่ผูกกับ tracking sheet** ของกลุ่ม
delphi group-insurance และไม่จำกัดว่าต้อง sparse-checkout เฉพาะ App เดียว —
รับ repo url + ปลายทางตรง ๆ แล้ว clone ทั้ง repo

**สำคัญ — auth method**: GitBlit host ที่ใช้งานจริง (`10.100.2.187:29418`) **ไม่รองรับ
SSH key auth เลย รองรับแค่ username/password** (ยืนยันแล้ว 2026-09-16 — ลอง RSA key
ก่อนแล้วโดน reject) ดังนั้น skill นี้ auth ด้วย username/password เสมอ ไม่ลอง SSH key
ก่อน

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — เตรียม credential (username/password)

1. ดึง host จาก repo url ที่ user ให้มา (หรือถ้ายังไม่มีให้ถามใน Step 2 ก่อน)
2. ถ้า host คือ `10.100.2.187` → ใช้ credential ที่จำไว้แล้วใน memory
   `reference_gitblit_credentials` (username + password ที่บันทึกไว้) **ทันที
   โดยไม่ต้องถาม user**
3. ถ้าเป็น GitBlit host อื่นที่ยังไม่เคยมี credential บันทึกไว้ → ถาม username +
   password จาก user ก่อน แล้วเสนอจะจำไว้ในลักษณะเดียวกัน (memory ใหม่ type
   `reference`) สำหรับใช้ครั้งถัดไป — ถามยืนยันก่อนบันทึกเสมอ (เป็นการเก็บ credential
   ข้าม session ต้องให้ user โอเคก่อน)

**กฎเรื่อง password rotate ทุกเดือน**: ถ้า auth ล้มเหลวด้วย password ที่จำไว้ (ทั้ง
host `10.100.2.187` หรือ host อื่นที่เคยจำไว้) → **ห้าม retry ซ้ำด้วย password เดิม**
ให้ถาม user ขอ password ปัจจุบันทันที แล้วอัปเดต memory ทับด้วยค่าใหม่ก่อนลอง clone
อีกครั้ง

---

## Step 2 — ขอ parameter 2 ตัว

ถามให้ครบก่อน clone จริงเสมอ ห้ามเดาแทน user:

1. **repo url** — SSH URL ของ repo บน GitBlit ที่จะ clone (เช่น
   `ssh://user@host:port/repo-name.git`)
2. **ตำแหน่ง folder ที่จะ clone ไปวาง** — path ปลายทางในเครื่อง (ถ้าเป็น path แบบ
   Windows เช่น `D:\WORK\...` แต่รันอยู่ใน WSL ให้แปลงเป็น `/mnt/d/WORK/...` ก่อนใช้จริง)

ตรวจสอบก่อนว่า path ปลายทางยังไม่มีอยู่ หรือถ้ามีอยู่แล้วต้องเป็น empty directory —
ถ้ามีไฟล์อยู่แล้วให้เตือน user และถามยืนยันก่อน ห้าม clone ทับโดยไม่ถาม:

```bash
ls -A "<ตำแหน่ง folder ปลายทาง>" 2>/dev/null
```

---

## Step 3 — Clone ด้วย pexpect (password auth ผ่าน SSH ต้องมี TTY)

`git clone` ธรรมดาผ่าน SSH password auth จะค้างรอ password prompt แบบ interactive —
ใช้ `pexpect` ขับแทน (มีติดตั้งอยู่แล้วบนเครื่องนี้):

```bash
python3 - "<repo url>" "<ตำแหน่ง folder ปลายทาง>" "<username>" "<password>" <<'PYEOF'
import pexpect
import sys

repo_url, dest, username, password = sys.argv[1:5]
child = pexpect.spawn(f'git clone {repo_url} {dest}', timeout=120, encoding='utf-8')
child.logfile = sys.stdout

i = child.expect(['password:', 'yes/no', pexpect.EOF, pexpect.TIMEOUT])
if i == 1:
    child.sendline('yes')
    i = child.expect(['password:', pexpect.EOF, pexpect.TIMEOUT])
if i == 0:
    child.sendline(password)
    child.expect(pexpect.EOF, timeout=120)

child.close()
sys.exit(child.exitstatus or 0)
PYEOF
```

- Exit code `0` → clone สำเร็จ แจ้ง user พร้อม path ที่ clone มาลง
- Exit code ไม่ใช่ `0` และ output มีคำว่า `Permission denied` → password auth fail
  ให้กลับไปทำตามกฎ "password rotate ทุกเดือน" ใน Step 1 (ถาม password ใหม่ แล้ว
  ลองใหม่ ห้าม retry password เดิมซ้ำ)
- Error อื่น (เช่น repo ไม่พบ, path ปลายทางมีปัญหา) → แจ้ง user ตรง ๆ ห้ามเดาสาเหตุเอง
