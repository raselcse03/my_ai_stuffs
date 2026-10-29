---
name: requirement-analysis
description: "Orchestrates a 3-agent requirement analysis pipeline (maturity gate → analyst → reviewer) that turns client documents (PDF/Excel/Word/images) into an SRS, a project skill file, and a WBS. Use when asked to analyze requirement documents or produce an SRS. Triggered by the [Req-Analysis] tag or /req-analysis."
---

# Requirement Analysis Skill

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

Analyze client requirement documents (Excel, Word, PDF, images) through a 3-agent pipeline.
Auto-detects file types and converts Excel/Word attachments via `[Req-Convert]` before analysis.
**Includes a Maturity Gate** — assesses requirement readiness before SRS generation. Only 100% mature
requirements auto-proceed; otherwise the user decides whether to continue or stop and get a gap report.
Produces a final **SRS** and a **Project Skill File**, and delegates **WBS** generation to the dedicated `[WBS]` skill.

## Usage

Trigger with the `[Req-Analysis]` action tag and attach requirement files:

```
[Req-Analysis]                ← attach Excel, Word, PDF, or images
[Req-Analysis] --with-codebase ← also cross-check against codebase
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
EXCEL_FILES  = [.xlsx]   WORD_FILES = [.docx]   PDF_FILES = [.pdf]
IMAGE_FILES  = [.png, .jpg, .jpeg, .gif, .webp]
```

### 1b–1e: Convert, Extract, View, Compile

Convert Excel/Word → PDF+PNG, extract text from all PDFs, view all images, then compile everything into a single `RAW_REQUIREMENTS` variable with per-source attribution.

→ Full conversion/extraction procedure (dependency check, `requirement_converter.py`, `pdf_extractor.py`, `view_image`, RAW_REQUIREMENTS format): read `references/attachment-processing.md` when you reach this step (do not load earlier).

---

## Step 2: Requirement Maturity Assessment (Quality Gate)

**Runs BEFORE any SRS generation.** Only 100% maturity auto-proceeds.

### 2a: Dispatch Sub-Agent 0 — Maturity Assessor

```
Read → .claude/skills/agents/requirement-maturity-assessor.md
Agent(agentName: "Explore", description: "Assess requirement maturity",
      prompt: <maturity assessor prompt>)
```

Inject `{RAW_REQUIREMENTS}`, `{SOURCE_FILES}`, `{CODEBASE_CONTEXT}` (or "Not available"). Store as `MATURITY_REPORT`.

### 2b: Parse Maturity Score

Find the line `### MATURITY_SCORE: X%` and parse `X` as an integer.

### 2c: Decision Gate

- **If maturity = 100%:** display `✅ Requirement Maturity: 100% — Auto-proceeding` and go to Step 3.
- **If maturity < 100%:** show the score/dimension summary, then `AskUserQuestion` "Proceed with SRS generation?" — "Yes, proceed anyway" / "No, generate maturity report and stop".
  - **No** → write `docs/maturity-report/maturity-report-{feature-name}.md`, display the stop message, and **STOP** (no further steps).
  - **Yes** → log `MATURITY_SCORE` for the SRS header and go to Step 3.

→ Display box, maturity-report note, and stop/proceed message templates: read `references/maturity-gate.md` when maturity < 100% (do not load earlier).

---

## Step 3: Gather Codebase Context (Optional)

If `--with-codebase` is present or the requirements reference existing features, glob the high-level structure and store as `CODEBASE_CONTEXT`:

```bash
Glob → app/Customize/ , app/Customize/Entity/ , app/Customize/Service/ , app/Customize/Controller/
```

---

## Step 4: Dispatch Sub-Agent 1 — Requirement Analyst

```
Read → .claude/skills/agents/requirement-analyst.md
Agent(agentName: "Explore", description: "Analyze requirements", prompt: <analyst prompt>)
```

Inject `{RAW_REQUIREMENTS}`, `{CODEBASE_CONTEXT}`, `{REVIEWER_FEEDBACK}` (empty on iteration 1), `{ITERATION}` = "1". Store as `ANALYST_REPORT`.

## Step 4.5: Write Initial SRS Draft

Determine a short kebab-case `{feature-name}`. Write the analyst report to `docs/srs-{feature-name}.md` using the SRS template (`examples/req-analysis-templates.md` → "SRS Document Template") plus a DRAFT metadata header. This file is now the source of truth.

→ Draft metadata header format: read `references/srs-pipeline.md` § "Step 4.5" (do not load earlier).

## Step 5: Dispatch Sub-Agent 2 — Corrective Reviewer

```
Read → .claude/skills/agents/requirement-reviewer.md
Agent(agentName: "Explore", description: "Review and correct requirement analysis",
      prompt: <reviewer prompt with RAW_REQUIREMENTS + ANALYST_REPORT>)
```

