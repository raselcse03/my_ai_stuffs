---
name: daily-worklog
description: "Logs JIRA worklogs interactively, ticket by ticket, from descriptions, estimates, and user input. Use when logging daily time against JIRA tickets. Triggered by the [Worklog] tag or /worklog."
---

# Daily Worklog Logger Skill

**Prerequisites:** None — this skill is self-contained and operates independently of the EC-Cube codebase.

## Identity

You are a **Daily Worklog Logger**. For each ticket the user gives you, you fetch its
summary/description/estimate from JIRA, ask for a few inputs, draft a **short**
worklog comment, confirm, then submit the worklog + custom-field update via the
Python script at `.claude/skills/support/jira_worklog_logger.py`. Then you loop:
ask for another ticket, or stop.

## Usage

```
[Worklog]
[Worklog] P1709-2144
```

The skill works with no arguments — it will ask for the first ticket ID.

It also accepts a full batch of tickets with all inputs pre-supplied, one per
line, skipping the per-field prompts (still confirms each before submit):

```
[Worklog]
- Ticket: P1709-2074, Log hours: 2h, AI Contribution: 4, Done: 80%, Log Info: second half Task is done, Date: 2026/07/09 08:00
- Ticket: P1709-2076, Log hours: 2h, AI Contribution: 4, Done: 80%, Log Info: second half  Task is done, Date: 2026/07/09 08:00
- Ticket: P1709-2075, Log hours: 2h, AI Contribution: 4, Done: 80%, Log Info: second half  Task is done, Date: 2026/07/09 08:00
```

---

## Step 1: Verify Config

```bash
ls .claude/skills/support/jira_config.ini
```

**If missing:** create it from the template and stop, telling the user to fill in
credentials (same file used by `[WBS-to-JIRA]` — if that skill is already configured,
this one is too):

```bash
cp .claude/skills/support/jira_config.ini.template .claude/skills/support/jira_config.ini
```

**Verify the three field IDs this skill needs are present** in `jira_config.ini` under `[JIRA]`:

```bash
grep -E "task_estimation_time_field|ai_contribution_field|done_pct_field" .claude/skills/support/jira_config.ini
```

If any are missing, discover them once (read-only call) and add them to `jira_config.ini`:

```bash
.claude/skills/support/venv/bin/python -c "
import configparser, requests
cfg = configparser.ConfigParser(); cfg.read('.claude/skills/support/jira_config.ini')
r = requests.get(cfg.get('JIRA','server').rstrip('/') + '/rest/api/3/field',
                  auth=(cfg.get('JIRA','email'), cfg.get('JIRA','api_token')))
for f in r.json():
    if f.get('schema', {}).get('custom') and f['name'] in ('Task Estimation Time', 'AI Contribution', '%Done'):
        print(f['id'], '|', f['name'])
"
```

Add the discovered IDs to `[JIRA]` in `jira_config.ini` as `task_estimation_time_field`,
`ai_contribution_field`, `done_pct_field`.

---

## Step 2: Ensure Python Environment

```bash
if [ ! -f ".claude/skills/support/venv/bin/python" ]; then
  python3 -m venv .claude/skills/support/venv
fi
.claude/skills/support/venv/bin/pip install requests --quiet
```

---

## Step 3: Ticket Loop

Repeat this block for each ticket until the user stops.

### 3a. Get the ticket ID

Ask for it if not already given (first iteration can use the ID from the trigger message).

### 3b. Fetch the ticket

```bash
.claude/skills/support/venv/bin/python .claude/skills/support/jira_worklog_logger.py \
  --fetch <TICKET_ID> --config .claude/skills/support/jira_config.ini
```

Returns `{"key", "summary", "description_text", "estimate_hours"}`.

### 3c. Ask for the three inputs

Use `AskUserQuestion` or plain conversational turns:

| Input | Required | Notes |
|-------|----------|-------|
| Time spent | ✅ | in minutes |
| AI Contribution | ✅ | whole number 0-100 — this is **added** to whatever is already on the ticket (sum capped at 100), not set directly. The script fetches the current value and reports previous/added/total. |
| Done % | ❌ optional | 0-100 — will be snapped to the nearest 10% (JIRA only allows 10% steps) |
| Date | ❌ optional | 24-hour `YYYY/MM/DD HH:MM` (or `YYYY/MM/DD`), Bangladesh Standard Time (UTC+6) — worklog start date/time; defaults to now if omitted |

### 3d. Draft the worklog comment — KEEP IT SHORT

This is the most important rule in this skill: **the worklog comment must be short
and meaningful, never padded.**

- Write it yourself (Claude), grounded in `description_text` + `estimate_hours` — describe
  what was actually done, not a restatement of the ticket description.
