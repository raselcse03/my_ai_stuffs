# WBS Generation — Sub-agent Prompt Scaffolds

Prompt scaffolds for wbs-generation, loaded when dispatching a sub-agent: SINGLE_PASS_PROMPT (Step 3A), PHASE1_PROMPT and PHASE2_PROMPT (Step 3B).

## SINGLE_PASS_PROMPT (Step 3A)

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

{→ Splice in the full canonical template from ../../examples/wbs-output-format.md — document header, epic block, per-story blocks, and all AFTER-ALL-STORIES summary sections. Ignore its "WBS-Import additions" section.}
```

## PHASE1_PROMPT (Step 3B Phase 1 — only used when sub-agent is needed)

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

## PHASE2_PROMPT (Step 3B Phase 2 — one per batch)

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

{→ Splice in ONLY the per-story portion of ../../examples/wbs-output-format.md — from "### Story {N}: {Title}" through "###### Definition of Done". Do NOT include the document header, epic block, or AFTER-ALL-STORIES summary sections — those are assembled in Phase 2 Final. Ignore the "WBS-Import additions" section.}
```

---

# Phase 2 Batch Sizing (loaded at Step 3B Phase 2 — Adaptive Batch Expansion)

Batch by estimated sub-task count, NOT by fixed story count. Each sub-task produces ~25 lines of output; each story overhead is ~15 lines. **Target: ≤ 30 sub-tasks per batch** (~800 lines output) to avoid sub-agent truncation.

## Batch Sizing Algorithm

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

## Batch Size Reference

| Stories' avg sub-tasks | Stories per batch | Example |
|------------------------|-------------------|---------|
| 1-3 sub-tasks each | 8-10 stories | Simple config/setup stories |
| 4-6 sub-tasks each | 5-6 stories | Medium feature stories |
| 7-10 sub-tasks each | 3-4 stories | Complex stories |
| 11-15 sub-tasks each | 2 stories | Very dense stories |
| 15+ sub-tasks | 1 story (solo batch) | Mega stories |
