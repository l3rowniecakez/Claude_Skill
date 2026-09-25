---
name: forward
description: 'บันทึกงานที่ทำค้างไว้ (handoff) ลง vault กลาง ~/ψ/inbox/handoff เพื่อกลับมาทำต่อหลังปิด session/ปิดคอม — แยกตามสายงาน (grouplife ประกันกลุ่ม Delphi / cde / cam / bot) และตามเลข RM, จับสถานะ git/branch/deploy/FormEdit.txt/SQL script/logtime ที่ค้าง แล้วใช้ /recap เรียกกลับมา. Use when user says "/forward", "forward", "handoff", "wrap up", "บันทึกงานไว้ทำต่อ", "จะปิดคอมแล้ว", or before ending session.'
argument-hint: "[--close RM|key] [--plan] [--list]"
---

# /forward — บันทึกงานค้างไว้ทำต่อ (คู่กับ /recap)

> Ocean version (2026-09-25) ปรับจาก arra-oracle v26.5.16 — ใช้คู่กับ /recap, script กลางอยู่ที่ `forward/scripts/handoffs.py`
> (ต้องติดตั้ง forward + recap คู่กันเสมอ). Redmine API key: env `REDMINE_API_KEY` หรือ memory `reference_redmine_api_key.md`

เป้าหมายเดียว: **เปิด session ใหม่ (หรือเปิดคอมวันจันทร์) แล้ว `/recap` ต้องทำงานต่อได้ทันทีโดยไม่ต้องถามซ้ำ**
ดังนั้น handoff ต้องมีทุกอย่างที่ "หายไปพร้อม context" — path, branch, สถานะ phase, env ที่ deploy แล้ว,
สิ่งที่ผู้ใช้ยังไม่อนุมัติ, และกฎที่ต้องระวังของงานนั้น

## Usage

```
/forward                 # บันทึก handoff ของงานใน session นี้ (1 ไฟล์ต่อ 1 RM/งาน)
/forward --close 12345  # ปิดงาน RM นั้น (ไม่ขึ้นใน /recap อีก)
/forward --list          # ดูงานค้างทั้งหมด (= handoffs.py list)
/forward --plan          # บันทึกเสร็จแล้วเข้า Plan Mode ให้กด approve + clear context
```

Script กลาง (ใช้ร่วมกับ /recap): `python3 ~/.claude/skills/forward/scripts/handoffs.py`
(`list | show KEY | history KEY | verify KEY | close KEY | supersede KEY FILE | dir`)

## Hard Rules

1. **Vault ตายตัว** `~/ψ/inbox/handoff/` (absolute: `$HOME/ψ/inbox/handoff`) ไม่ว่า cwd จะอยู่ repo ไหน
   (`/mnt/d/WORK/...` ก็เขียนมาที่นี่) — ห้าม `git add` ไฟล์ handoff เข้า repo ใดๆ
2. **ห้าม commit / push / merge / deploy / post Redmine** ใดๆ ใน /forward — แค่ "บันทึกสถานะ" เท่านั้น
   ถ้ามีงานค้าง commit ให้เขียนเป็น pending "รอคำสั่ง" (ตาม feedback never-auto-commit)
3. **ห้ามสร้าง GitHub issue** — งานเราอยู่บน Gitblit + Redmine ไม่ใช่ GitHub
4. **ไม่ต้องใส่ credential ลง handoff** — อ้างชื่อ memory file แทน (เช่น "ใช้ credential จาก memory reference_db_credentials_…")
5. **1 ไฟล์ต่อ 1 งาน (key)** — session เดียวทำหลาย RM → เขียนหลายไฟล์ แยกกัน, key = `rm<เลข>` (ถ้าไม่มี RM ใช้ slug สั้น เช่น `cde-ocr-cost`)
6. ข้อความทั้งหมดเป็นภาษาไทย ยกเว้น path / ชื่อไฟล์ / identifier / คำสั่ง

## Step 1 — แยกงานใน session นี้ออกเป็น key

จาก context ของ session: มี RM / งานอะไรบ้างที่แตะ, จัดเข้า stream:

