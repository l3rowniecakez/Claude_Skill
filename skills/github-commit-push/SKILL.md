---
installer: create-shortcut
name: github-commit-push
description: 'Commit + push source code ขึ้น remote GitHub repo ผ่าน SSH (auth ผ่าน `gh` CLI ที่ login ไว้แล้ว) โดยถามข้อมูลครบ 4 อย่างก่อนเสมอ (Repo owner/repo หรือ URL, ตำแหน่ง source code, เลข GitHub issue ที่เกี่ยวข้อง (ถ้ามี), ข้อความ Commit — auto-generate ให้ หรือให้พิมพ์เองก็ได้ แต่ต้องปิดท้ายด้วย #ai-work ทุกครั้ง) จากนั้นสรุปให้ user confirm ก่อน commit/push จริงเสมอ และถ้าปลายทางเป็น default branch (main/master) ต้องมี warning สีแดงย้ำอีกรอบ ห้าม skip ขั้นตอน confirm แม้จะเรียก skill นี้มาแล้วก็ตาม. Use when user says "/github-commit-push" หรือขอให้ push source code ขึ้น GitHub.'
created_at: 2026-10-11T09:29:39+07:00
argument-hint: "[owner/repo หรือ repo URL] [source-code-path] [เลข GitHub issue ถ้ามี]"
---

# /github-commit-push — Commit + Push source code ขึ้น GitHub ผ่าน SSH

Skill นี้มีหน้าที่เดียว: เอา source code ที่แก้ไว้แล้วไป `git add` / `commit` /
`push` ขึ้น remote GitHub repo ผ่าน SSH ให้ถูกต้อง ปลอดภัย และมี `#ai-work` tag
ติดไปกับ commit message เสมอ ([[feedback_tag_ai_work_comments]]) — Sibling ของ
[[git-commit-push]] (GitBlit) แต่ auth ผ่าน `gh` CLI ที่ login ไว้แล้ว **ไม่ต้อง
จัดการ password/SSH key เอง** เหมือน GitBlit host เดิม

**กฎเหล็ก**: การเรียก `/github-commit-push` ไม่ใช่การอนุมัติให้ push อัตโนมัติ —
ต้องถามครบ 4 ข้อ + โชว์สรุปให้ confirm ก่อนแตะ git ทุกครั้ง แม้ user จะพิมพ์ข้อมูล
มาครบตั้งแต่แรกใน `$ARGUMENTS` ก็ตาม ยังต้องแสดงสรุปให้ confirm อีกครั้งอยู่ดี
([[feedback_never_auto_commit_wait_for_explicit_instruction]])

---

## Step 1 — ตรวจสอบ gh auth

```bash
gh auth status
```

ถ้ายังไม่ login/token หมดอายุ → แจ้ง user ให้รัน `gh auth login` เอง ห้ามเดา
credential หรือพยายาม auth แทน

---

## Step 2 — ถามข้อมูลให้ครบ 4 อย่าง

ถ้ามาใน `$ARGUMENTS` แล้วครบก็ใช้เลย ข้อไหนขาดให้ถามเพิ่ม:

1. **Repo** — รับได้ 2 แบบ: `owner/repo` หรือ URL (SSH form `git@github.com:owner/repo.git`
   หรือ HTTPS form ก็ตัดเอา `owner/repo` ออกมาใช้ได้ เพราะ push จริงใช้ remote
   `origin` ของ local repo อยู่แล้ว ไม่ต้องสร้าง URL เอง)
2. **ตำแหน่ง source code** — path บนเครื่องที่จะ push จาก path นี้ต้องมีอยู่จริงและ
   เป็น git repo (`git -C <path> rev-parse --is-inside-work-tree`) ถ้ายังไม่ใช่
   git repo ให้ถาม user ว่าจะ `git init` ให้ไหม อย่าทำเองโดยไม่ถาม
3. **เลข GitHub issue ที่เกี่ยวข้อง (ถ้ามี)** — ใช้ประกอบ commit message และ
   target branch default จะเป็น branch ปัจจุบันของ local repo (ปกติ `issue/<N>`
   ถ้าสร้างผ่าน [[github-new-branch]]) เว้นแต่ user ระบุ target branch อื่น
4. **ข้อความที่จะ Commit** — ดู Step 3

---

## Step 3 — Commit message (auto-generate หรือพิมพ์เอง)

ก่อนถาม ให้รัน `git -C <path> status` และ `git -C <path> diff` (หรือ `--cached`
ถ้ามีของ stage ค้างอยู่แล้ว) เพื่อดูว่าแก้อะไรไปบ้าง แล้วร่าง auto-generated
message จากสรุปนั้น รูปแบบ (ตาม pattern เดียวกับ [[feedback_tag_ai_work_comments]]):

```
<short title สรุปว่าแก้อะไร> (#<เลข issue ถ้ามี>) #ai-work
```

