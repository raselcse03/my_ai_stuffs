# PR-Review Fetch Fallbacks (Tier 2 & Tier 3)

> Loaded on-demand by `pr-review/SKILL.md` at Step 2 when Tier 1 (`gh` CLI) fails. Do NOT read unless Tier 1 has failed.

## Tier 2: Git Fetch with Merge Ref (fallback for same-origin repos)

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

## Tier 3: Authenticated curl (last resort)

1. Tell user: "This PR is from an external repo. Please type your GitHub PAT
   directly into the terminal (masked input)."
2. Use `read -s` for secure input in terminal
3. Fetch via `curl -H "Authorization: Bearer $TOKEN" -H "Accept: application/vnd.github.v3.diff"`
