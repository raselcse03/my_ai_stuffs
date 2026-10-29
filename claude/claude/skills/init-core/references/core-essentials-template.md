# File 1 Generation Template: `core-essentials.md`

Full generation template for File 1 — loaded by `init-core` SKILL.md Generation Phase when generating `core-essentials.md`.

**Required sections (in order):**

```markdown
---
name: "Core Essentials"
role: "Critical rules and key directories — auto-loaded every task"
scope: "{primary_source_directory}/"
---

# {Project/Framework Name} Core Essentials

## Critical Rules (NEVER VIOLATE)

{5-9 rules using ❌ for prohibitions and ✅ for mandates}
{Rules MUST be specific to the project's framework and conventions}
{Examples:}
{  ❌ NEVER modify core framework files → Use the extension/customization layer}
{  ❌ NEVER commit secrets or credentials → Use environment variables}
{  ✅ ALWAYS use dependency injection → No manual instantiation of services}
{  ✅ ALWAYS use parameterized queries → No SQL string concatenation}
{  ✅ ALWAYS validate user input at system boundaries}

## Key Directories

{ASCII tree of 5-8 most important directories}
{Use ✅ for directories to work in, ❌ for directories to never modify}

## Request Flow

{Simple ASCII diagram showing the request lifecycle}
{Framework-specific: e.g., Route → Middleware → Controller → Service → DB}

## Naming Conventions

{4-6 naming patterns using the format:}
{  **Type:** `{Pattern}` → `{Example}`}

## Validation Commands

{3-5 essential CLI commands for cache clearing, testing, linting}

## When You Need More

For full architecture, edge cases, business patterns, and deployment details → read `core-full.md`.
```
