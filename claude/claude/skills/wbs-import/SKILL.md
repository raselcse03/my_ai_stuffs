---
name: wbs-import
description: "Reverse-generates enriched WBS markdown from an Excel-WBS (.xlsx) or CSV export, cross-referenced with an SRS for acceptance criteria and traceability. Use when importing or reversing a spreadsheet WBS back to markdown. Triggered by the [WBS-Import] tag or /wbs-import."
---

# WBS Import Skill (Reverse Excel-WBS)

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **WBS Importer** that reconstructs a fully detailed, JIRA-ready WBS markdown document from an Excel-WBS spreadsheet (`.xlsx`) or its CSV export.

**Core principle:** The Excel/CSV is the **sole source of truth** for the WBS structure — stories, sub-tasks, their order, effort hours, assignees, and status. No stories or sub-tasks are added, removed, or reordered. The SRS document and project skill file are used **only** to generate descriptions, acceptance criteria, corner cases, risks, and requirement traceability for each story and sub-task.

## Usage

```
[WBS-Import] {path-to-excel-or-csv}
```

The user attaches **up to 3 context documents** alongside the prompt:

| Attachment | Required | Purpose |
|------------|----------|---------|
| Excel-WBS (`.xlsx`) or CSV (`.csv`) | **Yes** | Source: story/sub-task skeleton with titles, estimates, status |
| SRS document (`.md`) | **Yes** | Enrichment: requirement IDs, acceptance criteria, business rules |
| Project skill file (`.md`) | Optional | Domain context: file maps, business rule matrices, field hierarchies |

### Examples

```
[WBS-Import] docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
  (attach: docs/srs/srs-vpoint-card-linkage.md)

[WBS-Import] /tmp/cr4-wbs-export.csv
  (attach: docs/srs/srs-store-pickup.md, .claude/skills/requirements/cr4-phase2-store-pickup-inventory.md)

[WBS-Import] docs/wbs/excel/ac-installation-wbs.xlsx --srs docs/srs/srs-ac-installation.md
```

Slash command:
```
/wbs-import docs/wbs/excel/vpoint-card-linkage-wbs.xlsx
```

→ Input format (column spec A–P, row classification, CSV columns): read `references/excel-csv-parsing.md` when you reach Step 1 (do not load earlier).

---

## Execution Steps

### Step 1: Parse the Excel/CSV Source

Parse the source directly — there is no dedicated parser script for this format.

→ Full parsing scripts (openpyxl for `.xlsx`, `csv.DictReader` for `.csv`): read `references/excel-csv-parsing.md` § "Step 1 Parsing Scripts" when you reach this step (do not load earlier).

**Store result as `PARSED_DATA`.**

### Step 2: Build Story–Sub-task Tree

From `PARSED_DATA`, construct a hierarchical tree: iterate rows, start a new `current_story` on each story row (has an SL value), append each sub-task row to the current story's `subtasks`.

→ Tree-building pseudocode: read `references/excel-csv-parsing.md` § "Step 2 Tree-Building Pseudocode" (do not load earlier).

**Count:** Report `{N} stories, {M} sub-tasks parsed`.

### Step 3: Read the SRS Document

Read the SRS document provided as attachment or via `--srs` flag.

```
Read → {srs_path}
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
Read → .claude/skills/requirements/{project-skill}.md
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

**Single-Pass (≤ 10 stories):** dispatch one `Agent` with `<ENRICHMENT_PROMPT>`.

**Batched (11-50 stories):** split stories into batches of ≤ 10; dispatch one `Agent` per batch with `<ENRICHMENT_PROMPT>` containing only that batch's stories + relevant SRS sections. After all batches complete, assemble into a single document and append the summary sections (Cross-Story Dependencies, Sprint Allocation, Risk Summary, Traceability Matrix, Import Metadata).

→ ENRICHMENT_PROMPT scaffold + enrichment rules: read `references/enrichment-prompt.md` when dispatching (do not load earlier).
→ OUTPUT FORMAT (canonical template + "WBS-Import additions"): read `../examples/wbs-output-format.md` — the enrichment prompt splices it into its OUTPUT FORMAT section (do not load earlier).

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

---

## Related Skills

- **`wbs-generation`** — forward direction (SRS → WBS markdown)
- **`excel-wbs-generation`** — WBS markdown → Excel
- **`../examples/wbs-output-format.md`** — shared canonical output template
