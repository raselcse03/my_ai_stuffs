# Requirement Analysis — SRS Draft & Reviewer-Verdict Handling

SRS draft metadata header (Step 4.5) and the full verdict-handling blocks with metadata headers and the CRITICAL_REWORK loop (Step 6). Loaded when writing the SRS draft and applying reviewer corrections. Do not load earlier.

## Step 4.5: SRS Draft Metadata Header

When writing `docs/srs-{feature-name}.md`, use the SRS template from
`.claude/skills/examples/req-analysis-templates.md` → "SRS Document Template", populated with
the analyst's report data, and add this metadata header at the top:

```markdown
<!--
  STATUS: DRAFT (pending review)
  MATURITY SCORE: {MATURITY_SCORE}%
  ANALYST ITERATION: 1
  REVIEWER VERDICT: PENDING
-->
```

The SRS file is now the **source of truth** for all subsequent steps.

## Step 6: Apply Reviewer Corrections to SRS File

### VERDICT: APPROVED

Update the SRS file metadata header:
```markdown
<!--
  STATUS: FINAL
  MATURITY SCORE: {MATURITY_SCORE}%
  ANALYST ITERATION: 1
  REVIEWER VERDICT: APPROVED
-->
```

Proceed directly to Step 7.

### VERDICT: APPROVED_WITH_CORRECTIONS

1. For each corrected section in the reviewer's `CORRECTED_SECTIONS`:
   - Use `Edit` to apply the correction directly to `docs/srs-{feature-name}.md`
   - Replace the corresponding section in the file with the corrected version
2. Update the SRS file metadata header:
```markdown
<!--
  STATUS: FINAL
  MATURITY SCORE: {MATURITY_SCORE}%
  ANALYST ITERATION: 1
  REVIEWER VERDICT: APPROVED_WITH_CORRECTIONS
  CORRECTIONS APPLIED: {count} sections
-->
```
3. Proceed to Step 7

### VERDICT: CRITICAL_REWORK (Max 1 Re-iteration)

This is rare — only triggered when the analyst fundamentally misunderstood the requirements.

1. Re-dispatch Sub-Agent 1 (Step 4) with the reviewer's critical issues as `{REVIEWER_FEEDBACK}` and `{ITERATION}` = "2"
2. Update the SRS file with the revised analyst report using `Edit` on each changed section
3. Re-dispatch Sub-Agent 2 (Step 5) with the revised `ANALYST_REPORT`
4. Apply final corrections to the SRS file
5. Update metadata header:
```markdown
<!--
  STATUS: FINAL (with open items)
  MATURITY SCORE: {MATURITY_SCORE}%
  ANALYST ITERATION: 2
  REVIEWER VERDICT: {final verdict}
-->
```
6. If second reviewer verdict is still `CRITICAL_REWORK`:
   - Add remaining issues under "## 8. Open Items" in the SRS file
   - Proceed to Step 7 with the best available version

**Performance note:** The typical flow is Maturity Gate → Analyst → SRS Draft → Corrective Reviewer → apply corrections → done (3 sub-agent calls + file updates). The CRITICAL_REWORK loop adds 2 more calls but is rarely triggered.
