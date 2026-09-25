---
name: recap
description: 'กลับมาทำงานต่อจากที่ /forward บันทึกไว้ — แสดงงานค้างทุกสายงาน (grouplife ประกันกลุ่ม / cde / cam / bot) จาก ~/ψ/inbox/handoff, verify สถานะจริง (git branch, Redmine status) แล้วให้เลือกงานที่จะทำต่อ; /recap <RM> โหลดงานนั้นเต็มๆ. Also session orientation (--now, --quick). Use when starting a session, "recap", "ทำอะไรค้างไว้", "งานค้าง", "where are we", "status". Do NOT trigger for "standup" (use /standup) or "dig"/"past sessions" (use /dig).'
argument-hint: "[RM|key | --stream S | --all | --now | --quick]"
trigger: /recap
---

# /recap — Session Orientation & Awareness

> Ocean version (2026-09-25): โหมด default เปลี่ยนเป็น **Handoff Mode** ใช้คู่กับ /forward (ต้องติดตั้ง skill forward ด้วย). โหมด --now / --quick / Rich เดิมยังใช้ได้ (อยู่ด้านล่าง)
> ตอบเป็นภาษาไทยเสมอ

## HANDOFF MODE (default)

```
/recap                 # งานค้างทุกสายงาน → verify → ถามว่าจะทำอันไหนต่อ
/recap 12345          # โหลด handoff ล่าสุดของ RM #12345 เต็มๆ แล้วเริ่มทำต่อ
/recap --stream cde    # เฉพาะสายงาน (grouplife | cde | cam | bot | other)
/recap --all           # รวมงานที่ closed/superseded/legacy เก่า
/recap --rich          # โหมด Rich เดิม (recap-rich.ts, ψ ของ repo)
```

Vault: `$HOME/ψ/inbox/handoff/` (ตายตัว ไม่ขึ้นกับ cwd) — script กลาง:
`python3 ~/.claude/skills/forward/scripts/handoffs.py`

### A. `/recap` (ไม่มี argument)

1. **1 bash call**:
   ```bash
   H=~/.claude/skills/forward/scripts/handoffs.py
   python3 $H list            # (+ --stream S / --all ตาม argument)
   ```
2. Verify งาน **ที่อายุ ≤ 7 วัน หรือ status=open** (สูงสุด ~6 งาน) ใน bash call เดียว:
   ```bash
   for k in rm12345 rm23456; do python3 $H verify $k; done
   ```
   (`verify` = git branch/uncommitted/ahead ของ repo ใน frontmatter + สถานะ Redmine ผ่าน API)
3. แสดงผลเป็นตารางจัดกลุ่มตาม stream:
   ```
   ## 📋 งานค้าง (จาก /forward)
   ### grouplife
   | RM | งาน | status | อายุ | Redmine | git | next |
   |---|---|---|---|---|---|---|
   | #12345 | แก้ไขการนำเข้าไฟล์ OGL_App | open | 3d | In Progress | ticket/44 (3 uncommitted) | ถามผลทดสอบ Phase 3 |
   ```
   - `legacy` = handoff รุ่นเก่าไม่มี frontmatter (stream เดาจาก keyword) → ใส่ ⚠️ unverified ถ้า verify ไม่ได้
   - Redmine = Closed/Resolved แต่ handoff ยัง open → ขึ้นเตือน "น่าจะปิดได้" + เสนอ `handoffs.py close <key>` (**ถามก่อน** ไม่ปิดเอง)
   - branch ไม่ตรงกับ handoff / repo path หาย → เตือน
4. ปิดท้ายด้วยคำถาม (AskUserQuestion ถ้างาน ≤ 4, ไม่งั้นให้พิมพ์เลข RM): "จะทำงานไหนต่อ?"
   แล้วทำขั้นตอน B กับงานที่เลือก

### B. `/recap <RM|key>` — โหลดงานเดียว

