---
description: "🎫 [WBS-to-JIRA] — Create JIRA Stories and Sub-tasks from a WBS markdown file"
---
# WBS to JIRA Ticket Creator

Use the `[WBS-to-JIRA]` action tag with the path to a WBS markdown file.

Reads the WBS, runs a dry-run preview, then (after your confirmation) creates JIRA Stories + Sub-tasks via the JIRA REST API.

**First-time setup:** The agent will create `jira_config.ini` from the template if it doesn't exist. Fill in your JIRA credentials once — all future runs reuse it.

## Examples

```
[WBS-to-JIRA] docs/wbs/wbs-cr5-vpoint-card-linkage.md
```

```
[WBS-to-JIRA] docs/wbs/wbs-store-pickup.md --dry-run
```

```
[WBS-to-JIRA] /home/user/Desktop/wbs-feature.md
```

## Skill Context

Read .claude/skills/wbs-to-jira/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
