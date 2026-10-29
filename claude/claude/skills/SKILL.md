---
name: master-skill-index
description: "Master index of all agent skills. Read only when routing.md leaves the task type ambiguous, or when registering a new skill."
---

# Agent Skills — Master Index

Routing for tagged prompts lives in `routing.md` (read that first — it is smaller).
This index adds one-line purposes, output locations, and the authoring standard.

## Action Skills

| Tag | Skill | Purpose | Output |
|-----|-------|---------|--------|
| `[Bug]` | `bug-fixing/SKILL.md` | Diagnose and fix defects without touching core | code changes |
| `[CR]` | `change-request/SKILL.md` | Implement client change requests, backward compatible | code changes |
| `[Feature]` | `feature-development/SKILL.md` | New features via Entity → Service → Controller → Template | code changes |
| `[Refactor]` | `refactoring/SKILL.md` | Extract services, replace raw SQL, reduce complexity | code changes |
| `[Review]` | `review-command/SKILL.md` | 7-agent review of this repo (PR #, branch, staged, diff) | `CODE-REVIEW-*.md` |
| `[Quick Review]` | `code-review/SKILL.md` | Single-agent 6-dimension review of this repo | `QUICK-REVIEW-*.md` |
| `[PR-Review]` | `pr-review/SKILL.md` | 7-agent review of any GitHub PR by URL (gh CLI) | `docs/review/CODE-REVIEW-PR-*.md` |
| `[Quick PR-Review]` | `quick-pr-review/SKILL.md` | Single-agent review of any GitHub PR by URL | `docs/review/QUICK-REVIEW-PR-*.md` |
| `[Unit Test]` | `testing/SKILL.md` | Generate + run tests from branch diff (Docker PHPUnit) | `tests/Customize/` |
| `[Investigation]` | `investigation/SKILL.md` | Read-only blast-radius / dependency trace | Impact Report |
| `[Disclose]` | `ai-disclosure/SKILL.md` | Detect AI-generated code in a diff, produce disclosure | `AI_GENERATED_CODE_DISCLOSURE_*.md` |
| `[BAT]` | `bat-generation/SKILL.md` | Developer BAT Excel reports from diff + auto-test | `docs/BAT/` |
| `[PR-Note]` | `pr-note/SKILL.md` | GitHub PR description from branch diff | `PR-Note-*.md` |
| `[Req-Analysis]` | `requirement-analysis/SKILL.md` | Client docs → SRS + project skill + WBS (3-agent pipeline) | `docs/srs-*.md`, `docs/wbs/` |
| `[WBS]` | `wbs-generation/SKILL.md` | SRS → JIRA-ready Work Breakdown Structure | `docs/wbs/wbs-*.md` |
| `[Excel-WBS]` | `excel-wbs-generation/SKILL.md` | WBS markdown → formatted .xlsx workbook | `docs/wbs/excel/` |
| `[WBS-Import]` | `wbs-import/SKILL.md` | Excel/CSV WBS → enriched WBS markdown | `docs/wbs/wbs-*.md` |
| `[WBS-to-JIRA]` | `wbs-to-jira/SKILL.md` | WBS markdown → JIRA Stories + Sub-tasks (REST API) | JIRA tickets |
| `[Req-Convert]` | `requirement-conversion/SKILL.md` | Excel/Word requirements → PDF + PNG per sheet | `docs/requirement-conversion/` |
| `[Worklog]` | `daily-worklog/SKILL.md` | Interactive JIRA worklog entry, ticket by ticket | JIRA worklogs |
| `[Init-Core]` | `init-core/SKILL.md` | Generate core-essentials.md + core-full.md for a project | `.claude/skills/core-*.md` |
| `[Register-Skill]` | `register-skill/SKILL.md` | Register a new skill, tag, and slash command | skill + routing entries |
| `[Clean]` | `clean/SKILL.md` | Reset framework for a new codebase | deletions |

## Project Skills (loaded by project tag)

| Tag | Skill | Covers |
|-----|-------|--------|
| `[CR2-Phase2]` | `requirements/cr2-phase2-ac-installation.md` | AC installation checkout, P1–P6 patterns, drilling validation |
| `[CR4-Phase2]` | `requirements/cr4-phase2-store-pickup-inventory.md` | Store pickup stock deduction, shipping status, admin UI |
| `[CR4-Phase3]` | `requirements/cr4-phase3-store-pickup-preorder.md` | Pre-order pickup (order_type=31), EC request export, authority_id=6 |
| `[CR5]` | `requirements/cr5-vpoint-card-linkage.md` | V-Point / credit card linkage, CCCMK API, BAT1–BAT5 batches |

Project skills with a `-deep.md` companion hold rarely-needed detail there — load the deep file only when the task touches those areas.

## Shared Files (not skills)

| File | Purpose | When to read |
|------|---------|--------------|
| `routing.md` | Tag → skill lookup | First stop for any tagged prompt |
| `core-essentials.md` | Critical rules, directories, naming | Every EC-Cube code task |
| `core-full.md` | AWS architecture, edge cases, full standards | Only when essentials is not enough |
| `examples/*.md` | Shared templates (review prompts, WBS format, CR/feature code) | When the owning skill points to them |
| `agents/*.md` | Sub-agent prompts for requirement-analysis | Dispatched by that skill |
| `support/*.py` | Python helpers (Excel, JIRA, PDF) | Invoked by skills via Bash |

## Skill-Authoring Standard

All new skills (see `register-skill/SKILL.md`) must follow:

1. **Frontmatter** — exactly two keys:
   - `name:` kebab-case slug matching the directory name.
   - `description:` double-quoted, third person: what it does + "Use when …" triggers + "Triggered by the [Tag] tag or /slash."
2. **Size** — SKILL.md ≤ 250 lines. It holds the operational workflow only: usage, steps, decision logic, commands, error handling, return contract.
3. **Progressive disclosure** — large verbatim templates, report formats, and sub-agent prompts live in `references/<topic>.md` inside the skill directory, pulled in via one-line pointers: "→ Read `references/x.md` when you reach this step (do not load earlier)."
4. **Project skills** — `requirements/*.md` ≤ 400 lines; overflow goes to a `<name>-deep.md` companion with pointer lines at the extraction points.
5. **Return contract** — every skill ends by defining what it reports back (≤3 bullets + file paths, never raw file dumps).
6. **Registration** — one row in `routing.md`, one row in the tables above, one row in CLAUDE.md's routing table, one command file in `.claude/commands/`.
