---
name: ocean-checkin-report
description: 'นับจำนวน "วัน" ที่แต่ละคนเข้าออฟฟิศ (ci/co) / Work From Home (wfh) / ลา (SL, VAC, PL, FAM, MAR, ET) จากห้อง Google Chat "developer-check-in" (หรือห้อง check-in อื่น) ตามช่วงเวลาที่กำหนด — อ่านอย่างเดียวผ่าน Google Chat API, ถามช่วงเวลาและชื่อคนทุกครั้งที่เรียก, ถ้าเครื่องยังไม่ได้เปิดสิทธิ์ Google Chat จะพาทำ setup ทีละขั้น. Use when user says "/ocean-checkin-report", ถามว่าใครเข้าออฟฟิศ/WFH กี่วัน, หรือขอสรุป check-in จาก Google Chat.'
created_at: 2026-10-29T12:00:00+07:00
argument-hint: "[ชื่อคน] [ช่วงเวลา]"
---

# /ocean-checkin-report — สรุปวันเข้าออฟฟิศ / WFH / ลา จาก Google Chat

อ่านข้อความในห้อง check-in ของ Google Chat (default: **developer-check-in**, `spaces/AAQA2x4c_Dw`)
แล้วนับเป็น **จำนวนวัน** (ไม่ใช่จำนวนข้อความ) ต่อเดือน

**ห้ามเด็ดขาด**: ส่ง/แก้/ลบข้อความใน Google Chat — skill นี้ขอแค่ scope `*.readonly`
**ห้ามเด็ดขาด**: เก็บ `client_secret.json` / `token.json` ไว้ในโฟลเดอร์ skill หรือ push ขึ้น repo ใดๆ —
secret อยู่ที่ `~/.config/ocean-google-chat/` เท่านั้น

---

## Step 0: Init + ตรวจสิทธิ์ Google Chat

```bash
SKILL_DIR="<ตำแหน่งโฟลเดอร์ของ skill นี้>"      # เช่น ~/.claude/skills/ocean-checkin-report
CFG=~/.config/ocean-google-chat
VPY=$CFG/.venv/bin/python3; [ -x "$VPY" ] || VPY=$CFG/.venv/Scripts/python.exe
[ -x "$VPY" ] || bash "$SKILL_DIR/scripts/setup_venv.sh"     # สร้าง venv + pip install ครั้งแรก
"$VPY" "$SKILL_DIR/scripts/chat_client.py" check
```

- `"ready": true` → ไป Step 1
- อย่างอื่น → ไป **Step 0b** (ตาม field ที่ไม่ผ่าน) แล้วค่อย `check` ซ้ำจน ready
  - `deps: false` → รัน `setup_venv.sh` ใหม่
  - `client_secret: null` → 0b ข้อ A หรือ B
  - `token: null` → 0b ข้อ C (authorize)
  - `api_error` มี 403/404 → ยังไม่ได้ Enable Chat API หรือยังไม่ได้กรอก Chat app Configuration (0b ข้อ B.1–B.2)
    หรือ Workspace admin บล็อก → แจ้ง user พร้อมข้อความ error ตรงตัว

## Step 0b: Setup สิทธิ์ Google Chat (ทำครั้งเดียวต่อเครื่อง) — อธิบายให้ user ทีละขั้นเป็นภาษาไทย

ต้องมี OAuth client แบบ **Desktop app** ที่อยู่ใน GCP project ซึ่งเปิด Google Chat API ไว้แล้ว เลือกทางใดทางหนึ่ง:

**A. ใช้ OAuth client เดิมของทีม (ง่ายสุด)** — project `292140200601` ("Claude For Access GDrive")
เปิด Chat API + กรอก Configuration ไว้แล้ว
1. ขอไฟล์ `client_secret.json` จาก ภาณุพันธ์ (Panupun.su) **ทางช่องทางส่วนตัว** (ห้ามแนบใน repo/ห้อง chat สาธารณะ)
2. วางไว้ที่ `~/.config/ocean-google-chat/client_secret.json` (`chmod 600`)
3. ถ้า OAuth consent screen ของ project เป็น External + Testing ต้องให้เจ้าของ project เพิ่มอีเมลผู้ใช้ใหม่เป็น Test user ก่อน
   (ถ้าเป็น Internal ข้ามได้)
