---
installer: create-shortcut
name: redmine-ur
description: 'Implement a Redmine UR (User Request) code fix in any Delphi7 group-insurance program suite repo (OGL_Operation, OGL_Claim, OGL_Benefit, OGL_Center_Report, OGL_FindInfo, OGL_Premium, OGL_Reinsurance, OGL_Sale, GroupLife, etc. — not limited to OGL_Operation): read + analyze the RM, plan (with Phase/Task breakdown for large work), get developer approval before any coding, implement phase-by-phase with a review gate at each phase, then record the result as DB script file(s) + a FormEdit.txt update in the ticket folder. Use when user says "/redmine-ur", sends a Redmine UR ticket, or asks to fix/แก้ไข a program point in this suite. Never write code before explicit approval, never touch anything outside the requested scope, and never skip the FormEdit.txt/db-script recording step when a fix is done. Also supports Speckit mode: when the ticket has a speckit/<RM>/ folder (REQ + spec.md + plan.md + tasks.md from the /speckit-* workflow, any stack incl. PHP Web Bot), tasks.md becomes the plan, each tasks.md Phase is one approval gate, finished tasks are ticked in tasks.md, and /speckit-converge closes the loop.'
created_at: 2026-07-24T12:23:48+07:00
argument-hint: "[redmine-issue-url-or-number] [ticket-folder-path]"
---

# /redmine-ur — Redmine UR Fix + FormEdit.txt/DB-Script Recorder

Workflow for a Redmine **UR (User Request)** ticket against **any Delphi 7 program in the
group-insurance suite** — not just `OGL_Operation`. The suite includes multiple sibling
programs living as separate repo folders under `D:\WORK\` (e.g. `OGL_Operation`, `OGL_Claim`,
`OGL_Benefit`, `OGL_Center_Report`, `OGL_FindInfo`, `OGL_Premium`, `OGL_Reinsurance`,
`OGL_Sale`, `GroupLife`) — which one applies depends on the ticket. It's unconfirmed whether
each sibling repo has its own `CLAUDE.md`/doc structure the way `OGL_Operation` does (see
`reference-delphi7-group-insurance-repo` memory — `/mnt/d/WORK/delphi7_for_claude`), so
**always ask the developer for the exact repo/working-copy path** for the program this ticket
targets — every time, don't assume or reuse a path from a previous ticket. The point of this
skill is not just to make the code change, but to plan it properly, get it approved
phase-by-phase, and make sure every fix is **recorded** the way this project always records
them: a numbered DB script file per stored procedure/table touched, and a `FormEdit.txt`
update in the same ticket folder.

**Speckit mode (added 2026-10-26):** the same workflow also runs on tickets that are managed
with Spec Kit (`speckit/<RM>/` folder, e.g. the Web Bot repo). In that mode the Spec Kit
documents replace Step 2's hand-drafted plan, and Steps 3/4/7/8 gain a few extra rules — see
the **Speckit mode** section right after Step 1. Everything else (approval gates, scope
discipline, never commit/push, `#ai-work`, FormEdit.txt) still applies unchanged.

---

## Step 1 — Get the Redmine URL

**Never create a new Redmine issue as part of this skill** — every Redmine call this skill
makes is a read (`GET`); it never `POST`s to `https://redmine.ochi.link/issues.json`. If a
new/related RM genuinely needs opening, that requires the user's explicit instruction and a
separate action (e.g. `/redmine-create-ur-pattern` or manual creation) — never something
done incidentally while planning or implementing this ticket.

