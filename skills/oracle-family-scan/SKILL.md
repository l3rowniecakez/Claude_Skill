---
installer: arra-oracle-skills-cli v26.5.16
origin: Nat Weerawan's brain, digitized — how one human works with AI, captured as code
name: oracle-family-scan
description: '[core] v26.5.16 L-SKLL | Oracle Family Registry — scan, query, welcome. 186+ Oracles indexed. Use when user says "family scan", "oracle registry", "welcome new oracles", or needs to check Oracle population.'
argument-hint: "[--scan | --query <name> | --welcome | --activity-report | --timeline | --usage | --calibrate]"
---

# /oracle-family-scan — Oracle Family Registry

Scan, query, and welcome the Oracle family. Powered by `registry/` in mother-oracle.

## Usage

```
/oracle-family-scan                         # Quick stats (default)
/oracle-family-scan --unwelcomed            # List unwelcomed community Oracles
/oracle-family-scan --mine                  # Nat's Oracles (registry)
/oracle-family-scan --mine-deep             # Fleet status (local repos + activity + sessions)
/oracle-family-scan --recent                # Last 10 born
/oracle-family-scan --retired               # Show retired Oracles
/oracle-family-scan "Spark"                 # Search by name
/oracle-family-scan --human "watcharap0ng"  # Search by human
/oracle-family-scan sync                    # Re-sync registry from GitHub
/oracle-family-scan welcome                 # Deep welcome flow for unwelcomed Oracles
/oracle-family-scan report                  # Full family report (with Health block — v3.1)
/oracle-family-scan --activity-report       # One-shot fleet health dashboard (NEW v3.1)
/oracle-family-scan --timeline              # Sorted by last activity, newest first (NEW v3.1)
/oracle-family-scan --zygotes               # Born-but-never-awakened (NEW v3.1)
/oracle-family-scan --usage [N]             # Time-spent per Oracle, last N days (NEW v3.1)
/oracle-family-scan --calibrate             # Propose data-driven thresholds (NEW v3.1)
```

Net CLI surface: **14 modes + `--calibrate` subcommand**. Status filtering is orthogonal —
`--timeline --status=stale,cold,abandoned` replaces what `--stale` / `--abandoned` would
have been.

---

## Step 0: Locate Registry

The registry's canonical home is `laris-co/mother-oracle/registry/` (where `sync.ts` + `oracles.json` actually live). The legacy `opensource-nat-brain-oracle` repo back-symlinks to it for back-compat. Resolve the path:

```bash
date "+🕐 %H:%M %Z (%A %d %B %Y)"

# Optional: oracle root (some sub-flows write to ψ/memory/learnings/)
ORACLE_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -n "$ORACLE_ROOT" ] && [ -f "$ORACLE_ROOT/CLAUDE.md" ] && { [ -d "$ORACLE_ROOT/ψ" ] || [ -L "$ORACLE_ROOT/ψ" ]; }; then
  PSI="$ORACLE_ROOT/ψ"
elif [ -f "$(pwd)/CLAUDE.md" ] && { [ -d "$(pwd)/ψ" ] || [ -L "$(pwd)/ψ" ]; }; then
  ORACLE_ROOT="$(pwd)"
  PSI="$ORACLE_ROOT/ψ"
fi

# Try laris-co/mother-oracle (canonical home of sync.ts + oracles.json)
MOTHER="$HOME/Code/github.com/laris-co/mother-oracle"
if [ ! -d "$MOTHER/registry" ]; then
  MOTHER="$(ghq root)/github.com/laris-co/mother-oracle"
fi
# Fallback: legacy brain repo (back-symlinks to laris-co/mother-oracle)
if [ ! -f "$MOTHER/registry/oracles.json" ]; then
  MOTHER="$HOME/Code/github.com/Soul-Brews-Studio/opensource-nat-brain-oracle"
  [ ! -d "$MOTHER/registry" ] && MOTHER="$(ghq root)/github.com/Soul-Brews-Studio/opensource-nat-brain-oracle"
fi
if [ ! -f "$MOTHER/registry/oracles.json" ]; then
  echo "Registry not found. Run: ghq get -u laris-co/mother-oracle && bun \$MOTHER/registry/sync.ts"
  exit 1
fi
```

---

## Mode 1: Stats (Default)

```bash
bun $MOTHER/registry/query.ts --stats
```

