---
name: "WBS Importer"
role: "Generate detailed WBS markdown from Excel-WBS (.xlsx) or CSV — triggered by [WBS-Import] tag"
primary_tools: [read_file, run_in_terminal, runSubagent, create_file]
scope: "docs/"
---

# WBS Import Skill (Reverse Excel-WBS)

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **WBS Importer** that reconstructs a fully detailed, JIRA-ready WBS markdown document from an Excel-WBS spreadsheet (`.xlsx`) or its CSV export.

**Core principle:** The Excel/CSV is the **sole source of truth** for the WBS structure — stories, sub-tasks, their order, effort hours, assignees, and status. No stories or sub-tasks are added, removed, or reordered. The SRS document and project skill file are used **only** to generate descriptions, acceptance criteria, corner cases, risks, and requirement traceability for each story and sub-task.

## Usage

```
@workspace [WBS-Import] {path-to-excel-or-csv}
```

The user attaches **up to 3 context documents** alongside the prompt:

| Attachment | Required | Purpose |
|------------|----------|---------|
| Excel-WBS (`.xlsx`) or CSV (`.csv`) | **Yes** | Source: story/sub-task skeleton with titles, estimates, status |
| SRS document (`.md`) | **Yes** | Enrichment: requirement IDs, acceptance criteria, business rules |
| Project skill file (`.md`) | Optional | Domain context: file maps, business rule matrices, field hierarchies |

### Examples

```
@workspace [WBS-Import] docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
  (attach: docs/srs/srs-vpoint-card-linkage.md)

@workspace [WBS-Import] /tmp/cr4-wbs-export.csv
  (attach: docs/srs/srs-store-pickup.md, .github/skills/requirements/cr4-phase2-store-pickup-inventory.md)

@workspace [WBS-Import] docs/wbs/excel/ac-installation-wbs.xlsx --srs docs/srs/srs-ac-installation.md
```

Slash command:
```
/wbs-import docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
```

---

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

---

## Input Format: CSV

When the user provides CSV instead of Excel, expect the same columns as above in comma-separated format. The first row is headers. Story vs sub-task distinction uses:
- Story rows have a numeric SL value in the first column
- Sub-task rows have an empty first column

---

## Execution Steps

### Step 1: Parse the Excel/CSV Source

#### For Excel (.xlsx):
```bash
python3 .github/skills/support/wbs_import_parser.py "{excel_path}" --format json
```

If the parser script is not available, parse manually:

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

#### For CSV (.csv):
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

**Store result as `PARSED_DATA`.**

### Step 2: Build Story–Sub-task Tree

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

**Count:** Report `{N} stories, {M} sub-tasks parsed`.

### Step 3: Read the SRS Document

Read the SRS document provided as attachment or via `--srs` flag.

```
read_file → {srs_path}
```

Extract:
1. **All FR-* requirement IDs** with their descriptions
2. **All US-* user story IDs** with their descriptions
3. **Business rules and validation logic**
4. **Corner cases and edge scenarios**
5. **Non-functional requirements (NFR-*)**
6. **Test cases (TC-*)**

**Store as `SRS_CONTENT`.**

### Step 4: Read Project Skill (Optional)

If a project skill file is attached or the user specifies a `[Project-Tag]`:

```
read_file → .github/skills/requirements/{project-skill}.md
```

Extract:
1. **File Map** — affected files and paths
2. **Business Rules** — decision matrices, validation chains
3. **Key Functions** — function/method names for code references

**Store as `PROJECT_CONTEXT`.**

### Step 5: Enrich via Sub-agent

Dispatch a sub-agent to combine the parsed skeleton with SRS content to produce a full WBS.

#### Size Routing

| Stories | Strategy |
|---------|----------|
| ≤ 10 stories | Single-pass sub-agent |
| 11-50 stories | Batched sub-agent (≤ 10 stories per batch) |

#### Single-Pass (≤ 10 stories)

```
runSubagent(
  description: "Enrich WBS skeleton with SRS details",
  prompt: <ENRICHMENT_PROMPT>
)
```

#### ENRICHMENT_PROMPT

