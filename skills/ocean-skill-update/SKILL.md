---
installer: create-shortcut
name: ocean-skill-update
description: 'ดึง skill ล่าสุดจาก public GitHub repo (l3rowniecakez/Claude_Skill) มา install/update ลงเครื่องของคนที่สั่งคำสั่งนี้ โดยหาตำแหน่งที่เก็บ skill ในเครื่องนั้นเอง (Claude Code CLI และ/หรือ Claude Desktop, ทุก OS) แล้ว sync ให้อัตโนมัติ — เลือกได้ว่าจะเอาทั้งหมดหรือเลือกเฉพาะบาง skill — พร้อมแสดง progress bar ระหว่างทำงาน. Use when user says "/ocean-skill-update" หรือต้องการ sync/update skill ของทีมจาก GitHub ลงเครื่อง.'
created_at: 2026-09-18T07:30:40+07:00
argument-hint: "[]"
---

# /ocean-skill-update — ดึง+ติดตั้ง skill ทีมจาก GitHub อัตโนมัติ

จุดประสงค์: ทำให้คนอื่นในทีม (ไม่ว่าจะใช้ Claude Code CLI หรือ Claude Desktop, ไม่ว่า
skill จะถูกเก็บไว้ตำแหน่งไหนในเครื่องของแต่ละคน) พิมพ์คำสั่งเดียว `/ocean-skill-update`
แล้วได้ skill จาก [[reference_claude_skill_github_repo]]
(`git@github.com:l3rowniecakez/Claude_Skill.git`, repo **public**) มาวางในเครื่องทันที
โดยไม่ต้องรู้ path หรือขั้นตอน git เอง — เลือกได้ว่าจะเอาทั้งหมดหรือเฉพาะบาง skill

**สำคัญ — ไม่ต้องใช้ deploy key ใดๆ**: repo นี้เป็น public repo อ่านอย่างเดียว (pull) จึง
clone ผ่าน HTTPS แบบไม่ต้อง auth ได้เลย (`https://github.com/l3rowniecakez/Claude_Skill.git`)
— ต่างจาก [[reference_claude_skill_github_repo]] ที่พูดถึง deploy key
`~/.ssh/deploy_keys/claude_skill_deploy` ซึ่งใช้เฉพาะตอน **push** เท่านั้น (เครื่องอื่นในทีม
ไม่มี key นี้และไม่จำเป็นต้องมี)

**สำคัญ — ขอบเขตตำแหน่งที่แตะ (ห้ามขยายเอง)**: สคริปต์นี้แตะเฉพาะตำแหน่งติดตั้ง skill ของ
Claude ที่รู้จักแน่ชัดเท่านั้น (`~/.claude/skills`, Claude Desktop/CLI บน Windows ผ่าน
`/mnt/c/Users/*`, macOS `~/Library/Application Support/Claude/skills`, Linux
`~/.config/Claude/skills`) — **ห้ามเพิ่ม logic แบบกวาดหาโฟลเดอร์ชื่อ `skills` ทั่วทั้งเครื่อง
(`find $HOME -iname skills`) เด็ดขาด** แม้จะดูสมเหตุผลว่าเป็น "safety net" ก็ตาม เพราะเคย
พิสูจน์แล้วว่ามีเครื่องมืออื่นจำนวนมาก (VS Code extension, bun/npm package cache, CLI agent
อื่นๆ) ก็ใช้ pattern โฟลเดอร์ `skills/<name>/SKILL.md` เหมือนกันโดยบังเอิญ — การกวาดแบบกว้าง
เคยเขียนทับไฟล์ของ VS Code extension และ cache ของ tool อื่นไปแล้วจริงในการทดสอบ ถ้าเจอ
ตำแหน่งติดตั้ง Claude ที่ไม่ตรงกับ pattern ที่รู้จักด้านบน ให้ถาม user ก่อนเพิ่มเข้าไปใน
สคริปต์ ห้ามเดา path เอง

