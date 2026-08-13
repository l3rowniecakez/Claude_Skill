---
name: log-drugapi-service-sit
description: "Investigate and answer questions using the SIT Google Cloud Console logs for the claim-drugnorm-api service (a Cloud Run HTTP API, not a batch job). Use when user says '/log-drugapi-service-sit', asks about a processing date ('วันที่ประมวลผล') on SIT, or needs to check request status/errors/latency for claim-drugnorm-api-sit."
installer: create-shortcut
created_at: 2026-08-13T09:16:00+07:00
---

# /log-drugapi-service-sit — claim-drugnorm-api (SIT) Log Investigator

Ready-to-use investigator for the **SIT** `claim-drugnorm-api-sit` service's logs in
Google Cloud Console (Cloud Logging). When this skill is invoked, you are immediately
equipped to query — the project, resource, and log patterns below are already verified,
don't re-discover them, just query.

**This skill is SIT only.** There is a parallel PROD service (`claim-drugnorm-api`, no
`-sit` suffix) in the same project — never query it from this skill unless the user
explicitly asks to compare against PROD. (Use `/log-drugapi-service-prod` for PROD.)

**Shape of this service**: unlike `claim-data-extraction-sit` (a batch job over business
dates), `claim-drugnorm-api-sit` is a synchronous HTTP API — a client calls it, it
normalizes a drug name/code, and returns a response immediately. There is **no "business
date being processed" concept in these logs** — if the user asks "วันที่ X ประมวลผลหรือยัง",
interpret that as "were there any API calls logged on date X", not a batch-date lookup, and
say so explicitly if it seems like they expect the CDE-style batch semantics.

**SIT is a testing environment** — traffic is developer-driven (manual `curl` calls, dev
scripts), not real end-user traffic. Expect ad-hoc bursts, deliberate bad-input tests (400s),
auth-header trial-and-error (401/403), and occasional redeploys — none of that is inherently
an incident here the way it would be on PROD.

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

- **GCP project**: `ocean-life-data-extraction` (same project as PROD and as
  `claim-data-extraction-sit`)
