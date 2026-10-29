---
name: "WBS Generator"
role: "Generate a JIRA-ready Work Breakdown Structure from an existing SRS document"
primary_tools: [read_file, runSubagent, create_file]
scope: "docs/"
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
read_file → {path from user prompt}
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
list_dir → app/Customize/Entity/
list_dir → app/Customize/Service/
list_dir → app/Customize/Controller/
```

If no: skip — set `CODEBASE_CONTEXT = "Not available — use placeholder paths"`.

---

## Step 3A: Single-Pass Generation (≤ 10 estimated stories)

Use one sub-agent call with the compressed SRS.

```
runSubagent(
  description: "Generate WBS from SRS",
  prompt: <SINGLE_PASS_PROMPT with SRS_COMPRESSED>
)
```

### SINGLE_PASS_PROMPT

```
You are a senior Agile PM and Tech Lead for EC-Cube 4.x.

TASK: Convert this SRS into a JIRA-ready WBS.

## SRS CONTENT
{SRS_COMPRESSED}

## CODEBASE CONTEXT
{CODEBASE_CONTEXT}

## RULES
- Group related FR-*/US-* into Stories
- Order Stories by dependency
- Sub-tasks split by layer (Entity/Repository/Service/Controller/Form/Template/Test), ≤8h each
- Use Gherkin for acceptance criteria
- Map EVERY FR-* and US-* (no gaps)
- Points: 1=trivial, 2=simple, 3=small, 5=medium, 8=large, 13=x-large
- Hours: 1h, 2h, 4h, 8h per sub-task
- SKIP empty sections — if a sub-task has no corner cases, omit that section entirely (do NOT output empty tables)
- Be concise in Notes — only include if there is genuinely useful information

## OUTPUT FORMAT

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
runSubagent(
  description: "Plan WBS stories from SRS",
  prompt: <PHASE1_PROMPT with SRS_COMPRESSED>
)
```

#### PHASE1_PROMPT (only used when sub-agent is needed)

```
You are a senior Agile PM for EC-Cube 4.x.

TASK: Analyze this SRS and produce a STORY PLAN with sub-task counts.

## SRS CONTENT
{SRS_COMPRESSED}

## RULES
- Group FR-*/US-* into Stories
- Order by dependency
- Points: 1=trivial, 2=simple, 3=small, 5=medium, 8=large, 13=x-large
- For each story, list planned sub-tasks with layer and hours
- Count sub-tasks per story (needed for batch sizing)

## OUTPUT FORMAT (compact — keep under 200 lines)

EPIC: {Feature Name}
EPIC_DESC: {1 sentence}
SOURCE: {filename}
TOTAL_STORIES: {N}
TOTAL_POINTS: {sum}

STORY 1: {Title}
PRIORITY: {H/M/L} | POINTS: {N} | SPRINT: {N} | SCOPE: {scope}
LINKED_REQS: FR-001, FR-002, US-001
SUMMARY: {1 sentence}
SUBTASKS({count}): {layer}:{1-line}({hours}) | {layer}:{1-line}({hours}) | ...
DEPENDS_ON: {Story N or "none"}

{repeat for all stories}

TRACEABILITY: FR-001→S1, FR-002→S2, US-001→S1, ...
UNCOVERED: {list or "none"}
```

Store result as `STORY_PLAN`.

---

### Phase 2: Adaptive Batch Expansion

**Key principle:** Batch by estimated sub-task count, NOT by fixed story count. Each batch must produce ≤ ~800 output lines to avoid sub-agent truncation.

#### Batch Sizing Algorithm

Each sub-task produces ~25 lines of formatted output. Each story overhead is ~15 lines.
**Target: ≤ 30 sub-tasks per batch** (~800 lines output).

```
For each story in STORY_PLAN:
  Read SUBTASKS({count}) value
  
current_batch = []
current_subtask_count = 0

For each story:
  story_subtasks = story's subtask count from STORY_PLAN
  
  If current_subtask_count + story_subtasks > 30 AND current_batch is not empty:
    → Finalize current_batch, start new batch
  
  Add story to current_batch
  current_subtask_count += story_subtasks
  
  If story_subtasks > 30:
    → This story gets its OWN batch (solo expansion)
