---
name: pr-note
description: "Generates a GitHub-compatible PR description from branch diffs — ticket link, summary, impact range, test commands, checklists, and AI disclosure. Use when preparing a pull request description. Triggered by the [PR-Note] tag or /pr-note."
---

# PR Note Generation Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **PR Note Generator** that analyzes a branch diff and produces a structured,
GitHub-compatible PR description in markdown format. The output starts with a PR Title line,
followed by 10 sections: ticket link, summary, impact range, performance checklist, test commands,
code checklists, screenshots placeholder, AI-generated code disclosure, review report (with a
findings table when a matching review report exists), and a BAT placeholder.

## Usage

```
[PR-Note] branch feat/1709632-packing-list-barcode-enhancement base feat/1709504-cr4-phase2
[PR-Note] branch feat/1709632-packing-list-barcode-enhancement base develop
[PR-Note]
```

**Both `branch` and `base` are strongly recommended.** Without them, the diff may include
commits from other branches merged into the base, producing noisy results.

Default mode (no arguments): current branch vs auto-detected default branch.

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

## Step 4: Analyze Changes & Generate Sections

The output starts with a `PR Title:` line (generated from the branch suffix), followed by 10 sections:
1. Related Tickets — Jira link built from `TICKET_ID`
2. What's this PR do? — 1-3 bullet summary derived from the diff
3. Impact range — affected user-facing areas from changed files, or N/A
4. Performance — static checklist
5. Command — 5a unit-test commands for test files in the diff; 5b schema-update commands if schema changes detected
6. Checklists — static; 7. Screenshots — static N/A
8. AI-generated code — `ai-disclosure` sub-agent output on the three-dot diff, or N/A
9. Code review report using AI — High-severity findings table if a matching report exists, else N/A
10. BAT — static N/A

→ Full per-section instructions and verbatim templates: read `references/pr-note-template.md` when you reach this step (do not load earlier).

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

Concatenate the `PR Title:` line followed by all 10 sections into a single markdown file.
No YAML frontmatter. The file should be directly pasteable into a GitHub PR description.

## Step 6: Validation

Before returning, verify:
- [ ] `PR Title:` line present at the top of the file
- [ ] Ticket ID extracted correctly from branch name
- [ ] "What's this PR do?" is concise and accurate (1-3 short bullets)
- [ ] Impact range lists specific pages/areas, short bullets, not generic descriptions
- [ ] Test commands reference actual test files from the diff, using `docker exec ec-cube`
- [ ] Schema update commands present only if the diff has schema changes
- [ ] AI disclosure section has sub-agent output (not empty)
- [ ] Code review section is a findings table if a matching report was found, else `N/A`
- [ ] BAT section present (`N/A`)
- [ ] File written to correct output path

## Return Contract

After generating the PR note, return **only**:
1. **File created** — full path to the PR note file
2. **Ticket** — extracted ticket ID and Jira link
3. **Summary** — 1-line description of what the PR does

Do NOT paste the full file contents in the chat response.

## Related Skills

- **`ai-disclosure`** — Used as sub-agent for Section 8 (AI-generated code detection)
- **`core-essentials`** — Critical rules and directory structure
- **`review-command`** — Full 7-agent code review (separate concern)
- **`bat-generation`** — BAT test case generation (separate concern)
