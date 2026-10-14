---
name: delphi-build-run
description: Compile (dcc32) และ run โปรแกรม Delphi 7 อัตโนมัติจาก Claude Code บน Windows หรือ WSL — ถามหา path โปรแกรม, ตรวจว่าโปรแกรมรับ parameter login (ParamStr) หรือไม่ แล้วถามว่าจะใช้ user/pass ที่บันทึกไว้หรือเปลี่ยนใหม่ ก่อน run. ใช้ได้กับเครื่องอื่นที่ลง Delphi 7 (script Python ติดมากับ skill, ใช้ standard library อย่างเดียว). ขอบเขต: build/run + แก้ IP ใน Config.ini เท่านั้น ห้ามแก้ source code. Use when user says "/delphi-build-run", ขอ compile/build/run โปรแกรม Delphi 7 หลังแก้โค้ด.
---

# /delphi-build-run

> ## ⛔ ขอบเขตของ skill นี้ (เด็ดขาด)
> - **ห้ามแก้ไข source code โดยเด็ดขาด** — ทุกไฟล์ `.pas` `.dfm` `.dpr` `.dof` `.cfg` `.res` และไฟล์โค้ด/โปรเจกต์อื่นใดทั้งหมด ไม่ว่า build จะ error หรือ run ไม่ผ่านก็ตาม และห้ามแก้ผ่านเครื่องมืออื่น (Edit/Write/sed/python ฯลฯ) ในนามของ skill นี้
> - สิ่งที่ skill นี้ทำได้ **มีเพียง 2 อย่าง**: (1) แก้ **IP/server ในไฟล์ `Config.ini`** ตามที่ผู้ใช้เลือกเท่านั้น (ผ่าน `use-config`) และ (2) **build + run** โปรแกรม Delphi
> - ถ้า build ไม่ผ่าน ให้ **รายงาน error ตามจริง** (ไฟล์/บรรทัด/ข้อความ) แล้วหยุด ห้ามแก้โค้ดเพื่อให้ผ่าน ผู้ใช้เป็นคนตัดสินใจเองว่าจะแก้อย่างไร
> - ห้ามเปลี่ยนค่าอื่นใน `Config.ini` นอกจาก `Data_Source` (server/IP)

Build ด้วย `dcc32.exe` ของ Delphi 7 แล้ว run exe ที่ได้ ผ่าน script `scripts/delphi_build_run.py`
(Python 3 standard library อย่างเดียว ไม่ต้อง pip install) ทำงานได้ทั้ง Windows native และ WSL
ถ้าเป็น macOS/Linux ล้วน ไม่รองรับ (dcc32 เป็น Win32) — ให้บอกผู้ใช้ตรงๆ

เรียก script ด้วย: `python3 ~/.claude/skills/delphi-build-run/scripts/delphi_build_run.py <cmd> ...`
(บน Windows ใช้ `python` / `py` และ path ของ skill บนเครื่องนั้น)

## ขั้นตอน

1. **ตรวจเครื่อง**: `detect` — หา Delphi 7 root + dcc32 (ปกติ `C:\Program Files (x86)\Borland\Delphi7`)
   ถ้าไม่เจอ ให้ถามผู้ใช้หา folder แล้ว `set-delphi <root>` (จำไว้ใน `~/.config/delphi-build-run/config.json` ต่อเครื่อง ไม่อยู่ใน skill)
