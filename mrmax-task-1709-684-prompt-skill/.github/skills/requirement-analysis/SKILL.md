---
name: "Requirement Analyst"
role: "Orchestrate multi-agent requirement analysis — parse client documents, produce SRS + Project Skill File, delegate WBS to [WBS] skill"
primary_tools: [read_file, view_image, runSubagent, create_file, run_in_terminal]
scope: "full-repository"
---

# Requirement Analysis Skill

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

Analyze client requirement documents (Excel, Word, PDF, images) through a 3-agent pipeline.
Auto-detects file types and converts Excel/Word attachments via `[Req-Convert]` before analysis.
**Includes a Maturity Gate** — assesses requirement readiness before SRS generation. Only 100% mature
requirements auto-proceed; otherwise the user decides whether to continue or stop and get a gap report.
Produces a final **SRS** (Software Requirements Specification) and a **Project Skill File** (agent-optimized requirement reference for tagged prompts). Delegates **WBS** generation to the dedicated `[WBS]` skill (`wbs-generation.md`) for size-aware, adaptive processing.

## Usage

Trigger with the `[Req-Analysis]` action tag and attach requirement files:

```
@workspace [Req-Analysis]                ← attach Excel, Word, PDF, or images
@workspace [Req-Analysis] --with-codebase ← also cross-check against codebase
```

**Supported file types (auto-detected):**

| Type | Extensions | Processing |
|------|-----------|------------|
| **Excel** | `.xlsx` | Auto-convert via `[Req-Convert]` → PDF + PNG, then extract |
| **Word** | `.docx` | Auto-convert via `[Req-Convert]` → PDF + PNG, then extract |
| **PDF** | `.pdf` | Extract text via `pdf_extractor.py` + render page images |
| **Image** | `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp` | Use directly via `view_image` |

---

## Step 1: Classify and Prepare Attachments

### 1a: Classify Attached Files

Inspect all attached files and group by extension:

```
EXCEL_FILES  = [files with .xlsx extension]
WORD_FILES   = [files with .docx extension]
PDF_FILES    = [files with .pdf extension]
IMAGE_FILES  = [files with .png, .jpg, .jpeg, .gif, .webp extension]
```

### 1b: Convert Excel & Word Files (if any)

For each `.xlsx` or `.docx` attachment, ensure `[Req-Convert]` dependencies are ready:

```bash
echo "=== Dependency Check ==="
test -d .github/skills/support/venv && echo "✔ venv" || echo "✘ venv MISSING"
.github/skills/support/venv/bin/python -c "import openpyxl, fitz, PIL" 2>/dev/null && echo "✔ Python packages" || echo "✘ Python packages MISSING"
ls .github/skills/support/packages/libreoffice/*.AppImage 2>/dev/null && echo "✔ LibreOffice" || echo "✘ LibreOffice MISSING"
echo "========================"
```

If any dependency is missing, follow the setup in `requirement-conversion.md`.

Then convert each file (use `--dpi 300` for best AI analysis quality):

```bash
.github/skills/support/venv/bin/python .github/skills/support/requirement_converter.py \
  "<file_path>" \
  --output .github/docs/requirement-conversion \
  --dpi 300
```

Collect output paths for each converted file:
- **PDFs:** `.github/docs/requirement-conversion/{file-name}/pdf/*.pdf`
- **PNGs:** `.github/docs/requirement-conversion/{file-name}/images/*.png`

### 1c: Extract Text from All PDFs

For **every** PDF — both original attachments AND converted outputs from Step 1b:

```bash
python3 .github/skills/support/pdf_extractor.py "<path-to-pdf>" --output-dir /tmp/req-analysis-$$
```

This produces:
- `/tmp/req-analysis-$$/text_full.md` — extracted text (all pages)
- `/tmp/req-analysis-$$/page_N.png` — rendered page images (for diagrams/tables)

Read the extracted text:
```
read_file → /tmp/req-analysis-$$/text_full.md
```

### 1d: View All Images

For **best visual fidelity**, use `view_image` on:

1. **Converted PNGs from Step 1b** — these preserve shapes, arrows, charts that may not survive text extraction. These are higher quality than re-rendered PDF page images.
2. **Original image attachments** (PNG, JPG, etc.)
3. **Page images from pdf_extractor** — for pages with diagrams/tables in original PDFs