| stream | งาน | สัญญาณ |
|---|---|---|
| `grouplife` | ประกันกลุ่ม Delphi7 (OGL_Operation/Benefit/Claim/Sale/…) รวม /redmine-ur, /redmine-support, system-analyst | `.pas/.dfm`, FormEdit.txt, `D:\WORK\JIRA\<RM>...`, SQL Server .52/.22 |
| `cde` | claim-dataextraction (Cloud Run service/job, drugnorm API) | `/mnt/d/WORK/[Python]/DataExtraction/CDE`, deploy_cloud_run.sh |
| `cam` | ClaimAutomation (drug norm, Jenkins) | `/mnt/d/WORK/[Python]/ClaimAutomation`, Jenkins job |
| `bot` | ocean-bot / ocean-bot-admin (UR 20260219) | `/mnt/d/WORK/JIRA/BOT/...`, docker containers |
| `other` | อื่นๆ (skill, cost report, ฯลฯ) | — |

งานที่ **ปิดจบใน session นี้แล้ว** ไม่ต้องสร้าง handoff ใหม่ — แค่ `handoffs.py close <key>` ถ้ามี handoff เก่าค้างอยู่

## Step 2 — เก็บ state จริง (1 bash call ต่อ repo ที่แตะ)

```bash
python3 ~/.claude/skills/forward/scripts/handoffs.py history <key>   # มี handoff เก่าของงานนี้ไหม → อ่านเพื่อ merge pending
REPO="<repo path ที่แตะ>"
git -C "$REPO" branch --show-current; git -C "$REPO" log --oneline -3
git -C "$REPO" status --short; git -C "$REPO" rev-list --count @{u}..HEAD 2>/dev/null || echo no-upstream
```

ถ้ามี handoff เก่าของ key เดียวกัน: pending เก่าที่ยังไม่เสร็จต้อง **ยกมาไว้ในไฟล์ใหม่** (ไม่ใช่ทิ้ง) แล้วค่อย supersede

Session id: เอาจาก path ของ scratchpad/transcript ของ session ปัจจุบัน (uuid เต็ม) — ใช้ `claude --resume <uuid>` ได้

## Step 3 — Checklist เฉพาะสายงาน (ใส่ในหัวข้อ "State")

ตอบเฉพาะข้อที่เกี่ยว, ข้อไหนไม่รู้ให้เขียน `?` ไม่ต้องเดา

