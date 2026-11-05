---
installer: create-shortcut
name: redmine-logtime-more
description: 'Like /redmine-logtime but splits the session into as MANY separate time entries (Logtime) as possible, each with a thorough, detailed work summary. Use when user says "/redmine-logtime-more", "แยก logtime ให้ละเอียด", "ลง logtime หลายรายการ".'
created_at: 2026-11-05T00:00:00+07:00
argument-hint: "[redmine-issue-url-or-number]"
---

# /redmine-logtime-more — Split Session into Many Detailed Logtimes

Variant of `/redmine-logtime`. Summarize what was actually done in the current session and record
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

## Step 1 — Split the session into as many logtimes as possible

Review the whole session history and break the work into the **finest distinct units**
that can each stand as its own time entry — e.g. per analysis/investigation, per file or
program unit edited, per DB script/store, per bug fixed, per test round, per deploy step,
per discussion/decision. Prefer MORE entries over fewer, as long as each is a genuinely
separate piece of work that really happened (never invent or pad entries; never split one
atomic action artificially).

For each entry determine:
- **Activity type** (choose one: Testing, Analyst/Design, Discussion/Meeting, Planning,
  Coding, Review, Research, Administrative, Deployment, Other, Leave). Look up
  `activity_id` via `https://redmine.ochi.link/enumerations/time_entry_activities.json`.
- **Target issue** — default to the RM for this session; if work belongs to different RMs
  (or own subtasks — never log on a subtask
  opened/assigned to someone else), group accordingly.
- **Detailed summary** (see Step 2).

---

## Step 2 — Write each summary in detail

Every entry's text must be a **thorough** account based on the real conversation: what was
asked/found, what was changed (files, forms, stores, tables, columns), key decisions and
why, how it was verified, and the outcome. Not a 1-line headline. Use short numbered or
dashed points. Thai prose, code/identifiers in original form.

Constraint: Redmine time-entry `comments` max is **1024 BYTES utf-8** (not chars) —
compute `len(text.encode('utf-8'))` including the trailing ` #ai-work`. If an entry's
detail exceeds it, either split it into further sub-entries (preferred — fits the
"as many as possible" goal) or put the full detail into a Note and keep the time entry
comment as the densest 1024-byte version. Notes have no such limit.

---

## Step 3 — Ask where to save and how much time

Ask the user: **Note**, **Logtime**, or **both** (default suggestion: both — one
consolidated Note with all details plus the many Logtime entries).

If Logtime is chosen, propose hours for each entry in the draft table (accept hours or
minutes; convert minutes to decimal hours, e.g. 20 min → 0.33) and ask the user to
confirm or adjust. Ask for the total time budget first if the user wants it distributed
automatically across entries.

---

## Step 4 — Show the full draft table and get approval

Present all entries as a table/list: # | issue | activity | hours | full comment text
(with byte count). Get explicit confirmation (or edits) before posting anything — never
post a Note or Logtime without approval. If a Note is chosen, post ONE consolidated Note, not one per entry.

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

Logtime (repeat once per entry, pre-flight check `#ai-work` and the 1024-byte limit on each):
```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"time_entry":{"issue_id":<id>,"hours":<decimal-hours>,"activity_id":<id>,"comments":"<summary text> #ai-work"}}' \
  "https://redmine.ochi.link/time_entries.json"
```

---

## Notes

- Total of all entry hours should match what the user confirmed.
- Never post a Note or time entry without the user confirming the drafted text first.
- Every `notes`/`comments` field must end with `#ai-work` — check right before each
  `curl` call that writes one, every time, no exceptions.

---

ARGUMENTS: $ARGUMENTS
