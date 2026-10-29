---
name: pr-review
description: "Full 7-agent parallel review of any GitHub PR by URL using the gh CLI's authenticated session — no manual tokens needed. Use when given a GitHub PR link that needs comprehensive review. Triggered by the [PR-Review] tag or /pr-review."
---

# GitHub PR Link Review Skill

**Prerequisites:** Review `core-essentials` for critical rules, `code-review` for EC-Cube-specific patterns.

Perform a comprehensive code review of any GitHub Pull Request using its URL.
Uses the `gh` CLI's authenticated session (or a connected GitHub MCP server, if present) — **zero manual
credentials required** as long as `gh auth status` is logged in. Works with any repository the user has access to.
Reuses the same 7-agent parallel review pipeline and report format as the `[Review]` command.

## Usage

Trigger with the `[PR-Review]` action tag:

```
[PR-Review] https://github.com/owner/repo/pull/123
[PR-Review]
```

When no URL is provided, prompt the user for it.

---

## Severity Scale

All agents MUST use this consistent severity scale:

| Level | Criteria | Merge Impact |
|-------|----------|--------------|
| Critical | Security vulnerability, data loss risk, crash/outage, broken core functionality | Blocks merge |
| High | Significant bug, major performance issue, missing critical tests, auth/authz gap | Strongly blocks merge |
| Medium | Code smell, moderate performance concern, missing edge case tests, unclear error handling | Should fix, doesn't block |
| Low | Style inconsistency, minor refactoring opportunity, documentation gap | Optional improvement |

---

## Step 1: Obtain PR URL

If the user provided a URL in the prompt, extract it.
If no URL is present, ask:

```
Use AskUserQuestion:
  header: "PR URL"
  question: "Paste the full GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)"
```

### Parse the URL

Extract from the URL pattern `https://github.com/{owner}/{repo}/pull/{number}`:

- `PR_OWNER` — GitHub organization or user
- `PR_REPO` — Repository name
- `PR_NUMBER` — Pull request number

If the URL doesn't match the expected pattern, report the error and stop.

---

## Step 2: Fetch PR Data

Use a **tiered approach** to fetch PR metadata and diff. Try each method in order
until one succeeds.

### Tier 1: `gh` CLI (preferred)

```bash
gh pr view {PR_NUMBER} --repo {PR_OWNER}/{PR_REPO} \
  --json title,author,baseRefName,headRefName,url,state,body,additions,deletions,changedFiles,files
gh pr diff {PR_NUMBER} --repo {PR_OWNER}/{PR_REPO} > /tmp/pr-{PR_NUMBER}.diff
```

If `gh auth status` is not logged in, tell the user to run `gh auth login` first, then fall through to Tier 2/3.

If successful, extract:
- `PR_TITLE`, `PR_AUTHOR`, `PR_BASE` (`baseRefName`), `PR_HEAD` (`headRefName`), `PR_URL`, `PR_STATE`, `PR_BODY`
- `DIFF_CONTENT` — the contents of the fetched diff file

If a GitHub MCP server is connected (check available tools), its PR-detail/diff tools may be used instead of `gh` — same data, same fields.

If Tier 1 succeeds → skip to Step 3 validation.

### Tier 2: Git Fetch with Merge Ref (fallback for same-origin repos)

If `gh` is unavailable or fails, **and** the PR is from the current workspace's
remote (check `git remote -v` for `{PR_OWNER}/{PR_REPO}`), use git directly.

→ Full Tier 2 procedure (merge-ref fetch, base extraction, diff, metadata bash): read `references/fetch-fallbacks.md` when Tier 1 fails (do not load earlier).

### Tier 3: Authenticated curl (last resort)

If the PR is from a **different repository** not available locally, fall back to
GitHub REST API with user-provided PAT:

→ Full Tier 3 procedure: read `references/fetch-fallbacks.md` when Tiers 1–2 fail (do not load earlier).

---

## Step 3: Validate and Prepare Diff

### Validate Diff Content

If `DIFF_CONTENT` is empty, report: "No changes detected in this PR. Nothing to review." and stop.

### Diff Size Check

Count lines in `DIFF_CONTENT`:
- If > 3000 lines: Warn user about large diff and token usage.
- If > 8000 lines: Strongly recommend scoping the review or using `[Review]` locally.

### Extract Changed Files List

From the diff output, extract the list of changed filenames:

```bash
git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER} --name-only
```

### Cleanup Plan

After the review is complete (Step 8), clean up temporary branches:

```bash
git branch -D pr-review-{PR_NUMBER} pr-merge-{PR_NUMBER} 2>/dev/null
```

---

## Step 4: Detect Tech Stack

Set `TECH_STACK` and `IS_ECCUBE` from the changed files' extensions. Same-repo PRs (`bjit-inc/mrmax`) are EC-Cube; otherwise build the stack from detected extensions and set `IS_ECCUBE: false` (which drops EC-Cube rules from agent prompts).

