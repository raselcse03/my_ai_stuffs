# MrMax (EC-Cube) — Agent Instructions

This project uses a multi-skill orchestration system (migrated from a Copilot-based setup — see `.github/copilot-instructions.md` for the legacy version, kept for reference and untouched).

## How the skill system works

- **Skills** live at `.claude/skills/{name}/SKILL.md`. Claude auto-invokes the relevant one based on its `description` frontmatter, or you can point to it explicitly (e.g. "use the bug-fixing skill").
- **Slash commands** live at `.claude/commands/{slug}.md` (e.g. `/bug`, `/cr`, `/review`) — each just points at the matching skill and forwards your request as `$ARGUMENTS`.
- Skills still document themselves with an optional `[Tag]` convention (e.g. `[Bug]`, `[CR]`) inherited from the old system — typing a tag is not required, it's just a habit some skill files still reference in examples.
- For any task that reads more than ~3 files and produces more than 2 output files, prefer the `Agent` tool (subagent) to split discovery from implementation — skill files refer to this as `Agent(...)`.
- **Search before read:** use `Grep`/`Glob` to confirm relevance before `Read`-ing whole files. Avoid reading >150 lines in one call unless necessary.
- After finishing a sub-task delegated to a skill, summarize in ≤3 bullets rather than dumping full file contents back into context.

If no skill obviously matches, read `.claude/skills/routing.md` for the quick tag→skill lookup table, or `.claude/skills/SKILL.md` for the full index.

**Skill authoring standard** (enforced by `register-skill`, full spec in `.claude/skills/SKILL.md`): frontmatter = `name` (kebab-case, matches directory) + double-quoted `description` with "Use when …" triggers; SKILL.md ≤ 250 lines holding only the workflow; large templates/prompts go in the skill's `references/` directory behind one-line "read when you reach this step" pointers; project skills in `requirements/` ≤ 400 lines with overflow in a `-deep.md` companion.

## Critical Rules (NEVER VIOLATE)

1. ❌ **NEVER modify `src/Eccube/`** → use `app/Customize/` or a Plugin
2. ❌ **NEVER generate or run Doctrine migrations** → use manual SQL scripts
3. ✅ **ALWAYS use dependency injection** → no `new` keyword for services
4. ✅ **ALWAYS clear cache after config changes** → `bin/console cache:clear`
5. ✅ **ALWAYS use parameterized queries** → no SQL concatenation
6. ✅ **ALWAYS validate user input** → Symfony Form validation
7. ✅ **ALWAYS use transactions** → multi-step DB operations

## Key Directories

```
✅ app/Customize/       → Custom business logic
✅ app/Plugin/          → Plugin system
✅ app/config/          → Configuration
✅ app/template/        → Frontend templates (Twig)
❌ src/Eccube/          → Core (NEVER modify)
❌ app/DoctrineMigrations/ → Migrations (NEVER generate)
```

## Naming Conventions

- **Services:** `{Entity}Service` → `OrderService`
- **Repositories:** `{Entity}Repository` → `OrderRepository`
- **Controllers:** `{Feature}Controller` → `CheckoutController`
- **Forms:** `{Entity}Type` → `ProductType`
- **Namespacing:** `Customize\{Layer}\{Feature}`

## Agent Routing Table

Maintained by the `register-skill` skill — keep in alphabetical order by tag.

| Tag | Skill File | Agent Name |
|-----|-----------|------------|
| `[BAT]` | `.claude/skills/bat-generation/SKILL.md` | BAT Generator |
| `[Bug]` | `.claude/skills/bug-fixing/SKILL.md` | Bug Fixer |
| `[Clean]` | `.claude/skills/clean/SKILL.md` | Project Cleaner |
| `[CR]` | `.claude/skills/change-request/SKILL.md` | Change Request Engineer |
| `[Disclose]` | `.claude/skills/ai-disclosure/SKILL.md` | Disclosure Analyst |
| `[Excel-WBS]` | `.claude/skills/excel-wbs-generation/SKILL.md` | Excel WBS Generator |
| `[Feature]` | `.claude/skills/feature-development/SKILL.md` | Feature Builder |
| `[Init-Core]` | `.claude/skills/init-core/SKILL.md` | Core Skill Generator |
| `[Investigation]` | `.claude/skills/investigation/SKILL.md` | Impact Analyst |
| `[PR-Note]` | `.claude/skills/pr-note/SKILL.md` | PR Note Generator |
| `[PR-Review]` | `.claude/skills/pr-review/SKILL.md` | PR Link Reviewer |
| `[Quick PR-Review]` | `.claude/skills/quick-pr-review/SKILL.md` | Quick PR Link Reviewer |
| `[Quick Review]` | `.claude/skills/code-review/SKILL.md` | Quick Reviewer |
| `[Refactor]` | `.claude/skills/refactoring/SKILL.md` | Refactoring Specialist |
| `[Register-Skill]` | `.claude/skills/register-skill/SKILL.md` | Skill Registrar |
| `[Req-Analysis]` | `.claude/skills/requirement-analysis/SKILL.md` | Requirement Analyst |
| `[Req-Convert]` | `.claude/skills/requirement-conversion/SKILL.md` | Requirement Converter |
| `[Review]` | `.claude/skills/review-command/SKILL.md` | Review Commander |
| `[Unit Test]` | `.claude/skills/testing/SKILL.md` | Test Engineer |
| `[WBS-Import]` | `.claude/skills/wbs-import/SKILL.md` | WBS Importer |
| `[WBS-to-JIRA]` | `.claude/skills/wbs-to-jira/SKILL.md` | JIRA WBS Creator |
| `[WBS]` | `.claude/skills/wbs-generation/SKILL.md` | WBS Generator |
| `[Worklog]` | `.claude/skills/daily-worklog/SKILL.md` | Worklog Logger |

## Project Tag Routing

Project-specific requirement context, loaded when a `[Project-Tag]` is relevant to the task.

| Project Tag | Skill File |
|-------------|------------|
| `[CR2-Phase2]` | `.claude/skills/requirements/cr2-phase2-ac-installation.md` |
| `[CR4-Phase2]` | `.claude/skills/requirements/cr4-phase2-store-pickup-inventory.md` |
| `[CR5]` | `.claude/skills/requirements/cr5-vpoint-card-linkage.md` |
| `[CR4-Phase3]` | `.claude/skills/requirements/cr4-phase3-store-pickup-preorder.md` |

# Response Style

- Just implement what's asked. Don't explain your reasoning, don't narrate
  what you're about to do, and don't describe the code line-by-line.
- No preambles like "I'll now..." or "Let me...". Go straight to the work.
- Skip restating my request back to me before starting.
- While working, do NOT describe what the code is doing or why. No
  step-by-step commentary between edits.
- After finishing, output ONLY a short final summary in this format:

  **Summary:** one line describing what was implemented.

  **Changes:**
  - `path/to/file.ext` (lines 12-45) — what changed
  - `path/to/other.ext` (lines 3-8, 60-72) — what changed

- Keep the summary to 3-5 bullet points max. File path + line numbers +
  a few words per change. Nothing more.
- Only give detailed information (how it works, why decisions were made,
  walkthroughs of the code) when I explicitly ask with words like
  "explain", "describe", "why", or "details".
