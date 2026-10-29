---
name: "PR Note Generator"
role: "Generate GitHub-compatible PR description from branch diffs — triggered by [PR-Note] tag"
primary_tools: [run_in_terminal, grep_search, read_file, create_file, runSubagent]
scope: "full-repository"
---

# PR Note Generation Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **PR Note Generator** that analyzes a branch diff and produces a structured,
GitHub-compatible PR description in markdown format. The output contains 9 sections:
ticket link, summary, impact range, performance checklist, test commands,
code checklists, screenshots placeholder, AI-generated code disclosure, and review report placeholder.

## Usage

```
@workspace [PR-Note] branch feat/1709632-packing-list-barcode-enhancement base feat/1709504-cr4-phase2
@workspace [PR-Note] branch feat/1709632-packing-list-barcode-enhancement base develop
@workspace [PR-Note]
```

**Both `branch` and `base` are strongly recommended.** Without them, the diff may include
commits from other branches merged into the base, producing noisy results.

Default mode (no arguments): current branch vs auto-detected default branch.

---

## Step 1: Parse Arguments & Determine Branches

Parse the user's prompt for branch and base:

| Mode | Example |
|------|---------|
| branch + base | `[PR-Note] branch feat/xyz base develop` — **recommended** |
| branch only | `[PR-Note] branch feat/xyz` — auto-detects base |
| default | `[PR-Note]` — current branch, auto-detects base |

Set variables:
- `REVIEW_BRANCH`: The feature branch to generate PR notes for
- `BASE_BRANCH`: The base/target branch this PR will merge into

### Resolve branch names

The user may provide a shorthand (e.g., `cr4-phase2`). You MUST resolve it to the
actual full branch name. Search local and remote branches:

```bash
# If user provides "cr4-phase2", find the actual branch
git branch -a | grep -i "cr4-phase2" | head -5
# Pick the matching branch (e.g., feat/1709504-cr4-phase2)
```

### Auto-detect base branch (only if not provided)

```bash
# If no branch specified, use current
REVIEW_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# If no base specified, auto-detect default
BASE_BRANCH=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}')
if [ -z "$BASE_BRANCH" ]; then
  BASE_BRANCH=$(git branch -l main master --format '%(refname:short)' | head -1)
fi
```

### Verify branches exist

```bash
# Verify both branches exist locally or remotely
git rev-parse --verify "$REVIEW_BRANCH" 2>/dev/null || git rev-parse --verify "origin/$REVIEW_BRANCH" 2>/dev/null
git rev-parse --verify "$BASE_BRANCH" 2>/dev/null || git rev-parse --verify "origin/$BASE_BRANCH" 2>/dev/null
```

If either branch doesn't exist, stop and report the error.

---

## Step 2: Extract Ticket ID from Branch Name

Parse the branch name to generate the Jira ticket link.

**Pattern:** `feat/XXXXXXXN-description` or `cr/XXXXXXXN-description` etc.

**Logic:**
1. Strip the prefix before `/` (e.g., `feat/`, `cr/`, `fix/`, `chore/`)
2. Extract the numeric portion before the first `-`
3. Split: first 4 digits = project number, remaining digits = ticket number
4. Result: `P{first4}-{remaining}`

**Examples:**
- `feat/1709632-packing-list` → digits `1709632` → `P1709-632`
- `feat/1709631-total-picking` → digits `1709631` → `P1709-631`
- `cr/305055-enable-filter` → digits `305055` → `P3050-55`

```bash
# Extract digits before first dash after prefix
BRANCH_SUFFIX=$(echo "$REVIEW_BRANCH" | sed 's|.*/||')  # Remove prefix/
DIGITS=$(echo "$BRANCH_SUFFIX" | grep -oP '^\d+')
FIRST4=${DIGITS:0:4}
REMAINING=${DIGITS:4}
TICKET_ID="P${FIRST4}-${REMAINING}"
```

If no digits found, set `TICKET_ID` to `UNKNOWN` and warn the user.

---

## Step 3: Gather Diff & Changed Files

