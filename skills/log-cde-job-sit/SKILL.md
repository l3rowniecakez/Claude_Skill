---
name: log-cde-job-sit
description: "Investigate and answer questions using the SIT Google Cloud Console logs for the claim-folder-worker-sit Cloud Run Job (the actual per-date claim-data-extraction processing worker on SIT). Use when user says '/log-cde-job-sit', asks about a processing date ('วันที่ประมวลผล'), or needs job-level detail (per-date success/fail counts, extraction errors, upload results) for claim-folder-worker-sit."
installer: create-shortcut
created_at: 2026-08-13T09:21:31+07:00
---

# /log-cde-job-sit — claim-folder-worker-sit (SIT) Job Log Investigator

Ready-to-use investigator for the **SIT** `claim-folder-worker-sit` Cloud Run **Job** logs
in Google Cloud Console (Cloud Logging). This is the worker that does the actual
per-business-date extraction/processing for `claim-data-extraction-sit` — when this skill
is invoked, you are immediately equipped to query — the resource, execution model, and log
patterns below are already verified, don't re-discover them, just query.

**This skill is job-only, SIT-only.**
- It does not cover the orchestrator (`claim-data-extraction-sit` `cloud_run_revision` —
  launch/recover/stagger events); use `/log-cde-service-sit` for that, or if the question
  needs both sides (e.g. "was a job even launched for date X").
- There is a parallel PROD job (`claim-folder-worker`, no `-sit` suffix) — never query it
  from here unless the user explicitly asks to compare against PROD; use `/log-cde-job-prod`
  for that side.
- **SIT runs much less often than PROD** — a multi-day gap since the last execution is
  normal (this job only runs when someone triggers a SIT test), not a sign anything is
  broken. Don't read idle time as an incident.

---

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1: Auth check (do this before every investigation)

```bash
gcloud auth print-access-token --project=ocean-life-data-extraction >/dev/null 2>&1 && echo OK || echo REAUTH_NEEDED
```

- If `OK`: proceed straight to querying.
- If `REAUTH_NEEDED`: tell the user their gcloud session expired and ask them to run
  `! gcloud auth login` (the `!` prefix runs it in their own terminal so the interactive
  OAuth browser flow works — this tool cannot do it for them). Wait for confirmation, then
  retry the check before continuing.

---

## Access (verified)

- **GCP project**: `ocean-life-data-extraction` (same project as PROD — SIT is just a
  separate resource within it, not a separate project)
- **Account**: the gcloud identity you're authenticated as (check with `gcloud auth list`)
- **Region**: `us-central1`
- **Resource**: `resource.type="cloud_run_job"`, `resource.labels.job_name="claim-folder-worker-sit"`
- **Execution model**: the SIT orchestrator (`claim-data-extraction-sit` service) triggers
  one **execution** of this job per business date to process. Each execution shows up
  under label `run.googleapis.com/execution_name` (e.g. `claim-folder-worker-sit-<suffix>`)
  — use that to scope a query to one specific run if you already have the id.
- A job **execution can process more than one business date in sequence** within a single
  run — don't assume one execution = one date; always key off the per-date `complete` line,
  not the execution boundary.

Two distinct log sources live under this one resource — don't confuse them:

| Source | What it is | How to tell |
|---|---|---|
| Container stdout/stderr | The actual processing narration — extraction, retries, upload, completion | Has a real `textPayload` string |
| `cloudaudit.googleapis.com%2Fsystem_event` | GCP audit log for `/Jobs.RunJob` — records *that an execution was launched* and by whom | `severity=ERROR` with an **empty** `textPayload`, but `protoPayload.methodName="/Jobs.RunJob"`. **This is routine — it fires for every single execution launch, not an application error.** Never report a bare `severity=ERROR` here as a job failure without checking `protoPayload.methodName` to confirm before alarming the user.

---

## How to query

```bash
# All container output (this is where processing narration lives), oldest-first for reading a run in order
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker-sit"' \
  --project=ocean-life-data-extraction --format="value(timestamp,severity,textPayload)" \
  --order=asc --limit=200 --freshness=<Nd>

# Scope to one execution once you have its name (from a launch line or the orchestrator side)
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker-sit" AND labels."run.googleapis.com/execution_name"="<execution-name>"' \
  --project=ocean-life-data-extraction --format="value(timestamp,textPayload)" \
  --order=asc --limit=500

# Confirm whether a severity=ERROR hit is the routine RunJob audit entry or a real app error
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker-sit" AND severity=ERROR' \
  --project=ocean-life-data-extraction --format="value(timestamp,protoPayload.methodName,textPayload)" \
  --order=desc --limit=50 --freshness=<Nd>
```

