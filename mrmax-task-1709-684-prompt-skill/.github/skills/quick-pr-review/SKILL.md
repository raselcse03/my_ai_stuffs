---
name: "Quick PR Link Reviewer"
role: "Review any GitHub PR by URL with single-agent quick review and quick-review report output"
primary_tools: [mcp_gitkraken_pull_request_get_detail, mcp_gitkraken_git_log_or_diff, run_in_terminal, create_file, vscode_askQuestions]
scope: "full-repository"
---

# Quick GitHub PR Link Review Skill

**Prerequisites:** Review `core-essentials` for critical rules and `code-review` for quick-review standards.

Perform a lightweight review of any GitHub Pull Request using its URL.
This command reuses the same PR URL fetch strategy as `[PR-Review]`, but executes a
single-agent review aligned with `[Quick Review]` and writes output to `docs/quick-review/`.

## Usage

Trigger with the `[Quick PR-Review]` action tag:

```
@workspace [Quick PR-Review] https://github.com/owner/repo/pull/123
@workspace [Quick PR-Review]
```

When no URL is provided, prompt the user for it.

---

## Severity Scale

Use this severity scale consistently:

| Level | Criteria | Merge Impact |
|-------|----------|--------------|
| Critical | Security vulnerability, data loss risk, crash/outage, broken core functionality | Blocks merge |
| High | Significant bug, major performance issue, missing critical tests, auth/authz gap | Strongly blocks merge |
| Medium | Code smell, moderate performance concern, missing edge case tests, unclear error handling | Should fix, does not block |
| Low | Style inconsistency, minor refactoring opportunity, documentation gap | Optional improvement |

---

## Step 1: Obtain PR URL

If the user included a URL, extract it.
If no URL is present, ask for it:

```
Use vscode_askQuestions:
  header: "PR URL"
  question: "Paste the full GitHub PR URL (e.g., https://github.com/owner/repo/pull/123)"
```

### Parse URL

Expected pattern: `https://github.com/{owner}/{repo}/pull/{number}`

Extract:
- `PR_OWNER`
- `PR_REPO`
- `PR_NUMBER`

If parsing fails, report the invalid format and stop.

---

## Step 2: Fetch PR Data (Tiered)

Try tiers in order until one succeeds.

### Tier 1: GitKraken MCP (preferred)

Use pull request detail and changed files first:

```
mcp_gitkraken_pull_request_get_detail:
  provider: "github"
  repository_organization: "{PR_OWNER}"
  repository_name: "{PR_REPO}"
  pull_request_id: "{PR_NUMBER}"
  pull_request_files: true
```

Extract:
- `PR_TITLE`, `PR_AUTHOR`, `PR_BASE`, `PR_HEAD`, `PR_URL`, `PR_BODY`
- `PR_FILES` with per-file patch/additions/deletions

Construct `DIFF_CONTENT` from patches:

```
DIFF_CONTENT = ""
for each file in PR_FILES:
  DIFF_CONTENT += "diff --git a/{file.filename} b/{file.filename}\\n"
  DIFF_CONTENT += file.patch + "\\n"
```

If Tier 1 succeeds, continue to Step 3.

### Tier 2: Git Fetch Merge Ref (same-origin fallback)

If MCP is unavailable and repo remote matches current workspace:

```bash
git fetch origin \
  pull/{PR_NUMBER}/head:pr-review-{PR_NUMBER} \
  pull/{PR_NUMBER}/merge:pr-merge-{PR_NUMBER}
```

Extract merge parents:

```bash
PR_BASE_SHA=$(git log pr-merge-{PR_NUMBER} -1 --format="%P" | awk '{print $1}')
PR_HEAD_SHA=$(git log pr-merge-{PR_NUMBER} -1 --format="%P" | awk '{print $2}')
```

Get full diff and stats:

```bash
git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER} --stat
git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER}
```

Populate metadata:

```bash
PR_AUTHOR=$(git log pr-review-{PR_NUMBER} -1 --format="%an")
PR_TITLE=$(git log pr-review-{PR_NUMBER} -1 --format="%s")
PR_HEAD=$(git log pr-review-{PR_NUMBER} -1 --format="%H")
PR_URL="https://github.com/{PR_OWNER}/{PR_REPO}/pull/{PR_NUMBER}"
```

### Tier 3: Authenticated curl (last resort)

For external repos when Tier 1/2 cannot be used:
1. Ask the user to enter PAT directly in terminal (masked input).
2. Fetch via GitHub REST API with `Accept: application/vnd.github.v3.diff`.

---

## Step 3: Validate Diff and Detect Stack

### Validate Diff

If diff is empty, return: "No changes detected in this PR. Nothing to review." and stop.

### Diff Size Checks

- If diff > 3000 lines: warn about context/token size.
- If diff > 8000 lines: recommend scoping review to key directories.

### Detect Tech Stack

Infer from changed extensions:

| Extension | Stack |
|---|---|
| `.php` | PHP |
| `.twig` | Twig templates |
| `.js` / `.ts` | JavaScript / TypeScript |
| `.yaml` / `.yml` | Config |
| `.sql` | SQL |
| `.css` / `.scss` | Stylesheets |

### EC-Cube Overlay

If repo is this project or detected as EC-Cube:
- `IS_ECCUBE: true`
- Enforce EC-Cube rules from `core-essentials`

