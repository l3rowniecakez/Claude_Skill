---
name: install-statusline
description: 'ติดตั้งหรืออัพเดท Claude Code status line (แสดง model/effort/cost/context/rate limit + แถว git repo ของโปรแกรมที่ session กำลังทำงานอยู่ พร้อม branch/ticket/สถานะ) จาก public GitHub repo (l3rowniecakez/Claude_Skill) ลงเครื่องของคนที่สั่ง — เขียน ~/.claude/statusline.py และตั้งค่า statusLine ใน ~/.claude/settings.json ให้เอง สำรองของเดิมไว้ก่อนทุกครั้ง รันซ้ำได้ = อัพเดท. Use when user says "/install-statusline" หรือต้องการติดตั้ง/อัพเดท status line.'
argument-hint: "[]"
---

# /install-statusline — ติดตั้ง/อัพเดท status line จาก GitHub

พิมพ์คำสั่งเดียว `/install-statusline` แล้วเครื่องนั้นจะได้ status line ล่าสุด รันซ้ำเมื่อไหร่ก็ได้
เพื่ออัพเดท (ถ้าไม่มีอะไรเปลี่ยนจะรายงานว่าเป็นเวอร์ชันล่าสุดอยู่แล้ว)

สคริปต์ `scripts/install.py` ทำทุกอย่างเอง (ใช้ Python standard library อย่างเดียว ไม่ต้อง `git`/`pip`):

1. ดึง `statusline.py` จาก
   `https://raw.githubusercontent.com/l3rowniecakez/Claude_Skill/main/skills/install-statusline/scripts/statusline.py`
   (repo เป็น public อ่านอย่างเดียว ไม่ต้อง auth/deploy key)
2. เทียบ hash กับ `~/.claude/statusline.py` ที่มีอยู่ — ถ้าต่างกันจะสำรองของเดิมไว้ที่
   `~/.claude/backups/statusline.py.<เวลา>.bak` ก่อนเขียนทับ
3. ตั้ง `statusLine` ใน `~/.claude/settings.json` (merge เฉพาะ key นี้ key อื่นไม่แตะ, สำรอง
   `settings.json` ไว้ที่ `~/.claude/backups/` ก่อนแก้)
4. ทดสอบรันสคริปต์ด้วยข้อมูลตัวอย่าง แล้วรายงานผล

**ขอบเขต**: แตะเฉพาะ `~/.claude/statusline.py`, key `statusLine` ใน `~/.claude/settings.json`
และไฟล์สำรองใน `~/.claude/backups/` เท่านั้น ห้ามเพิ่ม logic ที่กวาดหา/แก้ไฟล์อื่นในเครื่อง

---

## Step 1 — รันตัวติดตั้ง

```bash
python3 "$SKILL_DIR/scripts/install.py"
```

`$SKILL_DIR` = โฟลเดอร์ของ skill นี้ในเครื่องนั้น (เช่น `~/.claude/skills/install-statusline`)
บน Windows ใช้ `python` แทน `python3` ปล่อย output ไหลออกมาตามธรรมชาติ (มี progress bar แบบ text)

## Step 2 — จัดการตาม exit code

- **0** — สำเร็จ (ติดตั้งใหม่ / อัพเดท / เป็นเวอร์ชันล่าสุดอยู่แล้ว) → ไป Step 3
- **3** — ไฟล์ติดตั้งแล้ว แต่ `settings.json` มี `statusLine` **อื่น** (ไม่ใช่ของ skill นี้) จึงยังไม่ได้แตะ
  ให้แสดงค่าเดิมที่สคริปต์พิมพ์ออกมา แล้วถามด้วย AskUserQuestion ว่าจะ
  - **แทนที่ด้วยของ skill นี้** → รันซ้ำพร้อม `--force-settings` (ค่าเดิมถูกสำรองไว้ใน
    `~/.claude/backups/settings.json.<เวลา>.bak` กู้คืนได้)
  - **คงของเดิมไว้** → จบ แจ้งว่าไฟล์ `~/.claude/statusline.py` พร้อมใช้ถ้าอยากสลับทีหลัง
- **1** — error (เน็ตมีปัญหา / ดึงไฟล์ไม่ได้ / `settings.json` เสีย / ทดสอบรันไม่ผ่าน) → แจ้ง error
  ตามที่สคริปต์พิมพ์ ห้ามเดาสาเหตุเอง และห้ามแก้ไฟล์ด้วยมือเพื่อ "ให้ผ่าน"

## Step 3 — รายงานผล

สรุปสั้นๆ: ติดตั้งใหม่/อัพเดท/ล่าสุดอยู่แล้ว, path ที่เขียน, ไฟล์สำรอง (ถ้ามี), ผลทดสอบรัน
แล้วบอกว่า status line จะเปลี่ยนในรอบรีเฟรชถัดไป ถ้าไม่เห็นให้เริ่ม session ใหม่

## สิ่งที่ status line แสดง (สำหรับอธิบายให้ผู้ใช้)

- บรรทัดบน: model, effort, cost, context, ระยะเวลา session
- แถว 📁 ต่อ repo: ชื่อโฟลเดอร์ | 🌿 branch | 🎫 ticket (จากชื่อ branch `ticket/N`) | ✏️ จำนวนไฟล์ที่แก้ /
  ✅ Clean | ⬆️⬇️ ahead/behind — แสดงเฉพาะ git repo ที่ session นี้แตะ (อ่าน/แก้ไฟล์ หรือ
  คำสั่ง Bash ที่อ้าง path ใน repo) หรือ cwd ปัจจุบัน; สูงสุด 5 แถว
- บรรทัดล่าง: rate limit 5 ชั่วโมง / 7 วัน (ถ้า Claude Code ส่งข้อมูลมา)

## หมายเหตุสำหรับคนดูแล skill

- ไฟล์ต้นฉบับที่แจกจ่ายคือ `scripts/statusline.py` ใน skill นี้ — แก้ที่นี่แล้ว push ขึ้น repo
  คนอื่นจะได้เมื่อรัน `/install-statusline` อีกครั้ง
- ห้ามใส่ข้อมูลส่วนตัว (ชื่อ/อีเมล/path เฉพาะเครื่อง) ในสคริปต์ที่แจกจ่าย เพราะ repo เป็น public
