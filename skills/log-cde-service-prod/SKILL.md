---
name: log-cde-service-prod
description: "Investigate and answer questions using the PRODUCTION Google Cloud Console logs for the claim-data-extraction service (Cloud Run service + its claim-folder-worker Cloud Run Job). Use when user says '/log-cde-service-prod', asks about a processing date ('วันที่ประมวลผล'), or needs to check job status/errors/upload results for claim-data-extraction in prod."
installer: create-shortcut
created_at: 2026-08-13T09:04:43+07:00
---

# /log-cde-service-prod — claim-data-extraction (PROD) Log Investigator

Ready-to-use investigator for the **production** `claim-data-extraction` service's logs in
Google Cloud Console (Cloud Logging). When this skill is invoked, you are immediately
equipped to query — the project, resources, and log patterns below are already verified,
don't re-discover them, just query.

**This skill is PROD only.** There is a parallel SIT stack
(`claim-data-extraction-sit` / `claim-folder-worker-sit`) — never query those resources
from this skill unless the user explicitly asks to compare against SIT.

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
- Two resources make up this service, and they log different things:

| Resource | Type | Name | What it logs |
|---|---|---|---|
| Orchestrator (web UI / scheduler) | `cloud_run_revision` | `claim-data-extraction` | HTTP requests, job-launch/recover/stagger events |
| Worker (actual per-date processing) | `cloud_run_job` | `claim-folder-worker` | Folder scan, row-level success/fail counts, Drive upload confirmation |

The orchestrator launches a `claim-folder-worker` **Cloud Run Job execution** per business
date to process (batches historical backlog dates too, not just "today"). **Always check
the worker (`cloud_run_job`) logs for the actual processing outcome of a date** — the
orchestrator logs only tell you a job was launched/recovered, not whether it succeeded.

---

## How to query

Base commands (adjust `--freshness` / explicit `timestamp>=...` bounds per the patterns
below — an unbounded query can be slow):

```bash
# Orchestrator (service) logs
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-data-extraction"' \
  --project=ocean-life-data-extraction --format="value(timestamp,severity,textPayload)" \
  --order=asc --limit=200 --freshness=<Nd>

# Worker (job) logs — this is where actual processing results live
gcloud logging read \
  'resource.type="cloud_run_job" AND resource.labels.job_name="claim-folder-worker"' \
  --project=ocean-life-data-extraction --format="value(timestamp,textPayload)" \
  --order=asc --limit=200 --freshness=<Nd>
```

Add `AND textPayload:"<keyword>"` to scope to a specific date/job id/keyword — this is
much faster than pulling everything and grepping locally.

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

**Orchestrator (`claim-data-extraction`, `cloud_run_revision`)**:
- `✅ Launched Cloud Run Job for <YYYYMMDD> → .../operations/<uuid>` — a worker execution
  was kicked off for that business date
- `✅ Found target date folder: OPD/<year>/<Thai-month-name>/<YYYYMMDD> (day N)` — source
  folder located before launch
- `✅ Created N child job(s) in JobTracker` — a parent job fanned out into N child
  executions
- `🔄 Recovered active job via /api/active_job: job_<timestamp>_<id>` — orchestrator
  reattached to an in-flight job after a restart (not a new run)
- `👪 Parent job_<id> finalized by last child → completed` or `→ error (N failed)` —
  final rollup status for a parent job's children
- `⏳ Staggering next launch by <N>.0s...` — rate-limiting between launches, expected noise
- HTTP access lines (`logName` ending `%2Frequests`) — web UI traffic, only relevant for
  "is anyone using the dashboard" type questions

**Worker (`claim-folder-worker`, `cloud_run_job`)**:
- `✅ <YYYYMMDD> complete — success N, failed M` — **the definitive result line** for
  whether a date's processing succeeded; M > 0 means partial failure, go find the
  individual row/file errors around this timestamp for detail
- `✅ Uploaded Excel <filename>.xlsx to Drive` — output artifact confirmation, immediately
  follows a successful complete line
- Plain `INFO -` lines with the Python logger format
  (`YYYY-MM-DD HH:MM:SS,mmm - INFO - <message>`) — general processing narration
- `Container called exit(0).` — execution finished cleanly (exit(1) or non-zero = crashed,
  investigate the lines immediately before it)

**stderr (either resource)**:
- `WARNING:waitress.queue:Task queue depth is N` — request queue backlog on the web
  server; `N` of 1 is normal noise, only flag if it's unusually high and sustained

---

## Investigation patterns

**"วันที่ X ประมวลผลหรือยัง / ผลเป็นยังไง" (was date X processed, what was the result)**:
1. Query worker logs with `textPayload:"<YYYYMMDD>"`, no tight timestamp bound (the run
   could have happened anytime after that business date) — use `--freshness=90d` first,
   widen if nothing found.
2. Find the `✅ <YYYYMMDD> complete — success N, failed M` line — that's the answer.
3. If `M > 0`, read the surrounding `INFO` lines just before it for the specific
   failure reason.
4. Confirm the Drive upload line exists — if the complete line exists but no upload line
   follows, the export step itself may have failed even though row processing succeeded.
5. Report back: business date, when it ran (Bangkok time), success/fail counts, upload
   status.

**"ตอนนี้ระบบกำลังทำอะไรอยู่ / ทำงานล่าสุดเมื่อไหร่"**:
- Pull both resources' most recent lines (`--order=desc --limit=5`, no keyword filter) and
  compare timestamps to now — a large gap on both means idle.

**"มี error อะไรบ้างช่วงนี้"**:
- Search worker logs for `textPayload:"failed"` or severity `ERROR`, plus orchestrator logs
  for `→ error (` — cross-reference: an orchestrator "error (N failed)" rollup should have
  a matching worker `failed M` line with M ≥ N for the same business date/timeframe.

**Tracing one job's full lifecycle**:
- Get the `job_<timestamp>_<id>` id from a launch/recover line, then search both resources
  for that literal id string — orchestrator side shows launch/recovery/parent-finalize,
  worker side shows the actual per-date processing it fanned out into.

---

## Behavior

- Default to **prod only** — never silently include `-sit` resources.
- Convert Thai relative dates ("เมื่อวาน", "สัปดาห์ที่แล้ว") to explicit `YYYYMMDD` (Gregorian
  year, matching this project's convention — not Buddhist Era) before searching; if
  ambiguous, state the resulting date back to the user for confirmation.
- Always distinguish and report both "when it ran" (log timestamp, Bangkok time) and "what
  business date it processed" (the YYYYMMDD in the text) — don't conflate them.
- Quote the actual log line(s) rather than paraphrasing — the success/failed counts and
  filenames are usually exactly what's needed.
- Read-only, always: this skill only reads Cloud Logging, never modifies the service, its
  jobs, or triggers a new run.
- If `gcloud auth print-access-token` fails mid-session (token expired), stop and ask the
  user to `! gcloud auth login` again rather than guessing or retrying blindly.