> 💡 **Performance tip:** For Excel/Word sources, prefer converted PNGs over pdf_extractor
> page images. The converted PNGs are rendered directly from LibreOffice at high DPI.

### 1e: Compile RAW_REQUIREMENTS

Combine all extracted text and image references into a single `RAW_REQUIREMENTS` variable.
Include source file attribution for each section:

```
=== Source: {filename} (type: xlsx → converted) ===
{extracted text from converted PDF}

=== Source: {filename} (type: docx → converted) ===
{extracted text from converted PDF}

=== Source: {filename} (type: pdf → original) ===
{extracted text from pdf_extractor}

=== Source: {filename} (type: image → viewed directly) ===
[Image viewed via view_image — visual content integrated above]
```

---

## Step 2: Requirement Maturity Assessment (Quality Gate)

**This step runs BEFORE any SRS generation.** It evaluates whether the requirements are
mature enough to produce a high-quality SRS. Only 100% maturity auto-proceeds.

### 2a: Dispatch Sub-Agent 0 — Maturity Assessor

Read the maturity assessor prompt template:
```
read_file → .github/skills/agents/requirement-maturity-assessor.md
```

Invoke via `runSubagent`:

```
runSubagent(
  agentName: "Explore",
  description: "Assess requirement maturity",
  prompt: <maturity assessor prompt with RAW_REQUIREMENTS injected>
)
```

**Inject into prompt:**
- `{RAW_REQUIREMENTS}` — the full extracted requirements text
- `{SOURCE_FILES}` — list of source filenames and types
- `{CODEBASE_CONTEXT}` — file listing (if available, otherwise "Not available")

Store the returned assessment as `MATURITY_REPORT`.

### 2b: Parse Maturity Score

Extract the maturity percentage from the assessor's response:
```
Look for line: ### MATURITY_SCORE: X%
Parse X as integer.
```

### 2c: Decision Gate

**If maturity = 100%:**
- Display: `✅ Requirement Maturity: 100% — Auto-proceeding to SRS generation`
- Proceed to Step 3

**If maturity < 100%:**
- Display the maturity score and dimension summary to the user:

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

- Ask the user via `vscode_askQuestions`:
  - **"Proceed with SRS generation?"** — Options: "Yes, proceed anyway" / "No, generate maturity report and stop"

### 2d: If User Says "No" — Generate Maturity Report and STOP

Determine feature name (short kebab-case from requirements).

Create file: `docs/maturity-report/maturity-report-{feature-name}.md`

**For the maturity report template**, see `.github/skills/examples/req-analysis-templates.md` → "Maturity Report Template"

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

### 2e: If User Says "Yes" — Proceed with Acknowledged Gaps

- Log the maturity score for inclusion in the SRS metadata header
- Store `MATURITY_SCORE` for later use
- Proceed to Step 3

---

## Step 3: Gather Codebase Context (Optional)

If `--with-codebase` flag is present or the requirements reference existing features:

```bash
# Get high-level structure
list_dir → app/Customize/
list_dir → app/Customize/Entity/
list_dir → app/Customize/Service/
list_dir → app/Customize/Controller/
```

Store the file listing as `CODEBASE_CONTEXT` for sub-agents.

---

## Step 4: Dispatch Sub-Agent 1 — Requirement Analyst

Read the analyst prompt template:
```
read_file → .github/skills/agents/requirement-analyst.md
```

Invoke via `runSubagent`:

```
runSubagent(
  agentName: "Explore",
  description: "Analyze requirements",
  prompt: <analyst prompt with RAW_REQUIREMENTS injected>
)
```

**Inject into prompt:**
- `{RAW_REQUIREMENTS}` — the full extracted requirements text
- `{CODEBASE_CONTEXT}` — file listing (if available)
- `{REVIEWER_FEEDBACK}` — empty string on first iteration
- `{ITERATION}` — "1"

Store the returned report as `ANALYST_REPORT`.

---

## Step 4.5: Write Initial SRS Draft

Immediately write the analyst's report to disk as the SRS draft. This enables the reviewer
to reference the actual file and allows corrections to be applied directly.

### Determine Feature Name
Extract a short kebab-case feature name from the requirements (e.g., `ac-installation-phase3`, `loyalty-points`).

### Write SRS Draft

Create file: `docs/srs-{feature-name}.md`

