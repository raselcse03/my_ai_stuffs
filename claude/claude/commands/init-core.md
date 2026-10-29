---
description: "🏗️ [Init-Core] — Generate core-essentials.md and core-full.md coding guideline skill files for any project"
---
# Initialize Core Skill Files

Use the `[Init-Core]` action tag. This command generates two foundational skill files (`core-essentials.md` and `core-full.md`) that define coding guidelines, architecture rules, and conventions for any project.

## What It Produces

| File | Purpose | Size |
|------|---------|------|
| `core-essentials.md` | Critical rules, key directories, naming conventions — auto-loaded every task (~50-60 lines) | Compact |
| `core-full.md` | Full architecture, tech stack, edge cases, business patterns, validation commands (~200-250 lines) | Detailed |
| `CLAUDE.md` | VS Code auto-loader for source files | Minimal |
| `testing/SKILL.md` (updated) | scope, file classification table, run commands updated for new project | — |
| `feature-development/SKILL.md` (updated) | scope, Standard Feature Structure updated for new project | — |
| `change-request/SKILL.md` (updated) | scope, migration/schema approach updated for new project | — |
| `bug-fixing/SKILL.md`, `refactoring/SKILL.md`, `investigation/SKILL.md` (updated) | scope, role, title updated for new project | — |

## Modes

| Mode | When | What happens |
|------|------|-------------|
| With existing guidelines | You already have a coding guideline doc | Attach/paste it → agent parses and generates both files |
| Manual tech input | No guidelines but you know your stack | Agent asks framework, language, DB, etc. → generates both files |
| SRS-based inference | Tech stack not decided yet | Agent reads your SRS docs → suggests stack → you confirm/modify → generates both files |

## Examples

```
[Init-Core] Here is our coding guideline document — generate core skill files from it.
```

```
[Init-Core] We use Next.js 14 with TypeScript, PostgreSQL, Prisma ORM, deployed on Vercel.
```

```
[Init-Core] We haven't decided the tech stack yet. Please analyze our SRS and suggest one.
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/init-core/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
