---
description: "🕒 [Worklog] — Log daily JIRA worklogs interactively, ticket by ticket"
---
# Daily Worklog Logger

Use the `[Worklog]` action tag, optionally with a starting ticket ID.

Fetches each ticket's description + Task Estimation Time, asks for time spent /
AI Contribution / Done %, drafts a short worklog comment, confirms with you, then
submits the worklog and updates the custom fields via the JIRA REST API. Loops to
the next ticket until you say you're done.

**First-time setup:** Reuses `.claude/skills/support/jira_config.ini` (same file as
`[WBS-to-JIRA]`). If it doesn't exist yet, the agent creates it from the template and
asks you to fill in credentials.

## Examples

```
[Worklog]
```

```
[Worklog] P1709-2144
```

## Skill Context

Read .claude/skills/daily-worklog/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
