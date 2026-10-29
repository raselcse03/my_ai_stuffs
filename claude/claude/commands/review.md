---
description: "🔍 [Review] — Automated 7-agent code review (PR, branch, staged, diff)"
---
# Code Review

Use the `[Review]` action tag. Supports PR, branch, staged, and diff modes.

## Modes

| Mode | Usage |
|------|-------|
| PR | `[Review] pr 1234` |
| Branch | `[Review] branch feature/xyz` |
| Branch + Base | `[Review] branch feature/xyz base develop` |
| Staged | `[Review] staged` |
| Diff file | `[Review] diff changes.diff` |
| Default | `[Review]` (defaults to staged) |

## Examples

```
[Review] pr 1234
```

```
[Review] branch feature/loyalty-points
```

```
[Review] branch feature/loyalty-points base develop
```

```
[Review] staged
```

```
[Review][CR2-Phase2] pr 1234
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/review-command/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
