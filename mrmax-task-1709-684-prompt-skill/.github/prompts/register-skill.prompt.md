---
description: "🏷️ [Register-Skill] — Register a new skill, action tag, and slash command in the orchestrator"
---
# Register New Skill

Use the `[Register-Skill]` action tag. Guides you through creating all required files and wiring for a new skill.

## What It Creates

| File | Purpose |
|------|---------|
| `.github/skills/{name}.md` | Skill workflow file |
| `.github/prompts/{slug}.prompt.md` | Slash command (`/{slug}`) |
| Routing table entry | `copilot-instructions.md` update |
| Master index entry | `SKILL.md` update |

## Examples

```
@workspace [Register-Skill] Create a skill for database migration review
```

```
@workspace [Register-Skill] Register a project skill for CR6 Phase1 Payment Gateway
```

```
@workspace [Register-Skill]
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/register-skill/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Register-Skill] 