2. **หา path โปรแกรม** (ไฟล์ `.dpr` หรือ folder ที่มี `.dpr`) — เรียก `/delphi-build-run` เฉย ๆ โดยไม่ระบุ path ก็ได้ ตัดสินตามลำดับนี้:
   1. **ผู้ใช้ส่ง path มากับคำสั่ง** (args) → ใช้ตามนั้น
   2. **ไม่มี args** → รัน `recent` (อ่านรายการโปรเจกต์ที่เคยใช้บนเครื่องนี้จาก `~/.config/delphi-build-run/config.json` ที่ script จำให้อัตโนมัติทุกครั้งที่ scan/build/run สำเร็จ + `.dpr` ใน folder ปัจจุบัน) แล้วดูว่า **มั่นใจ** ไหม:
      - มั่นใจ = บทสนทนา/บริบทชี้ชัดว่าหมายถึงโปรเจกต์ไหน, หรือ `cwd_dpr` มี `.dpr` เดียว, หรือ `recent` มีโปรเจกต์เดียว → ใช้ตัวนั้นเลยไม่ต้องถาม แต่ให้บอกผู้ใช้ 1 บรรทัดว่าใช้โปรเจกต์ไหน
      - **ไม่มั่นใจ** (มีหลายตัวและบริบทไม่ชี้ชัด, หรือ `recent` ว่าง) → ถามด้วย AskUserQuestion แบบ radio (single-select) ให้เลือกว่าจะ run ตัวไหน: ใส่โปรเจกต์จาก `recent` (ล่าสุดเป็นข้อแรก + "(Recommended)", สูงสุด 4 ตัว, label = ชื่อโปรแกรม, description = path เต็ม) ผู้ใช้เลือก "Other" เพื่อพิมพ์ path ใหม่ได้; ถ้า `recent` ว่างให้ขอ path ผ่าน Other
   - ห้ามเดา path เองนอกเหนือจากที่ `recent`/args/บริบทระบุ
   - โปรเจกต์ต้องอยู่บน Windows drive (C:, D:, ...) — ถ้าอยู่ใน filesystem ของ WSL (UNC) script จะ error เพราะ Windows tool ใช้เป็น working folder ไม่ได้
   - ถ้า folder ที่ระบุไม่มี `.dpr` ในตัวเอง (เช่น อยู่ในโฟลเดอร์ย่อย `trunk`) ให้ค้นหา `.dpr` ใต้ folder นั้น (find) แล้วถามเป็น radio ถ้าเจอหลายไฟล์ (แค่ค้นหา ไม่แก้ไฟล์ใด)
3. **ถามโหมดการทำงาน** (ทุกครั้งที่ถูกเรียก ห้ามเดา แม้ผู้ใช้ส่ง path มาพร้อมคำสั่ง) **ต้องถามด้วย AskUserQuestion เป็นตัวเลือก radio (single-select, `multiSelect: false`) ห้ามให้ผู้ใช้พิมพ์ตอบ** ตัวเลือก 3 ข้อตามนี้ (Build + Run เป็นข้อแรกและใส่ "(Recommended)"):
   - **Build อย่างเดียว** → ทำขั้น 5 (ข้ามขั้น param/DB server/run)
   - **Run อย่างเดียว** (ใช้ exe ที่ build ไว้แล้ว ไม่ compile ใหม่) → ทำขั้น scan param, 4, 4.2 และ 6 — ถ้าไม่พบ exe ให้แจ้งผู้ใช้และเสนอเปลี่ยนเป็น Build + Run
   - **Build + Run** → ทำครบทุกขั้น; build ต้องผ่าน (`BUILD_RESULT: OK`) ก่อนจึง run ถ้า FAILED ห้าม run exe เก่าแทน
4. **scan parameter** (เฉพาะโหมดที่มี run): `scan <dpr>` — ดู `ParamStr(N)`/`ParamCount` ใน source (ข้าม `ParamStr(0)` เพราะคือ path exe)
   - ถ้า `needs_params` เป็น false → ข้ามไปขั้น build/run
   - ถ้ามี `saved_params_masked` อยู่แล้ว → ถามว่า "จะ login ด้วย user/param ชุดนี้ใช่ไหม?" (แสดง password เป็น `***`) ถ้าต้องการเปลี่ยนให้ผู้ใช้พิมพ์ user/pass หรือ param ใหม่
   - ถ้ายังไม่เคยบันทึก → ถามค่าของแต่ละ `ParamStr(N)` ที่จำเป็น (เช่น OGL_Operation: ParamStr(1)=user, ParamStr(2)=password) ผ่าน param ตรงๆ ไม่ต้องผ่านหน้า login
   - บันทึกด้วย `params-save <dpr> --set 1=<user> --set 2=<pass>` (ถามก่อนว่าจะให้จำไหม; ล้างด้วย `params-clear <dpr>`)
