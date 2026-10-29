---
description: "🏷️ [Register-Skill] — Register a new skill, action tag, and slash command in the orchestrator"
---
# Register New Skill

Use the `[Register-Skill]` action tag. Guides you through creating all required files and wiring for a new skill.

## What It Creates

| File | Purpose |
|------|---------|
| `.claude/skills/{name}.md` | Skill workflow file |
| `.claude/commands/{slug}.md` | Slash command (`/{slug}`) |
| Routing table entry | `CLAUDE.md` update |
| Master index entry | `SKILL.md` update |

## Examples

```
[Register-Skill] Create a skill for database migration review
```

```
[Register-Skill] Register a project skill for CR6 Phase1 Payment Gateway
```

```
[Register-Skill]
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/register-skill/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