→ Extension→stack lookup table and EC-Cube detection block: read `references/tech-stack-detection.md` when you reach this step (do not load earlier).

---

## Step 5: Launch 7 Parallel Review Agents

**⚠️ CRITICAL — PARALLEL EXECUTION REQUIRED:**
You MUST invoke all 7 `Agent` calls in a **single tool call batch**.
Do NOT call them sequentially.

Each agent receives:
- The full diff content
- The detected `TECH_STACK`
- The severity scale from above
- PR metadata (title, author, base, head, description)
- EC-Cube context only if `IS_ECCUBE` is true

### Agent Prompt Adaptation

When `IS_ECCUBE` is true, include in each agent prompt:
```
**EC-Cube Rules:**
- `src/Eccube/` must NEVER be modified — customization goes in `app/Customize/`
- All services must use dependency injection
- No Doctrine migrations — use manual SQL scripts
```

When `IS_ECCUBE` is false, replace with:
```
**General Rules:**
- Follow the project's established patterns and conventions
- Use dependency injection where the framework supports it
- Follow the language's standard coding style
```

### Agent Prompts (Agents 1–7)

→ Full agent prompts: read `.claude/skills/examples/review-agent-prompts.md` (shared with the `[Review]` skill) when you reach this step (do not load earlier). Apply these pr-review deltas:

- Prepend to every agent prompt: `**PR:** {PR_TITLE} by {PR_AUTHOR}` — and to Agent 1 also `**Branch:** {PR_HEAD} → {PR_BASE}`.
- The shared prompts hardcode EC-Cube context. When `IS_ECCUBE` is true, use them as-is, applying Agent 1's rules block per the adaptation above.
- When `IS_ECCUBE` is false: drop every "EC-Cube ... Context" block, swap Agent 1's EC-Cube Rules for the General Rules block above, and generalize stack-specific wording (Doctrine ORM → ORM, Twig `|raw` → unescaped output / raw filters, services.yaml → service/DI registration and configuration, Composer → dependency additions, JWT/session → session handling; drop Redis, PHPUnit/Codeception, and Twig template-rendering mentions).
- Agent 4, when `IS_ECCUBE` is false: add "OWASP Top 10 compliance" to Focus Areas.

---

## Step 6: Compile and Deduplicate Results

After all 7 agents complete: merge findings, deduplicate by `file:line` (keep highest severity; priority Security > Performance > Architecture > Code Quality), group into severity Tiers 1–3, number sequentially, determine the verdict (Approve / Approve with Comments / Request Changes), and run the EC-Cube checks when `IS_ECCUBE`.

→ Full dedup rules, tier mapping, verdict criteria, and EC-Cube checklist: read `references/scoring-rubric.md` when you reach this step (do not load earlier).

---

## Step 7: Generate Report

Create the report file:

**Output location:** `./docs/review/`

```bash
mkdir -p docs/review
```

**Filename:** `CODE-REVIEW-PR-{PR_OWNER}-{PR_REPO}-{PR_NUMBER}.md`

### Report Template

→ Full report template: read `references/report-template.md` when you reach this step (do not load earlier).

---

## Step 8: Output and Follow-up

After generating the report:

1. Display a summary to the user (verdict + count by severity tier)
2. Provide the report path: `Created: docs/review/CODE-REVIEW-PR-{owner}-{repo}-{number}.md`
3. Remind the user they can reference findings by section and number

### Cleanup

If Tier 2 (git fetch) was used, delete the temporary local branches:

```bash
git branch -D pr-review-{PR_NUMBER} pr-merge-{PR_NUMBER} 2>/dev/null
```

---

## Return Contract

After completing the review, return **only**:
1. **Verdict** — ✅ Approve / 🟡 Approve with Comments / ⚠️ Request Changes
2. **Report path** — `Created: docs/review/CODE-REVIEW-PR-{owner}-{repo}-{number}.md`
3. **Top 3 findings** — severity tier (🔴/🟡/🟢) + 1-line description each

Do NOT paste the full report content in the chat response.

---

## Notes

- **PARALLEL EXECUTION:** All 7 agents MUST be launched in a single tool call batch.
- **Merge ref is essential:** always fetch `refs/pull/N/merge` — its first parent is the PR's real base; without it you diff the wrong base and miss most changes.
- **Auth/tiers:** Tier 1 (`gh`) needs no local repo and uses its own stored auth; Tier 2 (git fetch) works only for same-origin PRs. Always delete temp branches (`pr-review-N`, `pr-merge-N`) after the report.
- **Same-repo optimization:** when the PR is from the current workspace repo, agents may also read local files for context around changed code.
- Review comments use a collaborative, educational tone; include code snippets for suggested fixes.

---

## Related Skills

`review-command` (7-agent local diff), `code-review` (quick single-agent), `quick-pr-review` (quick PR URL), `core-essentials`, `ai-disclosure`.