---

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
SKILL_DIR="<ตำแหน่งโฟลเดอร์ของ skill นี้ในเครื่องนี้>"   # เช่น ~/.claude/skills/ocean-skill-update
```

---

## Step 1 — ถามโหมดการติดตั้ง

ถามด้วย AskUserQuestion เสมอ (single-select, ไม่ multiSelect):

- **ติดตั้ง/อัพเดททั้งหมด (Recommended)** — เอา skill ทุกตัวใน repo
- **เลือกเฉพาะบาง Skill** — ไปทำ Step 2 เพื่อเลือกทีละตัว

---

## Step 2 — ถ้าเลือก "เฉพาะบาง Skill": แสดงรายการให้เลือก

**ข้อจำกัดสำคัญ**: AskUserQuestion รองรับสูงสุด 4 ตัวเลือกต่อคำถาม แต่ repo นี้มี skill
เป็นสิบๆ ตัว จึงใช้ AskUserQuestion แบบ checkbox ตรงๆ ไม่ได้ — ให้ทำแบบนี้แทน:

1. ดึงรายชื่อ skill + คำอธิบายสั้นจาก repo ก่อน (ยังไม่ copy ไปไหน):
   ```bash
   bash "$SKILL_DIR/scripts/update.sh" --list
   ```
   ผลลัพธ์แต่ละบรรทัดเป็น `name|description`
2. แสดงผลเป็น checklist แบบ markdown ในแชท ให้ user อ่านแล้วพิมพ์ตอบกลับมาเป็นชื่อ/เลข
   คั่นด้วย comma (ไม่ใช้ AskUserQuestion ตรงนี้ เพราะจำนวนตัวเลือกเกินข้อจำกัดของ tool):
   ```
   เลือก skill ที่ต้องการ install/update (พิมพ์ชื่อหรือเลข คั่นด้วย comma, หรือพิมพ์ "all"):

   1. [ ] about-oracle — ...
   2. [ ] awaken — ...
   3. [ ] redmine-ur — ...
   ...
   ```
3. รอ user ตอบกลับในข้อความถัดไป แล้วแปลงเป็นรายชื่อ skill จริง (map เลขกลับเป็นชื่อ) ก่อน
   ไปทำ Step 3

---

## Step 3 — รันสคริปต์ update จริง

```bash
# กรณีเลือกทั้งหมด (Step 1)
bash "$SKILL_DIR/scripts/update.sh"

# กรณีเลือกเฉพาะบาง skill (Step 2), ตัวอย่างเลือก git-clone กับ redmine-ur
bash "$SKILL_DIR/scripts/update.sh" --only git-clone,redmine-ur
```

สคริปต์นี้ทำ 4 ขั้นตอนหลัก พร้อมพิมพ์ progress bar แบบ text (`[####......] NN% ข้อความ`)
ทุกครั้งที่ผ่านแต่ละขั้น ให้ปล่อยให้ output ของสคริปต์ไหลออกมาตามธรรมชาติ (ไม่ต้อง
สรุปทับหรือย่อ progress bar เอง):

1. **เตรียมพื้นที่ทำงาน** — ล้าง cache เก่าที่ `~/.cache/ocean-skill-update/Claude_Skill`
   แล้วเตรียม clone ใหม่ทุกครั้ง (ให้ได้ของล่าสุดเสมอ ไม่ merge/diff กับของเก่าให้ยุ่งยาก)
2. **Clone repo** — `git clone --depth 1` แบบ HTTPS ไม่ต้อง auth
3. **หาตำแหน่งติดตั้ง skill ในเครื่องนี้** — เฉพาะ path ที่รู้จักแน่ชัดตามหัวข้อ "ขอบเขต
   ตำแหน่งที่แตะ" ด้านบนเท่านั้น
4. **Copy** — เฉพาะโฟลเดอร์ skill ที่มีอยู่จริงใน repo's `skills/*` (หรือเฉพาะที่ผ่าน
   `--only` ถ้าเลือกโหมดเฉพาะบางตัว) ไปทับ/เพิ่มในทุกตำแหน่งที่เจอใน Step 3 (ไม่แตะ skill
   อื่นที่ผู้ใช้สร้างเองซึ่งไม่ได้อยู่ใน repo นี้)

จบแล้วสคริปต์จะพิมพ์สรุป: commit ที่ pull มา, ตำแหน่งที่อัพเดททั้งหมด, รายชื่อ skill ที่
เพิ่มใหม่ vs อัพเดททับ

---

## Step 4 — รายงานผลให้ user

สรุปผลจาก output ของสคริปต์ให้ user แบบกระชับ:
- pull มาจาก commit ไหน วันที่เท่าไหร่
- โหมดที่ใช้ (ทั้งหมด หรือเลือกเฉพาะ — ถ้าเลือกเฉพาะ บอกด้วยว่าเลือกตัวไหนบ้าง)
- อัพเดทไปกี่ตำแหน่ง ตำแหน่งไหนบ้าง (พร้อม label เช่น Claude Code CLI / Claude Desktop)
- มี skill ใหม่กี่ตัว อัพเดททับกี่ตัว

ถ้า exit code ไม่ใช่ 0 (เช่น `git clone` ล้มเหลวเพราะเน็ตปัญหา/ไม่มี `git`) ให้แจ้ง error
message ตรงๆ จากสคริปต์ ห้ามเดาสาเหตุเอง

**หมายเหตุ**: skill ใหม่/อัพเดทจะขึ้นให้เห็นใน `/` autocomplete ทันทีโดยไม่ต้อง restart
Claude Code CLI — แต่ Claude Desktop บางเวอร์ชันอาจต้อง reload/restart app ก่อนถึงจะเห็น