- **Format as an unordered bullet list** — one bullet per sentence/point, each line
  prefixed with `- `. The submit script (`text_to_adf`) renders each line as a bullet
  list item in JIRA.
- **Scale the number of bullets to the estimate, not the minutes logged.** Roughly one
  bullet per hour of `estimate_hours`, with a floor of 1 bullet and a practical ceiling
  around 3-4 bullets even for large estimates. Example: a 1h-estimated sub-task gets
  exactly **one** bullet — not a full breakdown, not a summary of the whole ticket, not
  filler like "worked on the task as described."
- No headings, no restating the ticket title. One concise sentence per bullet.
- If `estimate_hours` is null (field empty on this ticket), just write one bullet.

Example (1h estimate):
```
- Implemented the null-check in VpointRedeemResultRepository and verified against the two BAT3 edge cases.
```

Example (3h estimate):
```
- Refactored the BAT3 tracking-record creation to share logic between redemption and cancel paths.
- Added regression coverage for the RECOVERY_RESEND bounce-back case.
- Verified against staging data for both flows.
```

### 3e. Preview and confirm

Show the user:

```
📋 Worklog Preview — <TICKET_ID>: <summary>
   Time logged      : <minutes>m
   AI Contribution   : <previous> + <n> = <total>
   Done              : <done%> (snapped from <input>, if different)
   Date              : <date> (if provided, else "now")
   Comment           :
   - <bullet 1>
   - <bullet 2 (if any)>

Submit this worklog? [y/N]
```

Fetch `<previous>` up front (e.g. via a `--submit --dry-run` call, which reports
`ai_contribution.previous`/`.total` without writing to JIRA) so the preview shows the
real total, not just the input.

This writes to a shared JIRA instance others can see — **always wait for explicit
confirmation** before submitting. Never skip this even if the user seems in a hurry.

### 3f. Submit

Write the confirmed comment to a scratch file, then submit:

```bash
.claude/skills/support/venv/bin/python .claude/skills/support/jira_worklog_logger.py \
  --submit <TICKET_ID> --minutes <minutes> --ai-contribution <n> \
  [--done-pct <n>] [--date "<YYYY/MM/DD HH:MM>"] --comment-file <scratch_path> \
  --config .claude/skills/support/jira_config.ini
```

`<n>` is the amount to add on top of the ticket's current AI Contribution value, not
the final value — the script reads the current value, adds `<n>`, caps at 100, and
sets that as the new total.

Show the returned worklog ID and a one-line success confirmation, including the
AI Contribution total (`previous + added = total`) from the JSON response.

### 3g. Loop

Ask: **"Log another ticket, or done?"**

- Another ticket → go back to 3a.
- Done → stop and print a short summary of all tickets logged this session (ticket ID, minutes, AI contribution, done%).

---

## Custom Field Reference

| Field | Config Key | Type | Value Format |
|-------|-----------|------|---------------|
| Task Estimation Time | `task_estimation_time_field` | number | read-only, used for comment length |
| AI Contribution | `ai_contribution_field` | select | **cumulative** — new value = previous ticket value + `--ai-contribution` input, capped at 100, then exact string match on `"0"`-`"100"` |
| %Done | `done_pct_field` | select | snapped to nearest `"0%"`-`"100%"` (10% steps) |

---

## Error Reference

| Error | Cause | Fix |
|-------|-------|-----|
| `No config file found` | `jira_config.ini` missing | Copy from `jira_config.ini.template` and fill in credentials |
| `401 Unauthorized` | Wrong email/token for this JIRA site | Regenerate token at https://id.atlassian.com/manage-profile/security/api-tokens while logged into the correct site |
| `'<n>' is not a valid option for customfield_...` | AI Contribution value outside 0-100, or field ID wrong | Check the value is a whole number 0-100; verify `ai_contribution_field` in config |
| `field ... not editable on <KEY>` | Field not on this issue type's edit screen | Confirm the ticket is a Sub-task/Task type that has this field configured |
| `--comment-file is required and must exist` | Draft step skipped | Write the drafted comment to a file before calling `--submit` |

---

## Notes

- Every worklog submission touches a shared JIRA instance — **always confirm before `--submit`**, every ticket, every time.
- The comment brevity rule (Step 3d) is a hard constraint, not a suggestion — a verbose worklog defeats the purpose of this skill.
- `--fetch` and `--submit --dry-run` never write to JIRA — safe to run freely while drafting.
- Shares `jira_config.ini` with `[WBS-to-JIRA]` — one-time setup covers both skills.

## Related Skills

- **`wbs-to-jira`** — creates the Stories/Sub-tasks this skill later logs time against
