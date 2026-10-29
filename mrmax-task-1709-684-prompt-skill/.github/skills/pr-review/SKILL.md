---
name: "PR Link Reviewer"
role: "Review any GitHub PR by URL — uses VS Code's GitHub auth, no manual tokens needed"
primary_tools: [mcp_gitkraken_pull_request_get_detail, mcp_gitkraken_git_log_or_diff, runSubagent, create_file, vscode_askQuestions]
scope: "full-repository"
---

# GitHub PR Link Review Skill

**Prerequisites:** Review `core-essentials` for critical rules, `code-review` for EC-Cube-specific patterns.

Perform a comprehensive code review of any GitHub Pull Request using its URL.
Uses VS Code's built-in GitHub authentication via GitKraken MCP tools — **zero manual
credentials required**. Works with any repository the user has access to in VS Code.
Reuses the same 7-agent parallel review pipeline and report format as the `[Review]` command.

## Usage

Trigger with the `[PR-Review]` action tag:

```
@workspace [PR-Review] https://github.com/owner/repo/pull/123
@workspace [PR-Review]
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
Use vscode_askQuestions:
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

### Tier 1: GitKraken MCP Tools (preferred)

```
mcp_gitkraken_pull_request_get_detail:
  provider: "github"
  repository_organization: "{PR_OWNER}"
  repository_name: "{PR_REPO}"
  pull_request_id: "{PR_NUMBER}"
  pull_request_files: true
```

If successful, extract:
- `PR_TITLE`, `PR_AUTHOR`, `PR_BASE`, `PR_HEAD`, `PR_URL`, `PR_STATE`, `PR_BODY`
- `PR_FILES` — changed files with filenames, additions, deletions, and patch content

Then construct `DIFF_CONTENT` from file patches:
```
DIFF_CONTENT = ""
for each file in PR_FILES:
  DIFF_CONTENT += "diff --git a/{file.filename} b/{file.filename}\n"
  DIFF_CONTENT += file.patch + "\n"
```

If MCP succeeds → skip to Step 3 validation.

### Tier 2: Git Fetch with Merge Ref (fallback for same-origin repos)

If MCP tools require sign-in or fail, **and** the PR is from the current workspace's
remote (check `git remote -v` for `{PR_OWNER}/{PR_REPO}`), use git directly.

**⚠️ CRITICAL: Fetch BOTH the head ref AND the merge ref.**

The merge ref is essential — it contains the PR's actual base as its first parent.
Without it, you cannot determine the correct base branch.

```bash
# Fetch BOTH refs in a single command
git fetch origin \
  pull/{PR_NUMBER}/head:pr-review-{PR_NUMBER} \
  pull/{PR_NUMBER}/merge:pr-merge-{PR_NUMBER}
```

**Extract the real base from the merge ref:**

```bash
# The merge commit's first parent is the PR's target branch tip
PR_BASE_SHA=$(git log pr-merge-{PR_NUMBER} -1 --format="%P" | awk '{print $1}')

# The second parent is the PR head (should match pr-review-{PR_NUMBER})
PR_HEAD_SHA=$(git log pr-merge-{PR_NUMBER} -1 --format="%P" | awk '{print $2}')
```

**Why this matters:** GitHub's merge ref (`refs/pull/N/merge`) is an auto-generated
merge commit with exactly two parents:
- **First parent** = tip of the PR's target/base branch
- **Second parent** = tip of the PR's head branch

Without the merge ref, you'd have to guess the base branch by looking at remote
branch names — this is **unreliable** and will produce incomplete diffs (e.g., only
the last commit instead of all PR commits).

**Get the diff using the correct base:**

```bash
# This captures ALL commits in the PR, not just the last one
git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER} --stat
git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER}
```

**Extract PR metadata from git:**

```bash
# Get commit info for the PR head
PR_AUTHOR=$(git log pr-review-{PR_NUMBER} -1 --format="%an")
PR_TITLE=$(git log pr-review-{PR_NUMBER} -1 --format="%s")
PR_HEAD=$(git log pr-review-{PR_NUMBER} -1 --format="%H")
PR_URL="https://github.com/{PR_OWNER}/{PR_REPO}/pull/{PR_NUMBER}"

# Try to find the base branch name from the base SHA
PR_BASE_BRANCH=$(git branch -r --contains ${PR_BASE_SHA} | head -1 | sed 's/^ *//' | sed 's|origin/||')

# Count changes
CHANGED_FILES=$(git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER} --name-only | wc -l)
ADDITIONS=$(git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER} --numstat | awk '{s+=$1} END {print s}')
DELETIONS=$(git diff ${PR_BASE_SHA}...pr-review-{PR_NUMBER} --numstat | awk '{s+=$2} END {print s}')
```

### Tier 3: Authenticated curl (last resort)

If the PR is from a **different repository** not available locally, fall back to
GitHub REST API with user-provided PAT:

1. Tell user: "This PR is from an external repo. Please type your GitHub PAT
   directly into the terminal (masked input)."
2. Use `read -s` for secure input in terminal
3. Fetch via `curl -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.v3.diff"`

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

