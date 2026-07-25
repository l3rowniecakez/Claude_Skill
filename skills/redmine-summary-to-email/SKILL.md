---
installer: create-shortcut
name: redmine-summary-to-email
description: 'Summarize a day''s Redmine spent time (logtime) into a formal email report and save it as a Draft (not sent) for an executive/ผู้บริหาร to review. Use when user says "/redmine-summary-to-email", "สรุปงาน redmine ส่งอีเมล", "ทำ draft email สรุปงาน", or wants a daily work-summary email drafted from Redmine time entries. Never actually sends the email — always stops at Draft for the user to check first.'
created_at: 2026-07-25T14:15:48+07:00
argument-hint: "[YYYY-MM-DD]"
---

# /redmine-summary-to-email — Redmine Spent-Time → Draft Email

Builds a formal daily work-summary email from Redmine time entries (spent time / logtime) on
a given date, and saves it as a **Draft only** — never sent automatically. The user must
review the draft before actually sending it themselves.

This skill remembers several things **permanently across sessions** (API key, user's own
email, To list, CC list, and the email template/wording). Only ask for each of these **the
first time ever**; every later invocation (even in a brand-new session) must load them from
memory silently and never ask again, unless the user explicitly asks to change one.

---

## Step 1 — Verify Redmine connection

Check the `reference-redmine-api-key` memory (also used by `/redmine-logtime`,
`/redmine-support`, `/redmine-ur`) for a stored key. Test it:

```bash
curl -s -o /dev/null -w "%{http_code}" -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/users/current.json"
```

- **HTTP 200** → connection OK, continue to Step 2.
- **No key stored, or non-200** → ask the user for a valid Redmine API access key. Once a
  key tests successfully, **save/update it in the `reference-redmine-api-key` memory**
  immediately so it's remembered forever, even in future sessions — do not proceed without
  saving it.

Keep the current-user JSON response (`id`, `mail`, `firstname`, `lastname`) — needed in Step
6 to filter time entries to this user.

---

## Step 2 — User's own email

Check the `reference-redmine-summary-email-contacts` memory for a saved `from` address.

- **Already saved** → use it silently, no need to ask.
- **Not saved yet** → ask the user for their own email address. Save it into the
  `reference-redmine-summary-email-contacts` memory (create the memory if it doesn't exist
  yet).

---

## Step 3 — Recipient (To) list

Check the same `reference-redmine-summary-email-contacts` memory for a saved `to` list.

- **Already saved** → use it silently.
- **Not saved yet** → ask the user for the recipient email(s). If more than one, join with
  `, ` (e.g. `abc@gmail.com, dfg@gmail.com`). Save into the memory.

---

## Step 4 — CC list

Same memory, `cc` field.

- **Already saved** → use it silently.
- **Not saved yet** → ask the user for CC email(s), same comma-joined format if multiple.
  Save into the memory (store an empty string if the user says there's no CC — still counts
  as "answered," don't ask again).

---

## Step 5 — Email draft template/wording

Check the `feedback-redmine-summary-email-template` memory for a saved template.

- **Already saved** → use it silently as the structure for Step 9.
- **Not saved yet** → ask the user to provide/confirm the wording, offering this as the
  default shape if they don't have their own:

  ```
  เรียน <Director_Name>

  เรียนแจ้งขอสรุปงานประจำวันที่ <Date_Logtime> ดังนี้
  1. <Job Desc1>
  2. <Job Desc2>
  3. <Job Desc3>

  จึงเรียนมาเพื่อทราบ
  ```

  Save whatever they confirm (their own wording or this default) into the
  `feedback-redmine-summary-email-template` memory, keeping the placeholders
  (`<Director_Name>`, `<Date_Logtime>`, job-desc list) intact so it can be reused with
  different content each time. Note the recipient's name/greeting may need to change per
  run even though the *shape* is remembered — if `<Director_Name>` isn't fixed, ask which
  name to greet with each time it's needed in Step 9.

---

## Step 6 — Which date to summarize

Ask the user which date's Redmine work to summarize (every time — this is not remembered,
it changes per run). Accept relative terms ("เมื่อวาน", "วันนี้") and resolve to an absolute
`YYYY-MM-DD` before continuing.

---

## Step 7 — Verify spent time exists for that date

