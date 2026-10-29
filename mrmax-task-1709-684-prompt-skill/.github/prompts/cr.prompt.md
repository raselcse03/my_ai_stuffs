---
description: "📋 [CR] — Implement a client change request"
---
# Change Request

Use the `[CR]` action tag. Add a `[Project-Tag]` for project-specific context (recommended).

## Examples

```
@workspace [CR][CR2-Phase2] Add "ceiling_height" field to AC installation queries. Visible only when installation_type = NEW_INSTALLATION. Options: Under 2.5m / 2.5-3m / Over 3m.
```

```
@workspace [CR] Client requests adding a "gift wrapping" option at checkout. ¥330 charge, allow message (max 100 chars), show in order details and confirmation email.
```

```
@workspace [CR][CR4-Phase2] Add store backorder column to admin order list with sortable header
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/change-request/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [CR] 
