# Phase 5–6, ตารางสคริปต์, ข้อจำกัด (อ่านเมื่อถึงขั้นนั้นเท่านั้น)

## Phase 5 — แปะลิงก์กลับที่ Sheet ต้นทาง (App ที่ถูก WinExec จาก App อื่น)

```bash
$PY $S/speckit_stamp_origin.py <origin_spreadsheet_id> <app_spreadsheet_id> <YYYY-MM-DD> [--dry]
```
จับแถวต้นทางจาก `/d/<app_spreadsheet_id>/` ใน Sheet URL, เขียนเฉพาะ cell `SpecKit`, รันซ้ำได้. `<origin_spreadsheet_id>` ถามผู้ใช้/หาด้วย `find_app_sheet.py` — ห้ามเดา.

## Phase 6 — สรุปให้ผู้ใช้

ลิงก์โฟลเดอร์ App/เมนูบน Drive + Sheet; ต่อเมนู: จำนวนหน้าจอ (ไฟล์ REQ), ผล gate (verify_evidence / ผู้ตรวจ), Open Questions ที่ผู้ใช้ต้องตอบ, `sheet_vs_code_diffs`
(Sheet analyst ควรอัพเดท), unit ที่ไม่ได้อ่าน, ไฟล์ `stale`. ไม่ต้อง commit/push.

## สคริปต์

| สคริปต์ | หน้าที่ |
|---|---|
| `check_setup.py` | preflight |
| `find_app_sheet.py` / `read_menus.py` | หา Sheet / อ่าน Menu Contents (`list`), tab วิเคราะห์ (`tab`), tab ER (`er`) |
| `speckit_drive.py` | `ensure-app` / `ensure-feature` / `upload` (ทับชื่อเดิม ไม่ซ้ำ ไม่ลบ) / `download` |
| `sheet_speckit.py` / `speckit_stamp_origin.py` | คอลัมน์ `SpecKit` + "Speckit URL" (A5/B5) + B4 / แปะกลับต้นทาง WinExec |
| `init_workspace.py` | สร้าง workspace + `specs/<FEATURE>/req/` |
| `fetch_source.py` | snapshot source (`files [--max-bytes N]`, `tree`) และ DB object (`db`) แบบ read-only; กู้ไทยจาก Gitblit (cp874→mojibake) + `*.dfm.decoded.txt`; `tree` ข้ามโฟลเดอร์ที่ Gitblit ตอบ 500 |
| `verify_evidence.py` | gate "ห้ามเดา": quote/บรรทัด/ครอบคลุม ID/placeholder/path |

ต้องอ่านโค้ดจาก `source/` เสมอ ไม่ใช่ `browse_repo.py read` ตรง ๆ (ไทยเพี้ยน); `.dfm` เก็บไทยเป็นรหัส `#3650#…` — อ่านจาก `*.dfm.decoded.txt`.

## ข้อจำกัด

- "ตรง 100%" = ตรง master ของ repo + DB SIT `10.100.2.52` ณ วันที่สร้าง; runtime config/ข้อมูลจริงในตารางอ่านไม่ได้ → Open Issue.
- ไฟล์ใหญ่ (> 2MB เช่น `MainUnit.dfm`) ต้องใช้ `--max-bytes` แล้ว grep (อย่า Read ทั้งไฟล์); Gitblit ล็อกอิน timeout ได้ — ลองใหม่/แจ้งผู้ใช้ ไม่วนซ้ำ.
- ใช้เวลา/token ต่อเมนูมาก (อ่าน source+DB + เขียน REQ + ผู้ตรวจอิสระ) — แนะนำ Break point.
