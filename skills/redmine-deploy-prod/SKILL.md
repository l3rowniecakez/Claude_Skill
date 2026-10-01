---
installer: create-shortcut
name: redmine-deploy-prod
description: 'Create a new Redmine RM notifying IT Deploy team of App details to prepare a Production deploy, OR add another program + Redmine Ref to an existing Deploy Production RM — always asks first which of the two this call is. New-RM path copies its Master Pattern exactly (Assignee always IT Application Admin, Environment always Production/PROD; Due Date is the actual scheduled Deploy date, not the RM creation date), asking which RM number it should be a subtask of, then asking each unknown template variable one at a time (App name, REPOSITORY, COMMIT_HASH, PROGRAM_PATH, DPR_FILE, RELEASE_VERSION, deploy date, DB scripts, checklist sheet, Redmine refs, contact person). New-RM path also opens two fixed subtasks once (assigned to whoever called the skill, not IT Application Admin) — "01-Email ขออนุมัตินำขึ้น PROD" and "02-แนบผล UAT" — never repeated on later calls. Existing-RM path asks the existing RMs number, then checks if the named App is already listed in Section 1: if it IS, updates ONLY that program's COMMIT_HASH, RELEASE_VERSION, and (re-derived) APPROVED_TAG in both the RM description AND the linked Checklist Sheet's "Full Commit Hash"/"Approved Tag" columns (REPOSITORY/PROGRAM_PATH/DPR_FILE untouched); if it's a genuinely new App, appends a new numbered program block to Section 1 and new bullet(s) to Section 4 Redmine Ref. Never re-creates the two approval subtasks on this path. Always ends by giving the RM link to check. Use when user says "/redmine-deploy-prod" or wants to แจ้ง Deploy Production ให้ IT Deploy.'
created_at: 2026-09-28T00:00:00+07:00
argument-hint: "[parent-redmine-issue-number]"
---

# /redmine-deploy-prod — Notify IT Deploy for a Production Deploy

Creates a new Redmine RM that asks IT Deploy to run a Production deploy of an App — or,
if a Deploy Production RM for this round already exists, adds another program to it
instead of opening a duplicate. Either way it's built on its **Master Pattern** **exactly**, including its two fixed
fields (new-RM path only — an existing RM already has these set):

- **Assignee**: always `IT Application Admin` (`assigned_to_id` = `280`)
- **Environment**: always **Production** — custom field id `13` = `"Production"`, and the
  `ENVIRONMENT` table row is always `PROD`

Neither of these is ever asked or varied — they are fixed parts of the pattern, not
user-supplied variables. `Due Date` is **not** fixed — it's set to the actual scheduled
**Deploy date** the user gives in Step 4, not the date the RM happens to be created. This
skill only creates the issue — it never runs the actual deploy, never touches code, and
never marks any checklist row "Ready" itself (those get updated later, by hand, as the
real deploy actually gets checked off).

**Template editing rule (hard rule):** edit ONLY the text wrapped in `<...>` — replace the whole token, including the `<` and `>` characters, with the real value. Everything outside `<...>` (wording, headings, emoji, tables, links, fixed values such as `ENVIRONMENT`, warnings) must stay identical to the Master Pattern, character for character. Never add, delete, reword or reformat it unless this skill explicitly says so (e.g. the program count when there are multiple programs).

Redmine access: see the `reference-redmine-api-key` memory (`X-Redmine-API-Key` header,
`https://redmine.ochi.link`).

**Never create a new Redmine issue without the confirmation in Step 8 — hard rule, no
exceptions.** Never use this skill's create call (or any ad-hoc `POST /issues.json`) to
"test" API connectivity or curl syntax — that endpoint always creates a real, permanent
issue with no undo. Only create an issue here when the user has explicitly confirmed the
previewed content in Step 8 (new-RM path) or Step B4 (existing-RM path).

---

## Step 0 — New RM, or add to an existing one?

**Always ask this first, every time the skill is invoked**:

> สร้าง RM Deploy Production ใหม่ หรือมี RM Deploy Production นี้อยู่แล้ว (ต้องการเพิ่มโปรแกรมเข้าไป)?