1. `python3 $H show <key>` → Read ไฟล์ handoff นั้นทั้งไฟล์ (+ `history <key>` ถ้าต้องดูย้อนหลัง)
2. `python3 $H verify <key>` + ตรวจ pending แต่ละข้อกับของจริงตาม "Verify Before Reporting" ด้านล่าง
   (เช่น FormEdit.txt มี phase นั้นแล้วหรือยัง, SQL script รันแล้วหรือยัง, commit อยู่บน origin หรือยัง, deploy revision)
3. โหลด memory ที่ handoff อ้างถึงใน "Rules / Gotchas" (อ่านไฟล์ memory นั้น) — ต้องทำตามกฎนั้นตลอดงาน
4. แสดง:
   ```
   ## ▶ ทำต่อ: RM #12345 — <title>  (stream: grouplife)
   📡 Session เดิม: <uuid8> — `claude --resume <uuid>` ถ้าต้องการ context เต็ม
   **ทำไปแล้ว**: 2-4 บรรทัด
   **สถานะจริงตอนนี้**: git / Redmine / env
   | Pending | handoff บอก | ของจริง |
   **ขั้นต่อไป**: (จาก Next Session ข้อแรก)
   ⚠️ กฎของงานนี้: ...
   ```
5. **หยุดถาม** ก่อนลงมือ — การ /recap ไม่ใช่การอนุมัติให้เขียนโค้ด/commit/deploy
   (งาน grouplife ต้องได้คำว่า "เริ่ม" ต่อ phase ตามกฎ phase-by-phase approval ถ้ามี)

### เมื่องานจบระหว่าง session

บอกผู้ใช้ว่ารัน `/forward --close <key>` ได้ (หรือถามแล้วรัน `handoffs.py close <key>` ให้)

---

**Goal**: Orient yourself fast. Rich context by default. Mid-session awareness with `--now`.

## Usage

```
/recap --rich    # Rich: retro summary, handoff, tracks, git (ψ ของ repo)
/recap --quick   # Minimal: git + focus only, no file reads
/recap --now     # Mid-session: timeline + jumps from AI memory
/recap --now deep # Mid-session: + handoff + tracks + connections
```

---

## RICH MODE (`/recap --rich`, เดิมคือ default)

**Run the rich script, then add suggestions:**

```bash
bun ~/.claude/skills/recap/recap-rich.ts
```

Script reads retro summaries, handoff content, tracks, git state. Then LLM adds:
- **What's next?** (2-3 options based on context)

### Step 1.5: Detect INCUBATED_BY (#229)

The recap-rich.ts script auto-detects `.claude/INCUBATED_BY` breadcrumbs. If present, shows:

```
## ⚠️ INCUBATED REPO
oracle: mawui-oracle
date: 2026-04-13
source: https://github.com/...
```

This tells the oracle: "You are in a repo tracked by another oracle. Check the breadcrumb for context."

### Step 2: Git context

```bash
git status --short
git log --oneline -1
```

Check what's appropriate from git status:
- **Uncommitted changes?** → show them, suggest commit or stash
- **On a branch (not main)?** → `git log main..HEAD --oneline` to see branch work
- **Branch ahead of remote?** → suggest push or PR
- **Clean on main?** → just show last commit, move on

Only read what matters — don't dump 10 commits if status is clean.

### Step 3: Read latest ψ/ brain files

Sort all ψ/ files by modification time, read the most recent:

```bash
find ψ/ -name '*.md' -not -name 'CLAUDE.md' -not -name 'README.md' -not -name '.gitkeep' 2>/dev/null | xargs ls -t 2>/dev/null | head -5
```

Read those top 5 files. This recovers the same context `/compact` restores — handoffs, retros, learnings, drafts, whatever was touched last.

### Step 4: Dig last session

