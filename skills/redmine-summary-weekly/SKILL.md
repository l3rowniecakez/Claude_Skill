---
installer: create-shortcut
name: redmine-summary-weekly
description: 'Summarize Redmine spent time (logtime) over a week or custom date range, grouped by Project, for reporting in a status meeting with a supervisor. Use when user says "/redmine-summary-weekly", "สรุปงาน week นี้", "สรุปงานประจำสัปดาห์", or wants a project-grouped work summary to present in a meeting. Read-only — never posts/writes anything to Redmine.'
created_at: 2026-08-06T16:50:52+07:00
argument-hint: "[this-week|YYYY-MM-DD..YYYY-MM-DD]"
---

# /redmine-summary-weekly — Redmine Spent-Time → Project-Grouped Meeting Summary

Builds a work summary from Redmine time entries (spent time / logtime) over a chosen date
range, grouped by **Project**, for the user to read out or paste into a status meeting with
their หัวหน้างาน. Purely read-only — this skill never posts a Note or time entry, and never
sends anything anywhere; it only prints the summary in chat.

---

## Step 1 — Verify Redmine connection

Check the `reference-redmine-api-key` memory (shared with `/redmine-logtime`,
`/redmine-support`, `/redmine-ur`, `/redmine-summary-to-email`) for a stored key. Test it:

```bash
curl -s -o /dev/null -w "%{http_code}" -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/users/current.json"
```

- **HTTP 200** → OK, continue.
- **No key stored, or non-200** → ask the user for a valid Redmine API access key. Once it
  tests successfully, save/update it in the `reference-redmine-api-key` memory immediately.

Keep the current-user id from the response — needed for `user_id=me` filtering in Step 4.

---

## Step 2 — Which period

Ask the user to choose:

- **สรุปงาน week นี้** — this week. Compute via `date`: Monday of the current week through
  today (not through Sunday — a mid-week status meeting only cares about days already
  worked). E.g. `date -d monday` / `date +%u` to find how many days back Monday is, today's
  date as the end.
- **เลือกวันที่เริ่มต้น–สิ้นสุดเอง** — ask for a start and end date, accept relative or
  absolute input, resolve both to absolute `YYYY-MM-DD` before continuing.

If `$ARGUMENTS` already supplies `this-week` or a `YYYY-MM-DD..YYYY-MM-DD` range, use it
directly and skip asking.

---

## Step 3 — Detail level

Ask the user: **แบบละเอียด** or **แบบสรุปสั้น**.

- **สรุปสั้น** — one line per project per date: all entries on that date merged into a single
  short headline description and the day's total hours for that project.
- **ละเอียด** — one line per time entry (don't merge same-day entries), each prefixed with
  the ticket number (`#<issue.id>`) and using the full `comments` text, plus hours.

---

## Step 4 — Fetch time entries for the period

```bash
curl -s -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/time_entries.json?user_id=me&from=<start>&to=<end>&limit=100&offset=0"
```

Redmine's `time_entries.json` accepts `from`/`to` as an inclusive `spent_on` range. Page
through with `offset` in steps of 100 while `total_count` exceeds what's been fetched.

Each entry already includes `project` (`id`, `name`), `issue` (`id`), `hours`, `comments`,
and `spent_on` — no extra per-entry lookup needed for summary mode.

- **No entries in range** → tell the user there's no logged time for that period and stop —
  do not fabricate a summary.
- **Detailed mode only**: collect the distinct `issue.id` values and fetch each subject via
  `curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<id>.json"` so the
  detailed lines can reference the ticket title alongside the comment text.

---

## Step 5 — Group and build the summary

Group entries by `project.name`. Within each project, sort entries by `spent_on` ascending.
Sort the projects themselves by total hours in the range, descending (the most time-consuming
project leads the report).

Format each project block exactly like:

```
[<Project Name>]
<DD/MM/YYYY> : <งานที่ทำ> (<ชั่วโมง> ชั่วโมง)
<DD/MM/YYYY> : <งานที่ทำ> (<ชั่วโมง> ชั่วโมง)
```

with a blank line between project blocks. Dates in Gregorian `DD/MM/YYYY` (not พ.ศ.), hours
as they appear in Redmine (e.g. `0.5`, `1`, `2`).

- **สรุปสั้น**: per date, merge all of that project's entries on that date into one line —
  join the distinct task descriptions with `, ` and sum the hours.
- **ละเอียด**: one line per entry, e.g.
  `01/01/2026 : #12345 <issue subject> - <comments text> (2 ชั่วโมง)`. Do not merge entries
  even if same date/project.

After the per-project blocks, add a closing totals line per project and a grand total, e.g.:

```
รวม <Project Name>: <total> ชั่วโมง
...
รวมทั้งหมด: <grand total> ชั่วโมง
```

Print the finished summary directly in the chat — this skill's output ends there; it does
not save a file, draft an email, or write anything back to Redmine.

---

## Notes

- Purely read-only: never call POST/PUT against Redmine from this skill.
- Step 1's API key follows the same permanent-memory rule as every other `/redmine-*` skill.
- Do not invent task descriptions — only use what's actually in each entry's `comments`
  (and, in detailed mode, the issue subject).

---

ARGUMENTS: $ARGUMENTS
