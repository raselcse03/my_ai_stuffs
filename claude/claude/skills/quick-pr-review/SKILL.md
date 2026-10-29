---
name: quick-pr-review
description: "Quick single-agent review of any GitHub PR by URL using the gh CLI's authenticated session — lighter than the 7-agent [PR-Review]. Use for fast feedback on a remote PR link. Triggered by the [Quick PR-Review] tag or /quick-pr-review."
---

# Quick GitHub PR Link Review Skill

**Prerequisites:** Review `core-essentials` for critical rules and `code-review` for quick-review standards.

Perform a lightweight review of any GitHub Pull Request using its URL.
This command reuses the same PR URL fetch strategy as `[PR-Review]`, but executes a
single-agent review aligned with `[Quick Review]` and writes output to `docs/quick-review/`.

## Usage

Trigger with the `[Quick PR-Review]` action tag:

```
[Quick PR-Review] https://github.com/owner/repo/pull/123
[Quick PR-Review]
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
Use AskUserQuestion:
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

### Tier 1: `gh` CLI (preferred)

```bash
gh pr view {PR_NUMBER} --repo {PR_OWNER}/{PR_REPO} \
  --json title,author,baseRefName,headRefName,url,body,additions,deletions,changedFiles,files
gh pr diff {PR_NUMBER} --repo {PR_OWNER}/{PR_REPO} > /tmp/pr-{PR_NUMBER}.diff
```

Extract:
- `PR_TITLE`, `PR_AUTHOR`, `PR_BASE` (`baseRefName`), `PR_HEAD` (`headRefName`), `PR_URL`, `PR_BODY`
- `DIFF_CONTENT` — the contents of the fetched diff file

If a GitHub MCP server is connected, its equivalent PR-detail/diff tools may be used instead — same fields.

If Tier 1 succeeds, continue to Step 3.

### Tier 2 & Tier 3: Fallbacks (shared with `[PR-Review]`)

If `gh` is unavailable, use the shared fallback procedure — Tier 2 (git fetch merge ref, same-origin) and Tier 3 (authenticated curl for external repos).

→ Read `../pr-review/references/fetch-fallbacks.md` when Tier 1 fails (do not load earlier).

**Deltas for quick-pr-review (≤5 lines):** same `pr-review-{PR_NUMBER}` / `pr-merge-{PR_NUMBER}` refs, but this skill needs only `PR_AUTHOR`, `PR_TITLE`, `PR_HEAD`, `PR_URL` from the Tier-2 metadata block; the shared file's `PR_BASE_BRANCH`, `CHANGED_FILES`, `ADDITIONS`, `DELETIONS` extras are optional here.

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

→ Full report template: read `references/report-template.md` when you reach this step (do not load earlier).

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
- Prefer the `gh` CLI first for auth and cross-repo support
- If Tier 2 is used, always clean temporary branches
