---
description: "📋 [WBS] — Generate JIRA-ready Work Breakdown Structure from an existing SRS document"
---
# WBS Generation

Use the `[WBS]` action tag with the path to an SRS document.

Reads the SRS, gathers codebase context, and produces a detailed WBS with fully described Stories (Summary, Requirement Details, Acceptance Criteria, Dependencies, Corner Cases, Risks) and Sub-tasks (Description, Affected Files, Definition of Done), plus a Traceability Matrix ensuring full requirement coverage.

## Examples

```
@workspace [WBS] docs/srs-ac-installation.md
```

```
@workspace [WBS] docs/srs-loyalty-points.md
```

```
@workspace [WBS] /home/user/Desktop/requirements/srs-cr5.md
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/wbs-generation/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [WBS] 
