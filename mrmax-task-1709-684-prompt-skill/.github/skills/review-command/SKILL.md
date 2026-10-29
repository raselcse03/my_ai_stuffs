---
name: "Review Commander"
role: "Orchestrate 7-agent parallel code review — works with PR, branch, staged, or diff"
primary_tools: [grep_search, read_file, run_in_terminal, runSubagent, create_file]
scope: "full-repository"
---

# Code Review Command Skill

**Prerequisites:** Review `core-essentials` for critical rules, `code-review` for EC-Cube-specific patterns.

Perform a comprehensive code review using 7 specialized parallel agents. Tailored for
EC-Cube 4.x (Symfony/PHP) but adapts to any language in the diff.

## Usage

Trigger with the `[Review]` action tag:

```
@workspace [Review] pr 123
@workspace [Review] branch feature/auth-redesign
@workspace [Review] branch feature/auth-redesign base develop
@workspace [Review] staged
@workspace [Review] diff changes.diff
```

When no argument is provided, default to `staged` mode.

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

## Step 1: Parse Arguments and Determine Review Mode

Parse the arguments from the user's prompt:

| Mode | Example | Description |
|------|---------|-------------|
| pr | `[Review] pr 123` | Review a pull request by number |
| branch | `[Review] branch feature-x` | Compare branch against default branch (auto-detected) |
| branch + base | `[Review] branch feature-x base develop` | Compare branch against a specific base branch |
| staged | `[Review] staged` | Review currently staged changes |
| diff | `[Review] diff changes.diff` | Review a diff file |

Set variables:
- `REVIEW_MODE`: The detected mode
- `REVIEW_TARGET`: The specific target (PR number, branch name, file path)
- `BASE_BRANCH`: (branch mode only) Explicit base branch if provided after `base` keyword, otherwise auto-detected

---

## Step 2: Preflight Checks

Before gathering changes, validate the environment:

```bash
# Check if we're in a git repository
git rev-parse --is-inside-work-tree

# For PR mode: check gh CLI is installed and authenticated
# (only if REVIEW_MODE = pr)
command -v gh && gh auth status
```

If any check fails, stop and report the issue to the user.

---

## Step 3: Gather Changes Based on Mode

### Determine Base Branch

If `BASE_BRANCH` was explicitly provided (via `base <branch>` argument), use it directly.
Otherwise, auto-detect the default branch:

```bash
if [ -z "$BASE_BRANCH" ]; then
  BASE_BRANCH=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}')
  if [ -z "$BASE_BRANCH" ]; then
    BASE_BRANCH=$(git branch -l main master --format '%(refname:short)' | head -1)
  fi
  if [ -z "$BASE_BRANCH" ]; then
    BASE_BRANCH=main
  fi
fi
```

### Gather Diff Content

| Mode | Commands |
|------|----------|
| **pr** | `gh pr diff $REVIEW_TARGET` and `gh pr view $REVIEW_TARGET --json title,author,baseRefName,headRefName,additions,deletions,changedFiles,url` |
| **branch** | `git diff $BASE_BRANCH...$REVIEW_TARGET` and `git diff $BASE_BRANCH...$REVIEW_TARGET --stat` |
| **staged** | `git diff --cached` and `git diff --cached --stat` |
| **diff** | `cat $REVIEW_TARGET` (verify file exists first) |

### Validate Diff Content

```bash
# Check if diff is empty
if [ -z "$DIFF_CONTENT" ]; then
  echo "WARNING: No changes detected. Nothing to review."
  # Stop here
fi
```

### Diff Size Check

```bash
DIFF_LINES=$(echo "$DIFF_CONTENT" | wc -l)
```

- If `DIFF_LINES` > 3000: Warn user about large diff and token usage.
- If `DIFF_LINES` > 8000: Strongly recommend scoping the review to specific directories.

---

## Step 4: Detect Tech Stack

Auto-detect based on project files. For this EC-Cube project, the stack is known:

```
TECH_STACK: PHP 8.0+, Symfony 4/5, EC-Cube 4.x, Doctrine ORM, Twig, MySQL 8.0+
```

Also detect from changed files:
- `.php` → PHP
- `.twig` → Twig templates
- `.js` → JavaScript
- `.yaml/.yml` → Symfony config
- `.sql` → Database schema scripts

---

## Step 5: Launch 7 Parallel Review Agents

**⚠️ CRITICAL — PARALLEL EXECUTION REQUIRED:**
You MUST invoke all 7 `runSubagent` calls in a **single tool call batch** (one `<function_calls>` block).
Do NOT call them sequentially one after another — that defeats the purpose.
Since the 7 agents have zero dependencies on each other, they qualify for parallel invocation.

```
✅ CORRECT: All 7 runSubagent calls in ONE batch → run in parallel
❌ WRONG:  Call agent 1, wait, call agent 2, wait, ... → sequential, 7x slower
```

Each agent receives:
- The full diff content
- The detected `TECH_STACK`
- The severity scale from above
- EC-Cube-specific context: `app/Customize/` is the customization layer, `src/Eccube/` must NEVER be modified

### Agent Prompts (1–7)

**For full prompt templates for all 7 agents**, see `.github/skills/examples/review-agent-prompts.md`

