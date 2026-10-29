---
description: "🧪 [Unit Test] — Generate and run unit/integration tests from branch diff"
---
# Unit Testing

Use the `[Unit Test]` action tag. Generates test files based on the diff between your feature branch and base branch.

**Always specify both `branch` and `base` for accurate results.** Without `base`, tests may cover unrelated code changes.

## Modes

| Mode | Usage |
|------|-------|
| Branch + Base | `[Unit Test] branch feat/1709632-xyz base cr4-phase2` — **recommended** |
| Branch only | `[Unit Test] branch feat/1709632-xyz` — auto-detects base |
| Default | `[Unit Test]` — current branch, auto-detects base |

## Examples

```
@workspace [Unit Test] branch feat/1709632-packing-list-barcode-enhancement base cr4-phase2
```

```
@workspace [Unit Test] branch feat/1709632-packing-list-barcode-enhancement base feat/1709504-cr4-phase2
```

```
@workspace [Unit Test]
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/testing/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [Unit Test] 
