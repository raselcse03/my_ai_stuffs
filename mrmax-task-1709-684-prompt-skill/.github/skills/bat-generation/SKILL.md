---
name: "BAT Generator"
role: "Generate Developer BAT (Basic Acceptance Test) Excel reports from code diffs — triggered by [BAT] tag"
primary_tools: [run_in_terminal, grep_search, read_file, create_file]
scope: "full-repository"
---

# BAT Test Case Generation Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **BAT Generator** that analyzes code diffs to produce structured Developer BAT (Basic Acceptance Test) **Excel (.xlsx)** reports for EC-Cube 4.x features. You identify affected routes, controllers, templates, and services, then generate test cases organized by module.

The output Excel matches the sample at `.github/skills/sample/BAT Testcase - Sample.xlsx` — with colored headers, thin borders, data-validation dropdowns, and merged cells for grouped rows.

## Usage

```
@workspace [BAT] branch feat/P1709-733-posdata
@workspace [BAT] branch feat/P1709-733-posdata base staging
@workspace [BAT] pr 12345
@workspace [BAT] staged
```

Default mode (no arguments): `staged`.

---

## Step 1: Parse Arguments

| Mode | Example | Description |
|------|---------|-------------|
| pr | `[BAT] pr 123` | BAT from a pull request diff |
| branch | `[BAT] branch feature-x` | Branch vs default branch |
| branch + base | `[BAT] branch feature-x base staging` | Branch vs specific base |
| staged | `[BAT] staged` | Staged changes only |

---

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

---

## Step 3: Generate BAT Excel File

### 3a. Excel Structure (STRICT — matches sample)

The output `.xlsx` file must replicate the format in `.github/skills/sample/BAT Testcase - Sample.xlsx`.

**Row 1** — Title row:
- Cells A1:M1 **merged**
- Value: `Developer BAT Test Cases`
- Style: Blue fill (`#5B9BD5`), white bold font size 12, center-aligned, thin borders
- Row height: 23.25

**Row 2** — Column headers (exactly 13 columns):

| Col | Header | Width |
|-----|--------|-------|
| A | TC ID | default |
| B | Feature Test | 19.13 |
| C | Main Menu | 11.2 |
| D | Sub Menu | 10.3 |
| E | Manager Acces | 9.0 |
| F | User Acces | 7.87 |
| G | Test Scenario | 20.87 |
| H | Test Type | default |
| I | Test Items | 59.87 |
| J | Result (Dev1) | default |
| K | Result (Reviewe) | 11.8 |
| L | Result (PD) | default |
| M | Comments | default |

- Style: Blue fill (`#5B9BD5`), white bold font size 12, center-aligned, wrap text, thin borders
- Row height: 31.5

**Row 3+** — Data rows:
- Font: size 11, not bold
- Alignment: vertical center, wrap text; columns C–F additionally horizontal center
- Borders: thin on all sides
- Result columns (J, K, L) and Comments (M): always **empty** (filled during manual testing)

### 3b. Column Rules

| Column | Rule |
|--------|------|
| **A — TC ID** | Sequential integer from 1. Rows sharing the same feature group use the **same** TC ID |
| **B — Feature Test** | Feature group name (e.g., `Store Reorder: Add to Cart and Validation`). Same value on every row of the group |
| **C — Main Menu** | Page/section area (e.g., `Product Page`). `Impact Area` for regression rows |
| **D — Sub Menu** | Sub-section (e.g., `Add to Cart`) |
| **E — Manager Acces** | `○` (applicable) or `✕` (not applicable) |
| **F — User Acces** | `○` (applicable) or `✕` (not applicable) |
| **G — Test Scenario** | Short scenario label (e.g., `Installation Checkout Page Access`) |
| **H — Test Type** | `Positive` or `Negative` only (dropdown) |
| **I — Test Items** | `Verify [what] at [route] ([METHOD]) — should [expected behavior]` |
| **J–L — Results** | Always empty. Dropdown: `OK, NG, NA, NE` |
| **M — Comments** | Always empty |

### 3c. Cell Merging

When consecutive rows share the **same TC ID**, columns A through F are **merged** vertically. This groups related positive/negative/regression test items under one feature block.

### 3d. Data Validations (Dropdowns)

| Column(s) | Dropdown Values |
|-----------|----------------|
| H (Test Type) | `Positive, Negative` |
| J, K, L (Results) | `OK, NG, NA, NE` |

### 3e. Test Case Categories

For each module, generate ALL of:

**Positive (Happy Path):**
- Successful CRUD operations
- Correct UI display (data, labels, layout)
- Valid API responses
- Authentication/authorization flows
- Pagination, search, filter
- Mobile/Webview compatibility (if `is_webview()` present)

**Negative (Error Handling):**
- Unauthenticated access → redirect to login
- Invalid input → validation errors
- Missing required fields → error messages
- Boundary values (empty list, max length, zero quantity)
- Expired/invalid CSRF tokens
- Non-existent resources (404)

**Impact Area (Regression):**
- Existing features sharing routes/services with changed code
- Parent pages including changed templates
- APIs consumed by multiple pages
- Admin features related to changed entities

### 3f. Grouping

Test cases under the same feature share the same TC ID and Feature Test value. Rows are merged in columns A–F. Example grouping label:

```
"Store Reorder: Add to Cart, Stock Validation, and Cart Switching"
```

---

## Step 4: Build BAT JSON

### 4a. Prepare JSON Input

After analyzing the diff and generating test case data, create a temporary JSON file with this structure:

