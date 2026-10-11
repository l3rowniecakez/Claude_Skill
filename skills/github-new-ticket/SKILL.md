---
name: github-new-ticket
description: เปิด Issue ใหม่บน GitHub (title/body เท่านั้น ไม่มี code) ผ่าน `gh issue create` โดยถามครบ 2 อย่างก่อนเสมอ (owner/repo, เลข Ref RM ถ้ามี) แล้วดึงรายละเอียดจาก Redmine มาช่วยร่าง title/body พร้อมสรุปให้ confirm ก่อนสร้างจริง และข้อความ issue ต้องปิดท้ายด้วย #ai-work เสมอ. Use when user says "/github-new-ticket" หรือต้องการเปิด issue ใหม่บน GitHub.
installer: create-shortcut
created_at: 2026-10-11T09:29:39+07:00
argument-hint: "[owner/repo] [rm-ref ถ้ามี]"
---

# /github-new-ticket — เปิด Issue ใหม่บน GitHub (ไม่มี code)

Sibling ของ [[git-new-ticket]] (GitBlit) แต่สำหรับ GitHub แทน — งานของ skill นี้คือ
เปิด **issue record ใหม่** (title/body เท่านั้น) บน GitHub ผ่าน `gh issue create`
ซึ่งต่างจาก GitBlit ตรงที่ **ไม่ต้องขับ curl + Wicket AJAX hack เอง** (ไม่มี form
login, ไม่มี double-percent-encode, ไม่ต้อง parse wicket:interface) เพราะ `gh`
CLI login ไว้แล้วและมี native command ให้ใช้ตรง ๆ — คนละเรื่องกับการ push code เข้า
branch `issue/<N>` (ดู [[github-new-branch]] / [[github-commit-push]]) ซึ่งใช้ได้
เฉพาะ issue ที่มีอยู่แล้วเท่านั้น

**กฎเหล็ก**: ห้าม submit issue จริงจนกว่าจะถามครบ + โชว์สรุปให้ user confirm
ก่อนเสมอ แม้ข้อมูลจะมาครบใน `$ARGUMENTS` ตั้งแต่แรกก็ตาม
([[feedback_never_auto_commit_wait_for_explicit_instruction]] — logic เดียวกับ
push code: การเรียก skill ไม่เท่ากับอนุมัติให้ยิงจริงทันที)

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
gh auth status
```

ถ้ายังไม่ login/token หมดอายุ → แจ้ง user ให้รัน `gh auth login` เอง ห้ามเดา
credential หรือพยายาม auth แทน

---

## Step 1 — ถามข้อมูลให้ครบ

ถ้ามาใน `$ARGUMENTS` แล้วครบก็ใช้เลย ข้อไหนขาดให้ถามเพิ่ม:

1. **owner/repo** — รับได้ 2 แบบ: `owner/repo` ตรง ๆ หรือ URL เต็ม (ตัดเอาเฉพาะ
   `owner/repo` ออกมาเอง) ตรวจสอบก่อนว่า user มีสิทธิ์เปิด issue บน repo นี้จริง:
   ```bash
   gh repo view "<owner>/<repo>" --json nameWithOwner,hasIssuesEnabled
   ```
   ถ้า `hasIssuesEnabled: false` → แจ้ง user ว่า repo นี้ปิด issue tracker ไว้
   เปิด issue ไม่ได้ ห้ามพยายามเปิดต่อ
2. **Ref RM** ที่ issue นี้เกี่ยวข้อง (เช่น `12345`) — **ไม่บังคับ** ต่างจาก
   [[git-new-ticket]] เพราะ GitHub issue ไม่จำเป็นต้องผูกกับ Redmine เสมอไป ถ้า
   user ไม่มี RM ให้ข้ามไป Step 2 แล้วถาม title/body จาก user ตรง ๆ แทน

---

## Step 2 — ดึงรายละเอียดจาก Redmine มาช่วยตั้ง title/body (ถ้ามี Ref RM)

ใช้ [[reference_redmine_api_key]] ดึง subject ของ RM ที่ได้จาก Step 1 มาช่วยร่าง
เนื้อหา issue (ไม่บังคับต้องสำเร็จ — ถ้า fetch ไม่ได้ หรือ user ไม่มี RM ตั้งแต่
แรก ให้ถาม title/body จาก user แทน):

```bash
curl -s -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/issues/<RM>.json"
```

ร่างค่าที่จะใช้สร้าง issue:

- **title**: `RM #<RM>: <subject จาก Redmine>` (ถ้าดึง subject ไม่ได้/ไม่มี RM
  ให้ถาม user ว่าจะตั้ง title เองว่าอะไร)