```bash
ORACLE_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
ENCODED_PWD=$(echo "$ORACLE_ROOT" | sed 's|^/|-|; s|[/.]|-|g')
PROJECT_BASE=$(ls -d "$HOME/.claude/projects/${ENCODED_PWD}" 2>/dev/null | head -1)
export PROJECT_DIRS="$PROJECT_BASE"

# Strip -wt* suffix to find parent project dir
PARENT_ENCODED=$(echo "$ENCODED_PWD" | sed 's/-wt-[^/]*$//')
if [ "$PARENT_ENCODED" != "$ENCODED_PWD" ]; then
  PARENT_BASE=$(ls -d "$HOME/.claude/projects/${PARENT_ENCODED}" 2>/dev/null | head -1)
  [ -n "$PARENT_BASE" ] && export PROJECT_DIRS="$PROJECT_DIRS:$PARENT_BASE"
fi

# nullglob-safe worktree scan (both parent and self)
for base in "$PROJECT_BASE" "$PARENT_BASE"; do
  [ -z "$base" ] && continue
  for wt in "$base"-wt-*(N); do  # (N) = zsh nullglob qualifier
    [ -d "$wt" ] && export PROJECT_DIRS="$PROJECT_DIRS:$wt"
  done
done

python3 ~/.claude/skills/dig/scripts/dig.py 1
```

Include in recap:
```
📡 Last session: HH:MM–HH:MM (Xm, N msgs) — [topic]
```

Need more? `/dig 5` or `/dig --timeline`.

**Total**: 1 bash call + LLM analysis

---

## QUICK MODE (`/recap --quick`)

**Minimal, no content reads:**

```bash
bun ~/.claude/skills/recap/recap.ts
```

Script outputs git status + focus state (~0.1s). Then LLM adds:
- **What's next?** (2-3 options based on git state)

---

## "What's next?" Rules

| If you see... | Suggest... |
|---------------|------------|
| Handoff exists | Continue from handoff |
| Untracked files | Commit them |
| Focus = completed | Pick from tracks or start fresh |
| Branch ahead | Push or create PR |
| Streak active | Keep momentum going |

---

## Hard Rules

1. **Minimal bash calls** — list 1 call + verify 1 call (loop) ใน Handoff Mode; Rich/Quick mode ใช้ 1 call
2. **No subagents** — everything in main agent
3. **Ask, don't suggest** — "What next?" not "You should..."
4. **Verify pending before reporting** — see "Verify Before Reporting" section below. This is NON-NEGOTIABLE.
5. **Print absolute paths** — when referencing vault files, render the resolved `$ROOT/ψ/...` path (starts with `/`). Bare `ψ/...` is not clickable. See CONVENTIONS.md.

---

## Verify Before Reporting (MANDATORY)

Handoffs, retros, and memory files are **point-in-time claims**, not live state. Between the previous session ending and this one starting, work may have been done, PRs may have merged, files may have been copied. **Echoing a stale pending list as if it were current is a lie by omission** — the human ends up chasing items that are already done.

### The rule

Before outputting any "Pending" table or "Next action" suggestion, you MUST verify each claimed pending item against current reality:

| Claim type | How to verify |
|---|---|
| "Copy file X to path Y" | `ls path/Y` — is it already there? |
| "PR #N open/merged" | `gh pr view N --json state` |
| "Branch X needs push" | `git log origin/X..X` — any commits? |
| "Apply pattern P to file F" | `grep` for the pattern in F |
| "Issue #N pending" | `gh issue view N --json state` |
| "Migration ready to run" | check migrations table or list |

### What to do with each verified item

- **Already done** → drop from pending, note in "Actually done since handoff"
- **Still pending** → keep, show in table
- **Partially done** → split into remaining sub-items
- **Can't verify** (offline/ambiguous) → mark `⚠️ unverified` in the table, do not assert state

### The correction pattern

If the handoff pending list and reality diverge (>1 item stale), show the correction explicitly so the human sees the drift:

```
| Item | Handoff said | Reality |
|------|--------------|---------|
| Copy cache/ to maw-ui | pending | DONE (Apr 20 04:16) |
| PR #4 merge | open | MERGED |
```

### Why this is non-negotiable