4.1 (ไม่บังคับ) ถ้าผู้ใช้อยากให้เปลี่ยนค่าเฉพาะครั้งนี้ ใช้ `run --set N=V` แทนการบันทึก
4.2 **เลือก DB server ที่จะ run** (เฉพาะโหมดที่มี run และโปรแกรมมี `Config.ini` ข้าง exe): รัน `configs <dpr>` อ่าน config ที่ exe ใช้จริง (`Config.ini` ใน folder ของ exe — โปรแกรม Delphi กลุ่มนี้อ่าน `GetExePath + 'Config.ini'`) แล้วดู `current_server` และ `candidates` (Config*.ini ข้าง exe/folder แม่ที่มี Data_Source)
   - ถามด้วย AskUserQuestion แบบ radio (single-select): **.52** (10.100.2.52 = SIT) / **.139** (10.100.3.139) / **.22** (12.100.7.22 = UAT) — label ตามที่ผู้ใช้ยืนยัน ห้ามใช้ข้อความ `pnDatabaseName` ใน MainUnit.pas เป็นตัวอ้างอิง (มันเขียนสลับ: .52 ขึ้นว่า UAT) — **ค่า default คือ IP ที่อยู่ใน config ปัจจุบัน (`current_server`)**: ให้วางข้อที่ตรงกับ `current_server` เป็นข้อแรกสุดและใส่ "(Recommended) (ค่าใน config ปัจจุบัน)" ส่วนอีก 2 ข้อเรียงตามหลัง; ถ้า `current_server` ไม่ตรงกับ .52/.139/.22 (เช่น เป็น prod) ให้เพิ่มเป็นข้อแรกด้วย IP จริงนั้น (สูงสุด 4 ตัวเลือก); ไม่ต้องสลับ config ถ้าผู้ใช้เลือกข้อแรก
   - ถ้าเลือกต่างจากปัจจุบัน: `use-config <dpr> --server 52|139|22` — script copy template ini ที่ Data_Source ตรงมาเป็น `Config.ini` และสำรองไฟล์เดิมไว้ครั้งแรกเป็น `Config.ini.before-delphi-build-run` (ไม่ทับ backup เดิม)
   - ถ้าไม่มี template ของ server นั้น (ปัจจุบัน **.22 ไม่มี template**) script จะปฏิเสธ → บอกผู้ใช้ตรงๆ ว่าจะเป็นการ copy จาก template .52 แล้วเปลี่ยนเฉพาะ `Data_Source` ยังไม่ยืนยัน user/password ภายในไฟล์ ถามยืนยันด้วย radio ก่อน แล้วค่อย re-run ด้วย `--allow-derived`
   - login param (user/pass จากขั้น 4) เป็นคนละอย่างกับ DB account ใน Config.ini ห้ามเอามาปะปนหรืออ่านค่า password ใน ini ออกมาแสดง
   - ต้องสลับ config **ก่อน** `run` และตอนสรุปให้บอกว่า run ด้วย server ไหน
5. **Build**: `build <dpr>` (เพิ่ม `--rebuild` = -B build all)
   - อ่านบรรทัดท้าย `BUILD_RESULT: OK|FAILED exe=...` และ `errors=N warnings=N`
   - lib path ประกอบจาก `SearchPath` ใน `.dof` + Library path ของ Delphi 7 ใน registry (รวม TMS/ReportBuilder ที่ลงใน IDE)
   - FAILED → **รายงาน error ให้ผู้ใช้แล้วหยุด ห้ามแก้โค้ด**; ทำตาม `HINT:` ที่ script พิมพ์ให้ได้เฉพาะที่ไม่ใช่การแก้โค้ด (เช่น exe ยังรันค้างอยู่ให้ปิดก่อน แล้ว build ซ้ำ; unit ไม่พบใน library path ให้แจ้งผู้ใช้)
   - **หมายเหตุ**: dcc32 standalone ผ่าน ≠ build ใน IDE จริงเสมอไป (path/ตัวแปรบางอย่างต่างกัน) — ถ้าเจอ error แปลกที่ IDE ไม่เป็น ให้บอกผู้ใช้
6. **Run**: `run <dpr>` — เปิด exe พร้อม param ที่บันทึกไว้/ที่ `--set` ให้, รอ `--wait` วินาที (default 3) แล้วรายงาน `status` (running / exit_code)
   - ก่อน build ซ้ำ ต้องปิด exe ตัวเก่าก่อน (Windows lock ไฟล์ exe)

## DB server ที่รู้จัก (ผู้ใช้ยืนยันแล้ว)

| ตัวเลือก | IP | Environment |
|---|---|---|
| .52 | 10.100.2.52 | **SIT** |
| .139 | 10.100.3.139 | (ยังไม่ระบุ — ถามผู้ใช้ถ้าต้องใช้ชื่อ) |
| .22 | 12.100.7.22 | **UAT** |

