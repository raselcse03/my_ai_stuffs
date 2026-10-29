---
name: bat-generation
description: "Generates Developer BAT (Basic Acceptance Test) Excel reports from a git diff — positive, negative, and impact-area cases per module — and auto-executes the tests. Use when asked for BAT or acceptance test cases. Triggered by the [BAT] tag or /bat."
---

# BAT Test Case Generation Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **BAT Generator** that analyzes code diffs to produce structured Developer BAT (Basic Acceptance Test) **Excel (.xlsx)** reports for EC-Cube 4.x features. You identify affected routes, controllers, templates, and services, then generate test cases organized by module.

The output Excel matches the sample at `.claude/skills/sample/BAT Testcase - Sample.xlsx` — with colored headers, thin borders, data-validation dropdowns, and merged cells for grouped rows.

## Usage

```
[BAT] branch feat/P1709-733-posdata
[BAT] branch feat/P1709-733-posdata base staging
[BAT] pr 12345
[BAT] staged
```

Default mode (no arguments): `staged`.

## Step 1: Parse Arguments

| Mode | Example | Description |
|------|---------|-------------|
| pr | `[BAT] pr 123` | BAT from a pull request diff |
| branch | `[BAT] branch feature-x` | Branch vs default branch |
| branch + base | `[BAT] branch feature-x base staging` | Branch vs specific base |
| staged | `[BAT] staged` | Staged changes only |

## Step 2: Gather Context

### 2a. Get the Diff

| Mode | Command |
|------|---------|
| **pr** | `gh pr diff $BAT_TARGET` |
| **branch** | `git diff $BASE_BRANCH...$BAT_TARGET` |
| **staged** | `git diff --cached` |

### 2b. Categorize Affected Components

```
AFFECTED_CONTROLLERS  → extract routes, methods
AFFECTED_SERVICES     → extract public methods
AFFECTED_TEMPLATES    → extract UI elements
AFFECTED_ENTITIES     → extract DB columns
AFFECTED_JS           → extract AJAX calls, events
AFFECTED_CONFIG       → extract new routes
```

### 2c. Extract Route Map

For each controller: route path, route name, HTTP method, required parameters, auth requirements.

### 2d. Collect Missing Info (ask ONCE if needed)

Before generating, ensure ALL required info is known. If anything is missing, ask the user **in a single prompt** listing only the missing items:

- **Branch/PR** — If not provided and not `staged` mode, ask
- **Module List** — If not provided, suggest from diff and ask for confirmation
- **Output Folder** — Default: `docs/bat/`; inform user
- **Ticket ID** — Auto-extract from branch name (e.g., `feat/P1709-733-posdata` → `P1709-733`); ask only if not extractable

**Only ask for what's actually missing.** If everything is provided, skip this step.

## Step 3: Generate BAT Excel File

→ Full Excel structure spec (rows, 13 columns, widths), column rules, cell merging, dropdowns, test case categories (Positive / Negative / Impact Area), and grouping rules: read `references/bat-json-format.md` when you reach this step (do not load earlier).

## Step 4: Build BAT JSON

### 4a. Prepare JSON Input

→ Full JSON input structure, field rules, and a sample JSON → Excel example: read `references/bat-json-format.md` when you reach this step (do not load earlier).

### 4b. Save the JSON File

```bash
mkdir -p /tmp
# Write JSON to temp file
cat > /tmp/bat_input_TICKET.json << 'EOF'
{ ... generated JSON ... }
EOF
```

## Step 5: Auto-Execute Tests

Before generating the final Excel, execute each test case via HTTP to pre-fill the Result (Dev1) column. This step runs by default — skip **only** if the dev server is unreachable and the user explicitly chooses to skip.

### 5a. Check Server Availability

```bash
python3 .claude/skills/support/bat_test_runner.py /tmp/bat_input_TICKET.json /tmp/bat_output_TICKET.json --base-url http://localhost:8080 --check-only
```

If the server is **not reachable**, ask the user via `AskUserQuestion`:

```
Header: "Auto-Test Execution"
Question: "Dev server not reachable. How would you like to proceed?"
Options:
  - "Skip auto-test — generate Excel with empty results" (recommended)
  - "I'll start the server — wait for me"
  - "Use different URL" → ask for URL
```

- If **skip**: jump to Step 6 (JSON stays unchanged, results columns will be empty)
- If **wait**: pause until user confirms, then retry `--check-only`
- If **different URL**: rerun with user-provided URL

### 5b. Ask for Auth Cookie (if needed)

