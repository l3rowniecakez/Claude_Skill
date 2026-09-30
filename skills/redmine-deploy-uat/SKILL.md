---
installer: create-shortcut
name: redmine-deploy-uat
description: 'Create a new Redmine RM notifying IT Deploy of App details to prepare cutting a version (ตัด RC) — copies its Master Pattern exactly (Assignee always IT Application Admin, Environment always UAT, Due Date always today), asking which RM number it should be a subtask of, then asking each unknown template variable one at a time (App name, REPOSITORY, COMMIT_HASH, PROGRAM_PATH, DPR_FILE). Use when user says "/redmine-deploy-uat" or wants to แจ้งตัด RC / แจ้งตัด version ให้ IT Deploy.'
created_at: 2026-09-28T00:00:00+07:00
argument-hint: "[parent-redmine-issue-number]"
---

# /redmine-deploy-uat — Notify IT Deploy to Cut a Version (ตัด RC)

Creates a new Redmine RM that asks IT Deploy to cut a version of an App for deployment, by
copying its **Master Pattern** **exactly**, including its two fixed
fields:

- **Assignee**: always `IT Application Admin` (`assigned_to_id` = `280`)
- **Environment**: always `UAT` (custom field id `13` = `"UAT"`, and the `<ENVIRONMENT>`
  slot in the subject is always `UAT`)
- **Due Date**: always **today** — the date the RM is created (`due_date`, `YYYY-MM-DD`)

None of these three is ever asked or varied — they are not user-supplied variables, they
are fixed parts of the pattern. This skill only creates the issue — it never touches code,
never runs the actual deploy, and never fills in `RELEASE_VERSION`/`APPROVED_TAG` (those
are filled in later by the release team once they reply, same as in the master pattern
and its precedents).

Redmine access: see the `reference-redmine-api-key` memory (`X-Redmine-API-Key` header,
`https://redmine.ochi.link`).

**Never create a new Redmine issue without the confirmation in Step 5 — hard rule, no
exceptions.** Never use this skill's create call (or any ad-hoc `POST /issues.json`) to
"test" API connectivity or curl syntax — that endpoint always creates a real, permanent
issue with no undo. Only create an issue here when the user has explicitly confirmed the
previewed content in Step 5.

---

## Step 1 — Ask which RM this is a subtask of

Every RM this skill creates must be a subtask of an existing parent RM. **Always ask this
explicitly** — "ต้องการให้เป็น subtask ของ RM เลขอะไร?" — unless the user already gave the
parent RM number as `$ARGUMENTS` in this same invocation (that counts as having answered).

Fetch the parent RM to learn its project:

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<parent_id>.json"
```

Take `project.id` as `<project_id>` for the new RM (new RM lives in the **same project**
as its parent — same precedent as this pattern's own history).

---

## Step 2 — Resolve the "Deployment" tracker for that project

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/projects/<project_id>.json?include=trackers"
```

Find the tracker named `Deployment` in the returned list and take its `id` as
`<tracker_id>`. If that project has no `Deployment` tracker, tell the user and ask which
tracker to use instead — don't silently substitute one.

The assignee is **always** `IT Application Admin`, `assigned_to_id` = `280` (fixed, same
as its master pattern and its precedents) — never ask the user for this, never vary it. No need to look
this up each time, but if a create call ever rejects it, re-fetch
`https://redmine.ochi.link/users/280.json` to confirm the id is still valid before asking
the user for a replacement.

---

## Step 3 — Ask each template variable, one at a time

The Master Pattern is:

**Subject:**
```
แจ้งตัด version เพื่อ Deploy UAT (<App>)
```

**Description:**
```
เรียน IT Deploy

ขอตัด version software SQL จำนวน 1 โปรแกรม ดังนี้

| 1. | โปรแกรม <App>.exe |
| --- | --- |
| **PROGRAM_NAME** | `<App>.exe` |
| **REPOSITORY** | `<REPOSITORY>` |
| **COMMIT_HASH** | `<COMMIT_HASH>` |
| **PROGRAM_PATH** | `<PROGRAM_PATH>` |
| **DPR_FILE** | `<DPR_FILE>` |
| **ENVIRONMENT** | `UAT` |
| **RELEASE_VERSION** | |
| **APPROVED_TAG** | |

ขอบคุณครับ/ค่ะ

#ai-work
```

**Multiple programs in one RM:** if the user wants to cut more than one program, keep ONE RM, ONE greeting, ONE footer. Change `จำนวน 1 โปรแกรม` to the real count (e.g. `จำนวน 2 โปรแกรม`), repeat only the numbered table block (`| 2. | โปรแกรม <App2>.exe |` … `APPROVED_TAG`) once per program separated by a blank line, and put `ขอบคุณครับ/ค่ะ` + `#ai-work` exactly once after the LAST program block. Never repeat the footer per program, and use the subject `แจ้งตัด version เพื่อ Deploy UAT (<N> โปรแกรม)`.

