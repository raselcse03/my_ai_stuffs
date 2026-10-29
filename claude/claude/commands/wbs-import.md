---
description: "📥 [WBS-Import] — Reverse-generate enriched WBS markdown from Excel-WBS (.xlsx) or CSV"
---
# WBS Import (Reverse Excel-WBS)

Use the `[WBS-Import]` action tag with the path to an Excel-WBS file (.xlsx) or its CSV export.

Parses the Excel/CSV skeleton (stories, sub-tasks, effort hours, assignees, status), then enriches it with requirement details, acceptance criteria, corner cases, and traceability by cross-referencing an attached SRS document and optionally a project skill file.

## Required Attachments

- **Excel-WBS or CSV file** — the source spreadsheet (path in the prompt)
- **SRS document** — attach or pass via `--srs` flag (required for enrichment)
- **Project skill file** — attach optionally for domain-specific file maps and business rules

## Examples

```
[WBS-Import] docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
  (attach: docs/srs/srs-vpoint-card-linkage.md)
```

```
[WBS-Import] /tmp/cr4-wbs-export.csv --srs docs/srs/srs-store-pickup.md
  (attach: .claude/skills/requirements/cr4-phase2-store-pickup-inventory.md)
```

```
[WBS-Import] docs/wbs/excel/ac-installation-wbs.xlsx
  (attach: docs/srs/srs-ac-installation.md, .claude/skills/requirements/cr2-phase2-ac-installation.md)
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/wbs-import/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
