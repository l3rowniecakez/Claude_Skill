---
installer: create-shortcut
name: git-merge-master
description: 'เตรียม local repo ของ App ในกลุ่ม delphi group-insurance ให้พร้อม merge ticket/N (Gitblit) เข้า branch master โดยใช้ explicit merge commit ตาม convention ที่ยืนยันแล้ว (ห้าม plain fast-forward) แล้วส่งต่อให้ /git-commit-push ทำ push จริง. รับได้ทั้งชื่อ App (ค้นหา Repo URL ผ่าน /git-clone-grouplife) หรือ Repo URL ตรงๆ พร้อม path code ในเครื่องและเลข Redmine ไว้ดึง subject จริงมาประกอบ merge commit message. Use when user says "/git-merge-master" หรือต้องการเตรียม merge ticket เข้า master.'
created_at: 2026-09-03T10:22:18+07:00
argument-hint: "[ชื่อ App หรือ Repo URL] [Path code ในเครื่อง] [เลข ticket] [เลข Redmine]"
---

# /git-merge-master — เตรียม merge ticket/N เข้า master (Gitblit)

Sibling ของ [[git-clone-grouplife]] (ใช้ script `search_app.py` ตัวเดียวกันหา repo
จากชื่อ App) และ [[git-commit-push]] (ใช้ทำ push จริงในขั้นสุดท้าย) — งานของ skill
นี้คือเตรียม local repo ให้พร้อม push ขึ้น master แบบถูกต้องตาม convention ที่
ยืนยันแล้วใน [[reference_claim_dataextraction_gitblit]]: **ห้าม plain
fast-forward ticket/N เข้า master เด็ดขาด** ต้องเป็น explicit merge commit
รูปแบบ `Merged #N "<subject>"` เท่านั้น ไม่งั้น Gitblit ticket UI จะไม่ขึ้นสถานะ
"Merged" ให้ถูกต้อง (เคย fast-forward เฉยๆ มาแล้วครั้งหนึ่งกับ repo อื่น ผลคือ
ticket UI ไม่อัพเดทสถานะ ผู้ใช้ปฏิเสธผลลัพธ์นั้น)

**กฎเหล็ก**: skill นี้จบงานที่เตรียม merge commit ให้พร้อมบน local เท่านั้น — การ
push จริงต้องส่งต่อให้ [[git-commit-push]] ทำ (ซึ่งจะมี warning สีแดง + confirm
สองชั้นของมันเองเมื่อ target = master) **ห้าม push เองตรงนี้โดยไม่ผ่านขั้นตอนนั้น**

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1 — รับครบ 4 อย่าง + ตรวจสอบ path local

รับ argument ตามลำดับ `<ชื่อ App หรือ Repo URL> <Path code ในเครื่อง> <เลข ticket>
<เลข Redmine>` — ข้อไหนขาดให้ถามเพิ่ม ห้ามเดาแทน:

1. **App/Repo URL** รับได้ 2 แบบ — **เช็ครูปแบบก่อนตัดสินใจว่าจะทำแบบไหน อย่าเดา**:
   - **เป็น Repo URL อยู่แล้ว** (ขึ้นต้นด้วย `ssh://`, `git@`, หรือมี `.git` ต่อท้าย
     อย่างชัดเจน เช่น `ssh://<gitblit_user>@10.100.2.187:29418/delphi/xxx.git` หรือ
     `git@10.100.2.187:delphi/xxx.git`): **ใช้ตรง ๆ ได้เลย ข้ามการค้นหาไปเลย** — ไม่
     ต้องเรียก `search_app.py`
   - **เป็นชื่อ App** (คำธรรมดา ไม่ใช่ URL — พิมพ์บางส่วนก็ได้): ค้นด้วย script
     เดียวกับที่ [[git-clone-grouplife]] ใช้:
     ```bash
     ~/.config/redmine-summary-to-email/venv/bin/python3 \
       ~/.claude/skills/git-clone-grouplife/scripts/search_app.py "<คำค้น>"
     ```
     - **0 ผลลัพธ์ / มากกว่า 1 ผลลัพธ์**: จัดการเหมือน [[git-clone-grouplife]] เป๊ะ
       (แจ้งไม่เจอ หรือโชว์ทั้งหมดให้เลือกเจาะจง — ห้ามเดาว่าอันไหนที่ต้องการ)
     - **1 ผลลัพธ์**: ยืนยันชื่อเต็มสั้น ๆ กับ user แล้วเก็บค่า `repo` ไว้ (แทน
       placeholder `<gitblit_user>` ด้วย username จริงจาก
       `~/.config/gitblit-web/credentials.json` เช่นเดียวกับที่
       [[git-clone-grouplife]] ทำ)