4. ไปข้อ C

**B. สร้าง GCP project ของตัวเอง** (user ต้องทำเองใน Console — Claude เข้า Console ไม่ได้)
1. เปิด Google Chat API: `https://console.cloud.google.com/apis/library/chat.googleapis.com?project=<PROJECT>` → **Enable**
2. ตั้งค่า Chat app ขั้นต่ำ (จำเป็นแม้จะอ่านอย่างเดียว ไม่งั้น API ตอบ 404/403):
   `https://console.cloud.google.com/apis/api/chat.googleapis.com/hangouts-chat?project=<PROJECT>`
   - App name: `Claude Chat Reader`
   - Avatar URL: `https://developers.google.com/chat/images/quickstart-app-avatar.png`
   - Description: `read-only history`
   - **ไม่ต้องติ๊ก** Interactive features → Save
3. OAuth consent screen → ถ้า External ให้เพิ่ม scope `chat.spaces.readonly`, `chat.messages.readonly`,
   `chat.memberships.readonly` ในหน้า Data Access และเพิ่มตัวเองเป็น Test user
4. Credentials → Create OAuth client ID → **Desktop app** → Download JSON →
   บันทึกเป็น `~/.config/ocean-google-chat/client_secret.json`
5. ไปข้อ C

**C. Authorize (ได้ token.json)**
1. รันแบบ **background** (Bash `run_in_background: true`) — ห้ามรันซ้อนสองตัว (พอร์ต 8766 ชนกัน → `Address already in use`):
   ```bash
   "$VPY" "$SKILL_DIR/scripts/chat_client.py" authorize
   ```
2. อ่านบรรทัด URL จาก output ของ **process ที่กำลังรันอยู่นี้** แล้วส่งลิงก์เต็มให้ user
   (ลิงก์จากรอบเก่าใช้ไม่ได้ — `state` ต้องตรงกับ process ปัจจุบัน; ตัวรอรับ timeout 15 นาที)
3. user เปิดลิงก์ → login ด้วยบัญชี @ocean.co.th → **Allow** ครบทุกสิทธิ์
4. ผลลัพธ์:
   - เห็น "ยืนยันสิทธิ์สำเร็จ" → process จบเอง ได้ `token.json` → `check` ซ้ำ
   - เห็น `ERR_CONNECTION_REFUSED` (มักเกิดเมื่อ browser อยู่บน Windows แต่ script รันใน WSL) →
     ขอให้ user copy URL เต็มจากแถบที่อยู่ (`http://localhost:8766/?state=...&code=...`) มาวาง แล้วส่งต่อให้ตัวรอรับเอง:
     `curl -s "<URL ที่ user วาง>"` (ทำได้เฉพาะตอน process authorize ยังรันอยู่ และ `state` ตรงกัน)
   - หน้า Google ขึ้น "access blocked" / "admin restricted" → Workspace admin บล็อก ต้องให้ admin อนุญาต จบ skill

## Step 1: ถามช่วงเวลา + ชื่อคน (ถามทุกครั้งที่เรียก skill)

ใช้ `AskUserQuestion` 2 คำถามในครั้งเดียว (ถ้า user ระบุมาครบทั้งสองอย่างใน args แล้ว ให้ยืนยันสั้นๆ แทนการถามซ้ำ):

1. **ช่วงเวลา** — options: `3 เดือนล่าสุด (Recommended)`, `1 เดือนล่าสุด`, `เดือนนี้`, `เดือนที่แล้ว`
   (user กำหนดเองผ่าน Other ได้ เช่น `01/08/2026 - 30/09/2026`) → แปลงเป็น `--since/--until` (YYYY-MM-DD, ค.ศ.;
   ถ้า user ให้ พ.ศ. ลบ 543)