Add `AND textPayload:"<keyword>"` to scope to a specific date/job id/keyword — this is much
faster than pulling everything and grepping locally. Executions are infrequent on SIT, so
start with a wide `--freshness=180d` and narrow once you've found the run you're after.

**Timestamps**: `timestamp` field is UTC. Bangkok is UTC+7 — convert before reporting, and
say explicitly which timezone you're reporting in (log lines don't carry local time
themselves here, unlike the Kibana skill).

---

## Known log line patterns (don't reverse-engineer, use these — verified on SIT)

**⚠️ Important distinction**: the `YYYYMMDD` inside these messages is the **business date
being processed** (a source data folder date), NOT the timestamp the log line was written
at — a log emitted "today" can reference a business date from weeks ago. Always read both:
the log `timestamp` (when it ran) and the `YYYYMMDD` in the text (what date it processed).

**Result / lifecycle lines** (definitive, check these first):
- `✅ <YYYYMMDD> complete — success N, failed M` — **the definitive result line** for
  whether a date's processing succeeded. M can equal the full row count (e.g. `success 0,
  failed 78` has been observed on SIT) — a total-failure date is a real, meaningful result
  here, go find the cause in the lines just before it.
- `✅ Uploaded Excel <filename>.xlsx to Drive` / `✅ Uploaded result to Google Drive folder:
  <folder-id>, file_name: <filename>` (followed by a `File ID: ..., Size: N bytes` line) —
  output artifact confirmation, immediately follows a successful complete line
- `👪 Parent job_<id> finalized by last child → completed` or `→ error (N failed)` — final
  rollup status once all child executions for a parent job finish
- `Container called exit(0).` — execution finished cleanly (exit(1) or non-zero = crashed;
  investigate the lines immediately before it)

**Retry / transient-failure lines**:
- `⚠️ Drive upload attempt N/3 failed: Failed to upload to Google Drive: [Errno 32] Broken
  pipe — retrying in 5s` — transient network hiccup during the Drive upload step; only a
  real problem if all 3 attempts fail (no successful upload line follows for that date)
- `WARNING - drugnorm_v2 cache: GCS write failed for key='<name>' — result kept in local
  LRU only: 503 ... Service Unavailable` — the drug-norm result cache couldn't persist to
  GCS but the row still got processed via the in-memory LRU cache; **not a processing
  failure** by itself, just means that cache entry won't survive a restart

**Extraction / row-level failure lines** (these are what drive the `failed` count):
- `❌ Extraction error for <YYYYMMDD>: drugnorm_v2 rate limit reached (60 req/60s) — wait
  would exceed max_wait_seconds=5.0s` — the drug-norm call budget was exhausted for that
  date's batch; a real cause of failed rows, not transient noise — if this shows up right
  before a `failed M` with M > 0, this is very likely the reason
- `❌ Skipping invalid row from P<N> of <filename>.pdf: BILLING_ITEM='None',
  has_quantity=<bool>, has_financial_data=<bool>, is_subtotal=<bool>` — a row on page N of a
  source PDF didn't parse into a valid billing line item; the flags tell you which fields
  were missing. A handful scattered through a large file is normal noise from imperfect
  OCR/layout; many from the *same* file suggests that specific PDF is a bad
  scan/unsupported format.
- `❌ JSON decode error on Page N of <filename>.pdf: Empty JSON string: line 1 column 1
  (char 0)` — the extraction model returned no usable JSON for that page (Gemini
  empty/blocked response); contributes to that page's rows being lost from the count.

**Processing narration** (usually just context, not the answer itself):
- `📊 Extracted N row(s) for <YYYYMMDD>` — row count extracted before drug-norm processing
- `drugnorm_v2 (batch): skipped N non-drug row(s) via ITEMTYPE pre-filter (no Gemini call,
  no cache write)` — pre-filter stats, expected noise
- `HTTP Request: POST https://generativelanguage.googleapis.com/... "HTTP/1.1 200 OK"` /
  `AFC is enabled with max remote calls: 10.` — per-row Gemini calls for drug
  normalization; high volume is normal, only look here if hunting a non-200 Gemini response