2. **Path code ในเครื่อง** — path ที่ clone ไว้แล้วบนเครื่อง (path ที่มีการแก้ไข/
   commit ค้างอยู่บน branch `ticket/<N>` แล้ว — ปกติมาจากที่เคยใช้
   [[git-clone-grouplife]] + [[git-commit-push]] ทำไว้ก่อนหน้าในงานเดียวกัน) รับมา
   เป็น argument ตรง ๆ ได้เลย ไม่ต้องถามซ้ำถ้า user ใส่มาแล้ว แต่**ต้องตรวจสอบก่อน
   แตะอะไรเสมอ**:
   ```bash
   git -C "<path>" rev-parse --is-inside-work-tree
   git -C "<path>" branch --show-current
   git -C "<path>" remote get-url origin
   ```
   - ถ้า path ไม่มีอยู่จริง หรือไม่ใช่ git repo จริง หรือ remote ไม่ตรงกับ repo ที่
     หาได้ในข้อ 1 ให้หยุดแจ้ง user ทันที ห้ามเดาต่อ
   - ถ้า current branch ไม่ใช่ `ticket/<N>` (N จากข้อ 3) ให้เตือน user และถามยืนยัน
     ก่อนว่าจะดำเนินการต่อกับ branch ปัจจุบันนี้จริงไหม (เผื่อ user ตั้งใจจะ merge
     branch อื่น)
3. **เลข ticket** (Gitblit) ที่จะ merge (เช่น `15`) — ต้องได้มาจาก user ตรง ๆ ห้ามเดา
4. **เลข Redmine (RM)** ที่ ticket นี้ผูกอยู่ (เช่น `78856`) — ใช้ดึง subject จริงมา
   ประกอบ merge commit message ใน Step 3 ห้ามเดาหรือข้าม แม้ user จะไม่ได้ใส่มาก็ต้อง
   ถามเพิ่ม (ไม่มี fallback แบบเดา — ถ้า fetch จาก Redmine ไม่สำเร็จค่อย fallback ไปใช้
   subject จาก git log แทนตาม Step 3)

---

## Step 2 — Fetch + sync local `master` ให้ตรง origin/master ล่าสุดก่อน

```bash
git -C "<path>" fetch origin master ticket/<N>
git -C "<path>" checkout master 2>/dev/null || git -C "<path>" checkout -B master origin/master
git -C "<path>" log origin/master..master   # เช็คก่อนว่า local master มี commit ค้างที่ยังไม่ push อยู่หรือเปล่า
```

- ถ้า `git log origin/master..master` มีผลลัพธ์ (แปลว่า local master มี commit ที่
  ยังไม่ได้ push ค้างอยู่ก่อนหน้า) **ห้าม reset ทับเงียบ ๆ** ให้หยุดแจ้ง user ก่อนว่า
  พบ commit ค้างอะไรบ้าง ให้ user ตัดสินใจ
- ถ้าไม่มี commit ค้าง (สะอาด/ตรงกับ origin อยู่แล้ว หรือ local master ยังไม่เคยมี
  มาก่อน) ถึงจะทำ:
  ```bash
  git -C "<path>" reset --hard origin/master
  ```

---

## Step 3 — Merge `ticket/<N>` เข้า master ด้วย explicit merge commit (ตาม convention)

ดึง subject มาประกอบข้อความ merge commit — ใช้ **subject จริงจาก Redmine (RM)**
เป็นหลัก เพราะสั้น ตรงประเด็น และตรงกับที่ user อ้างอิงงานจริง (ดู
[[reference_redmine_api_key]]):

```bash
curl -s -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/issues/<RM>.json" | python3 -c "import json,sys; print(json.load(sys.stdin)['issue']['subject'])"
```