2. **ชื่อคนที่จะค้นหา** — options: `ระบุชื่อ (พิมพ์ใน Other)`, `ทุกคนในห้อง`, `ตัวเอง`
   - พิมพ์ชื่อไทยหรืออังกฤษบางส่วนได้ (เช่น `กฤตกร`, `Thongchai`) — หลายคนคั่นด้วย `,`
   - `ตัวเอง` → ใช้ชื่อเจ้าของเครื่อง (ดูจาก userEmail / memory)

ถ้า user ไม่ระบุห้อง ใช้ developer-check-in; ระบุห้องอื่นได้ด้วย `--space "<ชื่อห้องบางส่วน>"`

## Step 2: รัน

```bash
"$VPY" "$SKILL_DIR/scripts/checkin_report.py" --name "<ชื่อ>" --since YYYY-MM-DD --until YYYY-MM-DD [--space "<ห้อง>"] [--raw]
"$VPY" "$SKILL_DIR/scripts/checkin_report.py" --all --since ... --until ...       # ทุกคน
"$VPY" "$SKILL_DIR/scripts/checkin_report.py" --list-people --since ... --until ... # รายชื่อคนในห้อง
```

- ชื่อเจอหลายคน → script exit 2 พร้อมรายชื่อ → ถาม user ให้เลือก
- ไม่เจอชื่อ → รัน `--list-people` แล้วเสนอชื่อใกล้เคียง
- หลายคน → รัน `--name` ทีละคน
- ข้อมูลน่าสงสัย → เพิ่ม `--raw` เพื่อดูข้อความดิบรายวันก่อนสรุป

## Step 3: ตอบ user

แสดงตารางรายเดือน **หน่วยเป็น "วัน" ทุกช่อง** + รายการวัน, วันลา, วันที่ไม่ชัด, วันที่ไม่มีข้อความ
บอกข้อสังเกตที่กระทบตัวเลขทุกครั้ง (วัน ci+wfh ปนกัน, มีแค่ co ไม่มี ci, ลาบางช่วง, วันนี้ยังไม่ check-in)

## กติกาการนับ (script ทำให้แล้ว — ใช้อธิบาย user)

| ข้อความ (ไม่สนตัวเล็ก/ใหญ่) | นับเป็น |
|---|---|
| ขึ้นต้น `ci` / `co` | เข้าออฟฟิศ |
| ขึ้นต้น `wfh` (รวม `wfh-co`) | WFH |
| `SL`/`sick`, `VAC`, `PL`, `FAM`, `MAR`, `ET` ไม่มีช่วงเวลา หรือมีวันที่ (`19/10/2026-22/10/2026`, `24/08/2569, 25/08/2569`) | ลาเต็มวัน (ขยายช่วงวันที่ให้, ข้ามเสาร์-อาทิตย์, พ.ศ.→ค.ศ.) |
| ลามีช่วงเวลา (`sl 14.00-17.00`) ในวันที่มี ci/wfh ด้วย | ยังนับเป็นวันทำงานเต็ม + แจ้งเป็น "ลาบางช่วง" |

- 1 วันนับครั้งเดียว ไม่ว่าจะพิมพ์กี่ข้อความ
- ข้อความ check-out ก่อน 05:00 → นับเป็นของวันทำงานก่อนหน้า
- วันเดียวมีทั้ง ci/co และ wfh → "ไม่ชัด" แยกออกมา ให้ user ตัดสินเอง
- วันธรรมดาที่ไม่มีข้อความเลย → แสดงรายการ (อาจเป็นวันหยุดนักขัตฤกษ์หรือลาที่ไม่แจ้ง — script ไม่รู้ปฏิทินวันหยุด)
- เวลาเป็น Asia/Bangkok (UTC+7)