Query time entries for the current user (from Step 1's `users/current.json`, or `user_id=me`)
on that date:

```bash
curl -s -H "X-Redmine-API-Key: <key>" \
  "https://redmine.ochi.link/time_entries.json?user_id=me&spent_on=<date>&limit=100"
```

- **`total_count` is 0 (no entries)** → tell the user there's no logged time for that date
  and that they should run `/redmine-logtime` first to log it, then stop here — do not
  fabricate a summary from nothing.
- **Entries exist** → continue to Step 8. Note each entry's `issue.id`, `hours`, and
  `comments`; fetch each distinct issue's subject via
  `curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<id>.json"` so the
  summary can reference the ticket title, not just the raw comment text.

---

## Step 8 — Detail level

Ask the user: **detailed** or **summary** (แบบละเอียด or แบบสรุป).

- **Detailed** — one bullet per time entry (or per issue if several entries share an issue,
  merged into one bullet), including ticket number/title and what was actually done per the
  entry's `comments`.
- **Summary** — group by issue, one line per issue, headline outcome only.

---

## Step 9 — Draft the email

Using the Step 5 template shape and the Step 7 data, write a formal Thai numbered summary
(one item per job/ticket, per the Step 8 detail level) and fill it into the template:

- `<Director_Name>` → confirm greeting name for this send (ask if not fixed in the template).
- `<Date_Logtime>` → the Step 6 date, in a readable Thai date form.
- Numbered list → the actual job descriptions built from Step 7's time entries, formal
  wording, no invented content — only what's actually in the spent-time comments/issue
  titles for that date.

Assemble the final message with:
- **From**: Step 2 email
- **To**: Step 3 list
- **CC**: Step 4 list
- **Subject**: something like `สรุปงานประจำวันที่ <Date_Logtime>`
- **Body**: the filled-in template

---

## Step 10 — Save as Draft (never send)

**Never** call Gmail's `messages.send` or any send-equivalent — this skill's job always ends
at a reviewable Draft, whichever path below is available.

This skill ships with two helper scripts in its own directory (they travel with the skill
wherever it's installed — `SCRIPTS_DIR` below means the `scripts/` folder next to this
`SKILL.md`, e.g. `~/.claude/skills/redmine-summary-to-email/scripts/` for a global install):

- `scripts/authorize_gmail.py` — one-time OAuth consent flow, produces the token.
- `scripts/build_and_create_draft.py` — builds the MIME message correctly and creates the
  Gmail Draft (or is used for the local-file-only fallback).

Both read/write machine-local state under `~/.config/redmine-summary-to-email/`
(`client_secret.json`, `gmail_token.json`, and a `venv/`) — **never** inside the skill
directory itself, so secrets never get bundled/copied/committed along with the skill.

Check whether `~/.config/redmine-summary-to-email/gmail_token.json` exists.

- **Token exists (normal case, once set up)** — create a **real Gmail Draft** via the API:
  1. Write the from/to/cc/subject/body into a JSON file (a temp scratch file is fine), e.g.:
     ```json
     {"from": "...", "to": "...", "cc": "", "subject": "...", "body": "..."}
     ```
     Always build the message through `email.message.EmailMessage` (or equivalent), never
     hand-write raw header bytes — a raw Thai/UTF-8 `Subject:` header without RFC 2047
     encoding renders as mojibake once Gmail parses it (hit this exact bug during setup).
  2. Run:
     ```bash
     ~/.config/redmine-summary-to-email/venv/bin/python3 \
       <SCRIPTS_DIR>/build_and_create_draft.py <fields.json> ~/redmine-summary-drafts/draft_<date>.eml
     ```
     This creates the Draft directly in the user's real Gmail Drafts folder (via
     `drafts().create`, never `send`) **and** writes a matching local `.eml` copy to
     `~/redmine-summary-drafts/`.
  3. If the script errors with an expired/invalid token, it auto-refreshes using the stored
     `refresh_token` — no need to redo the OAuth consent flow. Only re-run
     `authorize_gmail.py` if the token file is missing entirely or refresh itself fails.

- **Token missing** (fresh machine/session that never did the Gmail OAuth setup) — this is
  the common case on a machine where this skill was just installed. Two options:
  - Walk the user through **Appendix A** below (one-time, ~10 minutes) so future runs push
    real Gmail Drafts.
  - Or, if they'd rather skip that for now, fall back to local-file-only mode: save to
    `~/redmine-summary-drafts/draft_<date>.eml` (create the dir if needed), built the same way
    (`email.message.EmailMessage`, not hand-written headers) and tell the user it's a local
    file only — they open it in Outlook/Thunderbird or copy the body themselves.

