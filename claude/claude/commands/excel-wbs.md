---
description: "📊 [Excel-WBS] — Generate formatted WBS Excel (.xlsx) from a WBS markdown file"
---
# Excel WBS Generation

Use the `[Excel-WBS]` action tag with the path to a WBS markdown file.

Parses the WBS markdown (stories and sub-tasks), then generates a formatted Excel workbook matching `WBS-Sample.xlsx` — with colored rows, status/assignee/review dropdowns, and proper column widths.

## Examples

```
[Excel-WBS] docs/wbs/wbs-vpoint-card-linkage.md
```

```
[Excel-WBS] docs/wbs/wbs-store-pickup.md --cr "CR4 (Phase-2)" --assignees "Dev1,Dev2,Dev3"
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/excel-wbs-generation/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
