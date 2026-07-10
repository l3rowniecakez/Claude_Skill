# 📘 วิธีใช้งาน ocean-ochi-skill-cli

คู่มือสำหรับทีม — ติดตั้ง Oracle skills + company skills ลง **Claude Cowork / Claude Desktop / Claude Code**

> skill ทั้งหมดอ่านจาก `~/.claude/skills/` ซึ่ง Claude Cowork, Claude Desktop และ Claude Code **ใช้ร่วมกัน** — ติดตั้งครั้งเดียวใช้ได้ทุกตัว

---

## เลือกวิธีติดตั้ง (เลือกอันเดียว)

### 🅰️ เครื่องบริษัท / ลงโปรแกรมไม่ได้ — แนะนำ

ไม่ต้องมี bun / npm / node — แค่ download ไฟล์แล้ววาง

1. โหลด ZIP:
   👉 https://github.com/firstnext/ocean-ochi-skill-cli/archive/refs/tags/v1.1.2.zip
   (หรือหน้า repo กดปุ่ม **`Code` ▸ `Download ZIP`**)
2. แตก ZIP → จะเจอโฟลเดอร์ `skills/` ข้างใน
3. เปิดโฟลเดอร์ skills ของ Claude:
   - **Windows** → `C:\Users\<ชื่อคุณ>\.claude\skills\`
   - **Mac / Linux** → `~/.claude/skills/`
   - (ถ้ายังไม่มีโฟลเดอร์ `.claude\skills` ให้สร้างเอง)
4. **copy โฟลเดอร์ย่อยทั้งหมด** จาก `skills/` (เช่น `rrr/`, `recap/`, `trace/` …) ไปวางใน `.claude/skills/`
   - ✅ ถูก: `~/.claude/skills/rrr/SKILL.md`
   - ❌ ผิด (ซ้อนลึกเกิน): `~/.claude/skills/skills/rrr/SKILL.md`
5. **ปิดแล้วเปิด Claude Cowork / Desktop ใหม่**

### 🅱️ เครื่องตัวเอง / มี Bun

```bash
bunx --bun ocean-ochi-skill-cli@github:firstnext/ocean-ochi-skill-cli#v1.1.2 install -p lab -y
```
จบในคำสั่งเดียว แล้ว restart Claude

---

## เรียกใช้ skill

หลัง restart แล้ว skill ทำงานแบบ **auto-trigger** — พิมพ์ภาษาธรรมชาติ Claude หยิบ skill เองตาม description

| อยากได้ | พิมพ์ |
|---|---|
| ปลุก/สร้าง Oracle ใหม่ | `awaken` (หรือ `awaken --fast`) |
| สรุป session + บันทึก learning | `rrr` |
| ปฐมนิเทศ / ดูว่าทำอะไรอยู่ | `recap` |
| ค้นหาโปรเจกต์ / โค้ด | `trace` |
| ศึกษา repo ภายนอก | `learn <repo-url>` |
| ส่งต่อ context ก่อนจบ session | `forward` |
| Morning check-in | `standup` |
| ขุด session history | `dig` |

> trigger words ของแต่ละ skill ดูได้จากบรรทัด `description:` ใน `skills/<ชื่อ>/SKILL.md`

---

## เช็คว่าติดตั้งสำเร็จ

- ในโฟลเดอร์ `~/.claude/skills/` ต้องมีหลายโฟลเดอร์ แต่ละอันมี `SKILL.md`
- ลองพิมพ์ `recap` ใน Claude — ถ้าตอบแบบรู้ context = ใช้ได้ ✅

### ⚠️ ถ้า Cowork เห็น skill ไม่ครบ
มี bug ที่รู้กันอยู่ ([anthropics/claude-code#50669](https://github.com/anthropics/claude-code/issues/50669)) —
UI บางเวอร์ชันสแกน `~/.claude/skills/` ไม่ครบ → **restart แอปอีกครั้ง** หรือวางเฉพาะ skill ที่ใช้จริง

---

## อัปเดต skill เป็นเวอร์ชันใหม่

ลบของเก่าแล้ววางชุดใหม่ทับ (หรือรันคำสั่ง 🅱️ ด้วย tag ใหม่)
เวอร์ชันล่าสุดดูได้ที่หน้า [Releases / Tags](https://github.com/firstnext/ocean-ochi-skill-cli/tags)

---

## License

MIT — ดู [LICENSE](./LICENSE) | derive จาก `arra-oracle-skills` (MIT)