If not passed as `$ARGUMENTS`, ask the user for the Redmine issue URL/number. Fetch it (see
`reference-redmine-api-key` memory for the key):

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<id>.json?include=journals"
```

Also ask the developer, every time, which program in the group-insurance suite this ticket
targets and the exact source repo/working-copy path for it (e.g. `/mnt/d/WORK/OGL_Claim`,
`/mnt/d/WORK/OGL_Operation`, ...) — don't assume it's `OGL_Operation`/`delphi7_for_claude` or
reuse a path from a previous ticket.

Also confirm the local ticket-group folder, e.g. `D:\WORK\JIRA\<ticket folder>\` (the
on-disk folder name may say "JIRA" and "UR <date>" — that's legacy naming, out of scope;
never write the word "JIRA" inside `FormEdit.txt` content itself, always "Redmine
<ticket-number>").

---

## Speckit mode — detect it right after Step 1

**Detect (do this every time, read-only):** look for a `speckit/` folder in the repo/ticket
folder (e.g. `<ticket folder>\speckit\`) that contains a folder named
after this RM number (`speckit/<RM>/`), or ask if the user said "speckit". Report which
artifacts exist: `REQ_*.md`, `spec.md`, `plan.md`, `tasks.md`, `research.md`,
`data-model.md`, `contracts/`, `quickstart.md`, `checklists/`, and whether `spec.md` has a
`## Clarifications` section. No `speckit/<RM>/` folder → this section does not apply, continue
with the classic flow (Delphi suite tickets normally have none).

**Which stage is the ticket at?** Follow the fixed Spec Kit order: REQ (`/STANDARD_REQ_TEMPLATE_v1_1`) → `/speckit-specify` →
`/speckit-clarify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-analyze` →
`/speckit-checklist` (optional) → implement → `/speckit-converge`. Tell the user the next
missing step and **do not skip ahead** (for example coding while `tasks.md` or the analyze
step is missing) without saying so and getting a yes. Never run `/speckit-taskstoissues`
(deprecated). Each `/speckit-*` command is run only when the user asks for that step.

**Before running any `/speckit-*` command**, make sure `speckit/.specify/feature.json` has
`{"feature_directory": "<RM>"}` for this ticket (the scripts locate the feature through it).
Show the user the change if it points at another feature; do not change it silently.

**What replaces what in Speckit mode**

| Classic step | In Speckit mode |
|---|---|
| Step 2 plan | `spec.md` + `plan.md` + `tasks.md` are the plan. Do **not** draft a second, parallel task list. Read them, summarise phases / constitution check / open risks, and compare against the RM description + journals for gaps. |
| Step 3 phase gates | One gate per `## Phase N` heading in `tasks.md`; the `**Checkpoint**` line under it is the review gate. |
| Step 7 FormEdit.txt | Still required. Take the changed files / stored procedures / tables from `tasks.md` + the actual diff. |
| Step 8 close | Add the Speckit close-out items below. |

**Changing requirements mid-flight:** when the user adds or changes something, update the
Spec Kit documents rather than only the chat plan: edit/clarify `spec.md` (record it under
`## Clarifications`), then regenerate or hand-edit `plan.md` / `tasks.md` so the three stay
consistent, and re-present the affected phases for approval. If it conflicts with
`.specify/memory/constitution.md`, stop and ask — amending the constitution is a separate
`/speckit-constitution` run that only happens on the user's instruction.

**Test-first facts to confirm, not assume:** `plan.md`/`research.md` often mark items
"ต้องยืนยันด้วย baseline" (to be confirmed by a baseline run). Do those baseline tasks first
and, if the result contradicts a spec statement, stop and tell the user before coding.

**Executing tasks (Step 3 in this mode)**
- Implement only the tasks of the phase the user has just approved with an explicit
  "เริ่ม" (or equivalent). Approving the plan, or a previous phase, is not approval for the next.
- Do **not** run `/speckit-implement` unfiltered — it executes every task in `tasks.md`.
  Either do the approved phase's tasks directly, or pass `/speckit-implement` an explicit
  filter limited to that one phase.
- Respect the task markers: tasks without `[P]` run in order; `[P]` tasks may run together only
  when they touch different files.
- Tick a task (`- [ ]` → `- [x]`) in `tasks.md` right after it is actually done **and verified**
  (the check named in the task passed). A task that failed, was skipped, or is blocked stays
  unticked with a one-line note under it. Never tick `checklists/*.md` boxes — those belong to
  `/speckit-specify`, `/speckit-clarify` and the reviewer.
- At the phase's `**Checkpoint**`, stop, summarise results against the task's own acceptance
  checks, and wait for the user's approval before the next phase.
- Anything a task marks as destructive-test (dropping a table, writing test rows) needs the
  backup step that the task lists first; never run it against SIT/UAT/Production unless the
  task and the user say so.

---

## Step 2 — Read, analyze, and plan (no coding yet)