- **body**: สรุปสั้น ๆ จาก Redmine (หรือที่ user ให้มา) ต่อท้ายด้วย `#ai-work`
  เสมอ — เช็คทุกครั้งว่ามี tag นี้ต่อท้ายจริง อย่าเชื่อว่าใส่แล้ว
  ([[feedback_tag_ai_work_comments]] — จุดที่เคยพลาดซ้ำมาแล้วในบริบทอื่น)
- **label** — ตรวจจาก field `tracker.name` ใน JSON ที่ดึงมาจาก Redmine (ไม่ใช่
  เดาจาก subject เฉย ๆ) แล้วเทียบกับ label ที่**มีอยู่จริง**บน repo นี้เท่านั้น:
  ```bash
  gh label list --repo "<owner>/<repo>" --json name --jq '.[].name'
  ```
  - ถ้า `tracker.name` เป็น **Bug** และ repo มี label ชื่อ `bug` อยู่แล้ว → ใส่
    label `bug`
  - กรณีอื่น หรือถ้า label ที่อยากใส่ยังไม่มีอยู่จริงบน repo → **ไม่ใส่ label**
    (ห้ามสร้าง label ใหม่เองโดยไม่ถาม) แจ้ง user เฉย ๆ ว่าไม่มี label ที่ตรงกัน
  - ถ้าดึง tracker จาก Redmine ไม่ได้ (fetch fail) หรือไม่มี RM ให้ถาม user ว่า
    อยากใส่ label อะไรแทนที่จะเดา

---

## Step 3 — สรุปให้ confirm ก่อนสร้างจริง

**ต้องรอให้ข้อมูลครบทุกฟิลด์ก่อน** (title, body พร้อม `#ai-work`, label ถ้ามี)
แล้วค่อยสรุปเป็นก้อนเดียวให้ user confirm ทีเดียว **ห้ามสรุปทีละส่วนหรือแยกถาม
เป็นหลายรอบ** และห้ามข้ามขั้นนี้ไม่ว่ากรณีใด แม้ `$ARGUMENTS` จะมาครบตั้งแต่แรก
ก็ตาม:

```
สรุปก่อนเปิด Issue บน GitHub
=======================================
Repo           : <owner/repo>
Ref RM         : #<RM> (ถ้ามี)
Title          : <title>
Body           : <body พร้อม #ai-work>
Label          : <label ถ้ามี / ไม่มี>
=======================================
```

ใช้ `AskUserQuestion` ถาม **Confirm สร้าง issue / ยกเลิก** ในขั้นตอนเดียวหลังจาก
ที่ข้อมูลทุกฟิลด์ครบแล้วเท่านั้น

---

## Step 4 — ลงมือสร้าง issue จริงด้วย `gh issue create`

หลัง confirm แล้วเท่านั้น:

```bash
gh issue create --repo "<owner/repo>" \
  --title "<title>" \
  --body "<body พร้อม #ai-work>" \
  $( [ -n "<label>" ] && printf -- '--label %s' "<label>" )
```

- `gh issue create` คืน URL ของ issue ใหม่ตรง ๆ ทาง stdout เมื่อสำเร็จ (ไม่ต้อง
  parse response/redirect เหมือน GitBlit)
- ถ้า fail (เช่น ไม่มีสิทธิ์เปิด issue, label ไม่มีจริง, repo ปิด issues) ให้
  รายงาน error ตรง ๆ กับ user ห้ามลองซ้ำเดา ๆ เอง

---

## Step 5 — รายงานผล

หลังสร้างสำเร็จ สรุปให้ user:

- เลข issue ใหม่ + URL เต็ม (จาก output ของ `gh issue create`)
- Ref RM ที่ผูกไว้ (ถ้ามี)
- เตือนว่านี่เป็นแค่ issue record (title/body) ยังไม่มี code ผูก — ถ้าจะเริ่มแก้
  โค้ดสำหรับ issue นี้ ให้ใช้ [[github-new-branch]] ต่อ (ตั้งชื่อ branch
  `issue/<เลขใหม่>`) แล้ว [[github-commit-push]] / [[github-merge-master]] ตาม
  ลำดับปกติ

ถ้า submit fail ให้รายงาน error ตรง ๆ กับ user พร้อมข้อความ error ที่ได้ ห้าม
ลองซ้ำเดา ๆ เอง

---

## Notes

- Skill นี้จบงานที่เปิด issue เท่านั้น — ไม่สร้าง branch, ไม่ push code, ไม่ log
  time กลับ Redmine อัตโนมัติ (ใช้ `/redmine-logtime` แยกถ้าต้องการ)
- ไม่ auth ผ่าน username/password แบบ GitBlit — ใช้ `gh` CLI session ที่ login
  ไว้แล้วเท่านั้น ถ้า auth หมดอายุให้แจ้ง user ไปรัน `gh auth login` เอง

---

ARGUMENTS: $ARGUMENTS
