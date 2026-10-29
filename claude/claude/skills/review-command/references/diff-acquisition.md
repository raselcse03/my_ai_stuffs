# Review Command — Mode Parsing & Diff Acquisition

> Loaded on-demand by `review-command/SKILL.md` at Steps 1–3 (argument parsing, preflight, gathering changes). Do NOT read until you reach those steps.

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
