# PR Note Section Templates

Reference for the `pr-note` skill — loaded at Step 4 (Analyze Changes & Generate Sections): per-section analysis instructions and verbatim output templates for the PR Title line and Sections 1–10.

### PR Title (auto-generated from branch name)

Generate a short, human-readable title from the branch's descriptive suffix — the part after
the ticket digits (e.g. `EC-Checkout-V-Point-Exchange-Flow` from
`feat/P1709-1213-EC-Checkout-V-Point-Exchange-Flow`):

1. Replace hyphens with spaces and Title Case each word.
2. Re-hyphenate domain compound terms that appear as single identifiers in the diff/codebase
   (e.g. `Vpoint` classes/services → render as "V-Point").
3. If the description reads as a feature area followed by a specific change (e.g. "EC Checkout"
   + "V-Point Exchange Flow"), separate them with " - " for readability.

Output as the very first line of the file, above Section 1:

```markdown
PR Title: {generated title}
```

**Example:** branch `feat/P1709-1213-EC-Checkout-V-Point-Exchange-Flow` →
`PR Title: EC Checkout - V-Point Exchange Flow`

If the branch suffix can't be parsed into a meaningful title, fall back to the raw branch name.

### Section 1: Related Tickets (auto-generated)

Use the `TICKET_ID` from Step 2:

```markdown
### 1. Related Tickets

- https://bjit.atlassian.net/browse/{TICKET_ID}
```

### Section 2: What's this PR do? (auto-generated from diff)

Analyze the diff to produce a concise bullet-point summary of what changed.
Focus on:
- New files added and their purpose
- Modified logic (what behavior changed)
- New UI elements, columns, fields added
- New services, controllers, or templates

Write **1-3 short bullet points** (roughly 10-15 words each). Summarize, don't narrate — state
the change, not the implementation detail. Use technical but readable language.

**If the diff is empty or no meaningful code changes detected, output:**
```markdown
### 2. What's this PR do?
- N/A
```

### Section 3: Impact range (auto-generated from diff)

From the changed files, identify which user-facing areas are affected:
- Admin pages (which specific pages)
- Frontend pages
- Batch jobs
- API endpoints
- PDF/CSV exports
- Email templates