- **fetch สำเร็จ**: ใช้ `SUBJECT="RM #<RM>: <subject จาก Redmine>"`
- **fetch ไม่สำเร็จ** (network/RM ไม่พบ ฯลฯ): fallback ไปใช้ subject ของ commit
  แรกสุดบน `ticket/<N>` แทน (นับจาก origin/master) แล้วแจ้ง user ว่า fallback แล้ว
  เพราะดึงจาก Redmine ไม่ได้:
  ```bash
  SUBJECT=$(git -C "<path>" log --reverse --format=%s origin/master..ticket/<N> | head -1)
  ```

จากนั้น merge:

```bash
git -C "<path>" merge --no-ff "ticket/<N>" -m "Merged #<N> \"$SUBJECT\""
```

- ข้อความ commit **ต้องเป๊ะตามฟอร์แมต** `Merged #<N> "<subject>"` เท่านั้น (อ้างอิง
  [[reference_claim_dataextraction_gitblit]] — ผิดฟอร์แมตแล้ว Gitblit ticket UI จะ
  ไม่ขึ้นสถานะ "Merged" ให้ถูกต้อง) — `<N>` ในฟอร์แมตนี้คือเลข **Gitblit ticket**
  เสมอ ไม่ใช่เลข Redmine (สองเลขนี้คนละตัวกัน อย่าสลับ)
- **ถ้าเกิด merge conflict**: หยุดทันที ห้ามแก้ conflict เดาเอง — แจ้ง user ว่าไฟล์
  ไหน conflict บ้าง (`git -C "<path>" status --short`) แล้วให้ user ตัดสินใจ/แก้เอง
  ก่อน (เสนอ `git merge --abort` ถ้า user อยากยกเลิกแล้วเริ่มใหม่)
- Merge สำเร็จแล้ว **ห้าม push เองตรงนี้** — ไปต่อ Step 4

---

## Step 4 — ส่งต่อให้ [[git-commit-push]] ทำ push จริง

แจ้ง user สรุปว่า local `master` พร้อม push แล้ว (โชว์
`git -C "<path>" log -1 --oneline` ของ merge commit ที่เพิ่งสร้าง) แล้วถามว่าจะ
push เลยไหมด้วย [[git-commit-push]] — ระบุให้ชัดเจนไปด้วยว่า:

- Repo (SSH) = จาก Step 1, target branch = `master`
- Source path = path เดิมที่ใช้ตลอด flow นี้
- **หมายเหตุสำคัญที่ต้องส่งต่อให้ [[git-commit-push]] รู้ด้วย**: ตอนนี้ working
  tree สะอาดแล้ว มีแค่ merge commit ที่รอ push เท่านั้น (ไม่มีไฟล์แก้ไขค้างให้ stage) —
  ดังนั้นขั้นตอน `git add -A && git commit -m ...` ใน Step 5 ของ
  [[git-commit-push]] **ต้องข้าม** (ไม่มีอะไรให้ commit ซ้ำ ถ้าพยายาม commit จะ
  error "nothing to commit") ให้ push `HEAD:master` ตรง ๆ เลย
- [[git-commit-push]] จะมี warning สีแดง + confirm สองชั้นของมันเองอยู่แล้วเพราะ
  target คือ `master` — ให้ user ยืนยันผ่าน flow นั้นตามปกติ ห้ามข้าม

ถ้า user ไม่ต้องการ push ตอนนี้ ให้หยุดไว้แค่นี้ (local master merge ไว้แล้ว รอ push
ทีหลังได้ ไม่มีอะไรเสียหาย)

---

## Notes

- Skill นี้ไม่ log time หรือ comment กลับ Redmine อัตโนมัติ
- ไม่ลบ/แก้ branch `ticket/<N>` หลัง merge — Gitblit เก็บ ticket branch ไว้เป็น
  ประวัติ ไม่ต้อง cleanup เอง เว้นแต่ user สั่งเอง
- ถ้า repo ไหนไม่ได้ใช้ pattern `ticket/N` แบบ Gitblit skill นี้ไม่รองรับ — แจ้ง
  user แทนที่จะเดา flow merge อื่น

---

ARGUMENTS: $ARGUMENTS
