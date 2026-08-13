---
name: log-drugapi-service-prod
description: "Investigate and answer questions using the PRODUCTION Google Cloud Console logs for the claim-drugnorm-api service (a Cloud Run HTTP API, not a batch job). Use when user says '/log-drugapi-service-prod', asks about a processing date ('วันที่ประมวลผล'), or needs to check request status/errors/latency for claim-drugnorm-api in prod."
installer: create-shortcut
created_at: 2026-08-13T09:09:46+07:00
---

# /log-drugapi-service-prod — claim-drugnorm-api (PROD) Log Investigator

Ready-to-use investigator for the **production** `claim-drugnorm-api` service's logs in
Google Cloud Console (Cloud Logging). When this skill is invoked, you are immediately
equipped to query — the project, resource, and log patterns below are already verified,
don't re-discover them, just query.

**This skill is PROD only.** There is a parallel SIT service (`claim-drugnorm-api-sit`) in
the same project — never query it from this skill unless the user explicitly asks to
compare against SIT.

**Shape of this service**: unlike `claim-data-extraction` (a batch job over business
dates), `claim-drugnorm-api` is a synchronous HTTP API — a client calls it, it normalizes a
drug name/code, and returns a response immediately. There is **no "business date being
processed" concept in these logs** — if the user asks "วันที่ X ประมวลผลหรือยัง", interpret
that as "were there any API calls logged on date X", not a batch-date lookup, and say so
explicitly if it seems like they expect the CDE-style batch semantics.

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

- **GCP project**: `ocean-life-data-extraction` (same project as `claim-data-extraction`)
- **Account**: the gcloud identity you're authenticated as (check with `gcloud auth list`)
- **Region**: `us-central1`
- **Resource**: `resource.type="cloud_run_revision"`, `resource.labels.service_name="claim-drugnorm-api"`
- **Service URL**: `https://claim-drugnorm-api-k6syfr56xq-uc.a.run.app`
- Known endpoint: `POST /api/v2/drugnorm` (the actual drug-normalization call)
- Runtime: Python FastAPI/Uvicorn on Cloud Run, autoscaled (scales to zero between calls —
  don't read a startup/shutdown cycle as an incident, it's normal idle behavior)

Three log sources under this one resource, each surfaced via `logName`:

| `logName` suffix | What it logs |
|---|---|
| `%2Frequests` | Auto-generated HTTP access log — has a `httpRequest` struct (method, URL, status, latency, request/response size, remoteIp, userAgent). **No request/response body is logged here or anywhere else** — you cannot see which drug/code was normalized, only whether the call succeeded and how fast. |
| `%2Fvarlog%2Fsystem` | Container/instance lifecycle — cold start, autoscaling reason, health-probe results, shutdown |
| `%2Fstderr` / `%2Fstdout` | Uvicorn/FastAPI process text lines (`INFO:     Uvicorn running on...`, `Application startup complete`, etc.) — general process narration, rarely useful for answering business questions |

---

## How to query

```bash
# Everything for this service (all log sources), most recent first
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api"' \
  --project=ocean-life-data-extraction --format="value(timestamp,severity,textPayload)" \
  --order=desc --limit=200 --freshness=<Nd>

# Just the HTTP request/response outcomes (this is where "did it work" lives)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api" AND logName:"requests"' \
  --project=ocean-life-data-extraction \
  --format="table(timestamp,httpRequest.requestMethod,httpRequest.requestUrl,httpRequest.status,httpRequest.latency,httpRequest.remoteIp,httpRequest.userAgent)" \
  --order=desc --limit=200 --freshness=<Nd>

# Only actual errors (auto request logs mark 4xx/5xx as WARNING/ERROR severity)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api" AND severity>=WARNING' \
  --project=ocean-life-data-extraction --format=json \
  --order=desc --limit=100 --freshness=<Nd>
```

Traffic on this service is low (single-digit to low-tens of calls per day as of 2026-08),
so a `--freshness=90d` pull with no keyword filter is usually cheap and fine — no need to
narrow aggressively like the CDE worker logs.

**Timestamps**: `timestamp` is UTC. Bangkok is UTC+7 — convert before reporting, and state
which timezone you're reporting in.

---

## Known log line / field patterns (don't reverse-engineer, use these)

**Request log (`%2Frequests`) — `httpRequest.status` meanings observed on this service**:
- `200` — normalized successfully. Legit callers seen so far use `curl` as the user-agent
  and a stable small set of `remoteIp` values — cross-check against prior 200s from the
  same IP/user-agent before assuming a new caller is legitimate.