ถ้าไม่มีเลข issue ให้ตัดส่วน `(#<N>)` ออก เหลือ `<short title> #ai-work`

ใช้ `AskUserQuestion` ถามว่าจะใช้ auto-generate หรือพิมพ์เอง โดยโชว์ preview ของ
ข้อความ auto-generate ให้ดูก่อน:

- **ใช้ข้อความที่ auto-generate ให้ (Recommended)**
- **พิมพ์เอง**

ถ้าเลือกพิมพ์เอง ให้ user พิมพ์มา แล้ว **เช็คและเติม `#ai-work` ต่อท้ายให้เองเสมอ**
ถ้า user ไม่ได้พิมพ์มาเอง — ห้ามปล่อยให้หลุดแม้ user จะลืมใส่ก็ตาม

---

## Step 4 — สรุปให้ confirm ก่อน push จริง

รวบรวมข้อมูลทั้งหมดเป็นสรุปเดียว แสดงให้ user เห็นชัดเจนก่อนแตะ git จริง:

```
สรุปก่อน Push
=======================================
Repo           : <owner/repo>
Source path    : <path>
Issue          : #<เลข issue ถ้ามี>
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

## Step 5 — Warning พิเศษถ้า target เป็น default branch (main/master)

เช็คว่า target branch คือ default branch จริงของ repo นั้นหรือเปล่าก่อน (อย่าเดา
ว่าต้องชื่อ `main` เสมอ — บาง repo ยังใช้ `master`):

```bash
gh repo view "<owner/repo>" --json defaultBranchRef --jq '.defaultBranchRef.name'
```

ถ้า target branch ตรงกับ default branch — ก่อนถาม confirm รอบสุดท้าย ให้แสดง
warning สีแดงเด่นชัดผ่าน terminal จริง:

```bash
printf '\033[1;41;37m %s \033[0m\n' "!!! WARNING: กำลังจะ PUSH ขึ้น DEFAULT BRANCH (<branch>) โดยตรง !!!"
```

ตามด้วยข้อความอธิบายว่ากำลังจะ push อะไรไปที่ default branch แล้วถามยืนยันอีกรอบ
แยกจาก Step 4 (สองชั้น ไม่รวบเป็นคำถามเดียว) — ตอบ "ไม่" ให้ยกเลิกทันที ไม่ต้องถาม
ซ้ำว่าจะเปลี่ยน branch ไหม (ให้ user เริ่มใหม่เองถ้าต้องการ target อื่น)

**หมายเหตุ**: ถ้า repo นี้มี branch protection เปิดอยู่บน default branch
(ปกติ GitHub จะ reject push ตรง ๆ ถ้าบังคับให้ผ่าน PR) ให้แนะนำ
[[github-merge-master]] แทนตั้งแต่ต้น แทนที่จะพยายาม push ตรง ๆ ซ้ำ ๆ

---

## Step 6 — ลงมือ commit + push

หลัง confirm ครบ (และผ่าน Step 5 กรณี default branch แล้ว):

```bash
git -C <path> add -A            # หรือเฉพาะไฟล์ที่ผ่านการเช็คใน Step 4
git -C <path> commit -m "<commit message สุดท้ายพร้อม #ai-work>"
git -C <path> push origin HEAD:<target branch>
```

- ห้ามใช้ `--force`/`--force-with-lease` เว้นแต่ user สั่งชัดเจนแยกต่างหาก
- ห้ามใช้ `--no-verify` ข้าม hook เว้นแต่ user สั่งชัดเจน
- ถ้า push fail เพราะ auth (`Permission denied (publickey)` หรือคล้ายกัน) ให้เช็ค
  `gh auth status` ก่อน แล้วแนะนำ `gh auth login` ถ้าจำเป็น ห้ามเดาสาเหตุอื่น
- ถ้า push fail เพราะ branch protection (`GH006: Protected branch update
  failed`) ให้แจ้ง user ตรง ๆ และแนะนำ [[github-merge-master]] (เปิด PR) แทน
- ถ้า push fail เพราะ non-fast-forward ห้าม force push เอง ให้รายงาน error กับ
  user แล้วถามว่าจะ `git pull --rebase` ก่อนไหม
- หลัง push สำเร็จ สรุปผลสั้น ๆ ให้ user: commit hash, branch, ปลายทาง

---

## Notes

- Skill นี้จบงานที่ push เท่านั้น — ไม่เกี่ยวกับการเปิด/merge Pull Request (ดู
  [[github-merge-master]] ถ้าต้องทำ flow นั้นแยกต่างหาก ไม่ใช่ scope ของ skill นี้)
- ไม่ log time หรือ comment กลับ Redmine ให้อัตโนมัติ — ถ้าต้องการให้ใช้
  `/redmine-logtime` แยก

---

ARGUMENTS: $ARGUMENTS
