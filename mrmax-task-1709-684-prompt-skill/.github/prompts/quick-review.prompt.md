---
description: "⚡ [Quick Review] — Lightweight single-agent code review (PR, branch, staged, diff) with [Review]-compatible report format"
---
# Quick Review

Use the `[Quick Review]` action tag. Single-agent review across 6 dimensions — faster than `[Review]`, with the same report structure as `[Review]`.

## Modes

| Mode | Usage |
|------|-------|
| PR | `[Quick Review] pr 1234` |
| Branch | `[Quick Review] branch feature/xyz` |
| Branch + Base | `[Quick Review] branch feature/xyz base develop` |
| Staged | `[Quick Review] staged` |
| Diff file | `[Quick Review] diff changes.diff` |
| Default | `[Quick Review]` (defaults to staged) |

## Examples

```
@workspace [Quick Review] pr 1234
```

```
@workspace [Quick Review] branch feature/loyalty-points
```

```
@workspace [Quick Review] branch feature/loyalty-points base develop
```

```
@workspace [Quick Review] staged
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/code-review/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Quick Review] 