ใช้ชื่อ SIT/UAT ตามตารางนี้เสมอเวลาถามหรือสรุป ห้ามอิงข้อความ `pnDatabaseName` ใน `MainUnit.pas` (เขียนสลับ: .52 ขึ้นว่า UAT)

## ข้อสังเกตจากการทดสอบจริง (OGL_Operation)

- Library path ของ IDE มี macro เช่น `$(DXVCL)` ซึ่งเป็น Windows environment variable — script แปลงให้เอง (ถ้า build ขึ้น `File not found: xxx.dcu` ให้เช็กว่า env var นั้นมีบนเครื่อง)
- `run` แล้วได้ `exited_early` exit_code 0 ทันที มักแปลว่าโปรแกรมเรียก `Application.Terminate` เพราะไม่มี `ParamStr(1)/(2)` (user/pass) — ไม่ใช่ bug ของ skill ให้ถามค่า param แล้ว run ใหม่
- build ใช้เวลาหลักสิบวินาทีสำหรับโปรเจกต์ใหญ่ (OGL_Operation ~32 วินาที) และสร้าง .dcu ใน folder โปรเจกต์เหมือน IDE

## การใช้งานผ่าน WSL (กฎสำคัญ)

- **โค้ดโปรแกรมต้องอยู่ฝั่ง Windows เสมอ (C:, D:, ...) ห้ามย้าย/copy โค้ดเข้า filesystem ของ WSL** เพื่อ build/run
- สั่งจาก WSL ได้เลยโดยให้ path แบบ `/mnt/d/WORK/OGL_Operation` หรือ `D:\WORK\OGL_Operation` ก็ได้ — script แปลงด้วย `wslpath` ให้เอง
  แล้วเรียก `dcc32.exe` และ exe ของโปรแกรมแบบ Windows process ตรงๆ (working folder = folder ของ .dpr บน Windows drive)
- path ที่อยู่ใน WSL (เช่น `/home/...`, `/tmp/...` → กลายเป็น `\\wsl.localhost\...`) จะถูก script ปฏิเสธ ห้ามแก้ด้วยการ copy โค้ดมาไว้ใน WSL ให้บอกผู้ใช้ให้ชี้ path ฝั่ง Windows แทน
- ไฟล์ทดสอบ/โปรเจกต์ตัวอย่างของ skill ให้วางที่ Windows drive เช่น `/mnt/c/Users/Public/...` แล้วลบทิ้งเมื่อเสร็จ
- Python ที่ใช้เรียก script รันใน WSL ได้ (Python ของ WSL เอง) ส่วนบน Windows ล้วนใช้ `python`/`py` — ไม่ต้องติดตั้งอะไรเพิ่ม

## กฎ

- **คำถามที่มีตัวเลือกจำกัดทั้งหมด** (โปรเจกต์ที่จะ run เมื่อไม่มั่นใจ, โหมด build/run, DB server .52/.139/.22, ใช้ user/pass ที่บันทึกไว้หรือเปลี่ยน, จะบันทึก param ไหม) ต้องถามด้วย AskUserQuestion แบบ radio ให้ผู้ใช้กดเลือก ไม่ให้พิมพ์ตอบ — พิมพ์เฉพาะกรณีที่ต้องกรอกค่าจริง (path โปรแกรม, user, password) ซึ่งใช้ช่อง "Other" ของ AskUserQuestion ได้
- ห้ามเขียน password ลงใน output/สรุปแบบ plain text — mask เป็น `***` เสมอ
- **ห้ามแก้ source code ทุกกรณี** (ดูกล่องขอบเขตด้านบน) — แก้ได้แค่ `Data_Source` ใน `Config.ini` ตามที่ผู้ใช้เลือก
- การตั้งค่าเฉพาะเครื่อง (Delphi root, param ที่จำไว้, รายการโปรเจกต์ล่าสุด `recent`) อยู่ที่ `~/.config/delphi-build-run/config.json` ไม่ใช่ใน skill — ย้ายเครื่องแล้วต้อง `detect`/ถามใหม่
- ถ้าต้องเขียน Python เพิ่มเพื่อจัดการเรื่องนี้ ให้ใส่ไว้ใน `scripts/` ของ skill นี้เท่านั้น (ห้ามเขียนสคริปต์ที่ไปแก้โค้ดโปรเจกต์)