Write as a short bullet list of affected areas — a few words each (e.g. "Checkout page —
coupon/V-Point redemption"), not full sentences.

**If no user-facing impact identified, output:**
```markdown
### 3. Impact range
- N/A
```

### Section 4: Performance (static checklist)

Always output this exact checklist:

```markdown
### 4. Performance (Required related Model and Logic)
- [ ] Resolved n + 1 query
- [ ] Time run batch task : should be < 30 minutes
- [ ] API response < 1000 ms
- [ ] Generated SQL query Explain
- [ ] Check memory usage: it should be < 100 MB
```

### Section 5: Command (auto-generated from diff analysis)

Detect two command types from the diff and output both under `### 5. Command`.
Use `- N/A` when nothing is detected for a sub-section.

##### 5a. Unit Test

Scan the diff for test files (`tests/`, `Tests/`, or `*Test.php`).
For each test file found, list: `- docker exec ec-cube bin/phpunit {test_file_path}`

**Example** (for a diff touching V-Point service/repository/processor tests):
```
- docker exec ec-cube bin/phpunit tests/Customize/Service/Vpoint/VpointApiClientServiceTest.php
- docker exec ec-cube bin/phpunit tests/Customize/Service/Vpoint/VpointCouponServiceTest.php
- docker exec ec-cube bin/phpunit tests/Customize/Service/Vpoint/VpointRedemptionServiceTest.php
- docker exec ec-cube bin/phpunit tests/Customize/Service/Vpoint/VpointRuntimeConfigServiceTest.php
- docker exec ec-cube bin/phpunit tests/Customize/Service/Vpoint/VpointReservationValidationResultTest.php
- docker exec ec-cube bin/phpunit tests/Customize/Service/PurchaseFlow/Processor/CouponDiscountProcessTest.php
- docker exec ec-cube bin/phpunit tests/Customize/Repository/VpointRedeemResultRepositoryTest.php
```

##### 5b. Schema Update

Scan the diff for database schema changes: new/modified/removed `@ORM\Column` properties,
entity trait changes, `->addColumn`, `ADD COLUMN`, `ALTER TABLE`, or SQL migration scripts.
If detected, list:
```
- docker exec ec-cube bin/console doctrine:cache:clear-metadata
- docker exec ec-cube bin/console doctrine:cache:clear-query
- docker exec ec-cube bin/console doctrine:cache:clear-result
- docker exec ec-cube bin/console cache:clear --no-warmup
- docker exec ec-cube bin/console doctrine:schema:update --dump-sql --force
```

##### Output format

```markdown
### 5. Command
#### 5a. Unit Test
- {test command(s) or N/A}

#### 5b. Schema Update
- {schema update command or N/A}
```

### Section 6: Checklists (static)

Always output this exact checklist:

```markdown
### 6. Checklists

- [ ] Is checked impact range of code update?
- [ ] Update the PR URL into related tickets.
- [ ] Manual test at local.
- [ ] Code style check successful.
- [ ] Commit convention is correct.
- [ ] Branch convention is correct.
- [ ] Without any debug code.
- [ ] Without any hard-coded in the code.
- [ ] Does the code follow DRY?: Do not Repeat Yourself?
- [ ] Do the names used in the program convey intent?
- [ ] Is there any new exception that are inserted in code, make sure it will be caught in callers ?
- [ ] Is the code related to only the specific issue assigned to you?
- [ ] Do loops have a set length and correct termination conditions?
- [ ] Is there any incomplete code? If so, should it be removed or flagged with a suitable marker like 'TODO'?
```

### Section 7: Screenshots (static)

```markdown
### 7. Screenshots

- N/A
```

### Section 8: AI-generated code (sub-agent delegation)

Use the `ai-disclosure` skill as a sub-agent to analyze the diff for AI-generated code.

**IMPORTANT:** Pass the exact `BASE_BRANCH` and `REVIEW_BRANCH` to the sub-agent
so it analyzes ONLY the feature branch changes.

**Invoke via `Agent`:**

Prompt the sub-agent with:
```
You are a Disclosure Analyst. Analyze the git diff between
{BASE_BRANCH} and {REVIEW_BRANCH} using three-dot diff:
  git diff {BASE_BRANCH}...{REVIEW_BRANCH}

This shows ONLY changes on the feature branch.

Return ONLY the structured list entries (no headings, no file paths, just filenames).
Use NO indentation — all lines start at column 0:
FileName.php
- Type: New / Modified
- Function/Class: <name>
- Line Range: <range>
- AI Scope: Full / Partial
- Reason: <concise description>

If no AI code detected, return: "No AI-generated code detected."
```

Place the sub-agent's output directly under the heading:

```markdown
### 8. AI-generated code

{sub-agent output here}
```

**If the sub-agent returns "No AI-generated code detected." or fails, output:**
```markdown
### 8. AI-generated code
- N/A
```

### Section 9: Code review report using AI (auto-generated if found)

Search for an existing code review report matching this PR's ticket or branch:

```bash
BRANCH_SLUG=$(echo "$REVIEW_BRANCH" | tr '/' '-')
ls docs/review/CODE-REVIEW-BRANCH-${BRANCH_SLUG}.md 2>/dev/null
grep -rl "$TICKET_ID" docs/review/ docs/quick-review/ 2>/dev/null
```

If a matching report is found, read it and extract only **High-severity** findings:
- Security/authorization bugs (IDOR, missing ownership checks)
- Data-integrity/correctness bugs (compensation/rollback gaps, race conditions, missing
  idempotency locks)
- Performance-critical issues (unscoped/unbounded queries, missing indexes, missing timeouts
  on external calls)

Skip cosmetic, style, naming, docblock, or minor-hygiene findings even if the report marks
them fixed. Renumber the included findings sequentially starting at 1, regardless of the
original report's numbering. Keep each "Finding" cell to one short paraphrased line — do not
paste the full write-up.

```markdown
### 9. Code review report using AI

| # | Severity | Finding | Status |
|---|----------|---------|--------|
| 1 | 🔴 High | {short finding summary} | {✅ Fixed / 🟡 Partially Fixed / ❌ Open} |
```

**If no matching review report is found, output:**
```markdown
### 9. Code review report using AI
- N/A
```

### Section 10: BAT (static)

```markdown
### 10. BAT
- N/A
```