**Footer rule:** the description must end with exactly ONE footer — `ขอบคุณครับ/ค่ะ`, blank line, `#ai-work` (with the hyphen, never `#aiwork`). The template above already contains it, so never append another `ขอบคุณครับ`/`#ai-work` after filling in the template.

`RELEASE_VERSION` and `APPROVED_TAG` stay **blank** — they get filled in later by the
release team's reply, never at creation time.

Ask the user for each variable below **one question at a time** (don't dump them all as
one big form) — skip a question only if the user already supplied that value unprompted
earlier in the conversation:

1. **App name** (e.g. `OGL_Operation`, `OGL_Sale`) — used for the subject and as the base
   of `PROGRAM_NAME`. Confirm the derived `PROGRAM_NAME` (`<App>.exe`) with the user rather
   than asking it as a fully separate question.
2. **REPOSITORY** (e.g. `delphi/groupwork-system-2016.git`)
3. **COMMIT_HASH** (the commit being cut)
4. **PROGRAM_PATH** — the Sub Folder path (e.g.
   `GroupLifeInsuranceSystem_Operation/trunk`). If the user doesn't know it offhand,
   suggest using `/git-clone-grouplife` or `/git-clone-grouplife-update` to look it up
   from the tracking sheet's "Sub Folder" column for this App.
5. **DPR_FILE** (e.g. `OGL_Operation.dpr`) — usually `<App>.dpr`; confirm rather than
   ask fully separately if it follows that pattern.

`ENVIRONMENT` is **never asked** — it is always `UAT`, fixed, same as `Assignee` (Step 2).
So is **Due Date** — always **today's date** (the date the RM is created, `due_date` in
`YYYY-MM-DD`), never asked and never left blank.

If the RM covers more than one Defect/UR (like a precedent ticket's `*(ครอบคลุม Defect #12345,
#12346)*` line), ask whether to add that line and which issue numbers, and append it
right after the table, before "ขอบคุณครับ/ค่ะ".

---

## Step 4 — Assemble the preview

Fill the template from Step 3's answers. Build:
- `subject`
- `description` (with `#ai-work` at the end — never omit it)
- `custom_fields`: `[{"id": 13, "value": "UAT"}]` (fixed)
- `due_date`: today's date, `YYYY-MM-DD` (fixed — get the actual current date, don't guess it)
- `project_id`, `tracker_id` (Step 2), `parent_issue_id` (Step 1), `assigned_to_id` (280, fixed)

---

## Step 5 — Confirm before creating (hard gate)

Post the **full, verbatim** final text as its own message — not a summary, not a
bullet-point recap — so the user can actually read and check every field before anything
is created:
- the exact final **subject** line,
- the exact final **description** (the whole filled-in template, `#ai-work` included, in
  a fenced code block so formatting/line breaks are visible as they'll actually post),
- and a short line underneath naming the parent RM, project, tracker, and due date.

Then explicitly ask for confirmation (e.g. "ตรวจสอบข้อมูลด้านบน ถูกต้องให้สร้าง RM ได้เลยไหม?").
Do not proceed to Step 6 without an explicit yes — a prior "ok" earlier in the conversation
for a different RM, or for a different field, doesn't count. If the user asks for a
correction, apply it and show the **entire** updated text again before asking again.

---

## Step 6 — Create the RM

```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<parent_id>,"assigned_to_id":280,"due_date":"<YYYY-MM-DD-today>","subject":"<subject>","description":"<description>","custom_fields":[{"id":13,"value":"UAT"}]}}' \
  "https://redmine.ochi.link/issues.json"
```

If the response has an `errors` field or a non-2xx status, stop and show the raw error to
the user instead of silently retrying or guessing a fix.

---

## Step 7 — Report the result

**Always end by giving the user a clickable link to the new RM so they can open it and
check it themselves** — never just state the issue number in text. Post it as its own
line, e.g.:

```
เปิด RM ใหม่แล้ว: https://redmine.ochi.link/issues/<id>
```

Alongside the link, give its parent RM and a one-line summary of what was filled in.
Remind them that `RELEASE_VERSION` and `APPROVED_TAG` are still blank pending the release
team's reply.

---

## Notes

- This skill never logs time and never posts follow-up notes — it only creates the one
  RM. Use `/redmine-logtime` separately if the user wants to log time on this.
- Never invent values for `REPOSITORY`, `COMMIT_HASH`, `PROGRAM_PATH`, or `DPR_FILE` —
  always get them from the user (or, for `PROGRAM_PATH`, from the tracking sheet via
  `/git-clone-grouplife`), never guess from a similar-looking past RM.

---

ARGUMENTS: $ARGUMENTS
