---
description: "📜 [Disclose] — Generate AI-generated code disclosure for a PR"
---
# AI Code Disclosure

Use the `[Disclose]` action tag. Analyzes a git diff to detect AI-generated code and produces a disclosure file.

## Examples

```
@workspace [Disclose] Analyze diff between feat/170931-cr2-phase2 and feat/1709216-cr2-phase1-enhancement
```

```
@workspace [Disclose] Analyze current branch against main
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/ai-disclosure/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Disclose] 