| # | Agent | Focus |
|---|-------|-------|
| 1 | Code Quality | DRY, naming, SRP, complexity, fat controllers, inline CSS |
| 2 | Test Coverage | Unit tests, edge cases, mocking, 80%+ coverage target |
| 3 | Performance | N+1 queries, indexes, caching, pagination, transaction scope |
| 4 | Security | OWASP Top 10, SQL injection, XSS, CSRF, file uploads |
| 5 | Documentation | DocBlocks, README, config docs, compatibility guides |
| 6 | Error Handling | Try-catch, logging levels, graceful degradation, rollback |
| 7 | Configuration | services.yaml, SQL scripts, Composer deps, breaking changes |

---

## Step 6: Compile and Deduplicate Results

After all 7 agents complete:

### 6.1 Merge Findings
Collect all findings from all agents into a unified list.

### 6.2 Deduplicate
When the same `file:line` is flagged by multiple agents:
- Keep the **highest severity** rating
- Merge insights from both agents into a single finding
- Credit both perspectives
- Priority: Security > Performance > Architecture > Code Quality

### 6.3 Group by Severity Tier

Re-organize all deduplicated findings into three severity tiers:

| Tier | Label | Emoji | Maps From | Merge Impact |
|------|-------|-------|-----------|--------------|
| **Tier 1** | High-Risk Issues (Must Fix) | 🔴 | Critical + High | Blocks merge |
| **Tier 2** | Medium-Risk Issues (Should Fix) | 🟡 | Medium | Should fix, doesn't block |
| **Tier 3** | Low-Risk / Suggestions (Nice-to-Have) | 🟢 | Low | Optional improvement |

Number findings sequentially across all tiers (1, 2, 3, … N).

### 6.4 Determine Verdict

| Verdict | Emoji | Criteria |
|---------|-------|----------|
| **Approve** | ✅ | No Tier 1 issues. All findings are Tier 2/3. |
| **Approve with Comments** | 🟡 | No Tier 1 issues but notable Tier 2 findings remain. |
| **Request Changes** | ⚠️ | Any Tier 1 issues present. |

### 6.5 EC-Cube-Specific Checks
Always verify these regardless of agent findings:
- [ ] No files modified under `src/Eccube/`
- [ ] All services use constructor dependency injection
- [ ] Parameterized queries only (no SQL string concatenation)
- [ ] Cache cleared after config changes

---

## Step 7: Generate Report

Create the report file in the centralized output directory:

**Output location:** `./docs/review/`

Create the directory if it doesn't exist:
```bash
mkdir -p docs/review
```

| Mode | Filename |
|------|----------|
| PR | `CODE-REVIEW-PR-{number}.md` |
| Branch | `CODE-REVIEW-BRANCH-{safe-branch-name}.md` |
| Staged | `CODE-REVIEW-STAGED-{YYYY-MM-DD-HHMM}.md` |
| Diff | `CODE-REVIEW-DIFF-{safe-filename}.md` |

### Report Template

```markdown
# Code Review Report

**PR:** `{head-branch}` → `{base-branch}`
**Date:** {YYYY-MM-DD}
**Reviewer:** Principal Software Engineer (AI-assisted)
**Verdict:** {verdict-emoji} **{Verdict}**

---

## Summary of Changes

{2-4 sentence description of what the PR does — the core purpose and design approach.}

### Files changed ({count})

| Layer | File |
|---|---|
| {layer} | `{filename}` |
{... one row per changed file, grouped by layer: Controller, Entity, Repository, Service, Admin Service, Twig Extension, Templates, i18n, Config, Schema, Tests}

---

## 🔴 High-Risk Issues (Must Fix)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} — `{filename}` · **{status}**

**File:** `{full/path/to/file}` — Line {line}

{Detailed description of the issue: what's wrong, why it's dangerous, and the specific context.}

{If applicable, include a brief code snippet showing the problematic pattern and the recommended fix.}

**Status:** {Open / Resolved.}

---

{Repeat for each high-risk finding}

## 🟡 Medium-Risk Issues (Should Fix)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} — **{status}**

**File:** `{full/path/to/file}` — Line {line}

{Description of the concern and recommended approach.}

**Status:** {Open / Resolved.}

---

{Repeat for each medium-risk finding}

## 🟢 Low-Risk / Suggestions (Nice-to-Have)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} — **{status}**

**File:** `{full/path/to/file}` — Line {line}

{Description and suggestion.}

---

{Repeat for each low-risk finding}

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
{... one row per finding, ordered by severity desc}

---
*Generated by [Review] command — {YYYY-MM-DD HH:MM}*
```

---

## Step 8: Output and Follow-up

After generating the report:

1. Display a summary to the user (count by severity per category)
2. Provide the report path: `Created: docs/review/CODE-REVIEW-{identifier}.md`
3. Remind the user they can reference findings by section and number (e.g., "Security #2")

---

## Return Contract

After completing the review, return **only**:
1. **Verdict** — ✅ Approve / 🟡 Approve with Comments / ⚠️ Request Changes
2. **Report path** — `Created: docs/review/CODE-REVIEW-{identifier}.md`
3. **Top 3 findings** — severity tier (🔴/🟡/🟢) + 1-line description each

Do NOT paste the full report content in the chat response.

---

## Notes

- **PARALLEL EXECUTION:** All 7 agents MUST be launched in a single tool call batch — invoke all 7 `runSubagent` calls together, not sequentially. This is the single most important performance optimization.
- Each agent reads the relevant files from the diff and provides specific file:line references
- All agents use the same severity scale
- EC-Cube-specific rules are enforced as an overlay on all agents
- Findings are deduplicated before final report generation
- Review comments use a collaborative, educational tone — never confrontational
- Include code snippets for suggested fixes wherever applicable
- Consider the context of changes (feature, bugfix, refactor, hotfix) when calibrating severity
