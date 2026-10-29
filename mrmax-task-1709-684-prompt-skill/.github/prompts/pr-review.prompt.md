---
description: "🔗 [PR-Review] — Review any GitHub PR by URL with 7 parallel agents (zero manual tokens needed)"
---
# Review GitHub PR by URL

Use the `[PR-Review]` action tag. This command performs a comprehensive 7-agent parallel code review of any GitHub Pull Request using its URL. Uses VS Code's built-in GitHub authentication — no manual tokens needed.

## How It Works

| Step | What Happens |
|------|-------------|
| 1 | Parse PR URL → extract owner/repo/number |
| 2 | Fetch PR data via GitKraken MCP (preferred) or git fetch (fallback) |
| 3 | Auto-detect tech stack from file extensions |
| 4 | Launch 7 parallel review agents (Quality, Tests, Performance, Security, Docs, Error Handling, Config) |
| 5 | Compile, deduplicate, and generate structured report |

## Data Fetch Tiers

| Tier | Method | When Used |
|------|--------|-----------|
| 1 | GitKraken MCP tools | Default — uses VS Code GitHub auth |
| 2 | Git fetch (merge ref) | Fallback for same-origin repos |
| 3 | curl + PAT | Last resort for external repos |

## Verdict

- ✅ **Approve** — No high-risk issues
- 🟡 **Approve with Comments** — Notable medium-risk findings
- ⚠️ **Request Changes** — High-risk issues present

## Examples

```
@workspace [PR-Review] https://github.com/owner/repo/pull/123
@workspace [PR-Review]
```

## Skill Context

Read #file:.github/skills/core-essentials.md and #file:.github/skills/pr-review/SKILL.md — follow the skill workflow.
