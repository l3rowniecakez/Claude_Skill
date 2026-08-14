---
installer: create-shortcut
name: redmine-ur
description: 'Implement a Redmine UR (User Request) code fix in any Delphi7 group-insurance program suite repo (OGL_Operation, OGL_Claim, OGL_Benefit, OGL_Center_Report, OGL_FindInfo, OGL_Premium, OGL_Reinsurance, OGL_Sale, GroupLife, etc. — not limited to OGL_Operation): read + analyze the RM, plan (with Phase/Task breakdown for large work), get developer approval before any coding, implement phase-by-phase with a review gate at each phase, then record the result as DB script file(s) + a FormEdit.txt update in the ticket folder. Use when user says "/redmine-ur", sends a Redmine UR ticket, or asks to fix/แก้ไข a program point in this suite. Never write code before explicit approval, never touch anything outside the requested scope, and never skip the FormEdit.txt/db-script recording step when a fix is done.'
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

---

## Step 1 — Get the Redmine URL

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

## Step 2 — Read, analyze, and plan (no coding yet)

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

(`feedback-alter-script-one-file-per-proc`)

---

## Step 7 — Update FormEdit.txt

In the same ticket folder, update `FormEdit.txt` with **both** parts:

1. **Rebuild the top summary block** — one cumulative, deduplicated block covering every
   entry in the file's full history (not just this fix):

```
=================================
Redmine <ticket-number> : <ticket-group title>
=================================

[ Delphi Form ]
   - <ProgramName>.exe
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
      - OGL_Operation.exe
         - Form Edit : DMOper แก้ไข TMSStoreProc : ZGL_PolicySetting เพิ่ม field PolicyNo, PolicyYear
         - Form Edit : DMOper เพิ่ม TMSStoreProc : ZGL_DebtCollect
         - Form Edit : ListOperPolicy แก้ไข TMSQuery : ChkBenefitDate_Cov เพิ่ม field PolicyYear
   ```
   Same level of detail applies to any new/changed function, procedure, or field touched in
   that same unit (e.g. "Form Edit : DMOper เพิ่ม function GenBenefitsTablePDF") — the goal
   is that someone reading only the top summary block can tell exactly which component(s)
   were touched, in which unit, without opening the diff.

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
2. If any Table/View/Stored Procedure was touched, also overwrite the matching file(s)
   under `D:\WORK\delphi7_for_claude\Doc\db-schema\{OGL,OceanLife}\...` to match the newly
   deployed state (same encoding/format already used there — UTF-16LE, `Script Date`
   comment updated). If the phase was Delphi-code-only, this is a no-op — but check every
   time, don't skip the check.

(`feedback-phase-by-phase-approval`)

---

## Notes

- Never `git commit`/push/merge without explicit instruction, any repo, every time.
- To log the finished ticket's time/notes to Redmine afterward, use `/redmine-logtime`
  separately — this skill's job ends at Step 8.

---

ARGUMENTS: $ARGUMENTS
