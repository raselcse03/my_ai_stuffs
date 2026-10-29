---
description: "🔗 [PR-Review] — Review any GitHub PR by URL with 7 parallel agents (zero manual tokens needed)"
---
# Review GitHub PR by URL

Use the `[PR-Review]` action tag. This command performs a comprehensive 7-agent parallel code review of any GitHub Pull Request using its URL. Uses the `gh` CLI's authenticated session — no manual tokens needed.

## How It Works

| Step | What Happens |
|------|-------------|
| 1 | Parse PR URL → extract owner/repo/number |
| 2 | Fetch PR data via `gh` CLI (preferred) or git fetch (fallback) |
| 3 | Auto-detect tech stack from file extensions |
| 4 | Launch 7 parallel review agents (Quality, Tests, Performance, Security, Docs, Error Handling, Config) |
| 5 | Compile, deduplicate, and generate structured report |

## Data Fetch Tiers

| Tier | Method | When Used |
|------|--------|-----------|
| 1 | `gh` CLI (or GitHub MCP, if connected) | Default — uses `gh auth status` |
| 2 | Git fetch (merge ref) | Fallback for same-origin repos |
| 3 | curl + PAT | Last resort for external repos |

## Verdict

- ✅ **Approve** — No high-risk issues
- 🟡 **Approve with Comments** — Notable medium-risk findings
- ⚠️ **Request Changes** — High-risk issues present

## Examples

```
[PR-Review] https://github.com/owner/repo/pull/123
[PR-Review]
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/pr-review/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
