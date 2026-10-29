# WBS Output Format — JIRA Import Ready (Canonical Template)

Shared output-format template for the final WBS document — loaded by wbs-generation (Step 3A prompt, Step 3B Phase 2 prompt and Phase 2 Final assembly) and wbs-import (Step 5 enrichment prompt).

## Full Template

```
# Work Breakdown Structure — JIRA Import Ready
## {Feature Name}

**Generated:** {YYYY-MM-DD}
**Source:** {SRS filename}
**Total Stories:** {count}
**Total Story Points:** {sum}

---

## Epic: {Feature Name}

**Epic Description:**
> {1 sentence business objective}

---

FOR EACH STORY, output exactly:

### Story {N}: {Title}

**Type:** Story | **Priority:** {H/M/L} | **Points:** {N} | **Sprint:** {N}

#### Story Overview
{5-20 sentences providing a comprehensive description of this story. Cover: what functionality is being built, the business problem it solves, who the end users are, how it fits into the broader feature/epic, key technical approach, which layers are involved (frontend/backend/database), major workflows or user interactions, integration points with other stories or systems, and any important constraints or considerations. This should give a complete picture so that anyone reading it understands the full scope without needing to read each sub-task.}

- **Linked Requirements:** {FR-001, FR-002, US-001, ...}
- **Affected Components:** {Entity / Service / Controller / Template — list specific files if known}
- **Scope:** {Frontend/Backend/Full-stack}
- **Associated Epic:** {Feature Name}

#### Sub-task List
- [ ] {N}.1 — {Sub-task Title} ({Skill}, {hours})
- [ ] {N}.2 — {Sub-task Title} ({Skill}, {hours})

---

#### Sub-tasks:

##### Sub-task {N}.{M}: {Title}
**Type:** Sub-task | **Estimate:** {hours} | **Skill:** {Backend/Frontend/Full-stack/DevOps}

###### Summary
{One concise paragraph describing what this sub-task delivers and why it matters to the end user or business.}

###### Requirement Details
{Detailed description of the functional requirement this sub-task fulfills. Reference the SRS requirement IDs (e.g., FR-001, FR-002) that this sub-task implements. Include specific business logic, calculations, UI behavior, or API contracts as applicable.}

- **Linked Requirements:** {FR-001, FR-002, ...}
- **Affected Files:** {list specific files to create or modify}
- **Scope:** {Frontend / Backend / Full-stack}

###### Associated Story
- **Parent Story:** Story {N} — {Story Title}
- **Epic:** {Feature Name}

###### Acceptance Criteria
- [ ] **Given** {precondition}, **When** {action}, **Then** {expected result}
- [ ] **Given** {precondition}, **When** {action}, **Then** {expected result}
- [ ] {Additional criterion in simple checkbox format if Gherkin is not applicable}

###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| {Story N / Sub-task / External system / API} | {Blocks / Blocked-by / Related-to} | {Brief explanation} |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | {edge case description} | {how the system should handle it} |
| 2 | {edge case description} | {how the system should handle it} |

###### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| {risk description} | {Low/Medium/High} | {Low/Medium/High} | {mitigation strategy} |

###### Notes / Additional Information
- {Implementation hints, design considerations, or technical notes}
- {References to external documentation, Figma designs, or API specs}
- {Any assumptions made for this sub-task}

###### Definition of Done
- [ ] {specific completion criterion}
- [ ] {specific completion criterion}

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
```

## WBS-Import additions (apply only in wbs-import; wbs-generation ignores this section)

Document header — replace the **Source** line and add **Import Method** after **Total Story Points**:

```
**Source:** {Excel/CSV filename} + {SRS filename}
**Import Method:** Reverse-imported from Excel-WBS, enriched with SRS
```

Story heading — titles come from Excel; add after the **Type / Priority / Points / Sprint** line:

```
**Assignee:** {from Excel} | **Status:** {from Excel}
```

Sub-task heading — title and Estimate = {hours from Excel}, Skill = {inferred}; add after the **Type / Estimate / Skill** line:

```
**Assignee:** {from Excel} | **Status:** {from Excel}
```

Corner Cases & Edge Scenarios — prefix the section with:

```
(ONLY if SRS has relevant edge cases for this requirement)
```

Risks — prefix the section with (and omit the example row):

```
(ONLY if applicable)
```

Notes / Additional Information — use these bullets instead:

```
- {implementation hints from project skill}
- {Excel remarks if any: "{remarks from Excel}"}
```

Definition of Done — use these items instead:

```
- [ ] Code implemented and compiles
- [ ] Unit tests passing
- [ ] Code reviewed
- [ ] {additional criteria from SRS acceptance criteria}
```

Append after the Traceability Matrix:

```
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
