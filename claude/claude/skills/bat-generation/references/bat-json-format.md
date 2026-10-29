# BAT JSON & Excel Format

Reference for the `bat-generation` skill — loaded at Step 3 (Generate BAT Excel File) and Step 4a (Prepare JSON Input): Excel structure spec, column/content rules, test case categories, the BAT input JSON structure, and a sample JSON → Excel example.

## Excel Structure & Test Case Rules (loaded at Step 3)

### 3a. Excel Structure (STRICT — matches sample)

The output `.xlsx` file must replicate the format in `.claude/skills/sample/BAT Testcase - Sample.xlsx`.

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

## JSON Input Structure (loaded at Step 4a)

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
