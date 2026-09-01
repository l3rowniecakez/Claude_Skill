---
installer: create-shortcut
name: redmine-support
description: 'Handle a recurring Redmine Support ticket — find similar past cases, get the fix (SQL Query/Insert/Update/Delete) approved by the developer, then post the ready-to-run script as a Redmine note. Use when user says "/redmine-support", "งาน Support", or sends a Redmine RM link for a Support fix. NEVER run the SQL or post the Redmine note without explicit developer approval first.'
created_at: 2026-07-22T13:15:00+07:00
argument-hint: "[redmine-issue-url-or-number]"
---

# /redmine-support — Redmine Support Case Handler

Recurring workflow for "งาน Support": a Redmine ticket comes in, the fix is usually a
one-off SQL script, and the finished script gets posted back to Redmine as a note for
IT Admin to run. This skill remembers past cases so recurring patterns get faster over
time, but it must **never** run a fix or post a note without the developer's explicit
approval.

Redmine access: see the `reference-redmine-api-key` memory (`X-Redmine-API-Key` header,
`https://redmine.ochi.link`). Read the issue via `.json`, never scrape the HTML page.

**Never create a new Redmine issue — hard rule, no exceptions:** every write this skill
makes is a `PUT` to the existing `/issues/<id>.json` (status update in Step 2, note in
Step 5) or a `POST` to `/time_entries.json` (Step 8). This skill must never call
`POST https://redmine.ochi.link/issues.json` for any reason, including to sanity-check
the API key or curl syntax — use `GET .../users/current.json` for that instead.

Case knowledge base lives in `references/cases.md` next to this file — it grows over
time as more cases are handled. Treat it as the skill's memory of "cases we've seen
before," separate from the general Claude memory system.

---

## Step 1 — Get the Redmine URL

If not passed as `$ARGUMENTS`, ask the user for the Redmine issue URL or number.

Fetch it:
```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<id>.json?include=journals,attachments"
```

Read subject, description, and journals to understand what's being requested.

---

## Step 2 — Mark In Progress, then search for a similar past case

First, move the issue to **In Progress** (status_id `2`) so it's visibly being worked:
```bash
curl -s -X PUT -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"status_id":2}}' \
  "https://redmine.ochi.link/issues/<id>.json"
```

Then search **two** sources for a similar past case — the local case log is fast but
only knows what this skill has recorded; Redmine itself has the full history including
cases handled before this skill existed:

1. **Local knowledge base** — read `references/cases.md` (create it with just a header
   if it doesn't exist yet) and compare the new ticket's subject/description/keywords
   against past entries — same table/domain (e.g. "ทำจ่าย", "Drug Norm", "เบิกจ่าย"),
   same kind of request (re-run data, fix a status flag, correct a date field), same
   environment.
2. **Redmine full-text search** — search all past issues for the same keywords, not
   just what's in the local log:
   ```bash
   curl -s -H "X-Redmine-API-Key: <key>" \
     "https://redmine.ochi.link/search.json?q=<keywords>&issues=1&limit=25"
   ```
   Try a couple of keyword variants (Thai term, table/field name, ticket-type phrase).
   For any promising hit, fetch the full issue (`issues/<id>.json?include=journals`) to
   see whether it's really the same kind of fix, and if so what SQL/approach was used.

- **Match found** (from either source) → note which past case(s)/RM number(s) it
  resembles, then skip to **Step 4** (reuse/adapt that fix, still requires fresh
  approval — don't assume the old SQL is still correct as-is for the new ticket's
  specific rows/IDs).
- **No match** → continue to **Step 3**.

---

## Step 3 — Ask the developer how to fix it

Ask what kind of fix this needs (SQL Query / Insert / Update / Delete) and the actual
logic. If figuring out the fix requires looking at data first, ask the developer to
choose:

- **(a) Claude queries and shows the data** — developer supplies the query intent,
  Claude runs read-only SELECTs and reports results back, or
- **(b) Direct DB connection** — default host `10.100.3.139`. Always ask for
  username/password fresh, every time — never store or reuse DB credentials (per
  `feedback-never-store-db-credentials` memory).

Either way, only read-only exploration happens here. The actual fix script is drafted
from what's learned, not executed yet.

---

## Step 4 — Get the fix approved (hard gate)

Show the developer the exact SQL script you intend to hand off. Ask for explicit
approval ("ใช่/Approve" or equivalent).

**Absolute rule — do not skip or soften this:**
- Never execute the fix SQL yourself (read-only exploration in Step 3 is fine; the
  fix itself is not).
- Never post anything to the Redmine issue (comment/note) before this approval.

If the developer asks for changes, revise and ask again. Only proceed to Step 5 once
they've clearly approved the final script.

---

## Step 5 — Ask for the note pattern, then post

Ask the developer which note template/pattern to use for this ticket (environment name,
recipient, wording can vary case to case). Example pattern given by the developer:

```
เรียน IT Admin
   ขอนำส่ง Script เพื่อใช้ในการอัพเดทข้อมูลการทำจ่าย โดย Run ที่ Oceanlife
\`\`\`sql
[SQL Query ที่ได้รับการ Approve]
\`\`\`

ขอบคุณครับ
```

Fill in the approved SQL, confirm the final note text with the developer, then post it
(note: this is a **PUT** to the issue, not POST — POST on `/issues/<id>.json` 404s
since that path is only for creating a new issue):
```bash
curl -s -X PUT -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"notes":"<final note text>"}}' \
  "https://redmine.ochi.link/issues/<id>.json"
```

---

## Step 6 — Record the case

After the note is posted, append a new entry to `references/cases.md` so this case can
be matched against future tickets:

```markdown
### RM #<id> — <short subject> (<YYYY-MM-DD>)
- Keywords: <domain/table/field keywords>
- Environment: <e.g. Oceanlife>
- Fix type: <Query/Insert/Update/Delete>
- Tables touched: <table (key column)>, ...
- Summary: <1-2 lines on what the fix did, incl. any lookup steps needed>
- Date/value conversions: <any format quirks the RM tends to report in, e.g. Thai
  dd.mm.yy Buddhist-era dates that must convert to yyyy-mm-dd CE>
- Fix template: a **reusable** version of the approved SQL with real values swapped
  for placeholders (e.g. `<AcDocNo>`, `<PayDate>`) — this is what makes Step 2 useful
  for the next similar ticket, not just keywords
```

Never paste the literal approved SQL with real production values (real IDs, names,
amounts) into `cases.md` — always generalize it into the placeholder template above.
Keywords/summary/template is enough for Step 2 to recognize and reuse a repeat case.

---

## Step 7 — Ask what kind of work to log

Ask the developer whether to log time on the issue. If yes, ask which activity type it
falls under — choose one from:

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

Also ask for a short detail/comment for the time entry (default: the ticket subject if
not given).

Look up the matching `activity_id` for the chosen name via
`https://redmine.ochi.link/enumerations/time_entry_activities.json` before posting.

If the developer says no / skip, don't log anything and skip Step 8 too.

---

## Step 8 — Ask how much time to log

Ask how long (hours or minutes — accept either, e.g. "20 นาที" or "1.5 ชม."). Convert
minutes to decimal hours (e.g. 20 min → 0.33) before logging:
```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"time_entry":{"issue_id":<id>,"hours":<decimal-hours>,"activity_id":<id>,"comments":"<comment>"}}' \
  "https://redmine.ochi.link/time_entries.json"
```

---

## Notes

- This skill accumulates knowledge over time — the developer will keep adding context
  as more cases come in. Keep `references/cases.md` append-only and readable, don't
  reorganize it into something harder to grep.
- Steps 4 and 5 are separate approval gates — approving the SQL is not approval to post
  the note, and vice versa. Always confirm both.

---

ARGUMENTS: $ARGUMENTS
