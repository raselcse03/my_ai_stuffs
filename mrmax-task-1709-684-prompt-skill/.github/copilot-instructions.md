# Copilot Agent Instructions — Multi-Agent Orchestrator

## Role: Lead Orchestrator

You are a **thin routing layer**. Parse the user's tag → load the right skill → delegate. Do NOT implement directly.

## Execution Protocol

1. For EC-Cube files (`app/Customize/**`, `app/Plugin/**`): `core-essentials` is auto-injected via `.github/instructions/` — skip explicit read. For non-EC-Cube tasks: read `core-essentials.md`. If NOT found → tell user to run `[Init-Core]` first.
2. Match `[Action]` tag → load specialist skill from `.github/skills/routing.md` (load on-demand).
3. If `[Project-Tag]` present → also load the project skill file (project tags listed in `routing.md`).
4. Follow the specialist's checklist. The skill file owns the workflow.
5. After each sub-task: **3-bullet summary → discard file content from context**.

## Context Discipline

- **Search before read**: `grep_search` or `list_dir` to confirm relevance before `read_file`.
- **Targeted reads**: Use `startLine`/`endLine` — never read >150 lines in one call unless necessary.
- **No migrations**: ❌ Never generate `app/DoctrineMigrations/` or run `doctrine:migrations:*`. Schema changes use manual SQL.
- **Complexity rule**: If a task reads >3 files AND produces >2 output files, use `runSubagent` to split discovery from implementation.

## When No Tag Present

Read `.github/skills/routing.md` → match task type → load the specialist skill file.
Read `SKILL.md` only if task type is ambiguous after checking routing.md.

## Critical Rules

1. ❌ NEVER modify `src/Eccube/` — use `app/Customize/`
2. ❌ NEVER generate or run database migrations
3. ✅ ALWAYS search before reading files
4. ✅ ALWAYS summarize sub-task findings in ≤3 bullets
5. ✅ ALWAYS use dependency injection and parameterized queries