- `401 Unauthorized` — missing or invalid auth credential on the request. The bulk of 401s
  on `/` and `/api/v2/drugnorm` are **internet background-scan noise**: random browser
  `userAgent` strings (Chrome/Edge on Windows) hitting the public Cloud Run URL
  unsolicited, unrelated to real usage. Don't treat these as an incident by themselves.
- `403 Forbidden` — credential present but rejected (wrong key/token, not just missing).
  Seen occasionally from the same `curl` clients that also produced 200s nearby in time —
  likely a client mid-testing an auth header, not an attacker.
- `5xx` — has not been observed in production as of 2026-08; if you find one, treat it as
  a real incident and read the surrounding `%2Fstderr` lines for a stack trace.
- No `severity>=ERROR` entries have been seen at all — if a query surfaces one, don't
  assume it's routine, read it in full.

**Lifecycle (`%2Fvarlog%2Fsystem`)**:
- `Starting new instance. Reason: AUTOSCALING - ...` — cold start due to traffic (scale
  from zero); `Reason: DEPLOYMENT_ROLLOUT - ...` — cold start due to a new deploy, not
  traffic
- `STARTUP HTTP probe succeeded after N attempts for container "..." on port 8080 path
  "/healthz".` — container came up healthy
- `Default STARTUP TCP probe succeeded after N attempt(s).` — lower-level readiness check,
  precedes the HTTP probe line

**Process (`%2Fstderr`)**:
- `INFO:     Started server process [1]` → `Waiting for application startup.` →
  `Application startup complete.` → `Uvicorn running on http://0.0.0.0:8080 ...` — normal
  cold-start sequence, always in this order
- `INFO:     Shutting down` → `Waiting for application shutdown.` →
  `Application shutdown complete.` → `Finished server process [1]` — normal scale-to-zero
  sequence when idle; this is expected, not a crash

---

## Investigation patterns

**"วันที่ X มีเรียก API หรือยัง / ผลเป็นยังไง" (were there calls on date X, how did they go)**:
1. Query the request-log table above with `--freshness` wide enough to cover date X
   (convert to a UTC day-boundary window if precision matters, since `timestamp` is UTC).
2. List every `httpRequest` row for that day: status, latency, remoteIp, userAgent.
3. Report success/fail counts by status code. Remember: no body is logged, so you cannot
   say *which* drug/code was normalized — only call outcomes.
4. If the user seems to expect batch-style "processed N records" semantics, clarify this
   service doesn't work that way — each API call is one synchronous request.

**"ตอนนี้ระบบยังทำงานอยู่ไหม / เรียกล่าสุดเมื่อไหร่"**:
- Pull the most recent request-log rows (`--order=desc --limit=5`, no filter) and compare
  timestamp to now. A long gap is normal — this service scales to zero when idle, it's not
  down.

**"มี error หรือมีคนพยายามเข้าถึงแบบผิดปกติไหม"**:
- Filter `severity>=WARNING`, then split by `httpRequest.userAgent`/`remoteIp` pattern:
  browser user-agents hitting `/` or the API root with no prior 200 history from that
  IP = scan noise; `curl` clients with a mix of 401/403/200 close together in time = a
  real client working through auth, not an attack.
- Any `5xx` or `severity>=ERROR` line is unprecedented for this service — flag it clearly
  rather than filing it under normal noise, and pull the `%2Fstderr` lines around the same
  `insertId`/timestamp for a stack trace.

---

## Behavior

- Default to **prod only** — never silently include the `-sit` resource.
- Convert Thai relative dates ("เมื่อวาน", "สัปดาห์ที่แล้ว") to explicit dates before
  searching, state the resulting date back if ambiguous, and always note UTC vs Bangkok
  time explicitly when reporting a timestamp.
- Be explicit about the logging limitation: this service never logs request/response
  bodies, so questions about *which* drug name/code was processed cannot be answered from
  these logs — only call success/failure, timing, and caller metadata.
- Quote the actual `httpRequest` fields (status, latency, remoteIp, userAgent) rather than
  paraphrasing.
- Read-only, always: this skill only reads Cloud Logging, never modifies the service or
  triggers a new deploy/request.
- If `gcloud auth print-access-token` fails mid-session (token expired), stop and ask the
  user to `! gcloud auth login` again rather than guessing or retrying blindly.
