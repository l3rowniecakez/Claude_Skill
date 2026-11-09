---
name: redmine-draft-mail-uat
description: ร่างเมล "[แจ้ง UAT]" เป็น Gmail Draft (เฉพาะ subject + body พร้อมภาพ step-by-step ที่ปิดข้อมูลส่วนบุคคลตาม PDPA แล้ว ไม่ใส่ To/Cc และไม่ส่ง) จากงาน/Redmine ที่ทำ โดยใช้ "รูปแบบการส่งเมล UAT ของผู้ใช้คนนั้น" ที่เรียนรู้จากเมลขาออก (Sent) ของเขาเอง — ใช้ได้ทุกเครื่อง/ทุกบัญชี ครั้งแรกบนเครื่องใหม่จะเรียนรู้พฤติกรรมการส่งก่อน ภาพ capture หน้าจอผู้พัฒนาถ่ายเอง (skill ไม่จับภาพให้) แล้ว skill เบลอ PDPA ให้ และถ้างานมี Spec Kit (speckit/<RM>/) จะดึงสิ่งที่ทำ/หน้าจอที่ต้องทดสอบ/ผลที่คาดหวัง/ภาพที่ต้องมี จาก req + spec + tasks มาเขียนเมลให้ตรงกัน. Use when user says "/redmine-draft-mail-uat", "ร่างเมลแจ้ง UAT", "เตรียมส่ง UAT", "draft mail UAT".
---

# /redmine-draft-mail-uat — ร่างเมลแจ้ง UAT เป็น Gmail Draft

ทำ **subject + body** ของเมลแจ้ง UAT (ตามสไตล์ที่ผู้ใช้คนนั้นส่งจริง) พร้อมตำแหน่งภาพขั้นตอน UAT (ผู้พัฒนาถ่ายภาพเอง) แล้วบันทึกเป็น **Draft** ใน Gmail ให้ผู้ใช้ตรวจ/เติมผู้รับ/ส่งเอง

