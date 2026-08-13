---
name: log-cde-job-prod
description: "Investigate and answer questions using the PRODUCTION Google Cloud Console logs for the claim-folder-worker Cloud Run Job (the actual per-date claim-data-extraction processing worker). Use when user says '/log-cde-job-prod', asks about a processing date ('วันที่ประมวลผล'), or needs job-level detail (per-date success/fail counts, extraction errors, upload results) for claim-folder-worker in prod."
installer: create-shortcut
created_at: 2026-08-13T09:19:13+07:00
---

# /log-cde-job-prod — claim-folder-worker (PROD) Job Log Investigator

Ready-to-use investigator for the **production** `claim-folder-worker` Cloud Run **Job**
logs in Google Cloud Console (Cloud Logging). This is the worker that does the actual
per-business-date extraction/processing for `claim-data-extraction` — when this skill is
invoked, you are immediately equipped to query — the resource, execution model, and log
patterns below are already verified, don't re-discover them, just query.

**This skill is job-only, PROD-only.**
- It does not cover the orchestrator (`claim-data-extraction` `cloud_run_revision` —
  launch/recover/stagger events); use `/log-cde-service-prod` for that, or if the question
  needs both sides (e.g. "was a job even launched for date X").
- There is a parallel SIT job (`claim-folder-worker-sit`) — never query it from here unless
  the user explicitly asks to compare against SIT; use `/log-cde-service-sit` for that side.

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

- **GCP project**: `ocean-life-data-extraction`
- **Account**: the gcloud identity you're authenticated as (check with `gcloud auth list`)
- **Region**: `us-central1`
- **Resource**: `resource.type="cloud_run_job"`, `resource.labels.job_name="claim-folder-worker"`
- **Execution model**: the orchestrator (`claim-data-extraction` service) triggers one
  **execution** of this job per business date to process (backlog dates too, not just
  "today"). Each execution shows up under label
  `run.googleapis.com/execution_name` (e.g. `claim-folder-worker-txwm7`) — use that to
  scope a query to one specific run if you already have the id.
- A job **execution can process more than one business date in sequence** within a single
  run — don't assume one execution = one date; always key off the per-date `complete` line,
  not the execution boundary.

Two distinct log sources live under this one resource — don't confuse them:

| Source | What it is | How to tell |
|---|---|---|
| Container stdout/stderr | The actual processing narration — extraction, retries, upload, completion | Has a real `textPayload` string |
| `cloudaudit.googleapis.com%2Fsystem_event` | GCP audit log for `/Jobs.RunJob` — records *that an execution was launched* and by whom | `severity=ERROR` with an **empty** `textPayload`, but `protoPayload.methodName="/Jobs.RunJob"` and `protoPayload.resourceName` naming the execution. **This is routine — it fires for every single execution launch (usually via a dedicated service account), not an application error.** Never report a bare `severity=ERROR` here as a job failure without checking whether it's actually this audit entry — pull `protoPayload.methodName` to confirm before alarming the user.

---

## How to query

```bash
# All container output (this is where processing narration lives), oldest-first for reading a run in order
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker"' \
  --project=ocean-life-data-extraction --format="value(timestamp,severity,textPayload)" \
  --order=asc --limit=200 --freshness=<Nd>

# Scope to one execution once you have its name (from a launch line or the orchestrator side)
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker" AND labels."run.googleapis.com/execution_name"="<execution-name>"' \
  --project=ocean-life-data-extraction --format="value(timestamp,textPayload)" \
  --order=asc --limit=500

# Confirm whether a severity=ERROR hit is the routine RunJob audit entry or a real app error
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker" AND severity=ERROR' \
  --project=ocean-life-data-extraction --format="value(timestamp,protoPayload.methodName,textPayload)" \
  --order=desc --limit=50 --freshness=<Nd>
```

Add `AND textPayload:"<keyword>"` to scope to a specific date/job id/keyword — this is much
faster than pulling everything and grepping locally.

**Timestamps**: `timestamp` field is UTC. Bangkok is UTC+7 — convert before reporting, and
say explicitly which timezone you're reporting in (log lines don't carry local time
themselves here, unlike the Kibana skill).

---

## Known log line patterns (don't reverse-engineer, use these)

**⚠️ Important distinction**: the `YYYYMMDD` inside these messages is the **business date
being processed** (a source data folder date), NOT the timestamp the log line was written
at — the worker processes a backlog queue, so a log emitted "today" can reference a
business date from weeks ago. Always read both: the log `timestamp` (when it ran) and the
`YYYYMMDD` in the text (what date it processed).

**Result / lifecycle lines** (definitive, check these first):
- `✅ <YYYYMMDD> complete — success N, failed M` — **the definitive result line** for
  whether a date's processing succeeded; M > 0 means partial failure, go find the
  individual row/file errors around this timestamp for detail
- `✅ Uploaded Excel <filename>.xlsx to Drive` / `✅ Uploaded result to Google Drive folder:
  <folder-id>, file_name: <filename>` (immediately followed by a `File ID: ..., Size: N
  bytes` line) — output artifact confirmation, immediately follows a successful complete
  line
- `👪 Parent job_<id> finalized by last child → completed` or `→ error (N failed)` — final
  rollup status once all child executions for a parent job finish