Use the SRS template from Step 7, populated with the analyst's report data.
Add a metadata header at the top:

```markdown
<!--
  STATUS: DRAFT (pending review)
  MATURITY SCORE: {MATURITY_SCORE}%
  ANALYST ITERATION: 1
  REVIEWER VERDICT: PENDING
-->
```

The SRS file is now the **source of truth** for all subsequent steps.

---

## Step 5: Dispatch Sub-Agent 2 — Corrective Reviewer

Read the reviewer prompt template:
```
read_file → .github/skills/agents/requirement-reviewer.md
```

Invoke via `runSubagent`:

```
runSubagent(
  agentName: "Explore",
  description: "Review and correct requirement analysis",
  prompt: <reviewer prompt with RAW_REQUIREMENTS + ANALYST_REPORT injected>
)
```

**Inject into prompt:**
- `{RAW_REQUIREMENTS}` — the original requirements
- `{ANALYST_REPORT}` — Sub-Agent 1's output
- `{CODEBASE_CONTEXT}` — file listing (if available)

Store the returned feedback as `REVIEWER_FEEDBACK`.

The corrective reviewer produces one of three verdicts:
- **APPROVED** — analysis is correct as-is, proceed to Step 7
- **APPROVED_WITH_CORRECTIONS** — issues found and corrected inline, merge and proceed to Step 7
- **CRITICAL_REWORK** — fundamental misunderstanding, loop back to Step 4 (rare)

---

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
   - Use `replace_string_in_file` to apply the correction directly to `docs/srs-{feature-name}.md`
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
2. Update the SRS file with the revised analyst report using `replace_string_in_file` on each changed section
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

---

## Step 7: Compile Remaining Deliverables

The SRS document has already been written and reviewed in Steps 4.5 and 6.
Now generate the remaining deliverables.

### Determine Feature Name
Already determined in Step 4.5. Reuse the same `{feature-name}`.

### Generate SRS Document

The SRS file `docs/srs-{feature-name}.md` already exists from Step 4.5.
Verify it has been updated with reviewer corrections (Step 6).

Ensure the SRS contains all required sections (populated from the analyst report):

**For the full SRS document template**, see `.github/skills/examples/req-analysis-templates.md` → "SRS Document Template"

Required sections: Executive Summary, Functional Requirements (Core + Business Rules + User Stories), Non-Functional Requirements, Impact Analysis, Corner Cases, Test Cases, Assumptions & Dependencies, Open Items.

### Generate WBS Document

**Delegate to the dedicated `[WBS]` skill** — it handles size-aware routing, SRS compression, adaptive batching, and traceability validation.

```
read_file → .github/skills/wbs-generation.md
```

Then follow the WBS skill's full workflow using the SRS file as input:

```
[WBS] docs/srs-{feature-name}.md
```

The WBS skill will produce: `docs/wbs/wbs-{feature-name}.md`

Wait for WBS generation to complete before proceeding.

### Generate Excel WBS

**Delegate to the `[Excel-WBS]` skill** — converts the WBS markdown into a formatted Excel (.xlsx) workbook with colored rows, dropdowns, and proper column layout.

```
read_file → .github/skills/excel-wbs-generation.md
```

Then follow the Excel WBS skill's workflow using the generated WBS markdown as input:

```
[Excel-WBS] docs/wbs/wbs-{feature-name}.md
```

The Excel WBS skill will produce: `docs/wbs/excel/{feature-name}-wbs.xlsx`

Wait for Excel WBS generation to complete before proceeding.

### Generate Project Skill File

Create file: `.github/skills/requirements/{feature-name}.md`

This is a **condensed, agent-optimized** reference file (under 400 lines) that enables
future tagged prompts like `@workspace [Bug][{Project-Tag}] ...` to load pre-built context
instead of re-discovering the codebase every time.

**For the full project skill file template and guidelines**, see `.github/skills/examples/req-analysis-templates.md` → "Project Skill File Template"

Key sections to include: When to Use, Expected Outcome, File Map, Business Rules & Logic, Validation Rules, Key Functions/Methods, Implementation Checklist, Common Bug Patterns, Testing Scenarios.

---

## Step 7.5: Auto-Generate Core Skill Files (Conditional)

**Purpose:** If the project has a codebase but no `core-essentials.md` / `core-full.md`, offer to generate them so all other skills (bug-fixing, CR, feature, etc.) can leverage project-specific context.