- **สร้างใหม่ (new RM)** → continue at **Step 1** below (Path A) — **only in this branch**
  do you ask which RM to open it as a subtask of.
- **มีอยู่แล้ว (existing RM)** → ask for that RM's number, then skip straight to
  **Path B** (after Step 10) — don't run Steps 1–10, this is a different flow (update, not
  create). **Never ask the "subtask of which RM" question here** — an existing RM's
  parent is already whatever it is; this path only adds to it, it doesn't re-parent it.

---

# Path A — Create a new RM

## Step 1 — Ask which RM this is a subtask of (new-RM path only)

Only reached when Step 0 was answered "สร้างใหม่". Every new RM this skill creates must be
a subtask of an existing parent RM. **Always ask this explicitly** — "ต้องการให้เป็น subtask
ของ RM เลขอะไร?" — unless the user already gave the parent RM number as `$ARGUMENTS` in
this same invocation (that counts as having answered).

Fetch the parent RM to learn its project:

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<parent_id>.json"
```

Take `project.id` as `<project_id>` for the new RM (new RM lives in the **same project**
as its parent).

---

## Step 2 — Resolve the "Deployment" tracker for that project

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/projects/<project_id>.json?include=trackers"
```

Find the tracker named `Deployment` and take its `id` as `<tracker_id>`. If that project
has no `Deployment` tracker, tell the user and ask which tracker to use instead — don't
silently substitute one.

The assignee is **always** `IT Application Admin`, `assigned_to_id` = `280` (fixed, same
as its master pattern) — never ask the user for this, never vary it.

---

## Step 3 — The Master Pattern

**Subject:**
```
Deploy Production (<App>)
```

**Description** (Markdown/textile — Redmine renders this as-is):
```
เรียน IT Deploy

<div style="background-color:#fff3cd;border-left:4px solid #f7982c;padding-left:12px;padding-top:8px;padding-bottom:8px">
<strong>📌 ขอแจ้ง Deploy Production ในวันที่ <วันที่ Deploy> เวลา 20.00 - 24.00 น.</strong>
</div>

โดยมีรายละเอียดดังนี้

---

### 1️⃣ 📋 รายละเอียดโปรแกรม

| 1. | โปรแกรม <App> |
| --- | --- |
| **PROGRAM_NAME** | `<App>.exe` |
| **REPOSITORY** | `<REPOSITORY>` |
| **COMMIT_HASH** | `<COMMIT_HASH>` |
| **PROGRAM_PATH** | `<PROGRAM_PATH>` |
| **DPR_FILE** | `<DPR_FILE>` |
| **ENVIRONMENT** | `PROD` |
| **RELEASE_VERSION** | `<RELEASE_VERSION>` |
| **APPROVED_TAG** | `<APPROVED_TAG>` |

---

### 2️⃣ 🗄️ รายละเอียด DB Script

<DB script section — see Step 5>

---

### 3️⃣ 📝 Checklist

- [Sheet Checklist](<URL Google Sheet checklist>)

---

### 4️⃣ 🔗 Redmine Ref.

<Redmine Ref bullet list — see Step 6>

---

| No. | Description | Include | Ready to Deploy |
| --- | --- | --- | --- |
| 1. | ตรวจสอบ Path & Version RC & Revision | ✅ | ❌ |
| 2. | แนบ Script Database | <✅ or N/A> | ❌ |
| 3. | แนบ Checklist | ✅ | ❌ |
| 4. | แนบผล UAT | ✅ | ❌ |
| 5. | แนบไฟล์อนุมัติ | ✅ | ❌ |

---

| พร้อมขึ้น Production | ❌❌❌ |
| --- | --- |

---

📍 กรณีติดปัญหาติดต่อ **<ชื่อคนเปิด RM>**

ขอบคุณครับ/ค่ะ

#ai-work
```

`Ready to Deploy` and the bottom `พร้อมขึ้น Production` row **always start unchecked**
(`❌`) — this RM is freshly opened, nothing has been verified yet. Never mark any of
those `✅`/`⏳` at creation time, even if the user says everything is already done —
those get updated later by hand as the real deploy actually gets checked off.

---

## Step 4 — Ask each program-detail variable, one at a time