## สภาพแวดล้อมที่รองรับ (ต้องใช้ได้ทุกเครื่อง)
- **Windows native** (Claude Code CLI และ Claude Desktop บน Windows), **WSL**, **Linux/macOS** — สคริปต์ทุกตัวเป็น Python ล้วน (ไม่เรียก PowerShell/bash) เพราะบางเครื่องบล็อก PowerShell
- เรียกสคริปต์ด้วย Python ของเครื่องนั้น: Windows = `python` หรือ `py -3`, WSL/Linux/macOS = `python3` (ในตัวอย่างด้านล่างเขียน `python3` ให้แทนด้วยคำสั่งที่เหมาะกับเครื่อง); path ของ skill: Windows `%USERPROFILE%\.claude\skills\redmine-draft-mail-uat\scripts`, อื่นๆ `~/.claude/skills/redmine-draft-mail-uat/scripts`
- ติดตั้ง lib ครั้งเดียว: `py -m pip install google-api-python-client google-auth google-auth-oauthlib Pillow` (Windows) / `pip install ...` (อื่นๆ) — แนะนำ venv; `check_env.py` บอกว่าขาดอะไร
- ถ้า Python ที่ใช้มี Python 3.9 ขึ้นไปก็พอ (ไม่มี syntax ใหม่กว่านั้น); ข้อความไทยบนคอนโซล Windows ถูกตั้ง UTF-8 ในสคริปต์แล้ว; ค่าที่ต้องส่งเป็นภาษาไทยให้ส่งผ่านไฟล์ (`--subject-file`, `--text-file`, scenario JSON) ไม่ใส่ใน command line
- ข้อมูลเฉพาะเครื่อง/ผู้ใช้อยู่ใน `~/.config/redmine-draft-mail-uat/` (Windows: `%USERPROFILE%\.config\redmine-draft-mail-uat\`) — เครื่องใหม่ = profile ว่าง จึงต้องเรียนรู้ (Step 1) ใหม่เสมอ

## กฎเหล็ก
1. **ห้ามส่งเมล** — สร้างได้แค่ Draft (`drafts.create`) ไม่มีการเรียก `messages.send` / `drafts.send` เด็ดขาด
2. **ไม่ใส่ To / Cc / Bcc** ผู้ใช้เติมเอง (เว้นแต่ผู้ใช้สั่งให้ใส่)
3. **PDPA**: ห้ามมีข้อมูลส่วนบุคคลทั้งในข้อความและในภาพ — ชื่อ-นามสกุลสมาชิก/ผู้เอาประกัน/ผู้รับผลประโยชน์, ชื่อบริษัทลูกค้า, วันเดือนปีเกิด, เลขบัตรประชาชน/Passport, เบอร์โทร, อีเมลบุคคลภายนอก, ที่อยู่, เลขบัญชี/ชื่อบัญชีธนาคาร, เลขกรมธรรม์+เลขที่สมาชิก (Cer No), ข้อมูลการรักษา/โรค ฯลฯ → **เบลอ/ทึบในภาพ** และใช้ข้อความกลาง/placeholder ในเนื้อเมล (ชื่อพนักงานภายในใช้ได้เท่าที่จำเป็น เช่น คำขึ้นต้นเมล)
4. **ห้ามสร้างภาพปลอม/ภาพจำลอง** และห้ามเดาข้อมูลที่ไม่รู้ — ภาพที่ยังไม่มีให้ใส่ placeholder ไฮไลต์เหลือง (`{{...}}`) บอกผู้ใช้ชัดเจนว่าต้องแทรกภาพไหน
5. ภาพจากเครื่องมือฐานข้อมูล (Navicat/SSMS) หรือหน้าต่างที่ไม่ใช่หน้าจอที่ผู้ใช้ปลายทางเห็น **ไม่ใช้** ในเมลแจ้ง UAT
6. credential/token ห้ามพิมพ์ออกมา; ข้อมูลเฉพาะคน/เครื่อง (profile, samples, token) อยู่ที่ `~/.config/redmine-draft-mail-uat/` ไม่เก็บใน skill และห้าม push ขึ้น repo ใดๆ

## Step 0 — เช็คความพร้อมของเครื่อง (ทุกครั้งที่เรียก)
```bash
PY=python3   # ถ้าเครื่องไม่มี lib ให้ใช้ venv ที่ติดตั้ง google-api-python-client google-auth Pillow
$PY ~/.claude/skills/redmine-draft-mail-uat/scripts/check_env.py
```
- แสดง OK/MISS ของ: python libs, Gmail token (สิทธิ์อ่าน Sent + สร้าง Draft), profile รูปแบบเมลของผู้ใช้
- ขาด lib → `pip install google-api-python-client google-auth google-auth-oauthlib Pillow` (แนะนำ venv `~/.config/redmine-draft-mail-uat/venv`)
- ขาด token → ใช้ OAuth ที่ติดตั้งไว้แล้วของ `claude-google-access` (scope `gmail.modify` พอสำหรับทั้งอ่านและร่าง) หรือรัน `scripts/auth_gmail.py` (ต้องมี `client_secret.json`; flow นี้ยังไม่ได้ทดสอบบนเครื่องต้นทาง) — token แบบ `gmail.compose` อย่างเดียวสร้าง Draft ได้แต่เรียนรู้จาก Sent ไม่ได้

## Step 1 — ครั้งแรกบนเครื่อง/บัญชีใหม่: เรียนรู้พฤติกรรมการส่งเมล UAT ของผู้ใช้คนนั้น
ถ้า `check_env.py` บอก MISS profile (หรือผู้ใช้สั่งเรียนรู้ใหม่):
```bash
python3 ~/.claude/skills/redmine-draft-mail-uat/scripts/learn_style.py            # ย้อนหลัง 3 ปี สูงสุด 60 ฉบับล่าสุด
python3 .../learn_style.py --refresh --years 2 --max 40                          # เรียนรู้ใหม่ (ถ้าต้องการ)
```
- อ่านเมลขาออก (Sent) ที่ subject ขึ้นต้น `[แจ้ง UAT]` / `[แจ้งUAT]` (ไม่นับ Re:/Fwd:) — **อ่านอย่างเดียว** มี retry/backoff กัน Gmail quota
- สรุปที่ได้ (บันทึก `profile.json` + ตัวอย่างล่าสุด 3 ฉบับใน `samples/`): รูปแบบ subject (Task #N / UR / GLF), คำขึ้นต้นที่ใช้บ่อย, บล็อก "ช่องทาง Path สำหรับ UAT" (ล่าสุดก่อน), ประโยคติดต่อ, หัวข้อที่ใช้, ประโยคปิดท้าย, ลายเซ็น, สี เดิม/หลังแก้ไข, ความกว้างภาพ
- **แสดงสรุปให้ผู้ใช้ดูและยืนยัน** ก่อนใช้ (โดยเฉพาะ Path UAT และคำขึ้นต้น) — ผู้ใช้แต่ละคนมีรูปแบบต่างกัน อย่านำรูปแบบของคนอื่นมาใช้
- ถ้าไม่พบเมล `[แจ้ง UAT]` เลย (เช่นเครื่อง/คนใหม่ที่ไม่เคยส่ง) → ถามผู้ใช้ว่าปกติแจ้ง UAT อย่างไร (subject, path, หัวข้อ, ปิดท้าย, ลายเซ็น) แล้วเขียน `profile.json` ตามโครงใน `references/profile_schema.md`
- รันซ้ำ `--refresh` เมื่อผู้ใช้เปลี่ยนวิธีส่ง (เช่น เปลี่ยน path UAT) — ระหว่างใช้งานถ้าผู้ใช้แก้ path/ถ้อยคำ ให้ถามว่าจะอัปเดต profile ไหม

## Step 2 — รวบรวมข้อเท็จจริงของงาน (เริ่มจาก Spec Kit ก่อนเสมอถ้ามี)
**2A. ตรวจว่างานนี้มี Spec Kit หรือไม่** (ตามกฎ /redmine-ur ทุก UR ควรวางแผนด้วย `speckit/<RM>/` — โฟลเดอร์ ticket หรือ `workspace/ur/<ur…>/speckit`):
```bash
python3 ~/.claude/skills/redmine-draft-mail-uat/scripts/speckit_extract.py <โฟลเดอร์ ticket/workspace/speckit> [--feature <RM>]
```
- หาไฟล์เองจาก `.specify/feature.json` → `speckit/<feature>/{spec.md, tasks.md, req/REQ_*.md}` (อ่านอย่างเดียว) แล้วรายงาน: งานใน `tasks.md` เสร็จ/ค้าง, User Story, และ **ทุกหน้าจอ/เมนูใน REQ** พร้อม Given/When/Then, ปุ่ม/เมนู, ข้อความที่ผู้ใช้เห็น, Q ที่ยังเปิด, ภาพที่ต้องมี
- ใช้เป็น **แหล่งหลัก** ของเมล: "ทำอะไรไปบ้าง" = FR/User Story ที่ tasks.md ติ๊กเสร็จ; "ขั้นตอน UAT + ภาพ" = 1 ขั้นตอนต่อ scenario ของแต่ละหน้าจอ (ผลที่คาดหวัง = Then); เคสทดสอบ = ตัวอย่างข้อมูลใน REQ (ห้ามเอาข้อมูลจริง/PDPA จาก SIT มาใส่ ใช้ placeholder เลขที่เตรียมไว้บน UAT)
- `tasks.md` ค้างที่เป็น **การเขียนโค้ด/ฟีเจอร์** = ยังไม่พร้อม UAT ห้ามเขียนในเมลว่าให้ทดสอบ; ค้างที่เป็น **ทดสอบ/ยืนยัน/deploy** = สิ่งที่ UAT จะช่วยปิด ใส่ได้ — Q ที่ยังเปิดและมีผลต่อผู้ทดสอบ (ขอบเขต/การพึ่ง API อื่น) ให้ทำเป็น `{{...}}` หรือแจ้งผู้ใช้ก่อนส่ง
- ตรวจข้อความใน REQ ว่ายังใช้อยู่ (ข้อความ/ปุ่มที่ถูกยกเลิกแล้วอาจยังอยู่ในตาราง MSG) — อย่าคัดลอกลงเมลโดยไม่ตรวจ
- ตั้งต้นเนื้อหา: `... speckit_extract.py <dir> --skeleton content.json` ได้ content.json โครงตั้งต้น (ขั้นตอน+placeholder ภาพ+ตารางเคสต่อ scenario) แล้ว Claude ปรับถ้อยคำ ตัดของที่ยังไม่เสร็จ เติมเดิม/หลังแก้ไข/วัตถุประสงค์
- ถ้า **ไม่มี Spec Kit**: ใช้ RM description + FormEdit.txt + งานใน session แทน และแจ้งผู้ใช้ว่าควรทำ speckit (`/redmine-ur` กำหนดให้วางแผนด้วย speckit) เพื่อให้เมล UAT อ้างอิงได้ครบ

**2B. ข้อมูลอื่น**
- เลข RM/Task + ชื่อเรื่อง: จาก args/บทสนทนา หรือถาม; อ่าน Redmine ผ่าน API (`X-Redmine-API-Key` — ถ้ายังไม่มีให้ถามผู้ใช้)
- สิ่งที่ปรับปรุง (เดิม/หลังแก้ไข/วัตถุประสงค์) — **ใช้เฉพาะข้อเท็จจริงที่ยืนยันได้** ส่วนที่ไม่แน่ใจ (ขอบเขต, path ที่ deploy จริง) ใส่ `{{...}}` ให้ผู้ใช้ยืนยัน
- เคสทดสอบ: ถ้ายังไม่มีข้อมูลทดสอบบน UAT ให้ทำตารางเคสโดยคอลัมน์เลข Batch/เอกสารเป็น `{{...}}`
- ผู้รับ/คำขึ้นต้น: เสนอตัวเลือกจาก `salutation_top` ใน profile ให้เลือกตามฝ่ายที่เกี่ยวข้อง (ไม่ต้องใส่อีเมล)

## Step 3 — ภาพประกอบขั้นตอน UAT (ผู้พัฒนาถ่ายเอง)
**นโยบาย (ผู้ใช้สั่ง 2026-11-09): skill นี้ไม่จับภาพหน้าจอ/ไม่ควบคุม GUI โปรแกรมเอง**  — ผู้พัฒนาแคปหน้าจอเอง Claude ทำแค่ร่างเมล + จัดการภาพที่ผู้ใช้ให้มา

**3A. รายการภาพที่ต้องมี** = หน้าจอ/scenario ทั้งหมดจาก `speckit_extract.py` (ก่อน+หลังทำของแต่ละ scenario) — ทำเป็นตารางให้ผู้พัฒนา (ขั้นตอนไหน / หน้าจอไหน / ต้องเห็นอะไร) แล้วใส่ placeholder ไฮไลต์เหลือง `{{[รอแทรกภาพ: ...]}}` ในเมลตรงขั้นตอนนั้น
- ข้อมูลที่ต้องพิมพ์ในหน้าจอ (ถ้าระบุในขั้นตอน): ช่องวันที่ของโปรแกรม Delphi/DevExpress ต้องเป็น `dd/mm/yyyy` ปี พ.ศ. มี `/` เช่น `01/11/2569` — เขียนรูปแบบนี้ในขั้นตอนของเมล

**3B. แหล่งภาพ** — เฉพาะภาพที่ผู้ใช้เตรียมให้: โฟลเดอร์ที่ให้ / ไฟล์แนบ Redmine (ผ่าน API) / Screenshots (Win+Shift+S → หยิบภาพล่าสุดจากโฟลเดอร์ Screenshots) ถ้ายังไม่มี → คง placeholder ไว้ ห้ามสร้าง/จำลองภาพเอง

**3C. ปิดข้อมูลส่วนบุคคล (PDPA) — บังคับทุกภาพ ทุกแหล่ง**
- (1) เปิดภาพดูด้วย Read (2) ระบุพิกัดทุกจุดที่เป็นข้อมูลส่วนบุคคล/ส่วนที่ไม่เกี่ยวข้อง (3) ครอป+เบลอด้วย `scripts/blur_images.py spec.json` (pixelate+gaussian ถอดกลับไม่ได้; `black` สำหรับเลขที่ต้องปิดแน่นอน; พิกัด blur/black อ้างอิงภาพต้นฉบับ ก่อนครอป) (4) **เปิดภาพผลลัพธ์ดูซ้ำ** ก่อนใช้ ถ้ายังอ่านข้อมูลได้ให้แก้พิกัดแล้วทำใหม่
- ไม่มี OCR/ตรวจจับอัตโนมัติ — การตัดสินว่าจุดไหนอ่อนไหวเป็นหน้าที่ของ Claude+ผู้ตรวจ ผู้ใช้ควรเปิดดูภาพก่อนส่งทุกครั้ง
- **ตัวกันในโค้ด:** `blur_images.py` บันทึก `.pdpa_processed.json` (sha256 ของภาพผลลัพธ์) และ `create_draft.py` **ปฏิเสธภาพที่ไม่ผ่านสคริปต์นี้** (ภาพ screenshot ดิบแนบเมลไม่ได้) — มี `--allow-unmasked-image` แต่ห้ามใช้กับ screenshot ดิบ
- ขนาด: ย่อกว้างไม่เกิน 1000px (`max_width`) ใน HTML ใช้ `width` ตาม `html_style.image_width_median` ของ profile (หรือ 640 ถ้าภาพมีตัวหนังสือเล็ก)

## Step 4 — สร้างเนื้อหา → HTML → Draft
1. เขียน `content.json` (โครงใน `references/content_example.json` + คำอธิบายหัว `scripts/build_mail.py`) ตามสไตล์ใน profile: ลำดับหัวข้อ (เรียน/เรื่อง → เนื่องจากได้รับแจ้งตาม Redmine… → ช่องทาง Path UAT → วัตถุประสงค์ → เดิม/หลังแก้ไข → รายละเอียดการปรับปรุง → ตารางเคสทดสอบ → ขั้นตอนการ UAT พร้อมภาพ → ประโยคปิดท้าย → ลายเซ็น)
2. `python3 scripts/build_mail.py content.json --out-dir <dir>` → `body.html`, `body.txt`, `subject.txt` (สี/ตัวหนา/เส้นคั่น/ปิดท้าย/ลายเซ็นมาจาก profile; `{{...}}` = ไฮไลต์เหลือง)
3. (ถ้ามี speckit) ตรวจความครอบคลุม: `python3 scripts/speckit_extract.py <dir> --coverage content.json` — ต้องไม่มีหน้าจอ [ ] ที่ไม่ครอบคลุม และดูรายการ "ต้องถ่าย" ของภาพที่ยังเป็น placeholder (heuristic จับวลีในเครื่องหมายคำพูด/ชื่อปุ่ม จึงอาจเตือนเกินสำหรับปุ่มที่ไม่เปลี่ยนใน UR)
3b. ตรวจเนื้อหา body.txt ซ้ำเรื่อง PDPA (ค้นชื่อคน/เลขบัตร/เลขบัญชี/เบอร์โทร) ก่อนสร้าง Draft
4. `python3 scripts/create_draft.py [--update <draft_id> ถ้าแก้ draft เดิม] --subject-file <dir>/subject.txt --html <dir>/body.html --text <dir>/body.txt --image NAME=path.png ...` (NAME ตรงกับ `cid:NAME` ใน HTML) → ได้ draft id (ไม่ส่ง, ไม่มีผู้รับ)
5. ตรวจ Draft ผ่าน `users.drafts.get` ว่า To/Cc ว่าง, label DRAFT, ภาพ inline ครบ

## Step 5 — รายงานผู้ใช้
สรุป: subject, ลิงก์ Gmail Drafts, ความครอบคลุมเทียบ speckit (หน้าจอไหนมีขั้นตอน/ภาพแล้ว หน้าจอไหนยังขาดภาพ), รายการจุดไฮไลต์เหลืองที่ต้องกรอก/แทรกภาพ (ระบุชัดว่าภาพไหน), สิ่งที่ต้องยืนยันก่อนส่ง (Path UAT/โปรแกรมที่ deploy, ขอบเขตทดสอบ, ข้อมูลทดสอบบน UAT), ภาพที่ผู้ใช้ให้มาและเบลอจุดไหนไปบ้าง (ถ้ามี)

## ไฟล์ใน skill
- `scripts/common.py` — config dir, ค้น token, Gmail service
- `scripts/check_env.py` — เช็ค lib/token/profile
- `scripts/auth_gmail.py` — ขอ OAuth token (ยังไม่ได้ทดสอบบนเครื่องต้นทาง)
- `scripts/learn_style.py` — เรียนรู้รูปแบบจาก Sent → `profile.json`
- `scripts/blur_images.py` — ครอป/เบลอ/ทึบ ภาพ (PDPA)
- `scripts/speckit_extract.py` — อ่าน speckit (req/spec/tasks) → รายงานหน้าจอที่ต้องทดสอบ / `--skeleton` content ตั้งต้น / `--coverage` เทียบกับเมลที่ร่าง
- `scripts/build_mail.py` — content.json → body.html/body.txt/subject.txt ตามสไตล์ profile
- `scripts/create_draft.py` — สร้าง Draft (multipart/related, ภาพ inline cid)
- `references/profile_schema.md`, `references/content_example.json`

## ลำดับงานร่วมกับ Spec Kit
specify → clarify → plan → tasks → implement → converge → **/redmine-draft-mail-uat** (แจ้ง UAT) — หลัง converge ที่ tasks.md ปิดงานโค้ดครบ ใช้ skill นี้ให้เมลตรงกับ spec/REQ; ถ้า REQ/spec เปลี่ยน ให้รัน `--coverage` ซ้ำก่อนส่ง

## หมายเหตุ
- Gmail quota: `learn_style.py` ดึง header ก่อนแล้วดึงเนื้อหาเต็มเฉพาะ N ฉบับล่าสุด พร้อม backoff — เมลที่มีภาพขนาดใหญ่ทำให้ quota หมดเร็ว ถ้าโดน 403 rateLimit ให้รอแล้วรันซ้ำ