- Handoffs are written before work stops, but work often continues between sessions (other Oracles, scheduled tasks, user actions).
- Memory files age — an older memory claiming "feature X is broken" may be stale if a fix shipped.
- Humans trust recap output as ground truth. An unverified echo breaks that trust fast.

**Patterns over intentions** — the code is the truth, the handoff is an intention. Always verify.

---

---

## NOW MODE (`/recap --now`)

**Mid-session awareness from AI memory** — no file reading needed. Use when user asks "where are we", "now", "status", "what are we doing".

AI reconstructs session timeline from conversation memory:

```markdown
## This Session

| Time | Duration | Topic | Jump |
|------|----------|-------|------|
| HH:MM | ~Xm | First topic | - |
| HH:MM | ~Xm | Second topic | spark |
| HH:MM | ongoing | **Now**: Current | complete |

**Noticed**:
- [Pattern - energy/mode]
- [Jump pattern: sparks vs escapes vs completions]

**Status**:
- Energy: [level]
- Loose ends: [unfinished]
- Parked: [topics we'll return to]

**My Read**: [1-2 sentences]

---
**Next?**
```

### Jump Types

| Icon | Type | Meaning |
|------|------|---------|
| spark | New idea, exciting |
| complete | Finished, moving on |
| return | Coming back to parked |
| park | Intentional pause |
| escape | Avoiding difficulty |

**Healthy session**: Mostly sparks and completes
**Warning sign**: Too many escapes = avoidance pattern

---

## NOW DEEP MODE (`/recap --now deep`)

Same as `--now` but adds bigger picture context.

### Step 1: Gather (parallel)

```
1. Current session from AI memory
2. Read latest handoff: ls -t ψ/inbox/handoff/*.md | head -1
3. Git status: git status --short
4. Tracks: cat ψ/inbox/tracks/INDEX.md 2>/dev/null
```

### Step 1.5: VERIFY pending from handoff

Before outputting, run verification checks against each pending item (see "Verify Before Reporting" above). Batch checks in parallel:
- `gh pr list --state all` for PR claims
- `ls path/to/file` for "copy X" claims
- `grep` for "apply pattern" claims

If any diverge from the handoff, show the correction table.

### Step 2: Output

Everything from `--now`, plus:

```markdown
### Bigger Picture

**Came from**: [Last session/handoff summary - 1 line]
**Working on**: [Current thread/goal]
**Thread**: [Larger pattern this connects to]

### Pending

| Priority | Item | Source |
|----------|------|--------|
| Now | [Current task] | This session |
| Soon | [Next up] | Tracks/discussion |
| Later | [Backlog] | GitHub/tracks |

### Connections

**Pattern**: [What pattern emerged]
**Learning**: [Key insight from session]
**Oracle**: [Related past pattern, if any]

**My Read**: [2-3 sentences - deeper reflection]

**Next action?**
```

---

## Session Context

The recap scripts (`recap.ts` and `recap-rich.ts`) auto-detect and display the current session:

```
📡 Session: 74c32f34 | arra-oracle-skills-cli | 2h 15m
```

Detection: scans `~/.claude/projects/[encoded-pwd]/*.jsonl` for the most recent session file, extracts short ID and elapsed time from first timestamp.

If session detection fails, skip silently — it's informational only.

---

## Demographics Context

If CLAUDE.md contains demographics from `/awaken` wizard v2, include in recap output:

```markdown
**Oracle**: [name] ([pronouns]) | **Human**: [name] ([pronouns]) | **Language**: [pref]
```

Add this as one line after the timestamp in any mode. If demographics not present, skip silently.

Look for fields in CLAUDE.md: `Human Pronouns`, `Oracle Pronouns`, `Language`, `Team`, `Experience`.

---

**Philosophy**: Detect reality. Surface blockers. Offer direction. *"Not just the clock. The map."*

**Version**: 8.0 (Merged where-we-are into --now mode)
**Updated**: 2026-02-10