```
You are a senior Agile PM and Tech Lead for EC-Cube 4.x.

TASK: Enrich this WBS skeleton (parsed from Excel/CSV) into a full, detailed
WBS markdown document by cross-referencing the SRS requirements.

## PARSED SKELETON
{STORY_TREE — story titles, sub-task titles, effort hours, status, assignees}

## SRS CONTENT
{SRS_CONTENT — requirement IDs, descriptions, business rules, corner cases}

## PROJECT CONTEXT (if available)
{PROJECT_CONTEXT — file map, business rules, key functions}

## ENRICHMENT RULES

1. **Excel is the source of truth for structure:** DO NOT add, remove, or reorder
   stories or sub-tasks. The Excel defines exactly what exists. Only enrich content.
2. **Match stories to requirements:** For each story title, find the corresponding
   FR-*/US-* IDs from the SRS. Use keyword matching and semantic similarity.
3. **Generate Story Overview:** Write 5-20 sentences covering functionality, business
   problem, users, technical approach, layers, workflows, integration points.
4. **Expand sub-tasks:** For each sub-task title from the Excel:
   - Infer the skill type (Backend/Frontend/Full-stack/DevOps) from the title
   - Use the dev_effort hours from Excel as the estimate
   - Write Summary, Requirement Details, Acceptance Criteria (Gherkin format)
   - Add Corner Cases if SRS mentions edge scenarios for that requirement
   - Add Risks if applicable
   - Add Definition of Done
5. **Preserve Excel metadata:** Keep assignee, status, effort hours from the original
6. **Story points:** Estimate from total sub-task hours:
   ≤4h → 1pt, ≤8h → 2pt, ≤16h → 3pt, ≤24h → 5pt, ≤40h → 8pt, >40h → 13pt
7. **Sprint assignment:** Respect dependency order, aim for ~20-30 points per sprint
8. **SKIP empty sections:** If no corner cases exist, omit that section entirely
9. **Traceability:** Every FR-*/US-* in the SRS MUST appear in the traceability matrix.
   Flag any uncovered as "⚠️ UNCOVERED"

## OUTPUT FORMAT

# Work Breakdown Structure — JIRA Import Ready
## {Feature Name}

**Generated:** {YYYY-MM-DD}
**Source:** {Excel/CSV filename} + {SRS filename}
**Total Stories:** {count}
**Total Story Points:** {sum}
**Import Method:** Reverse-imported from Excel-WBS, enriched with SRS

---

## Epic: {Feature Name}

**Epic Description:**
> {1 sentence business objective from SRS}

---

FOR EACH STORY, output exactly:

### Story {N}: {Title from Excel}

**Type:** Story | **Priority:** {H/M/L} | **Points:** {N} | **Sprint:** {N}
**Assignee:** {from Excel} | **Status:** {from Excel}

#### Story Overview
{5-20 sentences — comprehensive description cross-referenced from SRS}

- **Linked Requirements:** {FR-001, FR-002, US-001, ...}
- **Affected Components:** {from project skill file map, or inferred}
- **Scope:** {Frontend/Backend/Full-stack}
- **Associated Epic:** {Feature Name}

#### Sub-task List
- [ ] {N}.1 — {Sub-task Title from Excel} ({Skill}, {hours from Excel})
- [ ] {N}.2 — {Sub-task Title from Excel} ({Skill}, {hours from Excel})

---

#### Sub-tasks:

##### Sub-task {N}.{M}: {Title from Excel}
**Type:** Sub-task | **Estimate:** {hours from Excel} | **Skill:** {inferred}
**Assignee:** {from Excel} | **Status:** {from Excel}

###### Summary
{One concise paragraph — what this sub-task delivers, cross-referenced from SRS}

###### Requirement Details
{Detailed description referencing SRS requirement IDs. Include business logic,
calculations, UI behavior, or API contracts from the SRS.}

- **Linked Requirements:** {FR-001, FR-002, ...}
- **Affected Files:** {from project skill or inferred}
- **Scope:** {Frontend / Backend / Full-stack}

###### Associated Story
- **Parent Story:** Story {N} — {Story Title}
- **Epic:** {Feature Name}

###### Acceptance Criteria
- [ ] **Given** {precondition from SRS}, **When** {action}, **Then** {expected result}
- [ ] **Given** {precondition from SRS}, **When** {action}, **Then** {expected result}

###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| {dependency} | {Blocks / Blocked-by / Related-to} | {explanation} |

###### Corner Cases & Edge Scenarios
(ONLY if SRS has relevant edge cases for this requirement)
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | {from SRS} | {from SRS} |

###### Risks
(ONLY if applicable)
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|

###### Notes / Additional Information
- {implementation hints from project skill}
- {Excel remarks if any: "{remarks from Excel}"}

###### Definition of Done
- [ ] Code implemented and compiles
- [ ] Unit tests passing
- [ ] Code reviewed
- [ ] {additional criteria from SRS acceptance criteria}

---

AFTER ALL STORIES, output:

## Cross-Story Dependencies
| Story | Depends On | Type | Details |
|-------|-----------|------|---------|

## Suggested Sprint Allocation
| Sprint | Stories | Total Points | Sprint Goal |
|--------|---------|-------------|-------------|

## Risk Summary (Across All Stories)
| # | Risk | Affected Stories | Likelihood | Impact | Mitigation |
|---|------|-----------------|-----------|--------|-----------|

## Assumptions
- {list}

## Traceability Matrix
| SRS Requirement | Story | Sub-tasks | Status |
|----------------|-------|-----------|--------|
{EVERY FR-* and US-* must appear. Flag uncovered as "⚠️ UNCOVERED"}

## Import Metadata
| Field | Value |
|-------|-------|
| Source Excel/CSV | {filename} |
| SRS Document | {filename} |
| Project Skill | {filename or "N/A"} |
| Stories Imported | {count} |
| Sub-tasks Imported | {count} |
| Import Date | {YYYY-MM-DD} |
```