Store as `REVIEWER_FEEDBACK`. The reviewer returns one verdict:
- **APPROVED** — correct as-is → Step 6/7
- **APPROVED_WITH_CORRECTIONS** — issues corrected inline → apply and proceed
- **CRITICAL_REWORK** — fundamental misunderstanding → loop back to Step 4 (max 1 re-iteration, rare)

## Step 6: Apply Reviewer Corrections to SRS File

Apply the verdict: update the SRS metadata header for APPROVED; `Edit` each `CORRECTED_SECTIONS` block for APPROVED_WITH_CORRECTIONS; run the bounded re-iteration for CRITICAL_REWORK. Then proceed to Step 7.

→ Full verdict-handling blocks (metadata headers + CRITICAL_REWORK loop): read `references/srs-pipeline.md` § "Step 6" (do not load earlier).

---

## Step 7: Compile Remaining Deliverables

The SRS already exists (Steps 4.5, 6). Verify it has reviewer corrections and all required sections:
Executive Summary, Functional Requirements (Core + Business Rules + User Stories), Non-Functional Requirements, Impact Analysis, Corner Cases, Test Cases, Assumptions & Dependencies, Open Items.

→ Full SRS section template: see `.claude/skills/examples/req-analysis-templates.md` → "SRS Document Template".

Then produce the remaining deliverables by delegating:

- **WBS** → `[WBS] docs/srs-{feature-name}.md` (read `wbs-generation/SKILL.md`). Produces `docs/wbs/wbs-{feature-name}.md`. Wait for completion.
- **Excel WBS** → `[Excel-WBS] docs/wbs/wbs-{feature-name}.md` (read `excel-wbs-generation/SKILL.md`). Produces `docs/wbs/excel/{feature-name}-wbs.xlsx`. Wait for completion.
- **Project Skill File** → create `.claude/skills/requirements/{feature-name}.md`, a condensed agent-optimized reference (≤400 lines) so future `[Tag][{Project-Tag}]` prompts load pre-built context. Sections: When to Use, Expected Outcome, File Map, Business Rules & Logic, Validation Rules, Key Functions/Methods, Implementation Checklist, Common Bug Patterns, Testing Scenarios.

→ Full project skill file template + guidelines: see `.claude/skills/examples/req-analysis-templates.md` → "Project Skill File Template".

## Step 7.5: Auto-Generate Core Skill Files (Conditional)

If the project has a codebase but no `core-essentials.md` / `core-full.md`, offer to generate them so all other skills gain project-specific context.

| Core files exist? | Codebase exists? | Action |
|:-:|:-:|--------|
| Yes | Any | Skip silently |
| No | No | Skip silently |
| No | Yes | `AskUserQuestion` → if "Yes", delegate to `init-core/SKILL.md` **Step 3** (infer from codebase + the fresh SRS) |

Codebase detected via `composer.json` / `package.json` / `requirements.txt` / `go.mod` / `Cargo.toml` / `pom.xml` / `pubspec.yaml` / `Gemfile`.

## Step 8: Cleanup Temporary Files

**⚠️ CRITICAL — always run after deliverables are created:**

```bash
rm -rf /tmp/req-analysis-*
ls /tmp/req-analysis-* 2>/dev/null && echo "WARNING: temp files remain" || echo "Cleanup complete"
```

> Converted files in `.github/docs/requirement-conversion/` are kept permanently for future reference.

---

## Output Summary (Return Contract)

Report to the user: maturity %, and paths to the SRS (`docs/srs-{feature-name}.md`), WBS (`docs/wbs/wbs-{feature-name}.md`), Excel WBS (`docs/wbs/excel/{feature-name}-wbs.xlsx`), project skill (`.claude/skills/requirements/{feature-name}.md`), and core-skills status (Generated / Already existed / Skipped). Include stats (FR/US/TC counts, sub-agents used = 3, iterations, final verdict) and next steps (register the `[Project-Tag]` in CLAUDE.md and `SKILL.md`).

---

## Error Handling

| Error | Action |
|-------|--------|
| PDF extraction fails | Inform user, suggest converting to images manually |
| pymupdf not installed | Run `pip install -r .claude/skills/support/requirements.txt` and retry |
| Excel/Word conversion fails | Check [Req-Convert] dependencies — venv, LibreOffice AppImage |
| LibreOffice not found | Follow setup in `requirement-conversion.md` (download AppImage) |
| Attached file is unsupported type | Inform user: supported formats are .xlsx, .docx, .pdf, and images |
| Sub-agent returns empty | Retry once, then report failure |
| SRS file write fails | Check disk space and directory permissions |
| Cleanup fails | Log warning but do not block deliverable output |
