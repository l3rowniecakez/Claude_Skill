---
installer: create-shortcut
name: git-commit-push
description: 'Commit + push source code ขึ้น remote git repo ผ่าน SSH โดยถามข้อมูลครบ 4 อย่างก่อนเสมอ (Repo URL แบบ SSH, ตำแหน่ง source code, เลข Ticket, ข้อความ Commit — auto-generate ให้ หรือให้พิมพ์เองก็ได้ แต่ต้องปิดท้ายด้วย #ai-work ทุกครั้ง) จากนั้นสรุปให้ user confirm ก่อน commit/push จริงเสมอ และถ้าปลายทางเป็น branch master ต้องมี warning สีแดงย้ำอีกรอบ ห้าม skip ขั้นตอน confirm แม้จะเรียก skill นี้มาแล้วก็ตาม (การเรียก skill นี้ไม่ได้แปลว่าอนุญาตให้ push ทันทีโดยไม่ถาม). Use when user says "/git-commit-push" หรือขอให้ push source code ขึ้น git.'
created_at: 2026-08-27T00:00:00+07:00
argument-hint: "[repo-url-ssh] [source-code-path] [ticket-number]"
---

# /git-commit-push — Commit + Push source code ขึ้น git ผ่าน SSH

Skill นี้มีหน้าที่เดียว: เอา source code ที่แก้ไว้แล้วไป `git add` / `commit` /
`push` ขึ้น remote repo ผ่าน SSH ให้ถูกต้อง ปลอดภัย และมี `#ai-work` tag ติดไปกับ
commit message เสมอ ([[feedback_tag_ai_work_comments]])

**กฎเหล็ก**: การเรียก `/git-commit-push` ไม่ใช่การอนุมัติให้ push อัตโนมัติ —
ต้องถามครบ 4 ข้อ + โชว์สรุปให้ confirm ก่อนแตะ git ทุกครั้ง แม้ user จะพิมพ์ข้อมูล
มาครบตั้งแต่แรกใน `$ARGUMENTS` ก็ตาม ยังต้องแสดงสรุปให้ confirm อีกครั้งอยู่ดี
([[feedback_never_auto_commit_wait_for_explicit_instruction]] — การเรียก skill นี้
คือ instruction ที่ชัดเจนพอสำหรับ "จะ push" แต่ยังไม่ใช่ "push เลยไม่ต้องถามอะไรอีก")

---

## Step 1 — ถามข้อมูลให้ครบ 4 อย่าง

ถ้ามาใน `$ARGUMENTS` แล้วครบก็ใช้เลย ข้อไหนขาดให้ถามเพิ่ม:

1. **Repo URL (SSH)** — ต้องเป็น SSH form เท่านั้น (`git@host:path.git` หรือ
   `ssh://user@host:port/path.git`) ถ้า user ให้มาเป็น `https://...` ให้ทักท้วงและขอ
   URL แบบ SSH แทน (เพราะ skill นี้ push ด้วย SSH key ไม่ใช่ password/token ผ่าน
   HTTPS)
2. **ตำแหน่ง source code** — path บนเครื่องที่จะ push จาก path นี้ต้องมีอยู่จริงและ
   เป็น git repo (`git -C <path> rev-parse --is-inside-work-tree`) ถ้ายังไม่ใช่ git
   repo ให้ถาม user ว่าจะ `git init` ให้ไหม อย่าทำเองโดยไม่ถาม
3. **เลข Ticket ที่จะ Push** — ใช้ประกอบ commit message (และถ้า repo นี้ใช้ pattern
   `ticket/N` แบบ Gitblit ก็ใช้ประกอบชื่อ branch ปลายทางได้ — ดู
   [[reference_claim_dataextraction_gitblit]] ถ้า host ตรงกับที่รู้จัก แต่ปกติ
   default target branch คือ branch ปัจจุบันของ local repo ไม่ใช่ ticket/N
   เว้นแต่ user ระบุ)
4. **ข้อความที่จะ Commit** — ดู Step 2

---

## Step 2 — Commit message (auto-generate หรือพิมพ์เอง)

ก่อนถาม ให้รัน `git -C <path> status` และ `git -C <path> diff` (หรือ
`--cached` ถ้ามีของ stage ค้างอยู่แล้ว) เพื่อดูว่าแก้อะไรไปบ้าง แล้วร่าง
auto-generated message จากสรุปนั้น รูปแบบ (ตาม pattern ที่ยืนยันแล้วใน
[[feedback_tag_ai_work_comments]] — "2026-07-20 refinement"):

```
Redmine #<ticket>: <short title สรุปว่าแก้อะไร> #ai-work
```

ใช้ `AskUserQuestion` ถามว่าจะใช้ auto-generate หรือพิมพ์เอง โดยโชว์ preview ของ
ข้อความ auto-generate ให้ดูก่อน:

- **ใช้ข้อความที่ auto-generate ให้ (Recommended)**
- **พิมพ์เอง**