### 7.5a: Check Preconditions

```
exists_core_essentials = file_search("**/core-essentials.md") in .github/skills/
exists_core_full       = file_search("**/core-full.md") in .github/skills/
has_codebase           = file_search("**/composer.json") OR file_search("**/package.json")
                         OR file_search("**/requirements.txt") OR file_search("**/go.mod")
                         OR file_search("**/Cargo.toml") OR file_search("**/pom.xml")
                         OR file_search("**/pubspec.yaml") OR file_search("**/Gemfile")
```

**Decision matrix:**

| Core files exist? | Codebase exists? | Action |
|:-:|:-:|--------|
| Yes | Any | Skip silently — core files already defined |
| No | No | Skip silently — no codebase to analyze |
| No | Yes | → Ask user (Step 7.5b) |

### 7.5b: Ask User

Use `vscode_askQuestions`:

```
Question: "No project-specific architecture rules are defined (core-essentials.md / core-full.md).
           These files help all skills (bug-fixing, CR, feature, etc.) understand your project conventions.
           Do you want to generate them from your codebase?"
Options: ["Yes, generate core skill files", "No, skip this step"]
```

**If "No"** → Skip to Step 8.

**If "Yes"** → Proceed to Step 7.5c.

### 7.5c: Delegate to Init-Core Skill

Read the init-core skill:
```
read_file → .github/skills/init-core.md
```

Since a codebase already exists, follow init-core's **Step 3** (Infer Technology from codebase + SRS).
The freshly generated SRS at `docs/srs-{feature-name}.md` provides additional context alongside the codebase files.

After generation, confirm to the user:
```
🏗️ Core skill files generated:
   - .github/skills/core-essentials.md (~60 lines, auto-loaded)
   - .github/skills/core-full.md (~250 lines, on-demand)
```

---

## Step 8: Cleanup Temporary Files

**⚠️ CRITICAL — Always run this after deliverables are created:**

```bash
# Remove all temporary extracted files
rm -rf /tmp/req-analysis-*
```

Verify cleanup:
```bash
ls /tmp/req-analysis-* 2>/dev/null && echo "WARNING: temp files remain" || echo "Cleanup complete"
```

> 📝 **Note:** Converted files in `.github/docs/requirement-conversion/` are kept permanently
> as they may be useful for future reference.

---

## Output Summary

After completion, present to the user:

```
✅ Requirement Analysis Complete

📊 Requirement Maturity: {MATURITY_SCORE}%
📄 SRS Document: docs/srs-{feature-name}.md
📋 WBS Document: docs/wbs/wbs-{feature-name}.md
📊 Excel WBS: docs/wbs/excel/{feature-name}-wbs.xlsx
🏷️ Project Skill: .github/skills/requirements/{feature-name}.md
🏗️ Core Skills: {Generated / Already existed / Skipped}

📊 Analysis Stats:
- Requirement Maturity: {MATURITY_SCORE}%
- Functional Requirements: {count}
- Test Cases: {count}
- User Stories: {count}
- Sub-Agents Used: 3 (Maturity Assessor + Analyst + Reviewer)
- Feedback Iterations: {1 or 2}
- Reviewer Mode: Corrective
- Final Verdict: {APPROVED / APPROVED_WITH_CORRECTIONS / APPROVED WITH OPEN ITEMS}

🧹 Temporary files cleaned up

💡 Next Steps:
- Register the project tag [{Project-Tag}] in .github/copilot-instructions.md (Project Tag Routing table)
- Register the skill in .github/skills/SKILL.md
- Use: @workspace [CR][{Project-Tag}] ... to leverage the pre-built context
```

---

## Error Handling

| Error | Action |
|-------|--------|
| PDF extraction fails | Inform user, suggest converting to images manually |
| pymupdf not installed | Run `pip install -r .github/skills/support/requirements.txt` and retry |
| Excel/Word conversion fails | Check [Req-Convert] dependencies — venv, LibreOffice AppImage |
| LibreOffice not found | Follow setup in `requirement-conversion.md` (download AppImage) |
| Attached file is unsupported type | Inform user: supported formats are .xlsx, .docx, .pdf, and images |
| Sub-agent returns empty | Retry once, then report failure |
| SRS file write fails | Check disk space and directory permissions |
| Cleanup fails | Log warning but do not block deliverable output |