#### Batched (11-50 stories)

Split stories into batches of ≤ 10. For each batch:

```
runSubagent(
  description: "Enrich WBS batch {B}: stories {start}-{end}",
  prompt: <ENRICHMENT_PROMPT with only batch stories + relevant SRS sections>
)
```

After all batches complete, assemble into a single document and append summary sections
(Cross-Story Dependencies, Sprint Allocation, Risk Summary, Traceability Matrix, Import Metadata).

### Step 6: Write Output

Save the enriched WBS markdown to:

```
docs/wbs/wbs-{feature-name}.md
```

Derive `{feature-name}` from:
1. The Excel filename (strip `-wbs.xlsx`, strip `excel/` prefix)
2. Or the SRS filename (strip `srs-` prefix, strip `.md`)
3. Or ask the user if neither yields a clean name

### Step 7: Report

```
✓ WBS imported and enriched: docs/wbs/wbs-{feature-name}.md
  Source: {excel/csv filename}
  SRS: {srs filename}
  Project Skill: {skill filename or "N/A"}
  Stories: {N}, Sub-tasks: {M}
  Story Points: {total}
  Traceability: {covered}/{total} requirements mapped ({uncovered} uncovered)
```

---

## Error Handling

| Error | Action |
|-------|--------|
| Excel/CSV file not found | Report error, ask user to verify path |
| No stories parsed from Excel | Report error, check column format |
| SRS not attached or not found | Report error — SRS is required for enrichment |
| openpyxl not installed | Run `pip3 install openpyxl` then retry |
| Story-requirement mismatch | Flag unmatched stories in output with "⚠️ NO SRS MATCH" |
| FR/US not covered | List in Traceability Matrix as "⚠️ UNCOVERED" |
| CSV encoding issues | Try `utf-8-sig`, `shift_jis`, `cp932` encodings |

---

## Quality Checklist

Before finalizing output, verify:

- [ ] Every story from the Excel appears in the WBS
- [ ] Every sub-task from the Excel appears under its correct story
- [ ] Dev effort hours match the Excel source
- [ ] Assignee and status are preserved from the Excel
- [ ] Every FR-*/US-* from the SRS appears in the Traceability Matrix
- [ ] Acceptance criteria use Gherkin format where applicable
- [ ] No empty sections (Corner Cases, Risks) — omit if not applicable
- [ ] Import Metadata section is present at the end
- [ ] Output file saved to `docs/wbs/` directory
