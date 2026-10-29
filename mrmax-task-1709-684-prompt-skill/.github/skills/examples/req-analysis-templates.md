# Requirement Analysis — Output Templates

> Loaded on-demand by `requirement-analysis.md`. Do NOT read unless running `[Req-Analysis]`.

---

## Maturity Report Template

Use when maturity < 100% and user chooses "No, generate maturity report and stop."

Output file: `docs/maturity-report/maturity-report-{feature-name}.md`

```markdown
# Requirement Maturity Report
## {Feature Name}

**Generated:** {YYYY-MM-DD}
**Overall Maturity:** {X}%
**Source Files:** {list of attachment filenames}
**Verdict:** ❌ Not ready for SRS generation

---

## Dimension Scores

| Dimension | Score | Weight | Weighted Score |
|-----------|-------|--------|----------------|
| Completeness | X% | 25% | X.X |
| Clarity | X% | 20% | X.X |
| Testability | X% | 20% | X.X |
| Consistency | X% | 15% | X.X |
| Specificity | X% | 10% | X.X |
| Boundary Definition | X% | 10% | X.X |
| **Overall** | | **100%** | **{X}%** |

---

## Unclarified Items

{Full unclarified items table from assessor}

## Questions for Client

{Full questions table from assessor — these must be answered to improve maturity}

## Assumptions (if proceeding without clarification)

{Full assumptions table from assessor}

## Recommendations to Improve Maturity

{Full recommendations table from assessor}

---

## Next Steps

1. Review the questions above with the client / stakeholders
2. Get clarification on all unclarified items
3. Re-run: `@workspace [Req-Analysis]` with the original files + client answers
4. Target: 100% maturity before SRS generation
```

---

## SRS Document Template

Output file: `docs/srs-{feature-name}.md`

Add metadata header at top:
```markdown
<!--
  STATUS: DRAFT (pending review) / FINAL
  MATURITY SCORE: {MATURITY_SCORE}%
  ANALYST ITERATION: {1 or 2}
  REVIEWER VERDICT: {PENDING / APPROVED / APPROVED_WITH_CORRECTIONS}
  CORRECTIONS APPLIED: {count} sections (if applicable)
-->
```

```markdown
# Software Requirements Specification
## {Feature Name}

**Generated:** {YYYY-MM-DD}
**Source:** {attachment filenames}
**Requirement Maturity:** {MATURITY_SCORE}%
**Iterations:** {number of feedback loops}
**Status:** {APPROVED / APPROVED WITH OPEN ITEMS}

---

## 1. Executive Summary
{High-level overview from analyst report}

## 2. Functional Requirements

### 2.1 Core Requirements
| ID | Requirement | Priority | Acceptance Criteria |
|----|------------|----------|-------------------|
| FR-001 | {requirement} | {High/Medium/Low} | {criteria} |

### 2.2 Business Rules
{Business rules extracted from requirements}

### 2.3 User Stories
| ID | As a... | I want to... | So that... | Priority |
|----|---------|-------------|-----------|----------|
| US-001 | {role} | {action} | {benefit} | {priority} |

## 3. Non-Functional Requirements
| ID | Category | Requirement |
|----|----------|------------|
| NFR-001 | Performance | {requirement} |
| NFR-002 | Security | {requirement} |

## 4. Impact Analysis

### 4.1 Affected Components
{From analyst's impact analysis}

### 4.2 Risk Assessment
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|

## 5. Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior | Test Priority |
|---|---------|-------------------|--------------|

## 6. Test Cases
| TC-ID | Linked Req | Description | Steps | Expected Result | Priority |
|-------|-----------|-------------|-------|----------------|----------|

## 7. Assumptions & Dependencies
{List of assumptions made during analysis}

## 8. Open Items (if any)
{Unresolved discrepancies from feedback loop}
```

---

## Project Skill File Template

Output file: `.github/skills/requirements/{feature-name}.md`

**Guidelines:**
- Keep under **400 lines** — agent reads entire file each time
- Use **tables over prose** — agents parse structured data faster
- Include **exact file paths** in File Map when available
- Include **exact function names** — agent knows what to grep for
- Condense from the SRS — do NOT copy the full SRS content
- Follow the same structure as existing skills in `requirements/`

**Reference existing skills:** `read_file → .github/skills/requirements/cr2-phase2-ac-installation.md (lines 1-30)`

```markdown
---
name: "{feature-name}"
description: "{Feature Name} - {one-line summary of the feature scope}"
---

# {Project-Tag}: {Feature Name} Skill

**Prerequisites:** Review `core-essentials` for critical rules. Review `change-request` for CR methodology.

## When to Use

- {Scenario 1 — derived from functional requirements}
- {Scenario 2}
- {Scenario 3}
- {Scenario 4}

## Expected Outcome

- {Quality criterion 1 — derived from acceptance criteria}
- {Quality criterion 2}
- {Quality criterion 3}

---

## File Map (Key Files)

{If --with-codebase was used, populate from impact analysis.
 Otherwise, leave placeholder structure:}

```
Frontend:
  app/template/default/{feature}/
    {template}.twig                     → {Purpose}

  html/template/default/assets/dest/js/
    {script}.js                         → {Purpose}

Backend:
  app/Customize/Entity/
    {Entity}.php                        → {Purpose}

  app/Customize/Form/Type/
    {FormType}.php                      → {Purpose}

  app/Customize/Service/
    {Service}.php                       → {Purpose}

  app/Customize/Repository/
    {Repository}.php                    → {Purpose}
```

---

## Business Rules & Logic

{Condensed from SRS Section 2.2 — Business Rules.
 Use tables and decision matrices, not prose.}

| Rule | Condition | Action |
|------|----------|--------|
| {rule} | {condition} | {action} |

---

## Validation Rules

{Condensed from SRS corner cases + test cases.
 Include field-level validation, cross-field dependencies.}

| Field | Rule | Error Behavior |
|-------|------|----------------|
| {field} | {validation} | {what happens on failure} |

---

## Key Functions / Methods

| Function | File | Purpose |
|----------|------|--------|
| {function()} | {file.php} | {what it does} |

---

## Implementation Checklist

### Before Changes
- [ ] Identify affected files from File Map
- [ ] Check if change affects frontend, backend, or both

### During Changes
- [ ] {Naming convention to follow}
- [ ] {Pattern to respect}

### After Changes
- [ ] Frontend and backend logic synchronized
- [ ] Test all scenarios
- [ ] Clear cache: `bin/console cache:clear`

---

## Common Bug Patterns

| Bug | Root Cause | Fix Location |
|-----|-----------|-------------|
| {symptom} | {cause — from corner cases} | {file/function} |

---

## Testing Scenarios

{Top 5-10 most critical test cases from SRS Section 6}

1. **{Scenario}**: {Steps → expected result}
2. **{Scenario}**: {Steps → expected result}
```
