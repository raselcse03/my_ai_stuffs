---
description: "🔧 [Refactor] — Improve existing code structure"
---
# Refactoring

Use the `[Refactor]` action tag.

## Examples

```
@workspace [Refactor] OrderController::confirm() is 450 lines. Extract payment validation, stock check, and email sending into separate services.
```

```
@workspace [Refactor][CR2-Phase2] Extract pattern logic (P1-P6) from 001_001_checkout_installation.js into a testable module with pure functions.
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/refactoring/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Refactor] 