*(Speckit mode: the plan already exists as `spec.md`/`plan.md`/`tasks.md` — see the Speckit
mode section; summarise and get approval instead of drafting a new one.)*

Read the subject, description, and journals fully to understand what's actually being
requested. Analyze the impact, then draft a concrete, itemized task list.

- If the work is large, touches a lot of code, or has wide impact, break it into
  **Phases**, each containing its own smaller **Tasks**.
- This step is planning only — **do not write or edit any file yet**, no matter how
  small or obvious the fix looks, until the developer explicitly approves the plan.
- The developer may add more information or change requirements at any point during
  planning. When they do, fold it in and present a **revised, re-summarized plan** for
  approval again — don't silently patch the old plan or proceed on an unconfirmed
  update.

---

## Step 3 — Implement phase-by-phase, with a review gate at each phase

Once the developer approves the plan, implement **one phase at a time**:

- Never start a phase's implementation until the developer has approved that specific
  phase starting (approving the overall plan is not the same as "go implement all of
  it now").
- Wherever there's a point the developer can check the result (compile, run a form,
  preview a report, review a query), stop and actively ask them to verify and approve
  it before moving to the next phase — don't assume it's fine and continue on your own.
- Never advance to the next phase without that explicit approval.

(`feedback-phase-by-phase-approval`)

---

## Step 4 — Implement, following this repo's conventions

*(Speckit mode, non-Delphi repos such as the PHP Web Bot: the Delphi-specific bullets below —
`TMSStoredProc`, `.pas`/`.dfm`, ReportBuilder — do not apply. The repo's own
`speckit/.specify/memory/constitution.md` and the plan's "Constraints" govern instead; keep the
file's existing line endings (check for CRLF before editing — use byte-safe splicing when a
file is CRLF), use the exact existing user-facing messages, and keep the scope-discipline and
`#ai-work` rules below.)*

- **Stick to the existing code pattern.** Before writing any new SQL/component, grep
  the codebase for the same table/operation and mirror its exact shape and
  component-reuse convention — never invent a fresh/ad-hoc query or component just
  because it would be "cleaner." (`feedback-no-adhoc-queries`)
- **Never touch anything outside the requested fix.** If a form/menu/screen is not part
  of what this ticket asks for, do not modify it, even if it looks related or you spot
  something else that could be improved — always get explicit permission first.
- Call stored procedures only via a dedicated `TMSStoredProc` component, never
  `sql.Add('EXEC ...')` on a generic `TMSSQL`. (`feedback-storedproc-use-tmsstoredproc`)
- `.pas` files: **never use the Edit tool** — byte-safe Python splicing only (`"rb"`/`"wb"`,
  exact single-occurrence anchor replace, verify no new `EF BF BD` mojibake and CRLF stays
  consistent). `.dfm` files are plain ASCII and fine to Edit normally, but never insert
  `{ }`-style comments into a `.dfm` (breaks the binary resource parser).
  (`feedback-never-use-edit-tool-on-pas-files`, `feedback-dfm-pas-editing-pitfalls`)
- Porting/cloning a component or a ReportBuilder (`ZGL_Report`/`OGL_Report`) BLOB across
  forms: run the full name-collision + `DataPipelineName`/`On*`-event audit before calling
  it done — see `feedback-dfm-pas-editing-pitfalls` for the exact checklist, it has caused
  repeat silent bugs. A standalone `dcc32` compile passing is a weak signal only, not proof
  the real IDE build passes.
- Code comments/change-log lines: `-- Redmine #<id> Add By <Developer Name> <date> : ... #ai-work`
  — fill in the actual developer's name/initials; ask if not already known from context.

---

## Step 5 — DB access, if needed

If the fix requires connecting to the DB to inspect data, ask the developer fresh, every
time: Server IP, username, password, and DB Name. **Never remember or store credentials
across sessions or even later in the same session** — ask again whenever a new connection
is actually needed. (`feedback-never-store-db-credentials`)

---

## Step 6 — Write/update the DB script file(s)

For every stored procedure created or altered for this ticket, in the ticket folder:

- **Every `.sql` script file must start with a `USE [<DB>]` / `GO` header** naming the
  target database, before any other statement, e.g.:
  ```sql
  USE [OGL]
  GO
  ```
  or
  ```sql
  USE [Oceanlife]
  GO
  ```
  This applies to every script generated in this step — Store and Structure alike.
- Check whether `NNN_<DB> Alter Store <ProcName>.sql` (or `Create Store`) already exists
  for that **exact proc name**, regardless of which Redmine ticket originally created it.
  - Exists → **overwrite it in place** with the new full body, same filename/number (an
    `ALTER PROCEDURE` body is always complete, never a diff — the newest file already
    supersedes the old one, so don't create a second numbered file for the same proc).
  - Doesn't exist → create it with the next unused number in the folder.
- Table/View DDL changes get their own `NNN_<DB> Create/Alter Table <TableName>.sql`,
  same folder-scoped numbering rule.
- **`CREATE PROCEDURE` vs `ALTER PROCEDURE` inside the file body — decided by whether the
  proc has ever actually shipped to Production, never by how many times the file itself
  was edited during SIT/UAT development:**
  - Proc has **never been deployed to Production** (brand-new this ticket, still
    mid-development, ticket hasn't gone live yet) → the statement must stay
    `CREATE PROCEDURE` no matter how many rounds of SIT/UAT bugfix edits it goes through.
    Prepend a guard so repeat SIT/UAT redeploys don't error, but the real statement stays
    CREATE:
    ```sql
    IF EXISTS (SELECT 1 FROM sys.objects WHERE object_id = OBJECT_ID(N'[dbo].[ProcName]') AND type = 'P')
        DROP PROCEDURE [dbo].[ProcName]
    GO

    CREATE PROCEDURE [dbo].[ProcName]
    ```
    Using `ALTER` here silently corrupts the deploy script: it looks fine on SIT/UAT
    (object already exists there from your own earlier deploy) but fails outright the
    first time it actually runs against Production, since Production has never seen the
    object.
  - Proc **already exists on Production** (a pre-existing legacy proc being modified, or
    a proc from this same ticket that has already gone live in an earlier release) →
    `ALTER PROCEDURE` is correct, no guard needed.
  - The trap: fixing a bug found during SIT/UAT testing on a not-yet-shipped proc makes
    `ALTER` *feel* right because the object already exists on the environment you're
    staring at — but the file describes what must run on a virgin Production DB, not what
    reruns cleanly on your dev copy. Before touching this keyword on any edit, check
    whether the ticket has a Go-live/deploy-together dependency still pending — if
    nothing in the ticket has reached Production yet, everything net-new in it stays
    CREATE regardless of edit count.
  - (`feedback-sql-script-create-vs-alter`)

(`feedback-alter-script-one-file-per-proc`)

---

## Step 7 — Update FormEdit.txt

*(Speckit / web projects: open the project's existing `FormEdit.txt` first — for a web project it
is the `FormEdit.txt` in that project's ticket folder — and **reuse the section headings it already uses**
(for example `[ Web App ]` instead of `[ Delphi Form ]`). The Delphi block below is the
template for the Delphi suite only. Keep both parts (cumulative top block + dated entry), and
list the DB script files under the folder that project already uses for them.)*

In the same ticket folder, update `FormEdit.txt` with **both** parts:

1. **Rebuild the top summary block** — one cumulative, deduplicated block covering every
   entry in the file's full history (not just this fix):

```
=================================
Redmine <ticket-number> : <ticket-group title>
=================================

[ Delphi Form ]
   - <ProgramName>.exe [<ticket-number-or-branch>] [<repo-url>]
     - Form Edit : <Path\FormName>      (existing form modified)
     - Form Add : <Path\FormName>       (brand-new form)

[ Store Procedure ]
   - <DB name, e.g. OGL / Oceanlife>
     - Alter Store : <StoredProcName>   (existing SP modified)
     - Create Store : <StoredProcName>  (brand-new SP)

[ Structure ]
   - <DB name>
     - Create Table : <TableName> <path-to-create-script>
     - Alter Table : <TableName> <FieldName> <path-to-alter-script>
   (write "(ไม่มี)" under a bracket section if nothing of that kind changed)

[ Report ]
   - <DB name, e.g. Oceanlife>
     - ReportName : <ReportName as stored in ZGL_Report.ReportName>

===================================
รายละเอียดประวัติการแก้ไข
===================================
```

   Dedupe by name — list a form/SP/table only once even if touched by multiple dated
   entries below. Only mark "Add"/"Create" if genuinely new, otherwise "Edit"/"Alter".

   **Any form/unit where a `TMSStoredProc`/`TMSQuery`/`TMSAccess`(-family) component was
   added or altered needs component-level detail, not just the filename** — this applies
   everywhere, not only Data Modules (`DMOper`, `DMOGL`). A `[ Delphi Form ]` line must say
   exactly what changed — which component was added/altered and how — not just "Form Edit :
   <FileName>". Examples:
   ```
   [ Delphi Form ]
      - OGL_Operation.exe [ticket/3] [ssh://<gitblit_user>@10.100.2.187:29418/delphi/some-repo.git]
         - Form Edit : DMOper แก้ไข TMSStoreProc : ZGL_PolicySetting เพิ่ม field PolicyNo, PolicyYear
         - Form Edit : DMOper เพิ่ม TMSStoreProc : ZGL_DebtCollect
         - Form Edit : ListOperPolicy แก้ไข TMSQuery : ChkBenefitDate_Cov เพิ่ม field PolicyYear
   ```
   Same level of detail applies to any new/changed function, procedure, or field touched in
   that same unit (e.g. "Form Edit : DMOper เพิ่ม function GenBenefitsTablePDF") — the goal
   is that someone reading only the top summary block can tell exactly which component(s)
   were touched, in which unit, without opening the diff.

   **The App name line itself must carry the Gitblit ticket/branch and the repo URL, each in
   its own `[...]` bracket**, e.g.
   `- CLPro63_P.exe [ticket/1] [ssh://<gitblit_user>@10.100.2.187:29418/delphi/groupwork.git]` —
   this suite has many sibling programs living in different git repos (not just
   `OGL_Operation`), so the App name alone doesn't tell a future reader where the code
   actually lives or which Gitblit ticket tracks it. Fill this in as soon as a ticket/branch
   exists for the change (even if code+push happens in a later phase) — don't leave it blank
   and back-fill "later." If no ticket/repo exists yet at the time this line is first written
   (planning/Phase 1 before any commit), write `[ticket TBD] [repo TBD]` as a placeholder and
   correct it once the ticket is created — never silently omit both fields going forward.

2. **Append a new dated entry below the existing history** — never delete or rewrite past
   entries. Format: `YYYY-MM-DD - Redmine #NNNN : <title> #ai-work` (or
   `YYYY-MM-DD - (ไม่มี Redmine) <title> #ai-work` if no ticket), followed by the prose/
   bullet description of what changed and why, plus the DB script filename(s) from Step 6.

(`feedback-formedit-txt-template`)

---

## Step 8 — Close-phase checklist

Only once the developer explicitly approves the fix/phase as done (per Step 3's review
gate):

1. Confirm Step 7 (`FormEdit.txt`) is done — this is a required part of closing, not an
   optional follow-up.
2. **Speckit mode only:** (a) every finished task is ticked in `tasks.md` and every
   unfinished one has its note; (b) offer `/speckit-converge` to compare the code against
   `spec.md` and add any missing tasks — run it only when the user says so; (c) when the work
   leaves results that the spec asked to be recorded (baseline/compare files, test notes),
   confirm they are saved under `speckit/<RM>/`; (d) remind the user that Redmine notes and
   time are posted separately (`/redmine-logtime`, Markdown, `#ai-work`) and that commit/push
   needs their explicit instruction (`/git-commit-push`).

Do **not** touch `D:\WORK\delphi7_for_claude\Doc\db-schema\...` — those doc snapshots are
no longer maintained. For any table/stored-procedure structure question, query the live DB
directly instead of reading or writing files under that path.
(`feedback-phase-by-phase-approval`, `feedback-no-read-dbschema-docs-use-db52`)

---

## Notes

- Never `git commit`/push/merge without explicit instruction, any repo, every time.
- To log the finished ticket's time/notes to Redmine afterward, use `/redmine-logtime`
  separately — this skill's job ends at Step 8.

---

ARGUMENTS: $ARGUMENTS
