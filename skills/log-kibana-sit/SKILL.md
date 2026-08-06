---
name: log-kibana-sit
description: "Investigate and answer questions using the SIT environment's Kibana logs. Use when user says '/log-kibana-sit', asks to check Kibana log on SIT, or needs to find/verify something (task status, ESB errors, whether a schedule ran, whether a user did X) from SIT application logs."
installer: create-shortcut
created_at: 2026-08-06T08:12:34+07:00
---

# /log-kibana-sit — SIT Kibana Log Investigator

Ready-to-use investigator for the SIT environment's Kibana logs. When this skill is
invoked, you are immediately equipped to search and answer questions from SIT logs — the
query mechanism is already known, don't re-discover or explain it, just query. Credentials
are handled per Step 1 below (never hardcoded in this file, since it's mirrored to a
public repo).

---

## Step 0: Init

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"
```

---

## Step 1: Credentials (first invocation only, then never again)

This skill needs Basic Auth credentials for the Kibana instance below. **Never hardcode
them in this file.**

1. Check for a previously-saved reference memory holding these credentials (e.g. a memory
   named along the lines of `reference-kibana-sit-credentials`). If found, use it — skip
   straight to querying, don't ask the user anything.
2. If no such memory exists (this is the first time this skill has ever been invoked),
   ask the user for the Kibana username and password.
3. Verify what they gave you before trusting it:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" -u '<user>:<pass>' "http://kibana.thaisamut.co.th/s/sit/api/status"
   ```
   A `200` confirms it works. If it fails (non-200), tell the user and ask again — do not
   save invalid credentials, and do not proceed to query with them.
4. Once verified, save them as a reference-type memory per this project's memory-saving
   convention, so no future invocation of this skill (this session or any later one) ever
   asks again.
5. From then on, every future run of this skill just uses the saved memory silently.

---

## Access

- Kibana instance (SIT space): `http://kibana.thaisamut.co.th/s/sit`
- Auth: HTTP Basic Auth — credentials per Step 1 above (a read-only log viewer account,
  low privilege)
- Sanity check: `curl -s -u '<user>:<pass>' "http://kibana.thaisamut.co.th/s/sit/api/status"`
- Kibana version at last check: 7.17.8

---

## How to query (do this, not the obvious REST endpoints)

The Logs-app's own REST endpoints **do not work** with this account/setup — don't waste
time on them:
- `/api/log_entries/entries`, `/api/infra/log_entries/entries` → 404
- `/api/console/proxy` → 403 Forbidden (no Dev Tools console-proxy privilege)

**What works**: Kibana's internal search API (the same one Discover/Logs UI uses under
the hood):

```bash
curl -s -u '<user>:<pass>' -X POST "http://kibana.thaisamut.co.th/s/sit/internal/search/es" \
  -H "kbn-xsrf: true" -H "Content-Type: application/json" \
  -d '{
    "params": {
      "index": "filebeat-sit*,fb-sit*",
      "body": {
        "size": 100,
        "query": {
          "bool": {
            "filter": [
              {"range": {"@timestamp": {"gte": "<ISO8601-utc>", "lte": "<ISO8601-utc>"}}}
            ],
            "should": [
              {"match_phrase": {"message": "<search term>"}}
            ],
            "minimum_should_match": 1
          }
        },
        "sort": [{"@timestamp": {"order": "asc"}}],
        "_source": ["@timestamp", "message"]
      }
    }
  }'
```

Parse results at `.rawResponse.hits.hits[]._source`. Sort `asc` for reading a timeline in
order, `desc` (with small `size`) for "what's the latest thing that happened".

**Index pattern**: `filebeat-sit*,fb-sit*` (underlying Kibana source config is named
"LOG SIT"; field mapping: `container` → `container.id`, `message` → `["message",
"@message"]`, `timestamp` → `@timestamp`).

**Timezone**: query timestamps must be UTC ISO8601. Bangkok is UTC+7 — convert before
querying (e.g. 20:30 Bangkok = 13:30 UTC same day). Always report findings back in
Bangkok local time (as shown inside the log `message` string itself, which is already
Bangkok time) and say so explicitly, since the `@timestamp` field and the in-message
timestamp differ by the UTC offset.

**Scoping to one application's own log lines**: this index carries logs from many
unrelated services (Kong gateway, Java "algebra7" services, SFTP pollers, etc.) — a bare
keyword search will drown in noise. Add a `log.file.path` filter. Known app log paths:

- ClaimAutomation (CAM): `/usr/local/claimautomation/logs/server.log` (host `Jeff`, not
  containerized — filebeat reads the file directly, not via Docker)

If investigating an app whose log path isn't listed above, find it first: search a
distinctive keyword from that app without the path filter, inspect one hit's full
`_source` (not just `message`) to read its `log.file.path`, then reuse that path filter
for everything else in the investigation.

---

## Investigation patterns

**Tracing one async task's full lifecycle**: first find its creation/"type:" line to get
the task_id (usually a uuid), then search for occurrences of that uuid across a *wide*
time window (don't assume a task finished just because there's no more activity in the
next few minutes — task lifecycles can span tens of minutes to hours). Read the
lifecycle in order: created → started → processing steps → completed/error.

**ESB SOAP send failures**: the generic `ERROR ... Failed to send X to ESB: HTTP 500:
Server Error` line does NOT contain the real reason. The actual SOAP Fault detail
(faultstring, e.g. a DB constraint violation message) is in the **WARNING**-level line
right before it, from `esb_soap_client._send_soap_request:536` (`HTTP {status}:
{response.text[:200]}...`) — always fetch and quote that line, not just the ERROR line.

**"Is anyone using the system right now"**: check the single most recent log line for
that app's `log.file.path` (sort `desc`, size 1-5, no time filter) and compare its
timestamp to now — a large gap means idle.

**Counting how many times a specific action happened**: search for the exact log line
that fires once per action (e.g. the route's "Starting ..." log line), not for a task
type that might also cover other trigger sources (scheduled jobs, other buttons) — cross-
check by reading a few of the returned hits' surrounding context if the count seems
surprising.

---

## Behavior

- Don't ask the user for credentials or explain the connection mechanism — just query.
- If the user hasn't asked something specific yet, ask what they want to know (a time
  window, a task/user/error to look for) rather than guessing.
- Convert relative Thai time references ("เที่ยง" noon, "เมื่อคืน" last night, "2
  ทุ่มครึ่ง" 8:30pm) to explicit UTC ranges before querying; if the mapping is at all
  ambiguous, state the resulting Bangkok-time window back to the user for confirmation.
- Report findings with exact timestamps and quote the relevant raw log line(s) rather
  than paraphrasing vaguely — task ids, error codes, and fault strings are usually
  exactly what's needed.
- Read-only, always: this skill only searches/reads logs, never writes to or modifies
  anything in Kibana or the systems being logged.