Ask **one question at a time** (don't dump them all as one form) — skip a question only
if the user already supplied that value unprompted earlier in the conversation:

1. **App name** (e.g. `OGL_Operation`, `OGL_Sale`) — used in the subject, the table
   header, and as the base of `PROGRAM_NAME`. Confirm the derived `PROGRAM_NAME`
   (`<App>.exe`) with the user rather than asking it fully separately.
2. **REPOSITORY** (e.g. `delphi/groupwork-system-2016.git`)
3. **COMMIT_HASH** (the commit being deployed)
4. **PROGRAM_PATH** — the Sub Folder path (e.g.
   `GroupLifeInsuranceSystem_Operation/trunk`). If the user doesn't know it offhand,
   suggest using `/git-clone-grouplife` or `/git-clone-grouplife-update` to look it up
   from the tracking sheet's "Sub Folder" column for this App.
5. **DPR_FILE** (e.g. `OGL_Operation.dpr`) — usually `<App>.dpr`; confirm rather than ask
   fully separately if it follows that pattern.
6. **RELEASE_VERSION** — the RC number (e.g. `2.198.2-RC`). This normally comes from the
   corresponding "ตัด RC" ticket created earlier via `/redmine-deploy-uat` — ask the user
   for that RC number (or that ticket's number so you can look it up on Redmine if they
   don't have the RC number handy).
7. **Deploy date** (e.g. `23/09/2026`) — the date this Production deploy is scheduled for.
   The time window (`20.00 - 24.00 น.`) is fixed per the pattern; only ask if the user
   says this particular deploy uses a different window. This date is used **both** for
   the `<วันที่ Deploy>` slot in the description **and** as the RM's `due_date` — convert
   it to `YYYY-MM-DD` for the `due_date` field (e.g. `23/09/2026` → `2026-09-23`), don't
   use today's date.

Once `PROGRAM_PATH`, `App`, and `RELEASE_VERSION` are known, **derive** `APPROVED_TAG` as:
```
<PROGRAM_PATH>/<App>/<RELEASE_VERSION>
```
e.g. `GroupLifeInsuranceSystem_Operation/trunk` + `OGL_Operation` + `2.198.2-RC` →
`GroupLifeInsuranceSystem_Operation/trunk/OGL_Operation/2.198.2-RC`. Show the derived
value to the user to confirm rather than asking it as a fully separate question.

8. **Deploy Path (ปลายทาง)** — the production deploy destination folder, needed for the
   Checklist Sheet's "Deploy Path (ปลายทาง)" column (Step 6). Past RMs across different
   Apps (`OGL_Operation`, `OGL_Premium`, `OGL_Sale`) have all used the same shared path
   `\\10.40.99.40\GroupLife_System\Operation_Program` — offer that as the likely default
   but confirm with the user rather than assuming it silently, since a future App could
   genuinely differ. Don't skip this question even though it's not part of the RM
   description template — it's only written into the Checklist Sheet, not the RM itself.

---

## Step 5 — Ask about DB Scripts

Ask whether this deploy round includes any DB scripts.

- **No DB script** → replace the whole Section 2 body with:
  ```
  **ไม่มี DB Script สำหรับรอบนี้** (deploy เฉพาะโค้ดโปรแกรม)
  ```
  and set the "แนบ Script Database" row's `Include` column to `N/A`.

- **Has DB script(s)** → keep Section 2's body as:
  ```
  รายละเอียด script ทั้งหมด (รายชื่อ/ประเภท/สถานะ) ดูที่หัวข้อ **"2.Run Script"** ใน Sheet Checklist (หัวข้อถัดไป) — ไฟล์ `.sql` จริงแนบไว้ท้าย ticket นี้

  ⚠️ **รันตามลำดับเลขที่กำกับไว้ในชื่อไฟล์/Sheet เสมอ** ห้ามสลับลำดับ
  ```
  and set that row's `Include` to `✅`. Ask the user for the actual `.sql` file path(s) to
  attach to the ticket, and list the script names/order in the Checklist Sheet's
  "2.Run Script" section (Step 6). To attach files to the Redmine issue, upload each one
  first to get an upload token, then reference the token(s) in the create call:
  ```bash
  curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/octet-stream" \
    --data-binary "@<path/to/script.sql>" \
    "https://redmine.ochi.link/uploads.json?filename=<script.sql>"
  ```
  Capture the returned `upload.token`, then include it in the issue create call (Step 9)
  as `"uploads":[{"token":"<token>","filename":"<script.sql>","content_type":"application/sql"}]`
  — one entry per file.

---

## Step 6 — Checklist Sheet and Redmine Ref

**Checklist Sheet**: ask if a Checklist Google Sheet already exists for this deploy
(paste its URL) — if not, offer to create one:
1. Find (or create) the subfolder named `Deploy Production <current year, ค.ศ.>` (e.g.
   `Deploy Production 2026`) inside
   [this Drive folder](https://drive.google.com/drive/folders/1vL03-7XfAFwqTafKXJUNIZ_K9LKOR-o0)
   using the Google Drive tools available in this session.
2. Copy the [master template Sheet](https://docs.google.com/spreadsheets/d/1QDBLj2hK0DqYHEMk3GezV83Gl0JeCPIRsAYBO3owoUI)
   into that subfolder. **Title it exactly per the master's own filename convention**
   (the master template's title *is* the pattern, read it literally rather than
   inventing a different scheme):
   ```
   <วันที่สร้างไฟล์ YYYYMMDD>_Deploy_<เลข RM ที่ครอบคลุม e.g. #12345, #12346>
   ```
   `<วันที่สร้างไฟล์>` is **today's actual date** (when this Sheet is created), not the
   scheduled Deploy date from Step 4. `<เลข RM ที่ครอบคลุม>` is the covered Defect/UR RM
   number(s) — the same ones that go into Section 4 Redmine Ref (Step 6 below) — **not**
   the Deploy Production RM's own number (that doesn't exist yet at this point in the
   flow; see the `ITD` cell note below). A title like `OGL_SALE 2026-09-30` (App name +
   deploy date) is **wrong** — don't invent a variant, copy the master's own title
   pattern verbatim with the placeholders substituted.
3. **The copy only duplicates structure — every `<...>` placeholder in it is still
   literal placeholder text until you fill it in.** Copying the file is not enough; you
   must write the real values into these cells before treating the Sheet as done. The
   `mcp__claude_ai_Google_Drive__*` tools only cover file metadata (title/parentId/copy)
   and **cannot write cell content** — use the Sheets API write path from the
   `reference-claude-google-access-oauth` memory instead (`~/.config/claude-google-access/`
   OAuth token; `sys.path.insert(..., "~/.config/claude-google-access")`,
   `from read_sheet import get_service`, then
   `service.spreadsheets().values().batchUpdate(...)` with `valueInputOption="USER_ENTERED"`
   — same path Step B2s below uses). **Check that memory before ever telling the user
   Sheet cell-writes aren't possible** — the Drive tools' lack of a cell-write call does
   not mean this skill has no way to write cells.
   In the `Deployment CheckList` sheet/tab, on the header block (around rows 3-6) and the
   `1.Deploy Program` table (around row 22-23, one row per program in Section 1, same
   order):
   - `Name` cell → the covered Defect/UR RM number(s), e.g. `#12345`
   - `Jira / KPI` cell → the matching Redmine URL(s), e.g.
     `https://redmine.ochi.link/issues/12345`
   - `Program` cell → `<App>`
   - `ITD` cell → `Deployment #<new_rm_id>` — **this Deploy Production RM's own number
     doesn't exist yet at this point** (Step 9 hasn't run). Leave a clear placeholder here
     for now (e.g. `Deployment #<รอสร้าง RM Deploy Production>`) and **come back and fill
     in the real `Deployment #<new_rm_id>` right after Step 9 succeeds** — don't forget
     this follow-up write, it's easy to leave stale since it happens out of sequence.
   - Program table row → `Program Name` = `<App>`, `Program Path` = `<PROGRAM_PATH>`,
     `Full Commit Hash` = `<COMMIT_HASH>` (full, untruncated), `Approved Tag` =
     `<APPROVED_TAG>`, `Deploy Path (ปลายทาง)` = the value from Step 4's new question 8
     (don't leave this column as the placeholder — it's a real required field, not
     optional decoration)
   Read the actual current cell values first (`values().get`) to find the exact row/column
   for this deploy's copy before writing — don't assume the row numbers above never shift
   between master-template revisions.
4. Confirm the new Sheet's URL and the values just written with the user before using it
   as the `[Sheet Checklist]` link, and fill its "2.Run Script" section with the DB script
   list from Step 5 if there are any.

**Redmine Ref.**: ask the user for the related Defect/UR RM number(s) this deploy covers
(fetch each one's subject via `GET /issues/<id>.json` to build the
`[Defect #<id> <subject>](https://redmine.ochi.link/issues/<id>)` links), plus
specifically the number of the corresponding **Deploy UAT ("ตัด RC")** RM created earlier
via `/redmine-deploy-uat`, linked as its own bullet (e.g.
`[Deployment #12345 (ตัด RC)](https://redmine.ochi.link/issues/12345)`).

---

## Step 7 — Contact person

Default `<ชื่อคนเปิด RM>` to the current Redmine user's display name:
```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/users/current.json"
```
Confirm this with the user rather than asking it as a fully open question — they may want
a different on-call contact for this particular deploy. Keep this response's `id` around
too — it's reused as the subtask assignee in **Step 9b**, no need to fetch it twice.

---

**Footer rule:** the description must end with exactly ONE footer — `ขอบคุณครับ/ค่ะ`, blank line, `#ai-work` (with the hyphen, never `#aiwork`). The template above already contains it, so never append another `ขอบคุณครับ`/`#ai-work` after filling in the template.

## Step 8 — Confirm before creating (hard gate)

Assemble the full subject + description from Steps 3–7 (`#ai-work` at the end — never
omit it), then post the **full, verbatim** final text as its own message — not a summary,
not a bullet-point recap — so the user can actually read and check every field before
anything is created:
- the exact final **subject** line,
- the exact final **description** (the whole filled-in template — Section 1 program
  table, Section 2 DB script wording, Section 3 Checklist Sheet link, Section 4 Redmine
  Ref list, the Include/Ready table, contact person — in a fenced code block so
  formatting/line breaks are visible as they'll actually post),
- and a short line underneath naming the parent RM, project, tracker, due date, and the
  attachment file list (if any `.sql` files from Step 5).

Then explicitly ask for confirmation (e.g. "ตรวจสอบข้อมูลด้านบน ถูกต้องให้สร้าง RM ได้เลยไหม?").
Do not proceed to Step 9 without an explicit yes — a prior "ok" earlier in the conversation
for a different RM, or for a different field, doesn't count. If the user asks for a
correction, apply it and show the **entire** updated text again before asking again.

---

## Step 9 — Create the RM

```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<parent_id>,"assigned_to_id":280,"due_date":"<YYYY-MM-DD, from the Deploy date in Step 4>","subject":"<subject>","description":"<description>","custom_fields":[{"id":13,"value":"Production"}],"uploads":[<upload tokens from Step 5, if any>]}}' \
  "https://redmine.ochi.link/issues.json"
```

If the response has an `errors` field or a non-2xx status, stop and show the raw error to
the user instead of silently retrying or guessing a fix. Capture the returned `id` as
`<new_rm_id>` — needed by Step 9b, and by Step 9c right below.

---

## Step 9c — Fill in the Checklist Sheet's `ITD` cell (new-RM path only, once)

Immediately after Step 9 succeeds, go back to the Checklist Sheet created in Step 6 and
replace its `ITD` cell placeholder with the real value now that `<new_rm_id>` exists:
```
Deployment #<new_rm_id>
```
Same Sheets API write path as Step 6 (the `reference-claude-google-access-oauth` OAuth
token — never the `mcp__claude_ai_Google_Drive__*` tools, they can't write cells). This is
the one cell in the Sheet that genuinely cannot be filled before the RM exists — don't
skip coming back for it once it does.

---

## Step 9b — Create the two approval subtasks (new-RM path only, once)

**Only on this Path A (new-RM) path, and only once per RM** — never on Path B (adding a
program to an existing RM; see the Path B intro). Immediately after Step 9 succeeds,
create exactly these two subtasks under `<new_rm_id>`, both assigned to **the person who
called this skill** — i.e. the current API user's `id` from Step 7, **not** `280`
(`IT Application Admin`):

```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<new_rm_id>,"assigned_to_id":<current_user_id>,"subject":"01-Email ขออนุมัตินำขึ้น PROD","custom_fields":[{"id":13,"value":"Production"}]}}' \
  "https://redmine.ochi.link/issues.json"

curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<new_rm_id>,"assigned_to_id":<current_user_id>,"subject":"02-แนบผล UAT","custom_fields":[{"id":13,"value":"Production"}]}}' \
  "https://redmine.ochi.link/issues.json"
```

Use the same `project_id`/`tracker_id` as the parent RM (Steps 1–2). **The `custom_fields`
Environment value is required on these subtasks too** — the `Deployment` tracker rejects
a create with `"Environment cannot be blank"` (422) if it's left off, even for a subtask
that's just an internal checklist item, not a real per-environment record. If either call
returns an `errors` field or a non-2xx status, show the raw error to the user — don't
silently retry or guess a fix. These two subject strings are fixed, exactly as shown —
don't ask the user to customize them.

---

## Step 10 — Report the result

**Always end by giving the user a clickable link to the new RM so they can open it and
check it themselves** — never just state the issue number in text. Post it as its own
line, e.g.:

```
เปิด RM ใหม่แล้ว: https://redmine.ochi.link/issues/<id>
```

Alongside the link, give its parent RM, the Checklist Sheet link, the two new subtask
links from Step 9b, and a one-line summary of what was filled in.

---

# Path B — Add to, or update a program on, an existing Deploy Production RM

Only reached when the user answered "มีอยู่แล้ว" in Step 0. This path never creates a new
issue, and **never creates the Step 9b approval subtasks again** — those are created
exactly once, at Path A's Step 9b, when the RM itself was first opened. This path only
edits the existing RM's description via `PUT`. It doesn't touch the existing RM's
subject, Assignee, Environment, Due Date, DB Script section, Checklist Sheet link, or the
bottom Include/Ready table — those stay exactly as they are.

Template editing rule applies here too: touch only the `<...>` values / the fields named below; everything else in the description stays byte-identical.

Two different situations land here, split at **Step B1b**:
- **The App is already listed** in Section 1 (e.g. a small fix got re-cut with a new
  commit before the actual deploy) — this only needs its `COMMIT_HASH`, `RELEASE_VERSION`,
  and `APPROVED_TAG` rows updated (**Step B2s**), nothing else.
- **The App isn't listed yet** — a genuinely new program joining this deploy round — gets
  a full new numbered block (**Step B2**) plus its own Redmine Ref bullet(s) (**Step B3**).

## Step B1 — Fetch the existing RM

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<existing_id>.json"
```

If it's not actually a `Deployment`-tracker "Deploy Production" RM (wrong tracker, or its
subject doesn't start with `Deploy Production`), stop and confirm with the user instead of
guessing — they may have given the wrong number.

Read its `description` and locate:
- **Section 1** (`### 1️⃣ 📋 รายละเอียดโปรแกรม`) — one or more program blocks, each its own
  small table starting with a row like `| 2. | โปรแกรม <App> |`, followed by that
  program's `PROGRAM_NAME`/`REPOSITORY`/`COMMIT_HASH`/etc. rows. Note the **App name (and
  `PROGRAM_NAME`) of every existing block** — needed for the Step B1b match check — and
  the **highest** existing number `N` — the new block you add (if it comes to that) uses
  `N + 1`.
- **Section 4** (`### 4️⃣ 🔗 Redmine Ref.`) — a bullet list, ending right before the `---`
  that leads into the Include/Ready table.

## Step B1b — Same App as an existing block, or a new program?

Ask which App this call is about (e.g. `OGL_Operation`) — needed either way. Then check
it against the App names/`PROGRAM_NAME`s found in Step B1:

- **Matches an existing block** — this is a **new commit for a program that's already
  listed** (e.g. a small fix re-cut before the actual deploy), not a new program. Skip
  straight to **Step B2s** below — do **not** run Step B2 or Step B3 for this App.
- **No match** (a genuinely new program for this deploy round) — continue at **Step B2**
  as before.

## Step B2s — Same-App path: update COMMIT_HASH, RELEASE_VERSION, APPROVED_TAG

Ask, one at a time:
1. **COMMIT_HASH** (e.g. `4bc1636fda7799ff6c960e8573381e5b98fc819f`) — the new commit.
2. **RELEASE_VERSION** (e.g. `2.198.3-RC`) — the new RC number this commit was cut under
   (same as Step 4/B2's question — normally comes from the corresponding `/redmine-deploy-uat`
   "ตัด RC" ticket).

**Don't** ask `REPOSITORY`, `PROGRAM_PATH`, or `DPR_FILE` again — those stay exactly as
already recorded in that program's existing block, unchanged. `PROGRAM_NAME` and
`ENVIRONMENT` obviously don't change either.

Re-derive `APPROVED_TAG` from that unchanged `PROGRAM_PATH`/`App` plus the **new**
`RELEASE_VERSION`, same formula as Step 4:
```
<PROGRAM_PATH>/<App>/<RELEASE_VERSION>
```
Show the derived value to the user to confirm rather than asking it as a separate
question.

**Also update the Checklist Sheet, not just the RM description.** The Checklist Sheet
linked in Section 3 has its own "Full Commit Hash" and "Approved Tag" columns per program
row — these must be kept in sync with the RM's `COMMIT_HASH`/`APPROVED_TAG` whenever this
step changes them, or the two silently drift apart:
1. Open the Checklist Sheet URL from Section 3.
2. Find the header row and the "Full Commit Hash" / "Approved Tag" columns (match the
   actual header wording in that sheet, which may differ slightly), and the row for this
   App/program (matched by its App/program name column).
3. Update just those two cells: "Full Commit Hash" ← the new (full, untruncated)
   `COMMIT_HASH`; "Approved Tag" ← the newly-derived `APPROVED_TAG`.
4. Use the Sheets write path from the `reference-claude-google-access-oauth` memory
   (`~/.config/claude-google-access/` OAuth token, `service.spreadsheets().values().update(...)`
   with `valueInputOption="USER_ENTERED"`) — the `mcp__claude_ai_Google_Drive__*` tools only
   cover file metadata and can't write individual cells.
5. Show the user the exact row/cells about to change (old → new) as part of the Step B4
   confirmation, before writing either the RM or the Sheet.

If the Checklist Sheet has no row for this App yet, or its columns don't match this
naming, stop and ask the user rather than guessing which row/column to touch.

In that program's existing block, replace **only** the `**COMMIT_HASH**`,
`**RELEASE_VERSION**`, and `**APPROVED_TAG**` row values with the new ones — every other
line in that block, every other program block, and every other section of the
description stays byte-for-byte identical.

Don't ask about DB scripts or Redmine Ref for this path by default — a same-program
commit bump doesn't imply a new script or a new Defect/UR reference. Only bring those up
if the user volunteers that this particular commit also needs one.

Skip Step B3 entirely and go straight to **Step B4** to confirm and apply the change.

## Step B2 — New-program path: ask each program-detail variable, one at a time

Same questions as **Step 4** in Path A (App name → confirm `PROGRAM_NAME`, `REPOSITORY`,
`COMMIT_HASH`, `PROGRAM_PATH`, `DPR_FILE`, `RELEASE_VERSION`), deriving `APPROVED_TAG` the
same way. `ENVIRONMENT` is still always `PROD` — don't ask it. Skip the "Deploy date"
question — that's already set on the existing RM and isn't repeated per program.

Build the new block using the next number `N + 1` from Step B1:
```
| <N+1>. | โปรแกรม <App> |
| --- | --- |
| **PROGRAM_NAME** | `<App>.exe` |
| **REPOSITORY** | `<REPOSITORY>` |
| **COMMIT_HASH** | `<COMMIT_HASH>` |
| **PROGRAM_PATH** | `<PROGRAM_PATH>` |
| **DPR_FILE** | `<DPR_FILE>` |
| **ENVIRONMENT** | `PROD` |
| **RELEASE_VERSION** | `<RELEASE_VERSION>` |
| **APPROVED_TAG** | `<APPROVED_TAG>` |
```
Insert this new table directly after the last existing program block in Section 1, before
that section's closing `---`.

Also ask whether this new program brings its own DB script(s). This path doesn't rewrite
Section 2's wording (it was written for the RM as a whole), but if there are new scripts
to attach, ask the user for the `.sql` file path(s) and attach them the same way as Path A
Step 5 (upload for a token, then `PUT` the token(s) in Step B4 the same way Step 9 does).
If Section 2 currently says "ไม่มี DB Script สำหรับรอบนี้" and this program *does* have
one, flag that mismatch to the user and ask how they want Section 2 reworded — don't
silently rewrite it yourself.

## Step B3 — Ask for the additional Redmine Ref(s)

Same as Path A's **Step 6** Redmine Ref part: ask for the related Defect/UR RM number(s)
this added program covers, fetch each subject to build
`[Defect #<id> <subject>](https://redmine.ochi.link/issues/<id>)`, and build the new
bullet line(s) to append at the end of Section 4's existing list (a "RM Deploy UAT Ref"
bullet for this program's own "ตัด RC" ticket too, if there is one).

## Step B4 — Confirm, then PUT the updated description (hard gate)

Post the **full, verbatim** text as its own message — not a summary — so the user can
actually read and check it before anything is sent:
- **Step B2s path (same App)**: the three changed rows — `**COMMIT_HASH**`,
  `**RELEASE_VERSION**`, `**APPROVED_TAG**` — old value and new value for each, clearly
  labeled, plus the full program block they belong to; and the Checklist Sheet row/cells
  ("Full Commit Hash", "Approved Tag") about to change, old → new.
- **Step B2/B3 path (new program)**: the new Section 1 program block (Step B2) exactly as
  it will be inserted, and the new Section 4 bullet(s) (Step B3) exactly as they will be
  appended.
- **Either way**: the **entire resulting description** (existing content plus this
  change, in a fenced code block) so the user sees the real final state, not just the
  diff.

Then explicitly ask for confirmation (e.g. "ตรวจสอบข้อมูลด้านบน ถูกต้องให้อัปเดต RM ได้เลยไหม?").
Do not proceed without an explicit yes — a prior "ok" earlier in the conversation doesn't
count. If the user asks for a correction, apply it and show the entire updated text again
before asking again. Then:
```bash
curl -s -X PUT -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"description":"<full updated description>","uploads":[<upload tokens, if any new .sql files>]}}' \
  "https://redmine.ochi.link/issues/<existing_id>.json"
```
If the response has an `errors` field or a non-2xx status, stop and show the raw error to
the user instead of silently retrying or guessing a fix.

## Step B5 — Report the result

Same as Path A's Step 10: **always give a clickable link** to the RM that was updated —
```
อัปเดต RM แล้ว: https://redmine.ochi.link/issues/<existing_id>
```
— plus a one-line summary: either "อัปเดต COMMIT_HASH/RELEASE_VERSION/APPROVED_TAG ของ
`<App>` เป็น `<new hash>` / `<new RC>`" (Step B2s path — plus a mention that the Checklist
Sheet's Full Commit Hash/Approved Tag were updated too, see Step B2s's Checklist Sheet
note) or the program and Redmine Ref bullet(s) just added (Step B2/B3 path).

---

## Notes

- This skill never logs time and never posts follow-up notes — it only creates or updates
  the one RM. Use `/redmine-logtime` separately if the user wants to log time on this.
- Never invent values for `REPOSITORY`, `COMMIT_HASH`, `PROGRAM_PATH`, `DPR_FILE`, or
  `RELEASE_VERSION` — always get them from the user (or, for `PROGRAM_PATH`, from the
  tracking sheet via `/git-clone-grouplife`), never guess from a similar-looking past RM.
- Never mark any checklist row (or `พร้อมขึ้น Production`) as done at creation time, and
  never touch that table at all on the Path B (existing-RM) path — those reflect real
  verification that hasn't happened yet.
- Companion skill: `/redmine-deploy-uat` opens the earlier "ตัด RC" RM that
  `RELEASE_VERSION`/`APPROVED_TAG` and "RM Deploy UAT Ref" bullets normally trace back to.

---

ARGUMENTS: $ARGUMENTS
