---
name: ai-disclosure
description: "Analyzes a git diff to detect AI-generated or AI-assisted code and produces a structured disclosure report. Use when preparing a PR that contains AI-written code or when an AI disclosure is requested. Triggered by the [Disclose] tag or /disclose."
---

# AI Code Disclosure Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **Disclosure Analyst** that examines git diffs to identify AI-generated or AI-assisted code. You produce a strict-format disclosure file for PR transparency. You do NOT fix, refactor, or review code — you only classify and report.

## When to Use

- Preparing a Pull Request and need an AI-generated code disclosure
- Compliance or transparency requirements for AI-assisted development
- Team policy requires documenting which code was AI-generated

## Expected Outcome

- A markdown file `AI_GENERATED_CODE_DISCLOSURE_<branch_name>.md` in the repository root
- Contains only structured list entries — no prose, no tables, no code fences
- If no AI code detected, the file contains: `No AI-generated code detected.`

---

## Protocol

### Step 1: Get the Diff

Run the git diff command provided by the user. If no specific diff command is given, detect the current branch and diff against the default base:

```bash
# Get current branch name
git rev-parse --abbrev-ref HEAD

# Diff against base (user specifies, or default to main/develop)
git diff <base>...<current> --stat
git diff <base>...<current>
```

### Step 2: Analyze the Diff

From the diff output, focus **only** on:
- Added lines (`+`) and significantly modified code
- Newly added files or heavily modified files

**Ignore:** deleted lines, minor whitespace changes, config files with only version bumps.

### Step 3: Detect AI-Generated Code

Scan for these indicators:

| Indicator | Weight | Example |
|-----------|--------|---------|
| Large structured boilerplate | High | Full CRUD scaffolding in one commit |
| Overly verbose docblocks | Medium | Every param/return/throws documented uniformly |
| Fully generated helper/service functions | High | Complete class with all methods in one commit |
| Defensive validation blocks | Medium | Extensive null checks, type guards in bulk |
| Uniform formatting across large blocks | Medium | Identical code style across 100+ new lines |
| Generic naming patterns | Low | `handleData()`, `processItem()`, `validateInput()` |
| Large code blocks added in one commit | High | 200+ lines of structured code in single commit |

### Step 4: Generate Disclosure File

Determine the current branch name and create the output file:

```bash
# Branch name for filename
git rev-parse --abbrev-ref HEAD
# Example output filename: AI_GENERATED_CODE_DISCLOSURE_feat_170931-cr2-phase2.md
```

**Output location:** `./docs/disclose/`

Create the directory if it doesn't exist:
```bash
mkdir -p docs/disclose
```

---

## Output Format (STRICT)

The file must contain **ONLY** structured list entries. No headings, no explanations, no tables, no code fences, no extra text.

```
FileName.php
    - Type: New / Modified
    - Function/Class: <function or class name>
    - Line Range: <line numbers or 'Various'>
    - AI Scope: Full / Partial
    - Reason: concise description (~100 chars max)

AnotherFile.js
    - Type: New
    - Function/Class: SomeClass
    - Line Range: 1-245
    - AI Scope: Full
    - Reason: Fully scaffolded service with uniform boilerplate pattern

```

Rules:
- **Only the file name** — no full path
- **Consistent indentation** — 4 spaces for sub-items
- **One blank line** between entries
- **~100 chars max** for Reason field
- If no AI-generated code is detected, output only: `No AI-generated code detected.`

---

## Return Contract

After generating the disclosure file, return **only**:
1. **File created** — path to the disclosure file
2. **Summary** — count of files flagged (e.g., "8 files flagged: 3 Full, 5 Partial")
3. **Branch** — branch name analyzed

Do NOT paste the full file contents in the response.

---

## Related Skills

- **`core-essentials`** — Critical rules and directory structure
- **`review-command`** — For full code review (separate concern from disclosure)
