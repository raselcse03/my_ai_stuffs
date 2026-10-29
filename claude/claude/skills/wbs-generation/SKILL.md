---
name: wbs-generation
description: "Generates a JIRA-ready Work Breakdown Structure — stories, sub-tasks, acceptance criteria, dependencies, traceability — from an existing SRS document, with adaptive single-pass or two-phase generation by size. Use when asked for a WBS from an SRS. Triggered by the [WBS] tag or /wbs."
---

# WBS Generation Skill

**Prerequisites:** Review `core-essentials` for critical rules.

Generate a detailed, JIRA-import-ready **WBS** (Work Breakdown Structure) from an existing **SRS** (Software Requirements Specification) document.

## Usage

```
[WBS] /path/to/srs-document.md
```

Examples:
```
[WBS] docs/srs-ac-installation.md
[WBS] docs/srs-loyalty-points.md
[WBS] /home/user/Desktop/requirements/srs-cr5.md
```

---

## Step 1: Read SRS and Determine Size

Read the SRS file and count lines to determine the processing strategy:

```
Read → {path from user prompt}
```

### Size Routing

Count FR-* and US-* IDs in the SRS to estimate story count, then route:

| Estimated Stories | Strategy | Why |
|-------------------|----------|-----|
| **≤ 10 stories** (SRS ≤ 500 lines) | **Single-pass** (Step 3A) | Fits in one sub-agent context |
| **11-50 stories** (SRS > 500 lines) | **Two-phase adaptive** (Step 3B) | Batches sized by sub-task density |

**Quick estimation:** Count FR-* IDs. Every 2-4 FRs typically produce 1 story. If FR count ÷ 3 ≤ 10, use single-pass.

### Pre-compress SRS (Always)

Before sending to any sub-agent, compress the SRS to reduce token usage:

1. **Keep only structured data** — tables (FR-*, US-*, NFR-*, TC-*), business rules, corner cases
2. **Strip prose paragraphs** — executive summary → 1 sentence, impact analysis → bullet list only
3. **Remove markdown formatting noise** — extra blank lines, decorative headers, horizontal rules
4. **Preserve all IDs and values** — requirement IDs, priorities, acceptance criteria text

Store compressed version as `SRS_COMPRESSED`.

**Target:** Reduce to ~40-50% of original token count while keeping 100% of structured data.

Compression techniques:
- Replace verbose table rows with pipe-delimited compact format
- Merge duplicate/overlapping requirements into single entries
- Remove test case "Steps" column (keep only TC-ID, Description, Expected Result)
- Collapse NFRs into a bullet list (drop table format)

---

## Step 2: Gather Codebase Context (Conditional)

**Only run if** the SRS Impact Analysis section mentions specific `app/Customize/` paths or component names:

```bash
# Quick check — does the SRS reference specific components?
grep -q "app/Customize\|Entity/\|Service/\|Controller/" {srs_file}
```

If yes:
```
Glob → app/Customize/Entity/
Glob → app/Customize/Service/
Glob → app/Customize/Controller/
```

If no: skip — set `CODEBASE_CONTEXT = "Not available — use placeholder paths"`.

---

## Step 3A: Single-Pass Generation (≤ 10 estimated stories)

Use one sub-agent call with the compressed SRS.

```
Agent(
  description: "Generate WBS from SRS",
  prompt: <SINGLE_PASS_PROMPT with SRS_COMPRESSED>
)
```

→ SINGLE_PASS_PROMPT: read `references/subagent-prompts.md` when dispatching this sub-agent (do not load earlier).
→ Output format: read `../examples/wbs-output-format.md` when assembling the prompt's OUTPUT FORMAT section (do not load earlier).
Delta vs canonical template: ignore its "WBS-Import additions" section (no Assignee/Status lines, no Import Metadata).

Store result as `WBS_OUTPUT` → go to **Step 4**.

---

## Step 3B: Two-Phase Adaptive Generation (11-50 stories)

### Phase 1: Story Planning

**Decide inline vs sub-agent based on SRS size:**

| SRS_COMPRESSED size | Phase 1 method |
|---------------------|----------------|
| ≤ 800 lines | **Inline** — orchestrator does it directly (saves a round-trip) |
| > 800 lines | **Sub-agent** — dispatch to avoid orchestrator context pressure |

#### Phase 1 Goal
Produce a `STORY_PLAN` with sub-task counts per story. This is critical for adaptive batching.

