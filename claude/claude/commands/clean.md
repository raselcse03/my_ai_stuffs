---
description: "🧹 [Clean] — Clean project-specific data and prepare framework for a new codebase"
---
# Clean Project Data

Use the `[Clean]` action tag. This command removes all project-specific files, requirement specs, generated documents, and core configuration — preparing the AI-Skills framework for installation on a new codebase.

## What Gets Cleaned

| Category | Files |
|----------|-------|
| Core config | `core-essentials.md`, `core-full.md`, `CLAUDE.md` |
| Requirement specs | Everything in `.claude/skills/requirements/` |
| Generated docs | Everything in `docs/` |
| Routing config | Project Tag rows in `CLAUDE.md` |
| SKILL.md | Project-specific entries, header, requirement sections |
| Individual skill files | Project-specific `scope`, `role`, title, and framework sections in `testing`, `feature-development`, `change-request`, `bug-fixing`, `refactoring`, `investigation` |

## What Stays Untouched

All skill workflow logic, 19+ prompt files, example templates, support scripts, sample files, and agent definitions.

## After Cleanup

You'll be asked: **"Generate new core files for a new codebase?"**
- **Yes** → Delegates to `[Init-Core]` to generate core files for your new project
- **No** → Framework stays clean, ready for manual setup later

## Examples

```
[Clean]
```

```
[Clean] I want to install this on a new Laravel project
```

```
[Clean] Clean everything and generate core files for a React + Node.js project
```

## Skill Context

Read .claude/skills/core-essentials.md and .claude/skills/clean/SKILL.md — follow the skill workflow.

## Task

$ARGUMENTS