Otherwise:
- `IS_ECCUBE: false`
- Follow repository conventions and language standards

---

## Step 4: Execute Single-Agent Quick Review

Review the full diff in one pass with these dimensions:

1. Bugs and logic errors
2. Code smells and maintainability issues
3. Performance concerns
4. Security vulnerabilities
5. Backward compatibility and side effects
6. Architecture and convention alignment
7. Test coverage gaps
8. Readability and complexity
9. Cross-module impact
10. PSR/style compliance (or language equivalent)

For each finding, record:
- severity (Critical/High/Medium/Low)
- file and line
- title
- risk explanation
- suggested fix
- status (`Open` by default unless user confirms fixed)

If the same `file:line` appears multiple times, keep one item with the highest severity.

---

## Step 5: Tiering and Verdict

Map findings to tiers:

| Tier | Label | Emoji | Maps From |
|------|-------|-------|-----------|
| Tier 1 | High-Risk Issues (Must Fix) | 🔴 | Critical + High |
| Tier 2 | Medium-Risk Issues (Should Fix) | 🟡 | Medium |
| Tier 3 | Low-Risk / Suggestions (Nice-to-Have) | 🟢 | Low |

Verdict rules:

| Verdict | Emoji | Criteria |
|---------|-------|----------|
| Approve | ✅ | No Tier 1 issues. All findings are Tier 2/3. |
| Approve with Comments | 🟡 | No Tier 1 issues but notable Tier 2 findings remain. |
| Request Changes | ⚠️ | Any Tier 1 issues present. |

When `IS_ECCUBE` is true, always verify:
- [ ] No edits under `src/Eccube/`
- [ ] Constructor dependency injection is used
- [ ] Parameterized queries only
- [ ] Cache clear reminder for config changes

---

## Step 6: Generate Report

**Output location:** `./docs/quick-review/`

```bash
mkdir -p docs/quick-review
```

**Filename:** `QUICK-REVIEW-PR-{PR_OWNER}-{PR_REPO}-{PR_NUMBER}.md`

Use the same report section structure as `[Quick Review]` (which is aligned with `[Review]`):

```markdown
# Code Review Report

**PR:** `{PR_HEAD}` -> `{PR_BASE}`
**Date:** {YYYY-MM-DD}
**Reviewer:** Principal Software Engineer (AI-assisted)
**Verdict:** {verdict-emoji} **{Verdict}**

---

## Summary of Changes

{2-4 sentence description of what the PR does.}

### Files changed ({count})

| Layer | File |
|---|---|
| {layer} | `{filename}` |

---

## 🔴 High-Risk Issues (Must Fix)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} - `{filename}` · **{status}**

**File:** `{full/path/to/file}` - Line {line}

{Detailed description of the issue and why it matters.}

**Status:** {Open / Resolved.}

---

## 🟡 Medium-Risk Issues (Should Fix)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} - **{status}**

**File:** `{full/path/to/file}` - Line {line}

{Description and recommendation.}

**Status:** {Open / Resolved.}

---

## 🟢 Low-Risk / Suggestions (Nice-to-Have)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} - **{status}**

**File:** `{full/path/to/file}` - Line {line}

{Description and suggestion.}

---

## Overall PR Readiness

| Dimension | Rating |
|---|---|
| Correctness | {✅ / ⚠️ / ❌} {Brief note} |
| Security | {✅ / ⚠️ / ❌} {Brief note} |
| Architecture | {✅ / ⚠️ / ❌} {Brief note} |
| Consistency | {✅ / ⚠️ / ❌} {Brief note} |
| Maintainability | {✅ / ⚠️ / ❌} {Brief note} |
| Tests | {✅ / ⚠️ / ❌} {Brief note} |
| Overall | **{Verdict}** |

---

## File-Line Suggestion Table

| File | Line | Severity | Status | Suggestion |
|------|------|----------|--------|------------|
| {path} | {line} | {High/Medium/Low} | {✅ Fixed / ⚠️ Open} | {One-line suggestion} |

---
*Generated by [Quick PR-Review] command — {YYYY-MM-DD HH:MM}*
*Source: {PR_URL}*
```

---

## Step 7: Output and Cleanup

After report generation:
1. Return verdict with severity counts
2. Return path: `Created: docs/quick-review/QUICK-REVIEW-PR-{owner}-{repo}-{number}.md`
3. Return top 3 findings (tier + one-line summary)

Cleanup temporary branches if Tier 2 was used:

```bash
git branch -D pr-review-{PR_NUMBER} pr-merge-{PR_NUMBER} 2>/dev/null
```

---

## Return Contract

After completing the review, return **only**:
1. **Verdict** — ✅ Approve / 🟡 Approve with Comments / ⚠️ Request Changes
2. **Report path** — `Created: docs/quick-review/QUICK-REVIEW-PR-{owner}-{repo}-{number}.md`
3. **Top 3 findings** — severity tier (🔴/🟡/🟢) + 1-line description each

Do NOT paste the full report content in the chat response.

---

## Notes

- This skill is the URL-based companion to `[Quick Review]`
- Use single-agent analysis only (do not launch 7 parallel agents)
- Prefer GitKraken MCP first for auth and cross-repo support
- If Tier 2 is used, always clean temporary branches
