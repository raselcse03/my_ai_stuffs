---
description: "📝 [Req-Analysis] — Analyze client requirements (PDF/Excel/Word/images) → SRS + WBS via 3-agent pipeline with maturity gate"
---
# Requirement Analysis

Use the `[Req-Analysis]` action tag. Attach requirement files (Excel, Word, PDF, or images) in the chat.

Three sub-agents (Maturity Assessor → Analyst → Reviewer) process the requirements. A maturity gate checks readiness before SRS generation — only 100% maturity auto-proceeds. Produces an SRS document, JIRA-ready WBS, and an agent-optimized project skill file.

## Examples

```
@workspace [Req-Analysis] Analyze the attached requirement document and produce SRS and WBS.
```

```
@workspace [Req-Analysis] --with-codebase Analyze these requirements and cross-check against the existing codebase for impact.
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/requirement-analysis/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Req-Analysis] 