**If inline:** Read SRS_COMPRESSED and produce the plan directly.
**If sub-agent:**
```
Agent(
  description: "Plan WBS stories from SRS",
  prompt: <PHASE1_PROMPT with SRS_COMPRESSED>
)
```

→ PHASE1_PROMPT (only used when sub-agent is needed): read `references/subagent-prompts.md` when dispatching (do not load earlier).

Store result as `STORY_PLAN`.

---

### Phase 2: Adaptive Batch Expansion

**Key principle:** Batch by estimated sub-task count, NOT by fixed story count. **Target: ≤ 30 sub-tasks per batch** (~800 output lines) to avoid sub-agent truncation; a story with >30 sub-tasks gets its own solo batch.

→ Batch-sizing algorithm (pseudocode) + batch-size reference table: read `references/subagent-prompts.md` § "Phase 2 Batch Sizing" when planning batches (do not load earlier).

#### Dispatch Each Batch

For each batch:

```
Agent(
  description: "Expand WBS batch {B}: stories {start}-{end} ({subtask_count} sub-tasks)",
  prompt: <PHASE2_PROMPT>
)
```

→ PHASE2_PROMPT: read `references/subagent-prompts.md` when dispatching (do not load earlier); its output section uses only the per-story portion of `../examples/wbs-output-format.md`.

Store each batch result as `WBS_BATCH_N`.

---

### Phase 2 Final: Assemble

Concatenate all batches into a single WBS document and append the summary sections:

→ Document header, epic block, and AFTER-ALL-STORIES summary skeleton: read `../examples/wbs-output-format.md` when assembling the final document (do not load earlier; ignore its "WBS-Import additions" section).
Assembly order: header → epic → {WBS_BATCH_1 … WBS_BATCH_N} → summary sections.
Fill from: Epic Description ← STORY_PLAN; Cross-Story Dependencies ← STORY_PLAN dependency data; Suggested Sprint Allocation ← STORY_PLAN sprint assignments; Risk Summary ← aggregate from all batches; Assumptions ← SRS + WBS-specific; Traceability Matrix ← STORY_PLAN traceability section.

Store as `WBS_OUTPUT` → go to **Step 4**.

---

## Step 4: Validate WBS Completeness

Quick validation (do NOT re-invoke sub-agent unless critical):

1. **Requirement Coverage** — Scan Traceability Matrix for "⚠️ UNCOVERED". If found, add missing stories inline.
2. **Format Compliance** — All sections present? Patch minor gaps inline.

Only re-invoke sub-agent if >20% of requirements are uncovered.

---

## Step 5: Determine Output Path and Save

### Extract feature name
Derive from the SRS filename:
- `docs/srs-ac-installation.md` → `ac-installation`
- `docs/srs-loyalty-points.md` → `loyalty-points`

### Save WBS
Create file: `docs/wbs/wbs-{feature-name}.md`

If a WBS file already exists at that path, ask the user before overwriting.

---

## Step 6: Output Summary

```
✅ WBS Generation Complete

📄 Source SRS: {path/to/srs}
📋 WBS Document: docs/wbs/wbs-{feature-name}.md

📊 WBS Stats:
- Epic: {Feature Name}
- Total Stories: {count}
- Total Sub-tasks: {count}
- Total Story Points: {sum}
- Suggested Sprints: {count}
- Requirement Coverage: {covered}/{total} FR/US IDs
- Processing: {Single-pass / Two-phase (N batches, adaptive)}
- Batch Strategy: {≤30 sub-tasks per batch, density-based}

💡 Next Steps:
- Review the WBS and adjust estimates as needed
- Import stories into JIRA
- Use [CR][{Project-Tag}] ... to start implementation
```

---

## Error Handling

| Error | Action |
|-------|--------|
| SRS file not found | Inform user, ask for correct path |
| SRS is not in standard format | Adapt — extract equivalent sections, log warnings for missing data |
| SRS has no functional requirements | Abort — cannot generate meaningful WBS without requirements |
| Sub-agent returns incomplete WBS | Re-invoke with specific feedback on missing sections |
| Sub-agent hits context limit | Reduce batch size: halve the sub-task target (≤15 per batch) and retry |
| Sub-agent output truncated | Re-invoke the batch with fewer stories (split the batch in half) |
| Phase 1 inline fails (SRS too large) | Fall back to sub-agent for Phase 1 |
| WBS file already exists | Ask user before overwriting |
| SRS references unknown components | Generate WBS with placeholder file paths, note in Assumptions |
| 50+ stories detected | Warn user about generation time, proceed with adaptive batching |
