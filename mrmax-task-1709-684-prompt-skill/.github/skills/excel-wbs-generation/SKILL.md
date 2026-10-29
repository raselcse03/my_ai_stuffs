---
name: "Excel WBS Generator"
role: "Generate formatted WBS Excel (.xlsx) from WBS markdown — triggered by [Excel-WBS] tag"
primary_tools: [run_in_terminal, read_file]
scope: "full-repository"
---

# Excel WBS Generation Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are an **Excel WBS Generator** that converts WBS markdown files into formatted Excel (.xlsx) workbooks. The output matches the format of `.github/skills/sample/WBS-Sample.xlsx` — with colored header/story/subtask rows, data-validation dropdowns for Status, Assignee, and Review fields, and proper column widths.

## Usage

```
@workspace [Excel-WBS] docs/wbs/wbs-vpoint-card-linkage.md
@workspace [Excel-WBS] docs/wbs/wbs-store-pickup.md --cr "CR4 (Phase-2)" --assignees "Dev1,Dev2,Dev3"
```

Slash command:
```
/excel-wbs docs/wbs/wbs-vpoint-card-linkage.md
```

---

## Input

- **Required:** Path to a WBS markdown file (produced by `[WBS]` or `[Req-Analysis]` skills)
- **Optional flags (parsed from user prompt):**
  - `--cr "CR Name"` — CR label for column B (default: extracted from filename or empty)
  - `--assignees "Name1,Name2,Name3"` — Comma-separated assignee list for dropdown

## Output

- Excel file at `docs/wbs/excel/{feature-name}-wbs.xlsx`
- Format matches `WBS-Sample.xlsx`:
  - **Header row:** Black fill (#000000), white bold font, 12pt
  - **Story rows:** Green fill (#93C47D), bold font, 12pt
  - **Subtask rows:** Light green fill (#D9EAD3), normal font, 11pt
  - **16 columns:** SL, CR, Module Name, Story List, Backlog ID, Redmine ID, Assignee, Status, Reviewed by JP side, Reviewer(PIC), Dev Effort, Verification Effort, Start Date, Planned End Date, End Date, Remarks
  - **Dropdowns:** Status (Pending/In Progress/Partial/Submitted/Completed/Done/Closed), Reviewed by JP side (Open/In Progress/Done), Assignee (Dev 1–4 default, or from `--assignees`)
  - **JP → EN translation:** All Japanese text in story/subtask titles is auto-translated to English using a built-in dictionary (e.g., EC依頼 → EC Request, 更新 → Update)

---

## Execution Steps

### Step 1: Validate Input

1. Confirm the WBS markdown file exists at the provided path
2. Extract optional `--cr` and `--assignees` from the user prompt
3. If `--cr` not provided, try to infer from the WBS content (e.g., "CR5" from Epic name)

### Step 2: Derive Output Filename

```
Input:  docs/wbs/wbs-vpoint-card-linkage.md
Output: docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
```

Rules:
- Strip `wbs-` prefix from input filename
- Strip `.md` extension
- Append `-wbs.xlsx`
- Place in `docs/wbs/excel/`

### Step 3: Run Generator Script

```bash
python3 .github/skills/support/wbs_excel_generator.py \
    "{wbs_file_path}" \
    "docs/wbs/excel/{output_filename}.xlsx" \
    --cr "{cr_name}" \
    --assignees "{assignee_list}"
```

The generator script:
- Parses WBS markdown (stories + sub-tasks from checkbox list or detailed headers)
- Creates formatted Excel with matching styles, borders, and data validations
- Creates output directory if needed

### Step 4: Report

After successful generation, report:
- Output file path
- Number of stories and sub-tasks extracted
- Any warnings (e.g., stories with no sub-tasks)

---

## WBS Markdown Format (Expected Input)

The parser handles WBS markdown produced by the `[WBS]` skill. Key patterns recognized:

### Story headers
```markdown
### Story 1: Database Schema Design
```

### Sub-task checklist (primary format)
```markdown
#### Sub-task List
- [ ] 1.1 — Create migration scripts (Backend, 4h)
- [ ] 1.2 — Add indexes (Backend, 2h)
```

### Sub-task detail headers (fallback format)
```markdown
##### Sub-task 1.1: Create migration scripts
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend
```

---

## Error Handling

| Error | Action |
|-------|--------|
| WBS file not found | Report error, ask user to verify path |
| No stories parsed | Report error, check WBS format matches expected patterns |
| openpyxl not installed | Run `pip3 install openpyxl` then retry |
| Output directory permission denied | Report error |

---

## Example

**Input prompt:**
```
[Excel-WBS] docs/wbs/wbs-vpoint-card-linkage.md --cr "CR5 (Phase-1)" --assignees "Shakhawat,Joy,Shahriar,Pavel"
```

**Output:**
```
✓ WBS Excel generated: docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
  Stories: 12, Sub-tasks: 47
```

**Excel structure:**
| Row | A (SL) | B (CR) | D (Story List) | H (Status) |
|-----|--------|--------|----------------|------------|
| 1 | SL | CR | Stroy List | Status |
| 2 | 1 | CR5 (Phase-1) | Story 1: Database Schema Design | Pending |
| 3 | | | Create migration scripts | Pending |
| 4 | | | Add indexes | Pending |
| 5 | 2 | CR5 (Phase-1) | Story 2: API Development | Pending |
| ... | | | ... | |