Either way, also print the full draft (To/CC/Subject/Body) directly in the chat so the user
can review it immediately without opening anything, and tell them explicitly: **this has NOT
been sent** — check the content, then send it themselves (from Gmail's real Drafts folder, or
from the local `.eml`).

---

## Appendix A — One-time Gmail API setup (per machine)

Only needed once per machine (the resulting token is reused by every future run on that
machine). Requires the user to do a few steps themselves in their own browser — you cannot
log into their Google account for them.

### A.1 — Create a dedicated GCP project

Prefer a **new, dedicated** project over reusing an existing/shared company GCP project —
adding this scope/client to a shared project affects other apps under it. In
https://console.cloud.google.com/: click the project picker (top-left) → **New Project** →
name it e.g. `redmine-summary-mailer` → Create → switch to it.

### A.2 — Enable the Gmail API

**APIs & Services → Library** → search `Gmail API` → **Enable**.

### A.3 — Configure Google Auth Platform

(Google renamed the old "OAuth consent screen" to **Google Auth Platform** — same menu
group, left sidebar: Overview / Branding / Audience / Clients / Data Access / Verification
Center / Settings. If the sidebar looks different, that's the tell — the naming/layout has
shifted before and may again; re-orient off these functional descriptions rather than exact
menu labels.)

1. **Branding** — set an App name and support email (may be pre-filled by the quick-setup
   flow when the project was just created).
2. **Audience** — set to **External**, then add the user's own email as a **Test user**
   (required — this app will not go through Google's verification process).
3. **Data Access** → **Add or remove scopes** → search/select
   `https://www.googleapis.com/auth/gmail.compose` → confirm → **Save**. This scope only
   allows managing drafts/sending what the app itself composed — it **cannot** read or
   search the mailbox, which is why it's the right choice for this skill (never needs to
   read mail, only ever creates Drafts).
4. **Clients** → **Create client** (or **Create OAuth client** from the Overview page) →
   Application type **Desktop app** → name it → Create → **Download JSON**.

### A.4 — Save the client secret

Save the downloaded JSON to:
```
~/.config/redmine-summary-to-email/client_secret.json
```
(create the directory if needed; `chmod 600` it — it's a credential, not code).

### A.5 — Set up an isolated Python environment

Run the bundled setup script:
```bash
bash <SCRIPTS_DIR>/setup_venv.sh
```

Use an isolated venv (not the system/`--user` Python) — a system-wide `requests` package can
end up on a version that no longer exposes `requests.packages.urllib3`, which
`google-auth`'s `requests` transport imports unconditionally; that raised a hard
`ModuleNotFoundError` during setup on this exact combination. The venv sidesteps the
conflict entirely instead of pinning versions that may drift again later.

### A.6 — Run the OAuth consent flow once

```bash
~/.config/redmine-summary-to-email/venv/bin/python3 <SCRIPTS_DIR>/authorize_gmail.py
```

It prints a URL — hand it to the user to open **in their own browser, logged into the
account they want drafts created in**. They will likely see a "Google hasn't verified this
app" warning (expected, since Step A.3 skipped verification) — they click **Advanced → Go to
<app name> (unsafe)** → **Continue/Allow**. The script's local server (listening on
`localhost:8765`) catches the redirect automatically and writes
`~/.config/redmine-summary-to-email/gmail_token.json`. Run this as a background command and
poll/monitor its output for `SAVED_TOKEN_OK` rather than blocking — the user needs a moment to
switch to their browser and click through.

Once `gmail_token.json` exists, Step 10's normal path (real Gmail Drafts) is live — no need
to repeat any of Appendix A again on this machine.

---

## Notes

- Steps 2–5 are asked **once ever** — check memory first, every single time this skill is
  invoked, before asking. Never re-ask just because it's a new session.
- Step 1's API key follows the same permanent-memory rule as every other `/redmine-*` skill
  in this project.
- Never send the email — this skill's job ends at a reviewable Draft.
- If the user later wants to change a remembered value (their email, To/CC list, or
  template), update the relevant memory file directly rather than treating it as a fresh
  "first time" ask.

---

ARGUMENTS: $ARGUMENTS