```json
{
    "sheet_name": "BAT Testcase - P1709-733",
    "test_cases": [
        {
            "tc_id": 1,
            "feature_test": "Store Reorder: Add to Cart and Validation",
            "main_menu": "Product Page",
            "sub_menu": "Add to Cart",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Add to Cart Flow",
            "test_type": "Positive",
            "test_items": "Verify that single product add to cart at /mypage/purchase/reorder (POST) — should add product and return success"
        },
        {
            "tc_id": 1,
            "feature_test": "Store Reorder: Add to Cart and Validation",
            "main_menu": "Product Page",
            "sub_menu": "Add to Cart",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Stock Check",
            "test_type": "Negative",
            "test_items": "Verify stock availability check at /mypage/purchase/reorder (POST) — should reject out-of-stock items"
        }
    ]
}
```

**Rules for JSON data:**
- Rows with the **same `tc_id`** will be merged in columns A–F in the Excel output
- Use `○` for applicable access, `✕` for not applicable
- `test_type` must be exactly `Positive` or `Negative`
- `sheet_name` should be `BAT Testcase - [TicketID]`

### 4b. Save the JSON File

```bash
mkdir -p /tmp
# Write JSON to temp file
cat > /tmp/bat_input_TICKET.json << 'EOF'
{ ... generated JSON ... }
EOF
```

---

## Step 5: Auto-Execute Tests

Before generating the final Excel, execute each test case via HTTP to pre-fill the Result (Dev1) column. This step runs by default — skip **only** if the dev server is unreachable and the user explicitly chooses to skip.

### 5a. Check Server Availability

```bash
python3 .github/skills/support/bat_test_runner.py /tmp/bat_input_TICKET.json /tmp/bat_output_TICKET.json --base-url http://localhost:8080 --check-only
```

If the server is **not reachable**, ask the user via `vscode_askQuestions`:

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

If authenticated routes exist, ask via `vscode_askQuestions`:

```
Header: "Auth Cookie"
Question: "Some tests require authentication. Provide session cookie or skip auth tests?"
Options:
  - "Skip auth routes — mark as NE"
  - "Provide cookie" → freeform input
```

⚠️ **NEVER** use `vscode_askQuestions` for the actual cookie value — it passes through the model. Instead, tell the user:
> "Please paste your session cookie directly in the terminal when prompted."

Then run the test runner in **sync mode** and use `send_to_terminal` for cookie input if provided by terminal.

### 5c. Execute Tests

```bash
python3 .github/skills/support/bat_test_runner.py \
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

---

## Step 6: Build & Write the Excel File

### 6a. Run the Generator Script

```bash
mkdir -p docs/bat
python3 .github/skills/support/bat_excel_generator.py /tmp/bat_output_TICKET.json docs/bat/BAT_[ModuleName]_[TicketID].xlsx
```

If auto-test was **skipped** in Step 5, use the original input JSON instead:

```bash
python3 .github/skills/support/bat_excel_generator.py /tmp/bat_input_TICKET.json docs/bat/BAT_[ModuleName]_[TicketID].xlsx
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

---

## Step 7: Cleanup Temporary Files

After the Excel file is successfully generated, delete all temporary files:

```bash
rm -f /tmp/bat_input_TICKET.json /tmp/bat_output_TICKET.json
```

Replace `TICKET` with the actual ticket ID used in Step 4. This prevents stale JSON from accumulating in `/tmp`.

---

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

---

## Sample JSON → Excel

**Input JSON:**
```json
{
    "sheet_name": "BAT Testcase - P1709-733",
    "test_cases": [
        {
            "tc_id": 1,
            "feature_test": "Store Reorder: Add to Cart, Stock Validation, and Cart Switching",
            "main_menu": "MyPage",
            "sub_menu": "Reorder",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Add to Cart Flow",
            "test_type": "Positive",
            "test_items": "Verify single product add to cart at /mypage/purchase/reorder (POST) — should add product and return success"
        },
        {
            "tc_id": 1,
            "feature_test": "Store Reorder: Add to Cart, Stock Validation, and Cart Switching",
            "main_menu": "MyPage",
            "sub_menu": "Reorder",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Stock Check",
            "test_type": "Positive",
            "test_items": "Verify stock availability check at /mypage/purchase/reorder (POST) — should reject out-of-stock items"
        },
        {
            "tc_id": 1,
            "feature_test": "Store Reorder: Add to Cart, Stock Validation, and Cart Switching",
            "main_menu": "MyPage",
            "sub_menu": "Reorder",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Auth Guard",
            "test_type": "Negative",
            "test_items": "Verify unauthenticated access to /mypage/purchase/reorder (POST) — should redirect to login"
        },
        {
            "tc_id": 2,
            "feature_test": "Cart Page Regression",
            "main_menu": "Impact Area",
            "sub_menu": "Cart",
            "manager_access": "✕",
            "user_access": "○",
            "test_scenario": "Cart Display",
            "test_type": "Positive",
            "test_items": "Verify existing cart page at /cart (GET) — should display unchanged behavior"
        }
    ]
}
```

**Resulting Excel:**
- Row 1: Merged title "Developer BAT Test Cases" (blue)
- Row 2: 13 headers (blue, white text, dropdowns)
- Rows 3–5: TC ID=1 group → columns A–F merged vertically
- Row 6: TC ID=2 (separate row, no merge)
- Dropdowns on H3:H6 and J3:L6

---

## Return Contract

After generating the BAT files, return **only**:
1. **Files created** — list of `.xlsx` file paths
2. **Summary** — total test case count per file (e.g., "1 Excel file: 39 test cases")
3. **Auto-test results** — OK/NG/NE counts if auto-test was executed, or "Skipped" if not
4. **Modules covered** — list of module names

Do NOT paste full file contents in the response.

---

## Related Skills

- **`core-essentials`** — Critical rules and directory structure
- **`testing`** — Write actual test code (unit, integration, functional)
- **`review-command`** — Automated code review with 7 parallel agents
- **`change-request`** — Requirements analysis and impact assessment