```

#### Batch Size Reference

| Stories' avg sub-tasks | Stories per batch | Example |
|------------------------|-------------------|---------|
| 1-3 sub-tasks each | 8-10 stories | Simple config/setup stories |
| 4-6 sub-tasks each | 5-6 stories | Medium feature stories |
| 7-10 sub-tasks each | 3-4 stories | Complex stories |
| 11-15 sub-tasks each | 2 stories | Very dense stories |
| 15+ sub-tasks | 1 story (solo batch) | Mega stories |

#### Dispatch Each Batch

For each batch:

```
runSubagent(
  description: "Expand WBS batch {B}: stories {start}-{end} ({subtask_count} sub-tasks)",
  prompt: <PHASE2_PROMPT>
)
```

#### PHASE2_PROMPT

```
You are a senior Agile PM and Tech Lead for EC-Cube 4.x.

TASK: Expand these stories into full WBS detail.

## STORY PLAN (dependencies context — DO NOT expand all, only the listed ones)
{STORY_PLAN — trimmed to: target stories + their direct dependencies only}

## EXPAND ONLY THESE STORIES: {list of story numbers}

## SRS SECTIONS NEEDED
{Only the FR-*/US-*/corner cases/risks relevant to these stories, extracted from SRS_COMPRESSED}

## CODEBASE CONTEXT
{CODEBASE_CONTEXT}

## RULES
- SKIP empty sections — if no corner cases, omit Corner Cases section entirely
- Be concise in Notes — only include if genuinely useful
- Use Gherkin for acceptance criteria

## OUTPUT — for each story, output:

### Story {N}: {Title}

**Type:** Story | **Priority:** {H/M/L} | **Points:** {N} | **Sprint:** {N}

#### Story Overview
{5-20 sentences providing a comprehensive description of this story. Cover: what functionality is being built, the business problem it solves, who the end users are, how it fits into the broader feature/epic, key technical approach, which layers are involved (frontend/backend/database), major workflows or user interactions, integration points with other stories or systems, and any important constraints or considerations.}

- **Linked Requirements:** {FR-001, FR-002, US-001, ...}
- **Affected Components:** {files if known}
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
{One concise paragraph describing what this sub-task delivers and why it matters.}

###### Requirement Details
{Detailed description of the functional requirement this sub-task fulfills. Reference SRS requirement IDs. Include specific business logic, calculations, UI behavior, or API contracts.}

- **Linked Requirements:** {FR-001, FR-002, ...}
- **Affected Files:** {list specific files to create or modify}
- **Scope:** {Frontend / Backend / Full-stack}

###### Associated Story
- **Parent Story:** Story {N} — {Story Title}
- **Epic:** {Feature Name}

###### Acceptance Criteria
- [ ] **Given** {precondition}, **When** {action}, **Then** {expected result}
- [ ] **Given** {precondition}, **When** {action}, **Then** {expected result}
- [ ] {Additional criterion if Gherkin is not applicable}

###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| {Story N / Sub-task / External system / API} | {Blocks / Blocked-by / Related-to} | {Brief explanation} |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | {edge case description} | {how the system should handle it} |

###### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| {risk description} | {Low/Medium/High} | {Low/Medium/High} | {mitigation strategy} |

###### Notes / Additional Information
- {Implementation hints, design considerations, or technical notes}
- {References to external documentation, Figma designs, or API specs}

###### Definition of Done
- [ ] {specific completion criterion}
- [ ] {specific completion criterion}
```

Store each batch result as `WBS_BATCH_N`.

---

### Phase 2 Final: Assemble

Concatenate all batches into a single WBS document and append the summary sections:

```markdown
# Work Breakdown Structure — JIRA Import Ready
## {Feature Name}

**Generated:** {YYYY-MM-DD}
**Source:** {SRS filename}
**Total Stories:** {count}
**Total Story Points:** {sum}

---

## Epic: {Feature Name}

**Epic Description:**
> {from STORY_PLAN}

---

{WBS_BATCH_1}

{WBS_BATCH_2}

{WBS_BATCH_N...}

---

## Cross-Story Dependencies
{Generate from STORY_PLAN dependency data}

## Suggested Sprint Allocation
{Generate from STORY_PLAN sprint assignments}

## Risk Summary (Across All Stories)
{Aggregate from all batches}

## Assumptions
{From SRS + WBS-specific}

## Traceability Matrix
{From STORY_PLAN traceability section}
```

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
- Use @workspace [CR][{Project-Tag}] ... to start implementation
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