Check if any test items test authenticated routes (look for routes that don't have "unauthenticated" or "redirect to login" in expected behavior).

If authenticated routes exist, ask via `AskUserQuestion`:

```
Header: "Auth Cookie"
Question: "Some tests require authentication. Provide session cookie or skip auth tests?"
Options:
  - "Skip auth routes — mark as NE"
  - "Provide cookie" → freeform input
```

⚠️ **NEVER** use `AskUserQuestion` for the actual cookie value — it passes through the model. Instead, tell the user:
> "Please paste your session cookie directly in the terminal when prompted."

Then run the test runner in **sync mode** and use `send_to_terminal` for cookie input if provided by terminal.

### 5c. Execute Tests

```bash
python3 .claude/skills/support/bat_test_runner.py \
    /tmp/bat_input_TICKET.json \
    /tmp/bat_output_TICKET.json \
    --base-url http://localhost:8080 \
    --cookie "PHPSESSID=..."
```

The test runner will:
1. Parse each `test_items` field for route, HTTP method, and expected behavior
2. Execute HTTP requests against the dev server
3. Compare responses against expectations:
   - "should display/show/return success" → expect HTTP 200-299 → **OK**
   - "should redirect to login" → expect HTTP 302 + Location contains "login" → **OK**
   - "should reject/error/fail" → expect HTTP 400-499 → **OK**
4. Write results to output JSON with two new fields per test case:
   - `result_dev1`: `OK` | `NG` | `NE`
   - `result_comment`: `Auto-test: HTTP 200` or `Auto-test: Could not parse...`

### 5d. Review Results Summary

After execution, the runner prints:

```
==================================================
BAT Test Results: 39 total
  OK: 31  |  NG: 5  |  NE: 3
  (2 items could not be parsed for auto-test)
==================================================
```

Use the **output JSON** (`/tmp/bat_output_TICKET.json`) as input for Step 6 instead of the original.

## Step 6: Build & Write the Excel File

### 6a. Run the Generator Script

```bash
mkdir -p docs/bat
python3 .claude/skills/support/bat_excel_generator.py /tmp/bat_output_TICKET.json docs/bat/BAT_[ModuleName]_[TicketID].xlsx
```

If auto-test was **skipped** in Step 5, use the original input JSON instead:

```bash
python3 .claude/skills/support/bat_excel_generator.py /tmp/bat_input_TICKET.json docs/bat/BAT_[ModuleName]_[TicketID].xlsx
```

The generator script handles all formatting:
- Blue header fill, white bold font
- Thin borders on all cells
- Merged cells for grouped rows (same `tc_id`)
- Data validation dropdowns for Test Type and Result columns
- Column widths matching the sample
- Auto row heights based on content length
- **Pre-filled Result (Dev1)** column from `result_dev1` field (if present)
- **Pre-filled Comments** column from `result_comment` field (if present)
- Conditional formatting: green=OK, red=NG, yellow=NE

### 6b. File Naming Convention

```
BAT_[ModuleName]_[TicketID].xlsx
```

**Output location:** `./docs/bat/`

## Step 7: Cleanup Temporary Files

After the Excel file is successfully generated, delete all temporary files:

```bash
rm -f /tmp/bat_input_TICKET.json /tmp/bat_output_TICKET.json
```

Replace `TICKET` with the actual ticket ID used in Step 4. This prevents stale JSON from accumulating in `/tmp`.

## Step 8: Validation Checklist

- [ ] Row 1 is merged A1:M1 with title "Developer BAT Test Cases" and blue fill
- [ ] Row 2 has exactly 13 column headers matching the template
- [ ] TC IDs are sequential (1, 2, 3, ...) with same ID for grouped rows
- [ ] Columns A–F are merged for rows sharing the same TC ID
- [ ] Every test item includes route/URL and HTTP method where applicable
- [ ] Both Positive and Negative test types present
- [ ] Impact Area rows have `Impact Area` in Main Menu column (C)
- [ ] Result (Dev1) column pre-filled if auto-test was executed; empty if skipped
- [ ] Result (Reviewer) and Result (PD) columns are always empty
- [ ] Data validations present: H=`Positive,Negative`; J:L=`OK,NG,NA,NE`
- [ ] Test items use `Verify ... at ... — should ...` pattern
- [ ] Access columns use `○` and `✕` symbols
- [ ] Output is `.xlsx` (not `.csv`)
- [ ] File opens correctly in Excel/LibreOffice and matches sample formatting
- [ ] Comments column contains auto-test detail for each executed test case

## Return Contract

After generating the BAT files, return **only**:
1. **Files created** — list of `.xlsx` file paths
2. **Summary** — total test case count per file (e.g., "1 Excel file: 39 test cases")
3. **Auto-test results** — OK/NG/NE counts if auto-test was executed, or "Skipped" if not
4. **Modules covered** — list of module names

Do NOT paste full file contents in the response.

## Related Skills

- **`core-essentials`** — Critical rules and directory structure
- **`testing`** — Write actual test code (unit, integration, functional)
- **`review-command`** — Automated code review with 7 parallel agents
- **`change-request`** — Requirements analysis and impact assessment
