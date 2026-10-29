# WBS Import — Excel/CSV Input Format and Parsing

Column spec, row classification, parsing scripts, and tree-building pseudocode — loaded by wbs-import Step 1 (parse source) and Step 2 (build tree).

## Input Format: Excel-WBS (.xlsx)

The Excel follows the format produced by `[Excel-WBS]` skill (matches `WBS-Sample.xlsx`):

| Column | Header | Content |
|--------|--------|---------|
| A | SL | Serial number (story-level only) |
| B | CR | CR label (e.g., "CR5 (Phase-1)") |
| C | Module Name | Module or component name |
| D | Story List | Story title (bold/green row) or sub-task title (light-green row) |
| E | Backlog ID | JIRA/backlog identifier |
| F | Redmine ID | Redmine ticket reference |
| G | Assignee | Developer name |
| H | Status | Pending / In Progress / Completed / Done / Closed |
| I | Reviewed by JP side | Open / In Progress / Done |
| J | Reviewer(PIC) | Reviewer name |
| K | Dev Effort | Development hours estimate |
| L | Verification Effort | QA/verification hours |
| M | Start Date | Planned start date |
| N | Planned End Date | Target completion date |
| O | End Date | Actual completion date |
| P | Remarks | Notes or comments |

### Row Classification

- **Story row:** Has a value in column A (SL number), green background (#93C47D)
- **Sub-task row:** No value in column A, light-green background (#D9EAD3)
- **Header row:** Row 1 with column headers, black background (#000000)

## Input Format: CSV

When the user provides CSV instead of Excel, expect the same columns as above in comma-separated format. The first row is headers. Story vs sub-task distinction uses:
- Story rows have a numeric SL value in the first column
- Sub-task rows have an empty first column

## Step 1 Parsing Scripts

### For Excel (.xlsx):

There is no dedicated parser script for this format — parse it directly with `openpyxl`:

```bash
python3 -c "
import openpyxl, json, sys
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
ws = wb.active
rows = []
for r in ws.iter_rows(min_row=2, values_only=False):
    vals = [c.value for c in r]
    rows.append({
        'sl': vals[0],
        'cr': vals[1],
        'module': vals[2],
        'title': vals[3],
        'backlog_id': vals[4],
        'redmine_id': vals[5],
        'assignee': vals[6],
        'status': vals[7],
        'jp_review': vals[8],
        'reviewer': vals[9],
        'dev_effort': vals[10],
        'verification_effort': vals[11],
        'start_date': str(vals[12]) if vals[12] else None,
        'planned_end': str(vals[13]) if vals[13] else None,
        'end_date': str(vals[14]) if vals[14] else None,
        'remarks': vals[15] if len(vals) > 15 else None,
        'is_story': vals[0] is not None and str(vals[0]).strip() != ''
    })
print(json.dumps(rows, indent=2, default=str))
" "{excel_path}"
```

### For CSV (.csv):
```bash
python3 -c "
import csv, json, sys
with open(sys.argv[1], 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    rows = []
    for r in reader:
        sl = r.get('SL', '').strip()
        rows.append({
            'sl': sl if sl else None,
            'cr': r.get('CR', ''),
            'module': r.get('Module Name', ''),
            'title': r.get('Story List', r.get('Stroy List', '')),
            'backlog_id': r.get('Backlog ID', ''),
            'redmine_id': r.get('Redmine ID', ''),
            'assignee': r.get('Assignee', ''),
            'status': r.get('Status', ''),
            'jp_review': r.get('Reviewed by JP side', ''),
            'reviewer': r.get('Reviewer(PIC)', ''),
            'dev_effort': r.get('Dev Effort', ''),
            'verification_effort': r.get('Verification Effort', ''),
            'start_date': r.get('Start Date', ''),
            'planned_end': r.get('Planned End Date', ''),
            'end_date': r.get('End Date', ''),
            'remarks': r.get('Remarks', ''),
            'is_story': bool(sl)
        })
print(json.dumps(rows, indent=2))
" "{csv_path}"
```

## Step 2 Tree-Building Pseudocode

From `PARSED_DATA`, construct a hierarchical tree:

```
stories = []
current_story = None

for row in PARSED_DATA:
    if row.is_story:
        current_story = {
            sl: row.sl,
            cr: row.cr,
            title: row.title,
            module: row.module,
            assignee: row.assignee,
            status: row.status,
            dev_effort: row.dev_effort,
            subtasks: []
        }
        stories.append(current_story)
    else:
        if current_story:
            current_story.subtasks.append({
                title: row.title,
                assignee: row.assignee,
                status: row.status,
                dev_effort: row.dev_effort,
                verification_effort: row.verification_effort
            })
```