- `Container called exit(0).` — execution finished cleanly (exit(1) or non-zero = crashed;
  investigate the lines immediately before it)

**Retry / failure lines**:
- `🔄 Billing retry N/3: M page(s) failed — re-extracting...` — the extractor is retrying M
  pages of a billing document up to 3 times; only a problem if it still shows failures in
  the following `complete` line's `failed` count after all 3 attempts
- `❌ Extraction worker failed (non-retryable): <HTTP status>. {...}` — a hard failure from
  an upstream call (observed cause: `502 Bad Gateway` from the Document AI / extraction
  backend under load) that the retry logic gave up on. Read the embedded status/message
  for the underlying cause; a burst of these in a short window points at an upstream
  outage/rate-limit, not a bug in this worker.

**Processing narration** (usually just context, not the answer itself):
- `📊 Extracted N row(s) for <YYYYMMDD>` — row count extracted before drug-norm processing
- `drugnorm_v2 (batch): skipped N non-drug row(s) via ITEMTYPE pre-filter (no Gemini call,
  no cache write)` — pre-filter stats, expected noise
- `HTTP Request: POST https://generativelanguage.googleapis.com/... "HTTP/1.1 200 OK"` /
  `AFC is enabled with max remote calls: 10.` — per-row Gemini calls for drug
  normalization; high volume is normal, only look here if hunting a non-200 Gemini response
- `💾 Memory after sub-batch N/M: <N> MB` — memory usage checkpoint; only relevant if
  chasing an OOM-style crash (compare against a spike right before an `exit(1)`)
- Plain `INFO -` lines with the Python logger format
  (`YYYY-MM-DD HH:MM:SS,mmm - INFO - <message>`) — general processing narration
- GCSFuse config dump (`message="GCSFuse Config" mount-id=...`, a very long single-line
  struct) — one-time volume-mount boot noise at the start of an execution, safe to ignore
  unless investigating a mount/storage-access failure

---

## Investigation patterns

**"วันที่ X ประมวลผลหรือยัง / ผลเป็นยังไง" (was date X processed, what was the result)**:
1. Query with `textPayload:"<YYYYMMDD>"`, no tight timestamp bound (the run could have
   happened anytime after that business date) — use `--freshness=90d` first, widen if
   nothing found.
2. Find the `✅ <YYYYMMDD> complete — success N, failed M` line — that's the answer.
3. If `M > 0`, read the surrounding lines just before it — look specifically for `🔄
   Billing retry` and `❌ Extraction worker failed (non-retryable)` lines for the concrete
   cause.
4. Confirm the Drive upload line exists — if the complete line exists but no upload line
   follows, the export step itself may have failed even though row processing succeeded.
5. Report back: business date, when it ran (Bangkok time), success/fail counts, upload
   status, and root cause of any failures found.

**"execution/job นี้เกิดอะไรขึ้นบ้าง (ตลอดทั้ง run)"**:
1. Get the execution name (`claim-folder-worker-<suffix>`) from either an audit `RunJob`
   entry, the orchestrator's launch line, or the parent-job-finalized line.
2. Query scoped to that `execution_name` label, `--order=asc`, and read start to finish —
   this shows every business date that one execution touched (an execution can span
   several).

**"ตอนนี้ระบบกำลังทำอะไรอยู่ / งานล่าสุดวิ่งเมื่อไหร่"**:
- Pull the most recent lines (`--order=desc --limit=10`, no keyword filter) and compare
  timestamps to now — a large gap means idle (this job doesn't run continuously, only when
  triggered per business date).

**"มี error อะไรบ้างช่วงนี้"**:
- Search `textPayload:"failed"` or `textPayload:"❌"` for application-level failures.
- Separately check `severity=ERROR` — for each hit, confirm via `protoPayload.methodName`
  whether it's the routine `/Jobs.RunJob` audit entry (launch record, not a failure) before
  reporting it as an error.
- A burst of `502 Bad Gateway` / non-retryable failures across multiple unrelated dates in
  a short window suggests an upstream outage (Document AI / extraction backend), not a
  code issue — say so if the pattern matches.

---

## Behavior

- Default to **prod only** — never silently include the `-sit` job.
- Convert Thai relative dates ("เมื่อวาน", "สัปดาห์ที่แล้ว") to explicit `YYYYMMDD` (Gregorian
  year, matching this project's convention — not Buddhist Era) before searching; if
  ambiguous, state the resulting date back to the user for confirmation.
- Always distinguish and report both "when it ran" (log timestamp, Bangkok time) and "what
  business date it processed" (the `YYYYMMDD` in the text) — don't conflate them.
- Never report a bare `severity=ERROR` hit as a job failure without checking
  `protoPayload.methodName` first — the routine `/Jobs.RunJob` audit entry fires on every
  execution launch and looks identical (`severity=ERROR`, empty `textPayload`) until you
  check the proto payload.
- Quote the actual log line(s) rather than paraphrasing — the success/failed counts,
  filenames, and HTTP status codes are usually exactly what's needed.
- Read-only, always: this skill only reads Cloud Logging, never modifies the job, triggers
  a new execution, or cancels a running one.
- If `gcloud auth print-access-token` fails mid-session (token expired), stop and ask the
  user to `! gcloud auth login` again rather than guessing or retrying blindly.
