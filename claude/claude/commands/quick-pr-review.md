---
description: "⚡ [Quick PR-Review] — Review any GitHub PR by URL with single-agent quick review"
---
# Quick Review GitHub PR by URL

Use the `[Quick PR-Review]` action tag. This command reviews any GitHub Pull Request URL using the quick-review pipeline (single-agent), then writes the report in `docs/quick-review/`.

## How It Works

| Step | What Happens |
|------|-------------|
| 1 | Parse PR URL -> extract owner/repo/number |
| 2 | Fetch PR data via `gh` CLI (preferred) or git fetch (fallback) |
| 3 | Run single-agent quick review across all dimensions |
| 4 | Generate quick-review format report in `docs/quick-review/` |

## Data Fetch Tiers

| Tier | Method | When Used |
|------|--------|-----------|
| 1 | `gh` CLI (or GitHub MCP, if connected) | Default - uses `gh auth status` |
| 2 | Git fetch (merge ref) | Fallback for same-origin repos |
| 3 | curl + PAT | Last resort for external repos |

## Verdict

- ✅ **Approve** - No high-risk issues
- 🟡 **Approve with Comments** - Notable medium-risk findings
- ⚠️ **Request Changes** - High-risk issues present

## Examples

```
[Quick PR-Review] https://github.com/owner/repo/pull/123
[Quick PR-Review]
```

## Skill Context

Read .claude/skills/core-essentials.md, .claude/skills/code-review/SKILL.md, and .claude/skills/quick-pr-review/SKILL.md - follow the skill workflow.

## Task

$ARGUMENTS
