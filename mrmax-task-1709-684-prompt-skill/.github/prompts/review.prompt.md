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
@workspace [Review] pr 1234
```

```
@workspace [Review] branch feature/loyalty-points
```

```
@workspace [Review] branch feature/loyalty-points base develop
```

```
@workspace [Review] staged
```

```
@workspace [Review][CR2-Phase2] pr 1234
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/review-command/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Review] 