- Plain `INFO -` lines with the Python logger format
  (`YYYY-MM-DD HH:MM:SS,mmm - INFO - <message>`) — general processing narration
- GCSFuse config dump (`message="GCSFuse Config" mount-id=...`, a very long single-line
  struct) — one-time volume-mount boot noise at the start of an execution, safe to ignore
  unless investigating a mount/storage-access failure

---

## Investigation patterns

**"วันที่ X ประมวลผลหรือยัง / ผลเป็นยังไง" (was date X processed, what was the result)**:
1. Query with `textPayload:"<YYYYMMDD>"`, no tight timestamp bound (SIT runs are
   infrequent, so the run could have happened long after that business date) —
   `--freshness=180d` is a safe starting width here, widen further if nothing found.
2. Find the `✅ <YYYYMMDD> complete — success N, failed M` line — that's the answer.
3. If `M > 0` (including `M` equal to the full count), read the lines just before it —
   look for `❌ Extraction error for <YYYYMMDD>: ... rate limit ...`, `❌ Skipping invalid
   row from P<N> of <file>.pdf`, and `❌ JSON decode error on Page N` lines for the concrete
   per-row/per-page causes.
4. Confirm the Drive upload line exists — if the complete line exists but no upload line
   follows (or all 3 `Drive upload attempt` retries failed), the export step itself may
   have failed even though row processing succeeded.
5. Report back: business date, when it ran (Bangkok time), success/fail counts, upload
   status, and root cause of any failures found.

**"execution/job นี้เกิดอะไรขึ้นบ้าง (ตลอดทั้ง run)"**:
1. Get the execution name (`claim-folder-worker-sit-<suffix>`) from either an audit
   `RunJob` entry, the orchestrator's launch line, or the parent-job-finalized line.
2. Query scoped to that `execution_name` label, `--order=asc`, and read start to finish —
   this shows every business date that one execution touched (an execution can span
   several).

**"ตอนนี้ระบบกำลังทำอะไรอยู่ / งานล่าสุดวิ่งเมื่อไหร่"**:
- Pull the most recent lines (`--order=desc --limit=10`, no keyword filter) and compare
  timestamps to now. Remember SIT is triggered manually/infrequently — a gap of days or
  weeks is expected, not a fault.

**"มี error อะไรบ้างช่วงนี้"**:
- Search `textPayload:"failed"`, `textPayload:"❌"`, or `severity=WARNING` for
  application-level issues.
- Separately check `severity=ERROR` — for each hit, confirm via `protoPayload.methodName`
  whether it's the routine `/Jobs.RunJob` audit entry (launch record, not a failure) before
  reporting it as an error.
- If many `❌ Skipping invalid row` lines cluster around the same source filename, call out
  that specific file as likely a bad scan rather than a systemic bug.
- A `drugnorm_v2 rate limit reached` line right before a large `failed M` count is very
  likely the cause — say so directly rather than just quoting the count.

---

## Behavior

- Default to **SIT only** — never silently include the PROD (`claim-folder-worker`, no
  `-sit` suffix) job.
- Convert Thai relative dates ("เมื่อวาน", "สัปดาห์ที่แล้ว") to explicit `YYYYMMDD` (Gregorian
  year, matching this project's convention — not Buddhist Era) before searching; if
  ambiguous, state the resulting date back to the user for confirmation.
- Always distinguish and report both "when it ran" (log timestamp, Bangkok time) and "what
  business date it processed" (the `YYYYMMDD` in the text) — don't conflate them.
- Never report a bare `severity=ERROR` hit as a job failure without checking
  `protoPayload.methodName` first — the routine `/Jobs.RunJob` audit entry fires on every
  execution launch and looks identical (`severity=ERROR`, empty `textPayload`) until you
  check the proto payload.
- Don't treat a long idle gap between executions as an incident — SIT only runs when
  someone triggers a test.
- Quote the actual log line(s) rather than paraphrasing — the success/failed counts,
  filenames, page numbers, and the specific validation flags on a skipped row are usually
  exactly what's needed.
- Read-only, always: this skill only reads Cloud Logging, never modifies the job, triggers
  a new execution, or cancels a running one.
- If `gcloud auth print-access-token` fails mid-session (token expired), stop and ask the
  user to `! gcloud auth login` again rather than guessing or retrying blindly.
