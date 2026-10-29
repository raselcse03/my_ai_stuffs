# WBS Import — Enrichment Prompt

ENRICHMENT_PROMPT scaffold with enrichment rules — loaded by wbs-import Step 5 when dispatching the enrichment sub-agent (single-pass or per batch).

## ENRICHMENT_PROMPT

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

{→ Splice in the full canonical template from ../../examples/wbs-output-format.md, applying its "WBS-Import additions" section: Source + Import Method header lines, Assignee/Status lines on stories and sub-tasks, "(ONLY if ...)" notes on Corner Cases and Risks, the fixed Definition of Done items, the import Notes bullets, and the trailing Import Metadata section. Structural values — titles, hours, assignee, status, remarks — come verbatim from the Excel.}
```
