---
installer: create-shortcut
name: redmine-logtime
description: 'Summarize the work just done in this session and record it on a Redmine issue as a Note and/or a time entry (Logtime). Use when user says "/redmine-logtime", "สรุปงาน", "ลง logtime", or wants to log time/notes for the Redmine issue currently being worked on.'
created_at: 2026-07-22T15:00:00+07:00
argument-hint: "[redmine-issue-url-or-number]"
---

# /redmine-logtime — Summarize & Log Work to Redmine

Quick wrap-up skill: summarize what was actually done in the current session and record
it against a Redmine issue, as a Note, a time entry (Logtime), or both. Distinct from
`/redmine-support`'s full support-ticket workflow — this is just "wrap up and log what I
did."

Redmine access: see the `reference-redmine-api-key` memory (`X-Redmine-API-Key` header,
`https://redmine.ochi.link`).

**#ai-work tag — hard rule, no exceptions:** every Note text and every time-entry
`comments` field this skill writes MUST end with `#ai-work`. Check this immediately
before every `curl` call that sets `notes` or `comments` (per the
`feedback-tag-ai-work-comments` memory — this exact thing has been missed 3 times
before). Treat it as a mandatory pre-flight check on that field, every single time, not
something to recall passively.

**Never create a new Redmine issue — hard rule, no exceptions:** every write this skill
makes is a `PUT` to an existing `/issues/<id>.json` (Note) or a `POST` to
`/time_entries.json` (Logtime). This skill must never call
`POST https://redmine.ochi.link/issues.json` for any reason — including to "test" that the
API key/curl syntax works. If connectivity ever needs a sanity check, use
`GET .../users/current.json` instead. Opening a brand-new RM is never something this skill
does incidentally.

---

## Step 0 — Identify the issue

If not passed as `$ARGUMENTS` and not already obvious from this conversation (e.g. an RM
number already mentioned or worked on this session), ask the user for the Redmine issue
URL or number.

---

## Step 1 — Ask what kind of work to log

Ask which activity type this falls under — choose one from:

- Testing
- Analyst/Design
- Discussion/Meeting
- Planning
- Coding
- Review
- Research
- Administrative
- Deployment
- Other
- Leave

Look up the matching `activity_id` via
`https://redmine.ochi.link/enumerations/time_entry_activities.json`.

---

## Step 2 — Ask where to save

Ask the user: **Note**, **Logtime**, or **both**.

- Note only → skip Step 4 (no duration needed).
- Logtime only → the time entry's `comments` field still needs text — use the Step 3
  summary for it.
- Both → the same summary text goes into both the Note and the time entry's comments
  (trim to fit Redmine's 1024-char time-entry comment limit if needed, keeping room for
  the `#ai-work` tag).

---

## Step 3 — Ask level of detail, then draft

Ask: **detailed** or **summary**.

- **Detailed** — write out what was actually done this session step by step (what was
  changed, files/tables touched, decisions made and why), based on the real
  conversation history — not a generic restatement.
- **Summary** — 1-3 lines, just the headline outcome.

Draft the text now from what genuinely happened in this session (don't invent or pad
content). Show the draft to the user and get explicit confirmation before posting
anything — never post a Note or Logtime without approval.

---

## Step 4 — Ask how much time (skip if Note-only)

Ask how long (hours or minutes — accept either, e.g. "20 นาที" or "1.5 ชม."). Convert
minutes to decimal hours before logging (e.g. 20 min → 0.33).

---

## Step 5 — New RM assignment check (if applicable)

If this session's work included a command/instruction to open a **new** Redmine issue
(RM), that new issue must be assigned to yourself only — never leave `assigned_to`
blank. Before posting, confirm the assignee is set (Redmine user id/login for the
current user) in the create payload; if the new RM was already created without an
assignee, patch it now via PUT before continuing to Step 6.

---

## Step 6 — Post

Once the user has confirmed the final text(s) and duration, post.

Note (this is a **PUT**, not POST — POST on `/issues/<id>.json` 404s, that path only
creates a new issue):
```bash
curl -s -X PUT -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"notes":"<summary text> #ai-work"}}' \
  "https://redmine.ochi.link/issues/<id>.json"
```

Logtime:
```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"time_entry":{"issue_id":<id>,"hours":<decimal-hours>,"activity_id":<id>,"comments":"<summary text> #ai-work"}}' \
  "https://redmine.ochi.link/time_entries.json"
```

---

## Notes

- Never post a Note or time entry without the user confirming the drafted text first.
- Every `notes`/`comments` field must end with `#ai-work` — check right before each
  `curl` call that writes one, every time, no exceptions.

---

ARGUMENTS: $ARGUMENTS
