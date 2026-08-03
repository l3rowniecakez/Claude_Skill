---
installer: create-shortcut
name: redmine-create-ur-pattern
description: 'Create the standard set of SubTasks under a parent Redmine UR (User Request) issue, all assigned to the current user: Get Req./ประเมิน CA/Design UI/Design การเก็บข้อมูล/Meet สรุปกับ User, Dev., SIT, UAT, รวมโปรแกรม+SIT+RC+Check Code+แจ้ง Deploy ระบบ, SIT+RC+Check Code+แจ้ง Deploy ระบบ, Deploy Production (with its own two sub-subtasks: 01-Email ขออนุมัตินำขึ้น PROD, 02-แนบผล UAT). Use when user says "/redmine-create-ur-pattern" or wants to scaffold the standard UR SubTask structure on a Redmine ticket.'
created_at: 2026-08-03T14:18:55+07:00
argument-hint: "[redmine-issue-url-or-number]"
---

# /redmine-create-ur-pattern — Scaffold Standard UR SubTasks

Creates the standard, fixed set of SubTasks under a parent Redmine UR issue. This skill
only creates the issue structure — it does not fill in content, do the work, or touch
code. For actually implementing a UR's code fix, use `/redmine-ur` separately.

Redmine access: see the `reference-redmine-api-key` memory (`X-Redmine-API-Key` header,
`https://redmine.ochi.link`).

---

## Step 1 — Get the parent RM

If not passed as `$ARGUMENTS`, ask the user for the parent Redmine issue (RM) URL or
number.

Fetch it to get `project_id`, `tracker_id`, and `subject`:

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/issues/<id>.json"
```

New SubTasks will use the **same `project_id` and `tracker_id`** as this parent issue
unless the user says otherwise.

---

## Step 2 — Get the current user's id (assignee)

Every SubTask created by this skill is assigned to **the current user** (whoever's API
key is being used), never left unassigned or assigned to someone else. Fetch it once,
reuse for every create call:

```bash
curl -s -H "X-Redmine-API-Key: <key>" "https://redmine.ochi.link/users/current.json"
```

Take the `id` field from the response as `<assigned_to_id>`.

---

## Step 3 — Confirm the SubTask list before creating anything

Show the user the exact set of SubTasks about to be created under RM `<id>` — this is a
write to a shared system, so get explicit confirmation before Step 4, every time:

Level-1 SubTasks (subject text verbatim, no numbering prefix):
1. `Get Req. / ประเมิน CA / Design UI / Design การเก็บข้อมูล / Meet สรุปกับ User`
2. `Dev.`
3. `SIT`
4. `UAT`
5. `รวมโปรแกรม + SIT + RC + Check Code + แจ้ง Deploy ระบบ`
6. `SIT + RC + Check Code + แจ้ง Deploy ระบบ`
7. `Deploy Production`

Under SubTask 7 (`Deploy Production`), two more SubTasks (level-2, i.e. child of
SubTask 7):
- `01-Email ขออนุมัตินำขึ้น PROD`
- `02-แนบผล UAT`

If the user wants to skip, reorder, or rename any of these for this particular RM, apply
their changes before creating. Do not proceed to Step 4 without confirmation.

---

## Step 4 — Create the level-1 SubTasks

Create each of the 7 SubTasks one at a time via POST, each with `parent_issue_id` set to
the RM from Step 1 and `assigned_to_id` set to the id from Step 2:

```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<rm_id>,"assigned_to_id":<assigned_to_id>,"subject":"<subject text>"}}' \
  "https://redmine.ochi.link/issues.json"
```

Capture the returned `id` for each created issue — you need SubTask 7's id (`Deploy
Production`) for Step 5.

---

## Step 5 — Create the two SubTasks under "Deploy Production"

Using the `id` returned for `Deploy Production` in Step 4 as `parent_issue_id`, and the
same `assigned_to_id` from Step 2:

```bash
curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<deploy_production_id>,"assigned_to_id":<assigned_to_id>,"subject":"01-Email ขออนุมัตินำขึ้น PROD"}}' \
  "https://redmine.ochi.link/issues.json"

curl -s -X POST -H "X-Redmine-API-Key: <key>" -H "Content-Type: application/json" \
  -d '{"issue":{"project_id":<project_id>,"tracker_id":<tracker_id>,"parent_issue_id":<deploy_production_id>,"assigned_to_id":<assigned_to_id>,"subject":"02-แนบผล UAT"}}' \
  "https://redmine.ochi.link/issues.json"
```

---

## Step 6 — Report the result

List every created SubTask (issue number + subject + its parent) back to the user, e.g.
as a link list to `https://redmine.ochi.link/issues/<id>`. If any `curl` call returned an
error (non-2xx / `errors` field in the JSON response), stop and show the raw error to the
user instead of silently retrying or guessing a fix — Redmine's error usually names the
missing/invalid field (e.g. a required custom field on that tracker).

---

## Notes

- This skill never touches code, never logs time, and never posts Notes — it only
  creates the issue/SubTask structure. Follow up with `/redmine-ur` for implementation or
  `/redmine-logtime` for logging work.
- Never create SubTasks without the Step 3 confirmation, even if the parent RM number was
  passed directly as `$ARGUMENTS`.
- Every SubTask is assigned to the current user (Step 2) — never leave `assigned_to_id`
  out of a create call.

---

ARGUMENTS: $ARGUMENTS