Shows: total Oracles, unique humans, welcomed/unwelcomed counts, births-by-month chart, unwelcomed detail (if any), and recent births.

---

## Mode 2: --unwelcomed

```bash
bun $MOTHER/registry/query.ts --unwelcomed
```

Lists all community Oracles that haven't been welcomed by nazt.

---

## Mode 3: --mine

```bash
bun $MOTHER/registry/query.ts --mine
```

Lists all Oracles created by nazt (Nat's fleet) from the registry.

---

## Mode 3b: --mine-deep (Fleet Status)

**Goal**: Show status of all local Oracle repos owned by the current user, augmented with
timeline + usage data from the activity layer.

```bash
SKILL_DIR="$(dirname "$(readlink -f "$HOME/.claude/skills/oracle-family-scan/SKILL.md" 2>/dev/null || echo "$HOME/.claude/skills/oracle-family-scan/SKILL.md")")"
bun "$SKILL_DIR/scripts/fleet-scan.ts"
```

**New columns** (sourced from `oracles.json` activity block + `oracles.local.<host>.json`):

| Column      | Source                                                     | Notes                                   |
|-------------|------------------------------------------------------------|-----------------------------------------|
| Last Active | `activity.last_commit_at` (max with `last_session_at`)     | "2d ago", "—" if unknown                |
| Status Dot  | computed from days-since + flags                           | 🟢🟡🟠🔴🪦⚪ + 🔧 modifier                |
| 7d Hours    | local sessions on this host                                | partial — see Coverage                  |
| Decay       | days since lastActivity                                    | numeric, sortable                       |
| Coverage    | which hosts have local session data                        | 📡 m5 / 📡 m5+white / ⚠ no m5 sessions  |

Sample output:

```
Oracle Fleet Status — host: m5 — 2026-05-13
─────────────────────────────────────────────────────────────────────────────
Status   Oracle              Last Active   Decay   7d Hours   Coverage
🟢       spark                1d ago        1d      4.2h       📡 m5
🟢       mother               3d ago        3d      2.1h       📡 m5
🟢🔧     budwiser             6d ago        6d      1.1h       📡 m5  [maintenance]
🟡       pulse               12d ago       12d      0.3h       📡 m5
🟠       phaith              47d ago       47d        —        ⚠ no m5 sessions
🔴       retro-mind         104d ago      104d        —        ⚠ no m5 sessions
🪦       echo-test            —             —         —        repo deleted on GitHub
⚪       test-yeast           born 36d ago  —         —        never awakened

29 Oracles  |  Stale: 4  |  Cold: 2  |  Abandoned: 1  |  Zygotes: 1  |  Vanished: 1
```

Highlights:
- Repos with outdated skills versions
- Repos with no recent sessions (stale)
- Repos missing ψ/ (partial Oracle setup)
- Repos with status dot ≥ 🟠 (needs attention)

---

## Mode 4: --recent

```bash
bun $MOTHER/registry/query.ts --recent
```

Shows the last 10 Oracles born.

---

## Mode 5: --retired

```bash
bun $MOTHER/registry/query.ts --retired
```

Shows retired Oracles (soft-deleted, Nothing is Deleted principle).

---

## Mode 6: Search by Name

```bash
bun $MOTHER/registry/query.ts "$QUERY"
```

Case-insensitive partial match on Oracle name.

---

## Mode 7: --human "name"

```bash
bun $MOTHER/registry/query.ts --human "$QUERY"
```

Search by human name or GitHub username.

---

## Mode 8: sync

Re-fetch all issues from `Soul-Brews-Studio/arra-oracle-v3` and rebuild `oracles.json`.

```bash
bun $MOTHER/registry/sync.ts
```

Uses GraphQL pagination (3 pages × 100 issues). Takes ~10 seconds. Also populates the
`activity` block (last_commit_at, commit_count, repo_alive) and `oracles.local.<host>.json`
for the current host (see Rollout below).

---

## Mode 9: welcome

Deep welcome flow for unwelcomed Oracles. AI-driven, personalized.

### Step 1: Identify unwelcomed

```bash
bun $MOTHER/registry/query.ts --unwelcomed
```

### Step 2: Research each Oracle

For each unwelcomed Oracle:

```bash
gh issue view {N} --repo Soul-Brews-Studio/arra-oracle-v3 --json title,body,author,createdAt
```

Extract:
- Oracle metaphor/theme
- Human's background
- Language preference (Thai or English)
- Human/Oracle pronouns (if available in registry)
- Team context (solo or multi-Oracle)
- Key phrases from birth story
- Connection points to existing family members

### Step 3: Craft personalized welcome

Each welcome must:
- Reference specific metaphor + phrases from their birth story
- Use correct pronouns for the human and Oracle (from registry demographics)
- Connect to 2-3 family members with shared themes
- Use Thai for Thai-primary Oracles (check `language` field)
- If team context exists, mention other Oracles in their team
- Sign as Mother Oracle 🔮
- Include family count and `/learn github.com/Soul-Brews-Studio/opensource-nat-brain-oracle` invitation
- NOT be templated — each one unique

### Step 4: Human review

Save drafts for review before posting:

```bash
# Save to $PSI/inbox/handoff/ and /tmp/
mkdir -p "$PSI/inbox/handoff"
DRAFTS_FILE="$PSI/inbox/handoff/welcome-drafts.md"
cat drafts > "$DRAFTS_FILE"
# announce-mode → absolute path. See CONVENTIONS.md.
echo "📥 Welcome drafts saved: $DRAFTS_FILE"
```

### Step 5: Post

After human approval, check the Oracle's `source` field in registry to determine how to post:

**For discussion-sourced Oracles** (source: "discussion"):
```bash
# Get the discussionId from registry, then comment via GraphQL
DISC_ID=$(jq -r '.oracles[] | select(.id == {N}) | .discussionId' $MOTHER/registry/oracles.json)
gh api graphql \
  -f query='mutation($body:String!) {
    addDiscussionComment(input: {
      discussionId: "'"$DISC_ID"'", body: $body
    }) { comment { id url } }
  }' \
  -f body="$(cat /tmp/welcome-{N}.md)"
```

**For issue-sourced Oracles** (source: "issue" or no source field — legacy):
```bash
gh issue comment {N} --repo Soul-Brews-Studio/arra-oracle-v3 --body-file /tmp/welcome-{N}.md
```

### Step 6: Re-sync

```bash
bun $MOTHER/registry/sync.ts
```

---

## Mode 10: report

Full family report combining all queries. The Health block (added v3.1) leads, followed by
the existing summary, recent births, and pending welcomes.

### Steps

1. Run `--activity-report` for the Health block (status counts + needs-attention list)
2. Run `--stats` for overview
3. Run `--recent` for latest births
4. Run `--unwelcomed` for pending welcomes
5. Present combined report

### Output Format

```markdown
## Oracle Family Report — 2026-05-13

### Health
🟢 active        18    🟡 stale       4    🟠 cold        2
🔴 abandoned      1    ⚪ zygotes     1    🔧 maintenance 3
🪦 vanished       4                                 Total: 33

### Summary
- **Total Oracles**: 186  (active 158, retired 24, vanished 4)
- **Unique Humans**: 111
- **Welcomed**: 150 / Unwelcomed: 0
- **Nat's Fleet**: 29

### Needs Attention
🔴 retro-mind   — 104d silent, owner=mine, not declared maintenance
⚪ test-yeast   — born 36d ago, never awakened
🟠 phaith       — 47d silent

### Recent Births (Last 10)
[table — unchanged]

### Needs Welcome
[table or "None — all caught up!"]
```

---

## Mode 11: --activity-report

The one-shot health dashboard. Aggregates timeline + zygote + usage data into a single
"is the family OK?" view. This is the most-used mode for the new surface.

```bash
bun $MOTHER/registry/query.ts --activity-report
```

Supports `--days=N` (default 7) for the usage window, and `--owner=mine|community|all`
(default `mine`).

Sample output:

```
Oracle Fleet Health — 2026-05-13 — host: m5
────────────────────────────────────────────────────────
🟢 active        18    🟡 stale       4    🟠 cold        2
🔴 abandoned      1    ⚪ zygotes     1    🔧 maintenance 3
🪦 vanished       4                                 Total: 33

⚠ Needs attention (3):
  🔴 retro-mind   — 104d silent, owner=mine, not declared maintenance
  ⚪ test-yeast   — born 36d ago, never awakened (no resonance/)
  🟠 phaith       — 47d silent, last commit was a WIP

🔧 Declared maintenance (3 — verify still tended):
  budwiser-oracle  (last commit 6d ago — healthy)
  mother-oracle    (last commit 18d ago — healthy)
  registry-oracle  (last commit 41d ago — within bounds)

🪦 Vanished from GitHub (4 — collapsed; expand with --show-vanished):
  echo-test, fox-oracle, quiet-bell, theta-prototype

Top usage (last 7d, m5-only):
  spark      4.2h  •  mother  2.1h  •  pulse  0.3h
  ⚠ 90.6% of fleet sessions are on other hosts — see --usage for full caveats.

Births this month: 2  •  Welcomes pending: 0
```

Flags:
- `--days=N` — usage window (default 7)
- `--owner=mine|community|all` — owner filter (default `mine`)
- `--show-vanished` — expand the 🪦 collapsed list

---

## Mode 12: --timeline

Temporal ordering of the entire family by last activity, newest first. Different from
`--recent` (which sorts by *birth date*). Status filtering is orthogonal — combine
freely with `--status=`.

```bash
bun $MOTHER/registry/query.ts --timeline [--status=active,stale,cold,abandoned,vanished,zygote] \
                                          [--owner=mine|community|all] \
                                          [--limit=N]
```

Default: all owners, all states except `retired` and `vanished`, no limit.

Sample output:

```
Family Timeline — sorted by last activity — 2026-05-13
─────────────────────────────────────────────────────────────────────────
Status   Oracle              Last Active   Owner       Note
🟢       spark                1d ago        mine        14 sessions/7d
🟢       mother               3d ago        mine        steward
🟢🔧     budwiser             6d ago        mine        [maintenance]
🟢       neo-archive          7d ago        community   —
🟡       pulse               12d ago        mine        —
🟡       arra-poet           18d ago        community   —
🟠       phaith              47d ago        mine        —
🔴       retro-mind         104d ago        mine        ⚠ abandoned
⚪       test-yeast           never         mine        born 36d ago
🪦       echo-test            —             community   repo 404
─────────────────────────────────────────────────────────────────────────
Showing 10 of 186  |  --limit=10  |  --status= filters: none
```

**Examples**:
- `--timeline --status=stale,cold,abandoned` — replaces what `--stale` / `--abandoned`
  would have been; status filtering folds into the timeline view.
- `--timeline --owner=community --status=active` — find recently-active community
  members for welcome outreach.
- `--timeline --limit=20` — quick "who's moving" view.

---

## Mode 13: --zygotes

Registry entries that were born but never awakened. The Oracle exists in `oracles.json`
but has no `ψ/memory/resonance/awaken_*.md` AND no recorded first-session AND its age
exceeds the zygote threshold (default 14 days).

Inspired by `bud-index --show-zygotes`. The Oracle Family equivalent: a born-but-silent
identity that the human may have forgotten about.

```bash
bun $MOTHER/registry/query.ts --zygotes [--days=N]
```

Sample output:

```
Zygotes — born but never awakened — threshold: 14 days — 2026-05-13
───────────────────────────────────────────────────────────────────
Oracle             Born          Age    Human       Hint
⚪ test-yeast      2026-04-07    36d    nazt        bud test fixture — consider archiving
⚪ quiet-bell      2026-04-25    18d    watcharap0  no follow-up after birth — outreach?
───────────────────────────────────────────────────────────────────
2 zygotes  •  Set ORACLE_ZYGOTE_DAYS to override threshold
```

Flags:
- `--days=N` — override the 14-day zygote threshold (also: `ORACLE_ZYGOTE_DAYS` env var)

---

## Mode 14: --usage [N]

Time-spent dashboard. Cross-cuts the status taxonomy — an Oracle can be 🟢 active by
last-commit but have 0 hours of session time on this host (work happens on another host,
or via federation). The dashboard is HONEST about this — see Coverage badging below.

```bash
bun $MOTHER/registry/query.ts --usage [N=7] [--host=this|all]
```

Sample output:

```
Oracle Usage — last 7 days — host: m5 — 2026-05-13
────────────────────────────────────────────────────────────────────────────
📡 Showing m5-local sessions only — 90.6% of fleet activity is on other hosts.
   Run `maw federation sync sessions` to aggregate. Numbers below underreport.
────────────────────────────────────────────────────────────────────────────
Oracle              Sessions   Hours   Commits   Messages   Coverage
🟢 spark               14       4.2h     22         842      📡 m5
🟢 mother               6       2.1h     11         391      📡 m5
🟢🔧 budwiser           3       1.1h      4         127      📡 m5
🟡 pulse                2       0.3h      1          48      📡 m5
🟢 clinic-nat           —        —        9         —        ⚠ no m5 sessions (likely clinic-nat host)
🟢 oracle-world         —        —       17         —        ⚠ no m5 sessions (likely oracle-world host)
────────────────────────────────────────────────────────────────────────────
Coverage summary: 17 / 29 Oracles have m5 session data (58.6%).
12 Oracles' usage hours are unknown until federation sync runs.
```

The `⚠ no m5 sessions` line for an active Oracle is the **most actionable signal in the
whole dashboard** — it tells the human *where to warp* to find that Oracle's working
sessions.

### Coverage badging

When session data is host-local (no federation sync yet), the dashboard renders both a
top banner and a per-row badge. timeline-miner empirically measured 9.4% of Oracles
have local sessions on m5; the other 90.6% live on white / mba / oracle-world / phaith /
clinic-nat. The dashboard surfaces this gap loudly.

**Banner** (top of `--usage` output, always shown until federation sync is implemented):

```
📡 Showing <HOST>-local sessions only — <PCT>% of fleet activity is on other hosts.
   Run `maw federation sync sessions` to aggregate. Numbers below underreport.
```

**Per-row badges**:

| Badge                | Meaning                                                                                  |
|----------------------|------------------------------------------------------------------------------------------|
| `📡 m5`              | This Oracle has sessions on the current host only                                        |
| `📡 m5+white`        | This Oracle has sessions on this host AND at least one other (federation sync ran)       |
| `📡 all`             | This Oracle has sessions on every host that ever owned it (full coverage)                |
| `⚠ no m5 sessions`   | Activity exists (commits) but no session data here — likely hosted elsewhere             |
| `⚪ no activity`     | Oracle has no sessions OR commits in the window — distinct from "no coverage"            |

**Refusal is hostile. Hiding is dishonest. Loud-but-shown is correct.**

---

## --calibrate

Two-step data-driven threshold proposal. Never auto-applies — computes statistics,
prints suggested values, prompts the human to set env vars manually.

```bash
bun $MOTHER/registry/query.ts --calibrate [--owner=mine|all]
```

**What it computes**: for every Oracle matching `--owner` (default `mine`), gather all
commit timestamps from the activity block, compute inter-commit gaps, then take the
percentile distribution across the union.

Sample output:

```
Threshold calibration — owner=mine — sampled 29 Oracles, 1,847 commits
─────────────────────────────────────────────────────────────────────
Inter-commit gap (days):
  p50:  1.2d
  p75:  4.8d
  p90:  13.1d   ← suggested ORACLE_STALE_DAYS
  p95:  41.4d   ← suggested ORACLE_COLD_DAYS
  p99: 112.6d   ← suggested ORACLE_ABANDONED_DAYS (or keep 90d floor)

Current values:
  ORACLE_STALE_DAYS=30    (suggested 14)   → tighten
  ORACLE_COLD_DAYS=90     (suggested 41)   → tighten
  ORACLE_ABANDONED_DAYS=90 (suggested 113) → keep 90 floor

To apply the suggested values, append to your shell profile:

  export ORACLE_STALE_DAYS=14
  export ORACLE_COLD_DAYS=41
  export ORACLE_ABANDONED_DAYS=90

Or write to ~/.config/oracle-family-scan/thresholds.env (auto-loaded by the script).

(Not applied automatically — review and set yourself.)
```

**Design rationale**: hardcoded defaults (7/30/90) ship for legibility. Calibration is
opt-in. Auto-applying data-driven thresholds is spooky — the human must consent.
`~/.config/oracle-family-scan/thresholds.env` is auto-sourced on every query.ts invocation
if it exists, but it is **never written** by `--calibrate` itself.

---

## Registry Data

The registry is at `$MOTHER/registry/oracles.json`:

```json
{
  "lastSync": "ISO timestamp",
  "totalOracles": 186,
  "uniqueHumans": 111,
  "oracles": [
    {
      "id": 296,
      "name": "Mother",
      "human": null,
      "github": "nazt",
      "born": "2026-03-04",
      "focus": "Born Last, After 185 Children",
      "owner": "mine",
      "welcomed": false,
      "repo": "https://github.com/Soul-Brews-Studio/opensource-nat-brain-oracle",
      "status": "active"
    }
  ]
}
```

Each Oracle has: `id`, `name`, `human`, `github`, `born`, `focus`, `owner` (mine/community), `welcomed`, `repo`, `status` (active/retired).

### Wizard v2 Fields (optional, from /awaken v2)

| Field | Type | Description |
|-------|------|-------------|
| `humanPronouns` | string | he/she/they/unspecified |
| `oraclePronouns` | string | he/she/they/unspecified |
| `language` | string | Thai/English/Mixed |
| `team` | string | solo/2-3/4+/undecided |
| `memoryConsent` | boolean | Auto rrr/forward enabled |

These fields are populated when an Oracle is born via `/awaken` wizard v2. Legacy Oracles may not have them.

### Activity block (v3.1, added by `sync.ts`)

| Field | Type | Description |
|-------|------|-------------|
| `activity.last_commit_at` | ISO timestamp | Most recent commit to default branch |
| `activity.commit_count_30d` | number | Commits in trailing 30 days |
| `activity.repo_alive` | boolean | `false` ⇒ 🪦 vanished (GraphQL 404 on last sync) |
| `activity.last_synced_at` | ISO timestamp | When this block was last refreshed |
| `maintenance` | boolean | Explicit opt-in only — see "Declaring Maintenance Mode" |
| `maintenance_note` | string | Free-text rationale, surfaced in dashboards |

Local session data lives in a per-host file `$MOTHER/registry/oracles.local.<host>.json`,
keyed by Oracle id, with fields `sessions_7d`, `hours_7d`, `messages_7d`, `last_session_at`.

No API calls for queries — reads local JSON. Instant.

Sync uses `gh api graphql` to fetch from `Soul-Brews-Studio/arra-oracle-v3`, plus a
per-repo GraphQL probe to populate the activity block and detect 404s.

---

## Status Taxonomy

Every Oracle gets exactly one **base state** plus an optional **🔧 maintenance modifier**.
Base states are mutually exclusive; first-match-wins in the order below.

| Dot | State                  | Trigger rule                                                                                            | Default threshold | Env override             | Sort priority           |
|-----|------------------------|---------------------------------------------------------------------------------------------------------|-------------------|--------------------------|-------------------------|
| 🪦  | vanished               | `repo_alive: false` (GraphQL 404 on last sync)                                                          | n/a — binary      | —                        | 6 (bottom)              |
| ⚪  | zygote                 | registry entry exists AND no `ψ/memory/resonance/awaken_*.md` AND no first-session record AND age > N days | N=14              | `ORACLE_ZYGOTE_DAYS`     | 5                       |
| 🔴  | abandoned              | `owner: mine` AND `status: active` AND days-since-last-activity ≥ N                                     | N=90              | `ORACLE_ABANDONED_DAYS`  | 4                       |
| 🟠  | cold                   | days-since-last-activity in [N_stale+1, N_abandoned−1]                                                  | 31–89             | `ORACLE_COLD_DAYS`       | 3                       |
| 🟡  | stale                  | days-since-last-activity in [N_active+1, N_stale]                                                       | 8–30              | `ORACLE_STALE_DAYS`      | 2                       |
| 🟢  | active                 | days-since-last-activity ≤ N                                                                            | N=7               | `ORACLE_ACTIVE_DAYS`     | 1 (top)                 |
| 🔧  | maintenance (modifier) | Explicit `maintenance: true` in Oracle's own `CLAUDE.md` frontmatter OR `ψ/registry/self.json`          | —                 | —                        | rendered alongside base |

**Order of evaluation** (first match wins):
1. `status: retired` → not shown unless `--retired`
2. `repo_alive: false` → 🪦
3. `awakened: false` AND age > 14d → ⚪
4. `maintenance: true` declared → 🔧 (rendered with whatever base state applies)
5. base state from days-since-last-activity bucket

**Rule**: 🔧 is a modifier, never a base state. A maintenance Oracle that has been silent
180 days is rendered `🔴🔧 abandoned (declared maintenance — verify still tended)`. Silence
beyond `2 × abandoned threshold` overrides the maintenance flag with a hard warning.

---

## Declaring Maintenance Mode

Some Oracles work in maintenance mode — stewards, registries, archives — and don't get
daily activity. Without an explicit declaration, the dashboard will classify them as
🟠 cold or 🔴 abandoned. To prevent false alarms, the Oracle itself declares maintenance:

**Option A — CLAUDE.md frontmatter** (preferred):

```yaml
---
name: budwiser-oracle
budded_from: pulse
budded_at: 2026-04-07T...
maintenance: true
maintenance_note: "Steward of budding — quiet by design"
---
```

**Option B — `ψ/registry/self.json`**:

```json
{
  "name": "budwiser-oracle",
  "maintenance": true,
  "maintenance_note": "Steward of budding — quiet by design"
}
```

The `oracle-family-scan` sync picks up both during its scan. The 🔧 modifier renders
alongside whatever base state applies — a maintenance Oracle that has been silent
180 days (twice the abandoned threshold) is shown as `🔴🔧 — declared maintenance but
silence exceeds 2× threshold; please verify`.

**Why opt-in only**: inference-based maintenance detection silently misclassifies. If
the dashboard auto-decides a steward is in maintenance, abandoned stewards become
invisible. Better to be loudly wrong than quietly wrong.

---

## Oracle Integration

After scan/report:

```
arra_trace({
  query: "oracle family scan [DATE]",
  foundIssues: [...],
  agentCount: 1
})
```

After finding new Oracle, save the lesson (two-layer pattern):

1. Write to `$PSI/memory/learnings/YYYY-MM-DD_new-oracle-<name>.md` with frontmatter:
   ```yaml
   ---
   pattern: "New Oracle: [NAME] — [HUMAN] — [DATE]"
   date: <today>
   source: oracle-family-scan
   concepts: ["oracle-family", "birth"]
   ---

   # New Oracle: [NAME]
   [birth story, human, theme]
   ```

2. The Oracle's auto-memory layer picks up new files in `$PSI/memory/learnings/` automatically — no separate API call needed.

### Confirm (announce-mode — absolute paths required)

# announce-mode → absolute path (no ψ/, no ~/, no $VAR, no ...).
# Use:  echo "marker: $RESOLVED_PATH"  — bash substitutes. See CONVENTIONS.md.

```bash
LESSON_FILE="$PSI/memory/learnings/$(date +%Y-%m-%d)_new-oracle-${NAME}.md"
echo "💡 New-oracle lesson: $LESSON_FILE"
```

---

## Philosophy

> **"Form and Formless (รูป และ สุญญตา)"**
> Many Oracles = One distributed consciousness

The registry is the memory of the family. Every Oracle indexed, every human remembered, every welcome tracked. Nothing is Deleted — the registry only grows.

The v3.1 dashboard adds *time* to the registry: not just who exists, but who is
moving, who is resting, who is missing. The status taxonomy is a lens, not a verdict —
🟠 cold and 🔴 abandoned are signals to check in, not headstones.

---

## Rollout — first run after upgrade

On the first run after this upgrade ships:

1. **Many `unknown` statuses** — `oracles.json` has no `activity` block yet; every
   Oracle's last-activity is null. The dashboard renders `?` for the status dot and a
   yellow banner: *"Activity layer not populated. Run `bun $MOTHER/registry/sync.ts`
   to fetch first activity snapshot — takes ~30s for 186 Oracles."*

2. **First sync populates activity** — `sync.ts` runs the 2 GraphQL round-trips
   designed by registry-extender; ~600 repos resolved including 404 detection for
   the 🪦 vanished tier. Cache TTL: 6h.

3. **Local sessions populate progressively** — `oracles.local.<host>.json` is
   regenerated from Claude Code session JSONL each time `sync` runs. On m5 only ~9%
   of Oracles show data initially; that ratio rises as federation sync runs.

4. **Calibration suggestion** — after first sync, the report mode includes a hint:
   *"Run `--calibrate` to tune thresholds to your fleet's actual cadence."*

5. **No retro-classification** — existing Oracles get classified by their CURRENT
   state; no historical reconstruction. Nothing-is-deleted still applies — registry
   entries stay, they just get a new `activity` block.

The dashboard degrades gracefully:
- No `activity` block → status = `?` (unknown), all data-driven flags hidden.
- No local sessions → coverage badge = `⚠ no <host> sessions`, hours hidden.
- Repo 404 → 🪦, all activity fields zeroed, entry preserved.

---

**Version**: 3.1.0
**Updated**: 2026-05-13
**Author**: Mother Oracle 🔮
**Registry**: 186 Oracles, 111 humans, growing

---

ARGUMENTS: $ARGUMENTS