**grouplife (Delphi)**
- Ticket folder (`D:\WORK\JIRA\<RM> ...`) + App/repo path + branch `ticket/N` (Gitblit ticket #N เปิดแล้ว?)
- Phase ไหนเสร็จ / ผู้พัฒนา compile+test ใน IDE แล้วหรือยัง / phase ถัดไป **ได้ "เริ่ม" แล้วหรือยัง** (ห้ามเริ่มโค้ดเองถ้ายังไม่อนุมัติ)
- ไฟล์ .pas/.dfm ที่แก้ (ย้ำ: cp874 + CRLF, แก้ด้วย Python splice เท่านั้น)
- SQL script: ชื่อไฟล์ `NNN_<DB> ...sql`, รันแล้วบน SIT(.52) / UAT(.22) หรือยัง (ต้องครบทั้งสอง)
- FormEdit.txt อัปเดตถึง phase ไหน
- Redmine: note / logtime ลงแล้วกี่ ชม. ส่วนไหนยังไม่ลง (#ai-work)
- scope ห้ามแตะ (ถ้ามี memory scope ของ RM นั้น ให้อ้างชื่อ memory)

**cde / cam (Python, GCP)**
- repo + branch `ticket/N` + commit hash + merge เข้า master แล้วหรือยัง (ต้องเป็น `Merged #N "..."`)
- Deploy: env ไหนแล้ว (SIT / UAT / PROD), image tag, revision, ใครสั่ง — env ที่ **ยังไม่ได้รับคำสั่ง deploy** ต้องเขียนชัด
- ทดสอบ functional บน env นั้นแล้วหรือยัง (log skill ที่ใช้เช็ก: /log-cde-*, /log-drugapi-*)
- cam: Jenkins job/build number ที่เกี่ยว

**bot (PHP)**
- repo (bot / admin) + branch, docker container ที่ต้องเปิด (`db`, admin :8080, bot :8081)
- deploy UAT แล้วหรือยัง, RM deploy notice ที่รอ IT
- FormEdit.txt (รูปแบบ `[ Web App ]`) อัปเดตแล้วหรือยัง

## Step 4 — เขียนไฟล์

ชื่อไฟล์: `~/ψ/inbox/handoff/YYYY-MM-DD_HH-MM_<key>-<slug>.md` (เวลา `date +%Y-%m-%d_%H-%M`)

```markdown
---
key: rm12345
stream: grouplife            # grouplife | cde | cam | bot | other
rm: 12345                   # หลายเลขคั่น comma ได้ เช่น 12345,12344
title: แก้ไขการนำเข้าไฟล์ (OGL_App)
status: open                 # open | waiting (รอคนอื่น/รอ user test) | closed
repo: /mnt/d/WORK/JIRA/12345 .../OGL_App   # หลาย repo คั่นด้วย ;
branch: ticket/44
session: <uuid เต็ม>
cwd: /home/<user>
created: 2026-09-25 16:17
next: ถามผลทดสอบ Phase 3 แล้วบันทึก FormEdit.txt   # 1 บรรทัด — /recap โชว์ตรงนี้
---

# Handoff: RM #12345 — <หัวข้อ>

📡 Session: <uuid 8 ตัวแรก> | <repo/app> | resume: `claude --resume <uuid>` (จาก cwd ข้างบน)
**Date**: YYYY-MM-DD HH:MM → ทำต่อ <วัน ถ้า user บอก>

## What We Did
- ... (สิ่งที่ทำจริง + หลักฐาน: commit hash, journal #, logtime #, revision)

## State
- (checklist Step 3 ของ stream นี้)

## Pending
- [ ] ... (รวม pending เก่าที่ยังไม่เสร็จจาก handoff ก่อนหน้า)
- [ ] commit/push ... — รอคำสั่งผู้พัฒนาเท่านั้น

## Next Session
- [ ] ขั้นแรกที่ต้องทำ/ถาม (เรียงลำดับ)

## ⚠️ Rules / Gotchas ของงานนี้
- (กฎจาก memory ที่ใช้กับงานนี้ — อ้างชื่อ memory เช่น feedback_phase_by_phase_approval ถ้ามี)

## Key Files
- (absolute path — Windows path ใส่ได้ แต่ใส่ /mnt/d/... คู่ด้วยถ้าสะดวก)
```

แล้วรัน:
```bash
python3 ~/.claude/skills/forward/scripts/handoffs.py supersede <key> "<ไฟล์ที่เพิ่งเขียน>"
```

## Step 5 — Outbox (รวม pending รายวัน)

append ลง `~/ψ/outbox/YYYY-MM-DD_pending.md` (สร้างถ้ายังไม่มี):

```markdown
## From: <stream> <key> (RM #N) /forward HH:MM
- [ ] item 1
```

## Step 6 — Memory (เฉพาะเมื่อจำเป็น)

ถ้างานนี้มี `project_*` memory อยู่แล้ว (เช่น project_<งาน>) และสถานะเปลี่ยนอย่างมีนัยสำคัญ
→ อัปเดต memory นั้นให้ตรง (สั้นๆ + ชี้ไปที่ไฟล์ handoff). **ไม่ต้อง** สร้าง memory ใหม่ทุกครั้งที่ forward — handoff คือที่เก็บหลัก

## Step 7 — สรุปให้ผู้ใช้

```
📤 Handoff บันทึกแล้ว
| stream | key | status | next |
|---|---|---|---|
| grouplife | rm12345 | open | ถามผลทดสอบ Phase 3 |
ไฟล์: $HOME/ψ/inbox/handoff/...md   (absolute path เสมอ)
ปิดงานที่จบแล้ว: rm12344 → closed
งานค้างอื่นใน vault: N งาน (ดู /recap)
▶ เปิด session ใหม่แล้วพิมพ์ /recap  (หรือ /recap 12345 เพื่อโหลดงานนี้ตรงๆ)
```

## --close KEY

`handoffs.py close <key>` (ปิดทั้ง chain ของ key นั้น) แล้วแจ้งผล — ใช้เมื่อ RM ปิด/งานจบ

## --plan

หลัง Step 7: `EnterPlanMode` → เขียน plan (สรุป + Next Session + path handoff) → `ExitPlanMode`
เพื่อให้ผู้ใช้กด approve + clear context ได้ในหน้าเดียว (ต้องทำครบ 3 ขั้น ไม่งั้น UI ไม่ขึ้น)
ถ้าไม่มี `--plan` ไม่ต้องเข้า Plan Mode

ถ้าเรียก /forward ซ้ำใน session เดิม: อัปเดตไฟล์ handoff เดิมของ key นั้น (ไม่สร้างไฟล์ใหม่ซ้ำ)

ARGUMENTS: $ARGUMENTS
