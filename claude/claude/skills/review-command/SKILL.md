---
name: review-command
description: "Full 7-agent parallel code review of this repo's PR number, branch, staged changes, or a diff file (for a GitHub PR URL use pr-review instead). Use for large or critical changes needing comprehensive review. Triggered by the [Review] tag or /review."
---

# Code Review Command Skill

**Prerequisites:** Review `core-essentials` for critical rules, `code-review` for EC-Cube-specific patterns.

Perform a comprehensive code review using 7 specialized parallel agents. Tailored for
EC-Cube 4.x (Symfony/PHP) but adapts to any language in the diff.

## Usage

Trigger with the `[Review]` action tag:

```
[Review] pr 123
[Review] branch feature/auth-redesign
[Review] branch feature/auth-redesign base develop
[Review] staged
[Review] diff changes.diff
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

→ Mode detection (pr / branch / branch+base / staged / diff), the `REVIEW_MODE` / `REVIEW_TARGET` / `BASE_BRANCH` variables, and the default-to-`staged` rule: read `references/diff-acquisition.md` when you reach this step (do not load earlier).

---

## Step 2: Preflight Checks

→ Environment validation (git-repo check; `gh` CLI install + auth for pr mode) and stop-on-failure: read `references/diff-acquisition.md` when you reach this step (do not load earlier).

---

## Step 3: Gather Changes Based on Mode

→ Base-branch detection, per-mode diff commands (pr / branch / staged / diff), empty-diff validation, and diff-size warnings (>3000 / >8000 lines): read `references/diff-acquisition.md` when you reach this step (do not load earlier).

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
You MUST invoke all 7 `Agent` calls in a **single tool call batch** (one `<function_calls>` block).
Do NOT call them sequentially one after another — that defeats the purpose.
Since the 7 agents have zero dependencies on each other, they qualify for parallel invocation.

```
✅ CORRECT: All 7 Agent calls in ONE batch → run in parallel
❌ WRONG:  Call agent 1, wait, call agent 2, wait, ... → sequential, 7x slower
```

Each agent receives:
- The full diff content
- The detected `TECH_STACK`
- The severity scale from above
- EC-Cube-specific context: `app/Customize/` is the customization layer, `src/Eccube/` must NEVER be modified

### Agent Prompts (1–7)

**For full prompt templates for all 7 agents**, see `.claude/skills/examples/review-agent-prompts.md`

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

→ Full report template: read `references/report-template.md` when you reach this step (do not load earlier).

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

- **PARALLEL EXECUTION:** All 7 agents MUST be launched in a single tool call batch — invoke all 7 `Agent` calls together, not sequentially. This is the single most important performance optimization.
- Each agent reads the relevant files from the diff and provides specific file:line references
- All agents use the same severity scale
- EC-Cube-specific rules are enforced as an overlay on all agents
- Findings are deduplicated before final report generation
- Review comments use a collaborative, educational tone — never confrontational
- Include code snippets for suggested fixes wherever applicable
- Consider the context of changes (feature, bugfix, refactor, hotfix) when calibrating severity