ถ้าเลือกพิมพ์เอง ให้ user พิมพ์มา แล้ว **เช็คและเติม `#ai-work` ต่อท้ายให้เองเสมอ**
ถ้า user ไม่ได้พิมพ์มาเอง — ห้ามปล่อยให้หลุดแม้ user จะลืมใส่ก็ตาม (นี่คือจุดที่เคย
พลาดซ้ำหลายครั้งกับ Redmine notes มาแล้ว ตาม memory เดียวกัน ต้องเช็คทุกครั้งไม่ใช่
เชื่อว่าจำได้)

---

## Step 3 — สรุปให้ confirm ก่อน push จริง

รวบรวมข้อมูลทั้งหมดเป็นสรุปเดียว แสดงให้ user เห็นชัดเจนก่อนแตะ git จริง:

```
สรุปก่อน Push
=======================================
Repo (SSH)     : <repo url>
Source path    : <path>
Ticket         : #<ticket>
Target branch  : <branch ปัจจุบันของ local repo>
Commit message : <ข้อความสุดท้ายที่จะใช้ รวม #ai-work>
-----------------------------------------
ไฟล์ที่จะ commit:
<ผลจาก git status --short>
=======================================
```

- เช็คไฟล์ที่จะ stage ทุกไฟล์ก่อนว่ามีอะไรที่ดูเป็นความลับ/credential หลุดมาไหม
  (`.env`, `*credentials*`, `id_rsa`, ไฟล์ config ที่มี password) — ถ้าเจอ ให้เตือน
  user และถามว่าจะ exclude ไฟล์นั้นไหม ก่อน stage
- ใช้ `AskUserQuestion` ถาม **Confirm push / ยกเลิก** — ห้ามข้ามขั้นนี้ไม่ว่ากรณีใด

---

## Step 4 — Warning พิเศษถ้า target เป็น master

ถ้า target branch (หรือ branch ปลายทางที่จะ push ไป) คือ `master` หรือ `main` —
ก่อนถาม confirm รอบสุดท้าย ให้แสดง warning สีแดงเด่นชัดผ่าน terminal จริง (ใช้ ANSI
escape ผ่าน Bash เพื่อให้ขึ้นสีแดงจริงในหน้าจอ ไม่ใช่แค่ bold markdown):

```bash
printf '\033[1;41;37m %s \033[0m\n' "!!! WARNING: กำลังจะ PUSH ขึ้น branch MASTER โดยตรง !!!"
```

ตามด้วยข้อความอธิบายว่ากำลังจะ push อะไรไปที่ master แล้วถามยืนยันอีกรอบแยกจาก
Step 3 (สองชั้น ไม่รวบเป็นคำถามเดียว) เช่น "ยืนยันจริง ๆ ว่าจะ push ตรงเข้า
master ใช่ไหม?" — ตอบ "ไม่" ให้ยกเลิกทันที ไม่ต้องถามซ้ำว่าจะเปลี่ยน branch ไหม
(ให้ user เริ่มใหม่เองถ้าต้องการ target อื่น)

---

## Step 5 — ลงมือ commit + push

หลัง confirm ครบ (และผ่าน Step 4 กรณี master แล้ว):

```bash
git -C <path> add -A            # หรือเฉพาะไฟล์ที่ผ่านการเช็คใน Step 3
git -C <path> commit -m "<commit message สุดท้ายพร้อม #ai-work>"
git -C <path> push <repo url> HEAD:<target branch>
```

- ห้ามใช้ `--force`/`--force-with-lease` เว้นแต่ user สั่งชัดเจนแยกต่างหาก
- ห้ามใช้ `--no-verify` ข้าม hook เว้นแต่ user สั่งชัดเจน
- ถ้า repo ปลายทางตรงกับ host ที่รู้จักอยู่แล้วว่าใช้ password auth ผ่าน SSH (ไม่ใช่
  key) เช่น `10.100.2.187:29418` ให้ใช้ credential จาก
  [[reference_gitblit_credentials]] แทนการเดา (password rotate รายเดือน ถ้า auth
  fail ให้ถาม user รหัสใหม่แล้วอัปเดต memory) — นอกเหนือจากนี้ให้ถือว่าใช้ SSH key/
  agent ที่ตั้งไว้ในเครื่องอยู่แล้ว ห้ามสร้างหรือแก้ SSH key เอง
- ถ้า push fail เพราะ non-fast-forward ห้าม force push เอง ให้รายงาน error กับ
  user แล้วถามว่าจะ `git pull --rebase` ก่อนไหม
- หลัง push สำเร็จ สรุปผลสั้น ๆ ให้ user: commit hash, branch, ปลายทาง

---

## Notes

- Skill นี้จบงานที่ push เท่านั้น — ไม่เกี่ยวกับการ merge ticket branch เข้า master
  แบบ Gitblit tickets (ดู [[reference_claim_dataextraction_gitblit]] ถ้าต้องทำ merge
  แบบนั้นแยกต่างหาก ไม่ใช่ scope ของ skill นี้)
- ไม่ log time หรือ comment กลับ Redmine ให้อัตโนมัติ — ถ้าต้องการให้ใช้
  `/redmine-logtime` แยก

---

ARGUMENTS: $ARGUMENTS
