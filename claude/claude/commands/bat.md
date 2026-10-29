---
description: "📊 [BAT] — Generate Developer BAT (Basic Acceptance Test) CSV reports from diffs"
---
# BAT Test Case Generation

Use the `[BAT]` action tag. Analyzes code diffs and generates structured BAT CSV test case reports per module.

## Modes

| Mode | Usage |
|------|-------|
| Branch | `[BAT] branch feat/P1709-733-posdata` |
| Branch + Base | `[BAT] branch feat/P1709-733-posdata base staging` |
| PR | `[BAT] pr 12345` |
| Staged | `[BAT] staged` |

## Examples

```
[BAT] branch feat/P1709-733-posdata
```

```
[BAT] branch feat/P1709-733-posdata base staging
```

```
[BAT] staged
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/bat-generation/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