**CRITICAL: Use three-dot diff (`...`) to get ONLY changes introduced on the feature branch.**
Two-dot diff (`..`) includes changes from both sides and will pull in unrelated commits.

```bash
# Get diff stat — ONLY changes on REVIEW_BRANCH since it diverged from BASE_BRANCH
git diff "$BASE_BRANCH"..."$REVIEW_BRANCH" --stat

# Get full diff — ONLY the feature branch changes
git diff "$BASE_BRANCH"..."$REVIEW_BRANCH"

# Get list of changed files — ONLY files changed on the feature branch
git diff "$BASE_BRANCH"..."$REVIEW_BRANCH" --name-only
```

### Validate diff is scoped correctly

```bash
# Count changed files — sanity check
FILE_COUNT=$(git diff "$BASE_BRANCH"..."$REVIEW_BRANCH" --name-only | wc -l)
echo "Files changed on feature branch: $FILE_COUNT"
```

If `FILE_COUNT` is 0, warn: "No changes detected between branches."
If `FILE_COUNT` > 50, warn: "Large diff detected. Verify the base branch is correct."

---

## Step 4: Analyze Changes & Generate Sections

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

Write **1-3 bullet points**, each a clear sentence. Use technical but readable language.

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

Write as a bullet list of affected areas.

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
For each test file found, list: `- docker exec mrmax_dev-ec-cube-1 bin/phpunit {test_file_path}`

##### 5b. Schema Update

Scan the diff for database schema changes: new/modified/removed `@ORM\Column` properties,
entity trait changes, `->addColumn`, `ADD COLUMN`, `ALTER TABLE`, or SQL migration scripts.
If detected, list:
```
- docker exec mrmax-ec-cube-1 php bin/console doctrine:cache:clear-metadata && docker exec mrmax-ec-cube-1 php bin/console eccube:generate:proxies
- docker compose -f docker-compose.yml -f docker-compose.mysql.yml -f docker-compose.dev.yml exec ec-cube bin/console cache:clear --no-warmup
- docker compose -f docker-compose.yml -f docker-compose.mysql.yml -f docker-compose.dev.yml exec ec-cube bash -c "rm -rf app/proxy/entity/src && bin/console eccube:generate:proxies"
- docker compose -f docker-compose.yml -f docker-compose.mysql.yml -f docker-compose.dev.yml exec ec-cube bin/console doctrine:schema:update --force
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

**Invoke via `runSubagent`:**

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

### Section 9: Code review report using AI (static)

```markdown
### 9. Code review report using AI
- N/A
```

---

## Step 5: Assemble & Write Output File

### Output Location

```
./docs/pr-note/
```

Create the directory if it doesn't exist:
```bash
mkdir -p docs/pr-note
```

### File Naming

```
PR-Note-{TICKET_ID}.md
```

Example: `PR-Note-P1709-632.md`

If the file already exists, overwrite it (PR notes are regenerated).

### Assemble

Concatenate all 9 sections into a single markdown file. No YAML frontmatter.
The file should be directly pasteable into a GitHub PR description.

---

## Step 6: Validation

Before returning, verify:
- [ ] Ticket ID extracted correctly from branch name
- [ ] "What's this PR do?" is concise and accurate (1-3 bullets)
- [ ] Impact range lists specific pages/areas, not generic descriptions
- [ ] Test commands reference actual test files from the diff
- [ ] AI disclosure section has sub-agent output (not empty)
- [ ] File written to correct output path

---

## Return Contract

After generating the PR note, return **only**:
1. **File created** — full path to the PR note file
2. **Ticket** — extracted ticket ID and Jira link
3. **Summary** — 1-line description of what the PR does

Do NOT paste the full file contents in the chat response.

---

## Related Skills

- **`ai-disclosure`** — Used as sub-agent for Section 8 (AI-generated code detection)
- **`core-essentials`** — Critical rules and directory structure
- **`review-command`** — Full 7-agent code review (separate concern)
- **`bat-generation`** — BAT test case generation (separate concern)