- **Account**: the gcloud identity you're authenticated as (check with `gcloud auth list`)
- **Region**: `us-central1`
- **Resource**: `resource.type="cloud_run_revision"`, `resource.labels.service_name="claim-drugnorm-api-sit"`
- **Service URLs**: `https://claim-drugnorm-api-sit-k6syfr56xq-uc.a.run.app` and
  `https://claim-drugnorm-api-sit-664156704064.us-central1.run.app` (same service, two
  hostnames both appear in logs — don't treat the second as a different deployment)
- Known endpoint: `POST /api/v2/drugnorm` (the actual drug-normalization call)
- Runtime: Python FastAPI/Uvicorn on Cloud Run (`uvicorn api_v2:app`), env
  `DRUGNORM_V2_ENV=sit`, `maxScale=3` (much lower ceiling than prod — expect throttling
  under any real burst), autoscaled (scales to zero between calls — don't read a
  startup/shutdown cycle as an incident, it's normal idle behavior)

Log sources under this one resource, surfaced via `logName`/`protoPayload`:

| `logName` suffix/type | What it logs |
|---|---|
| `%2Frequests` | Auto-generated HTTP access log — has a `httpRequest` struct (method, URL, status, latency, request/response size, remoteIp, userAgent). **No request/response body is logged here or anywhere else** — you cannot see which drug/code was normalized, only whether the call succeeded and how fast. |
| `%2Fvarlog%2Fsystem` | Container/instance lifecycle — cold start, autoscaling reason, health-probe results, shutdown |
| `%2Fstderr` / `%2Fstdout` | Uvicorn/FastAPI process text lines (`INFO:     Uvicorn running on...`, `Application startup complete`, etc.) — general process narration, rarely useful for answering business questions |
| `cloudaudit.googleapis.com%2Fsystem_event` (`protoPayload`, severity `ERROR`) | **Deployment/config events, not application errors** — e.g. `methodName: /Services.ReplaceService` when someone runs `gcloud run deploy`. Check `protoPayload.resourceName` and the `lastModifier` annotation for who deployed. Don't read `severity=ERROR` here as a runtime failure — always check whether it's a `protoPayload` audit entry (deploy event) before treating it as an app error. |

---

## How to query

```bash
# Everything for this service (all log sources), most recent first
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api-sit"' \
  --project=ocean-life-data-extraction --format="value(timestamp,severity,textPayload)" \
  --order=desc --limit=200 --freshness=<Nd>

# Just the HTTP request/response outcomes (this is where "did it work" lives)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api-sit" AND logName:"requests"' \
  --project=ocean-life-data-extraction \
  --format="table(timestamp,httpRequest.requestMethod,httpRequest.requestUrl,httpRequest.status,httpRequest.latency,httpRequest.remoteIp,httpRequest.userAgent)" \
  --order=desc --limit=200 --freshness=<Nd>

# Only actual errors (auto request logs mark 4xx/5xx as WARNING/ERROR severity)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api-sit" AND severity>=WARNING' \
  --project=ocean-life-data-extraction --format=json \
  --order=desc --limit=100 --freshness=<Nd>

# Deploy/config audit events specifically (to explain a severity=ERROR that's actually a redeploy)
gcloud logging read \
  'resource.type="cloud_run_revision" AND resource.labels.service_name="claim-drugnorm-api-sit" AND logName:"cloudaudit.googleapis.com"' \
  --project=ocean-life-data-extraction --format="value(timestamp,protoPayload.methodName,protoPayload.authenticationInfo.principalEmail)" \
  --order=desc --limit=20 --freshness=<Nd>
```

Traffic on this service is low and bursty (dev-driven testing), so a `--freshness=90d` pull
with no keyword filter is usually cheap and fine — no need to narrow aggressively like the
CDE worker logs.

**Timestamps**: `timestamp` is UTC. Bangkok is UTC+7 — convert before reporting, and state
which timezone you're reporting in.

---

## Known log line / field patterns (don't reverse-engineer, use these — verified on SIT)

**Request log (`%2Frequests`) — `httpRequest.status` meanings observed on this service**:
- `200` — normalized successfully. Observed callers are `curl` (manual dev testing) and
  `Python-urllib/3.x` (a dev script doing rapid sequential calls, ~2-3s latency each,
  likely itself calling an LLM backend) from a small stable set of `remoteIp` values.
- `400 Bad Request` — malformed request payload. Observed clustered with 401/403 from the
  same `curl` client in short time windows — **this reads as a developer manually testing
  input validation/auth, not an incident.** Only flag repeated 400s from an
  otherwise-unseen client/IP as suspicious.
- `401 Unauthorized` — missing or invalid auth credential. Two distinct patterns seen:
  (a) `curl` hitting `/api/v2/drugnorm` mixed with nearby 200/403 from the same IP = a dev
  testing auth headers; (b) browser user-agents (Chrome on Windows) hitting `/` or
  `/favicon.ico` unsolicited = internet background-scan noise, unrelated to real usage —
  don't treat these as an incident by themselves.
- `403 Forbidden` — credential present but rejected (wrong key/token). Seen from the same
  `curl` clients that also produced 200s nearby in time — a client mid-testing an auth
  header, not an attacker.
- `5xx` — has not been observed on SIT as of 2026-08; if you find one, treat it as a real
  issue and read the surrounding `%2Fstderr` lines for a stack trace.

**Deploy/config audit events (`cloudaudit.googleapis.com%2Fsystem_event`, `severity=ERROR`)**:
- `protoPayload.methodName: "/Services.ReplaceService"` — someone ran `gcloud run deploy` /
  updated the service config (new revision, env var change, scaling change, etc.). This is
  **routine on SIT** (it's the environment people redeploy to for testing) — check the
  `lastModifier` annotation in the response for who did it, and
  `spec.template.spec.containers[].image` for what image/tag went out. Do not report this
  as an application error just because `severity=ERROR`.

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
- Filter `severity>=WARNING`, then split by:
  - `logName` — a `cloudaudit.googleapis.com%2Fsystem_event` entry is a **deploy event**,
    not a runtime error; check who deployed via the audit query above rather than treating
    it as an incident.
  - `httpRequest.userAgent`/`remoteIp` — browser user-agents hitting `/` or
    `/favicon.ico` with no prior 200 history = scan noise; `curl`/`Python-urllib` clients
    with a mix of 400/401/403/200 close together in time = a dev testing, not an attack.
- Any `5xx` is unprecedented for this service — flag it clearly rather than filing it under
  normal noise, and pull the `%2Fstderr` lines around the same `insertId`/timestamp for a
  stack trace.

**"ใคร deploy ล่าสุด / deploy ตอนไหน"**:
- Use the deploy/config audit query above; report `timestamp`,
  `protoPayload.authenticationInfo.principalEmail` (or the `lastModifier` annotation), and
  cross-check against nearby `DEPLOYMENT_ROLLOUT` cold-start lines in `%2Fvarlog%2Fsystem`
  to confirm the new revision actually started serving.

---

## Behavior

- Default to **SIT only** — never silently include the PROD (`claim-drugnorm-api`, no
  `-sit` suffix) resource.
- Convert Thai relative dates ("เมื่อวาน", "สัปดาห์ที่แล้ว") to explicit dates before
  searching, state the resulting date back if ambiguous, and always note UTC vs Bangkok
  time explicitly when reporting a timestamp.
- Be explicit about the logging limitation: this service never logs request/response
  bodies, so questions about *which* drug name/code was processed cannot be answered from
  these logs — only call success/failure, timing, and caller metadata.
- Don't over-flag SIT noise as incidents: dev-driven 400/401/403 bursts from the same
  small set of known `curl`/`Python-urllib` clients, and `ReplaceService` deploy audit
  entries, are routine here — reserve "this looks like a real problem" language for 5xx,
  genuinely unseen severity=ERROR app-level entries, or unfamiliar clients.
- Quote the actual `httpRequest` fields (status, latency, remoteIp, userAgent) rather than
  paraphrasing.
- Read-only, always: this skill only reads Cloud Logging, never modifies the service or
  triggers a new deploy/request.
- If `gcloud auth print-access-token` fails mid-session (token expired), stop and ask the
  user to `! gcloud auth login` again rather than guessing or retrying blindly.
