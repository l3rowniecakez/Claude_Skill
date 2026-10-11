---
installer: create-shortcut
name: github-learn
description: 'อ่าน source code ของ repo ใดๆ จาก GitHub แบบ remote (ไม่ clone ลงเครื่อง) ผ่าน `gh api` + raw.githubusercontent.com โดยรับ owner/repo ตรงๆ จากผู้ใช้. Use when user says "/github-learn" หรือต้องการอ่าน/ศึกษา source code repo บน GitHub โดยไม่ต้องการ clone ลงเครื่อง.'
created_at: 2026-10-11T09:29:39+07:00
argument-hint: "[owner/repo หรือ URL] [sub path ถ้ามี]"
---

# /github-learn — อ่าน source code ของ repo ใดๆ จาก GitHub แบบไม่ clone

Sibling ของ [[github-clone]] เหมือนที่ [[git-learn]] เป็น sibling ของ
[[git-clone]] — ตัวนี้**ไม่ clone**อะไรลงเครื่องทั้งสิ้น ใช้ `gh api` (auth
ผ่าน `gh` ที่ login ไว้แล้ว — รองรับ private repo ที่มีสิทธิ์เข้าด้วย) สำหรับ
list โครงสร้างไฟล์ และ `raw.githubusercontent.com` (ผ่าน `gh auth token` เป็น
bearer token) สำหรับดึงเนื้อไฟล์ดิบ

เหมาะกับกรณีแค่อยากอ่าน/ทำความเข้าใจโค้ด ไม่ได้จะแก้ไขหรือ push อะไรกลับ (ถ้าต้อง
แก้ไขจริงต้องใช้ `/github-clone` แทน เพราะต้องมี `.git` ในเครื่องถึงจะ commit/push
ได้)

skill นี้เป็น read-only ต่อ repo บน GitHub — ไม่เคยเขียนอะไรกลับ

## Step 1 — ขอ owner/repo

ถาม repo จากผู้ใช้ก่อนเสมอ ห้ามเดา — รับได้ 2 แบบ:

1. **`owner/repo` ตรง ๆ** เช่น `anthropics/claude-code`
2. **URL เต็ม** เช่น `https://github.com/anthropics/claude-code` หรือ
   `git@github.com:anthropics/claude-code.git` — ตัดเอาเฉพาะ `owner/repo`
   ออกมาเองก่อนใช้

หา default branch ก่อน (ใช้ branch นี้ตลอดถ้า user ไม่ได้ระบุ branch อื่น):

```bash
gh repo view <owner>/<repo> --json defaultBranchRef --jq '.defaultBranchRef.name'
```

ถ้า error ว่าไม่พบ repo หรือไม่มีสิทธิ์เข้า → แจ้ง user ตรง ๆ ห้ามเดา owner อื่น

## Step 2 — สำรวจโครงสร้างไฟล์ก่อนอ่าน

```bash
gh api "repos/<owner>/<repo>/git/trees/<branch>?recursive=1" \
  --jq '.tree[] | select(.type=="blob") | .path'
```

- ถ้า response มี `truncated: true` (repo ใหญ่เกินเพดานของ GitHub API ในคำขอ
  เดียว) → ให้ไล่ดูทีละโฟลเดอร์ย่อยแทนด้วย contents API:
  ```bash
  gh api "repos/<owner>/<repo>/contents/<path>?ref=<branch>" \
    --jq '.[] | "\(.type)\t\(.path)"'
  ```
  (path ว่าง = root ของ repo) อย่าพยายาม recursive ทั้ง repo ทีเดียวถ้าชนเพดานแล้ว
- ใช้ contents API ข้างบนเพื่อดูทีละชั้นเวลาต้องการยืนยันด้วยตาหรือ path ลึกมากได้
  เช่นกัน

## Step 3 — อ่านไฟล์ที่ต้องการ

```bash
curl -sL -H "Authorization: token $(gh auth token)" \
  "https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<file path เต็ม>"
```

- ได้เนื้อไฟล์ดิบกลับมาตรง ๆ เป็น text — ถ้าไฟล์เป็น binary (รูปภาพ, compiled
  asset ฯลฯ) เนื้อหาที่ได้จะอ่านไม่ขึ้น ให้เช็คก่อนว่ามี NUL byte หรือ non-utf8
  เยอะผิดปกติไหม ถ้าใช่ให้ข้ามไฟล์นั้นไปเลย ไม่ต้องพยายาม decode เอง
- HTTP 404 → ไฟล์ path นั้นไม่มีจริงบน branch ที่ระบุ (เช็ค path จาก Step 2 อีกที)
- ไฟล์ใหญ่มาก (หลาย MB) → อ่านได้ตามปกติผ่าน raw endpoint (ไม่มีเพดาน ~1MB แบบ
  contents API ที่ส่ง base64) แต่ถ้าใหญ่เกินจำเป็นจริง ๆ ให้พิจารณาอ่านเฉพาะส่วนที่
  ต้องการแทนทั้งไฟล์
- อ่านทีละไฟล์ตามที่ต้องการเข้าใจ — skill นี้ไม่ได้ทำให้ grep ข้ามทั้ง repo ได้ใน
  ทีเดียวเหมือนมี local clone ต้องไล่เปิดเองทีละไฟล์ตามผลลัพธ์ Step 2

## ข้อจำกัดที่ต้องบอกผู้ใช้ล่วงหน้า (ถ้าเกี่ยวข้อง)

- **แก้ไข/commit/push ไม่ได้จาก skill นี้** — เป็น read-only เพียว ถ้าผู้ใช้บอกว่า
  จะแก้โค้ดหลังอ่านเสร็จ ให้แนะนำ `/github-clone` แทนตั้งแต่ต้น
- **ไม่มี local grep ข้ามทั้ง repo ในทีเดียว** — ถ้าผู้ใช้ต้องการค้นหา keyword ข้าม
  หลายไฟล์/ทั้ง repo เป็นจำนวนมาก การไล่ `tree` แล้วอ่านทีละไฟล์ผ่าน API อาจช้ากว่า
  clone จริงมาก ให้แจ้ง trade-off นี้และเสนอ `/github-clone` เป็นทางเลือกถ้างาน
  ลักษณะนี้
- GitHub มี API rate limit ต่อ token — ถ้าเจอ error `403` พร้อม
  `X-RateLimit-Remaining: 0` ให้แจ้ง user ตรง ๆ ว่าชน rate limit ต้องรอ reset
  (ไม่ต้องเดาวิธี bypass)
