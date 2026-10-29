---
description: "📝 [PR-Note] — Generate GitHub PR description with ticket link, summary, checklists, AI disclosure"
---
# PR Note

Use the `[PR-Note]` action tag. Generates a structured GitHub-compatible PR description.

**Always specify both `branch` and `base` for accurate results.** Without `base`, the diff may include unrelated commits from other branches.

## Modes

| Mode | Usage |
|------|-------|
| Branch + Base | `[PR-Note] branch feat/1709632-xyz base cr4-phase2` — **recommended** |
| Branch only | `[PR-Note] branch feat/1709632-xyz` — auto-detects base |
| Default | `[PR-Note]` — current branch, auto-detects base |

## Examples

```
@workspace [PR-Note] branch feat/1709632-packing-list-barcode-enhancement base cr4-phase2
```

```
@workspace [PR-Note] branch feat/1709632-packing-list-barcode-enhancement base feat/1709504-cr4-phase2
```

```
@workspace [PR-Note]
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/pr-note/SKILL.md — follow the skill workflow.

## Your prompt

@workspace [PR-Note] 
