# ocean-ochi-skill-cli

CLI สำหรับติดตั้ง **Oracle skills** + **company skills** ลง Claude Code (และ AI coding agents อื่น)
เป็น wrapper ครอบ [`arra-oracle-skills`](https://www.npmjs.com/package/arra-oracle-skills) (MIT) แล้วเสริม company skills จาก `src/skills/`

> ⚠️ **ต้องใช้ [Bun](https://bun.sh)** — bin เป็น TypeScript + shebang `#!/usr/bin/env bun` เรียกผ่าน `bunx --bun` ไม่ใช่ `npx`

> 👉 **ทีมอ่านวิธีใช้งานแบบ step-by-step ได้ที่ [USAGE.md](./USAGE.md)**

---

## 📦 วิธีติดตั้งแบบ "ไม่ต้องลงโปรแกรม" (offline / เครื่องบริษัทล็อก)

ถ้าเครื่องลง bun/npm ไม่ได้ ใช้ **static skills bundle** ในโฟลเดอร์ [`skills/`](./skills) ได้เลย —
เป็นไฟล์ `SKILL.md` สำเร็จรูป 34 skills (snapshot ของ `arra-oracle-skills@26.5.16` profile `lab`)
แค่ download แล้ววางลง `~/.claude/skills/` → **Claude Cowork / Claude Desktop / Claude Code อ่านจาก path เดียวกัน**

```bash
# วิธี A: git clone (ถ้ามี git)
git clone https://github.com/firstnext/ocean-ochi-skill-cli.git
mkdir -p ~/.claude/skills
cp -r ocean-ochi-skill-cli/skills/* ~/.claude/skills/

# วิธี B: ไม่มี git เลย — โหลด ZIP จากหน้าเว็บ GitHub (ปุ่ม Code ▸ Download ZIP)
#   แตก ZIP แล้วลากเฉพาะโฟลเดอร์ย่อยใน skills/ ไปไว้ใน ~/.claude/skills/
#   ต้องได้ path: ~/.claude/skills/<ชื่อ-skill>/SKILL.md  (อย่าซ้อนลึกเกิน)
```

จากนั้น **restart Claude Cowork / Desktop** ให้มันสแกน skill ใหม่

> ⚠️ ข้อจำกัดที่รู้กันของ Cowork ([anthropics/claude-code#50669](https://github.com/anthropics/claude-code/issues/50669)):
> UI บางเวอร์ชันสแกน `~/.claude/skills/` ไม่ครบ (โหลดได้บางตัว) — ถ้าเห็นไม่ครบให้ restart แอป หรือลดจำนวน skill ที่วาง

Windows path = `C:\Users\<you>\.claude\skills\` (เหมือนกันทุก OS)

---

## Install / Run (ผ่าน CLI — ต้องมี Bun)

```bash
# วิธีหลัก — รันตรงจาก GitHub (ไม่ต้อง publish npm, ไม่ต้องติดตั้งถาวร)
bunx --bun ocean-ochi-skill-cli@github:firstnext/ocean-ochi-skill-cli#v1.0.0 install -p lab -y

# หรือ clone มารันจาก source
git clone https://github.com/firstnext/ocean-ochi-skill-cli.git
cd ocean-ochi-skill-cli
bun install
bun run src/cli/index.ts install -p lab -y

# (ภายหลังถ้า publish ขึ้น npm registry แล้ว)
# bunx --bun ocean-ochi-skill-cli install -p lab -y
```

## `install` options

| Option | Default | คำอธิบาย |
|---|---|---|
| `-p, --profile <name>` | `standard` | Oracle skill profile: `minimal` / `standard` / `full` / `lab` |
| `--agent <name>` | `claude-code` | Target agent: `claude-code` / `cursor` / `opencode` / ... |
| `--oracle-version <ver>` | `26.5.16` | เวอร์ชัน `arra-oracle-skills` (เว้นว่าง = latest) |
| `-y, --yes` | — | ข้าม confirmation prompt |
| `--oracle-only` | — | ติดตั้ง Oracle skills อย่างเดียว |
| `--ochi-only` | — | ติดตั้ง company skills อย่างเดียว |

## Company skills

วาง skill ของบริษัทไว้ที่ `src/skills/<skill-name>/` — ตอน `install` จะถูก copy ไป `~/.claude/skills/`

## Credits & License

**MIT** — ดู [LICENSE](./LICENSE)

โปรเจกต์นี้ derive จาก `arra-oracle-skills` (MIT) และ redistribute เนื้อ skill ใน `skills/`
ภายใต้เงื่อนไข MIT — copyright ของผู้สร้างต้นทางเก็บไว้ครบใน [LICENSE](./LICENSE) ตามที่ MIT กำหนด
