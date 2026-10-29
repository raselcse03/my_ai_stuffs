# Requirement Analysis — Maturity Gate Display & Report

Display templates, user-facing report, and stop/proceed messages for Step 2 (Maturity Assessment). Loaded when maturity < 100% and you must show the score, ask the user, and either stop or proceed. Do not load earlier.

## 2c: Decision Gate — Display (maturity < 100%)

Display the maturity score and dimension summary to the user:

```
📊 Requirement Maturity Assessment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Maturity: {X}%

| Dimension            | Score |
|----------------------|-------|
| Completeness         | X%    |
| Clarity              | X%    |
| Testability          | X%    |
| Consistency          | X%    |
| Specificity          | X%    |
| Boundary Definition  | X%    |

⚠️ {count} unclarified items found
❓ {count} questions for client
📝 {count} assumptions would be required

Do you want to proceed with SRS generation at {X}% maturity?
```

Ask the user via `AskUserQuestion`:
- **"Proceed with SRS generation?"** — Options: "Yes, proceed anyway" / "No, generate maturity report and stop"

## 2d: If User Says "No" — Generate Maturity Report and STOP

Determine feature name (short kebab-case from requirements).

Create file: `docs/maturity-report/maturity-report-{feature-name}.md`

**For the maturity report template**, see `.claude/skills/examples/req-analysis-templates.md` → "Maturity Report Template"

**Display to the user:**

```
⏹️ Requirement Analysis Stopped — Maturity Below Threshold

📊 Overall Maturity: {X}%
📄 Maturity Report: docs/maturity-report/maturity-report-{feature-name}.md

📋 Summary:
- {count} unclarified items need resolution
- {count} questions to discuss with client
- {count} assumptions would be needed if proceeding

💡 Next: Review the maturity report, clarify with client, then re-run [Req-Analysis]
```

**STOP HERE** — do not proceed to any further steps.

## 2e: If User Says "Yes" — Proceed with Acknowledged Gaps

- Log the maturity score for inclusion in the SRS metadata header
- Store `MATURITY_SCORE` for later use
- Proceed to Step 3