Auto-detect from changed file extensions:

| Extension | Stack |
|---|---|
| `.php` | PHP |
| `.twig` | Twig templates |
| `.js` / `.ts` | JavaScript / TypeScript |
| `.yaml` / `.yml` | Configuration |
| `.sql` | Database scripts |
| `.css` / `.scss` | Stylesheets |
| `.py` | Python |
| `.java` | Java |
| `.go` | Go |

### EC-Cube Detection

If the PR is from the same repository (`bjit-inc/mrmax` or the current repo's remote):

```
TECH_STACK: PHP 8.0+, Symfony 4/5, EC-Cube 4.x, Doctrine ORM, Twig, MySQL 8.0+
IS_ECCUBE: true
```

Otherwise, build `TECH_STACK` from detected extensions and set `IS_ECCUBE: false`.

When `IS_ECCUBE` is false, omit EC-Cube-specific rules from agent prompts.

---

## Step 5: Launch 7 Parallel Review Agents

**⚠️ CRITICAL — PARALLEL EXECUTION REQUIRED:**
You MUST invoke all 7 `runSubagent` calls in a **single tool call batch**.
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

### Agent 1: Code Quality Review

```
You are reviewing code changes for CODE QUALITY.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Branch:** {PR_HEAD} → {PR_BASE}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

{EC-Cube rules OR General rules based on IS_ECCUBE}

**Focus Areas:**
- Code duplication and DRY violations
- Naming conventions (variables, functions, classes — clear, consistent)
- Single Responsibility Principle adherence
- Dead code and unused imports
- Function/method length and complexity (cyclomatic complexity)
- Magic numbers and hardcoded values (use constants)
- Deep nesting (> 3 levels)
- Fat controllers (business logic belongs in services)
- Inline CSS (`style="..."`) — must use external CSS files or utility classes
- Proper type hints on all parameters and return types
- DocBlocks on public methods

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |
|---|----------|------|------|-------|----------------|

#### Review Comments
For EACH finding, provide:
##### #N: {Brief title}
File: `{path}:{line}`
> [Comment in collaborative tone with code suggestion if applicable]
```

### Agent 2: Test Coverage Review

```
You are reviewing code changes for TEST COVERAGE.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- Presence of unit tests for new/modified code
- Edge case coverage (null, empty, boundary values)
- Error and exception scenario testing
- Mock and stub appropriateness (not over-mocking)
- Test isolation and independence
- Assertion quality and completeness
- Integration test considerations for data access methods
- Regression tests for bug fixes

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Missing Tests
- `{source file}:{function/method}` — {what should be tested} — Priority: {High/Medium/Low}

#### Review Comments
For EACH finding, provide collaborative comment with example test code.
```

### Agent 3: Performance Review

```
You are reviewing code changes for PERFORMANCE.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- N+1 query problems (ORM lazy loading)
- Missing database indexes on frequently queried columns
- SELECT * instead of specific columns
- Missing pagination on large result sets
- Unnecessary computations inside loops
- Missing caching opportunities
- Large data structure operations (deep clones, array copies)
- Transaction scope (keep transactions short)
- Batch processing opportunities

For each finding, estimate impact at 10x, 100x, 1000x data scale.

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Impact | Recommendation |

#### Review Comments
For EACH finding, include performance impact estimation and optimized code.
```

### Agent 4: Security Review

```
You are reviewing code changes for SECURITY.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- SQL injection (raw SQL with string concatenation)
- XSS (Cross-Site Scripting) — unescaped output, raw filters
- CSRF protection on forms
- Authentication and authorization checks
- Secrets and credentials exposure (hardcoded keys in code)
- File upload security (mime type validation, extension whitelist, size limits)
- Sensitive data in logs or error messages (PII, passwords, tokens)
- Path traversal risks
- Session handling
- Input validation on all external inputs
- OWASP Top 10 compliance

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Vulnerability | Risk | Remediation |

#### OWASP Compliance
For each applicable OWASP Top 10 category: ✅ Compliant, ⚠️ Concern, ❌ Violation, N/A

#### Review Comments
For Critical/High: be direct about the risk. Include secure code alternatives.
```

### Agent 5: Documentation Review

```
You are reviewing code changes for DOCUMENTATION.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- DocBlocks on public APIs and exported functions
- Code comments for complex logic (the "why", not the "what")
- README updates for new features or changed behavior
- Configuration documentation (new env vars, config files)
- Compatibility guides if breaking changes
- Inline documentation quality

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Documentation Checklist
Mark each as ✅, ⚠️, ❌, or N/A:
- DocBlocks on public methods
- Complex logic commented
- Configuration changes documented
- Compatibility guide provided (if needed)

#### Review Comments
Provide example documentation text when suggesting additions.
```

### Agent 6: Error Handling & Observability Review

```
You are reviewing code changes for ERROR HANDLING & OBSERVABILITY.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- Try-catch blocks — appropriate and specific exception types
- Error message clarity and usefulness
- Logging quality (appropriate levels: debug, info, warn, error)
- Sensitive data NOT in logs
- Graceful degradation patterns
- Error propagation (are errors properly bubbled up?)
- Stack trace preservation
- User-facing vs. internal error messages
- Transaction rollback on failure

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Observability Checklist
Mark each as ✅, ⚠️, ❌, or N/A:
- Appropriate logging levels
- No sensitive data in logs
- Error messages clear and actionable
- Graceful degradation implemented
- Transaction rollback on failure

#### Review Comments
Include error handling code examples.
```

### Agent 7: Configuration & Dependencies Review

```
You are reviewing code changes for CONFIGURATION & DEPENDENCIES.

**PR:** {PR_TITLE} by {PR_AUTHOR}
**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- Service/DI registration and configuration
- Environment variable usage
- Database schema script quality (reversible? idempotent?)
- Dependency additions (size, maintenance, license)
- Breaking changes and backward compatibility
- Framework configuration changes
- Default values appropriateness
- Feature flags

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Dependency Changes
For each new/updated dependency:
| Package | Previous Version | New Version | Risk |

#### Breaking Changes
List any breaking changes with compatibility steps, or "None identified."

#### Review Comments
Flag deployment risks clearly but collaboratively.
```

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

### 6.5 EC-Cube-Specific Checks (only when IS_ECCUBE is true)

- [ ] No files modified under `src/Eccube/`
- [ ] All services use constructor dependency injection
- [ ] Parameterized queries only (no SQL string concatenation)
- [ ] Cache cleared after config changes

---

## Step 7: Generate Report

Create the report file:

**Output location:** `./docs/review/`

```bash
mkdir -p docs/review
```

**Filename:** `CODE-REVIEW-PR-{PR_OWNER}-{PR_REPO}-{PR_NUMBER}.md`

### Report Template

```markdown
# Code Review Report

**PR:** [{PR_TITLE}]({PR_URL})
**Repository:** `{PR_OWNER}/{PR_REPO}`
**Branch:** `{PR_HEAD}` → `{PR_BASE}`
**Author:** @{PR_AUTHOR}
**Changes:** +{PR_ADDITIONS} / -{PR_DELETIONS} across {PR_CHANGED_FILES} files
**Date:** {YYYY-MM-DD}
**Reviewer:** Principal Software Engineer (AI-assisted)
**Verdict:** {verdict-emoji} **{Verdict}**
**Source:** GitHub PR #{PR_NUMBER} (reviewed via API)

---

## Summary of Changes

{2-4 sentence description of what the PR does — the core purpose and design approach.}

### PR Description

> {PR_BODY — the original PR description from GitHub}

### Files changed ({count})

| Layer | File |
|---|---|
| {layer} | `{filename}` |
{... one row per changed file, grouped by layer}

---

## 🔴 High-Risk Issues (Must Fix)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} — `{filename}` · **{status}**

**File:** `{full/path/to/file}` — Line {line}

{Detailed description of the issue.}

**Status:** {Open / Resolved.}

---

## 🟡 Medium-Risk Issues (Should Fix)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} — **{status}**

**File:** `{full/path/to/file}` — Line {line}

{Description of the concern and recommended approach.}

**Status:** {Open / Resolved.}

---

## 🟢 Low-Risk / Suggestions (Nice-to-Have)

{If no issues in this tier: "None identified."}

### {N}. {Brief Title} — **{status}**

**File:** `{full/path/to/file}` — Line {line}

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
*Generated by [PR-Review] command — {YYYY-MM-DD HH:MM}*
*Source: {PR_URL}*
```

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

- **PARALLEL EXECUTION:** All 7 agents MUST be launched in a single tool call batch
- **Merge ref is essential:** Always fetch `refs/pull/N/merge` — its first parent is the PR's real base. Without it, you'll diff against the wrong base and miss most changes
- **No local repo required for Tier 1:** MCP tools work via GitHub API independently
- **Tier 2 requires same-origin repo:** Git fetch fallback only works when the PR is from the same remote as the workspace
- **Zero credentials for Tier 1-2:** MCP uses VS Code auth; git uses SSH keys
- **Cleanup:** Always delete temporary branches (`pr-review-N`, `pr-merge-N`) after report generation
- **Same-repo optimization:** When the PR is from the current workspace repo, agents can also read local files for additional context around changed code
- Review comments use a collaborative, educational tone
- Include code snippets for suggested fixes wherever applicable

---

## Related Skills

- **`code-review`** — Single-agent quick review (local diff, 6 dimensions)
- **`review-command`** — 7-agent parallel review (local diff — PR, branch, staged)
- **`core-essentials`** — Critical rules and directory structure
- **`ai-disclosure`** — AI-generated code disclosure for PRs
