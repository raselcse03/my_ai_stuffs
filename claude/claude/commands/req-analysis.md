---
description: "📝 [Req-Analysis] — Analyze client requirements (PDF/Excel/Word/images) → SRS + WBS via 3-agent pipeline with maturity gate"
---
# Requirement Analysis

Use the `[Req-Analysis]` action tag. Attach requirement files (Excel, Word, PDF, or images) in the chat.

Three sub-agents (Maturity Assessor → Analyst → Reviewer) process the requirements. A maturity gate checks readiness before SRS generation — only 100% maturity auto-proceeds. Produces an SRS document, JIRA-ready WBS, and an agent-optimized project skill file.

## Examples

```
[Req-Analysis] Analyze the attached requirement document and produce SRS and WBS.
```

```
[Req-Analysis] --with-codebase Analyze these requirements and cross-check against the existing codebase for impact.
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/requirement-analysis/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
