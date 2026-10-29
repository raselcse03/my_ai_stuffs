---
description: "🔬 [Investigation] — Trace code paths, assess impact (read-only, no code changes)"
---
# Investigation & Impact Analysis

Use the `[Investigation]` action tag. This agent is **read-only** — it maps dependencies and assesses blast radius but makes zero code changes.

## Examples

```
[Investigation][CR4-Phase2] What is the full blast radius of changing the stock deduction logic for order type 31? Which services, subscribers, batch jobs, and templates depend on the current flow?
```

```
[Investigation] Trace the complete order confirmation flow from CartController through payment processing to email dispatch. List every service, event subscriber, and template involved.
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/investigation/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
