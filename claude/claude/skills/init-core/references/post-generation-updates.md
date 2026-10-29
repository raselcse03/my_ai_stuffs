# Post-Generation Step: Update Individual Skill Files

Per-file update instructions and success message template — loaded by `init-core` SKILL.md's "Post-Generation Step: Update Individual Skill Files" after core files are generated.

After updating SKILL.md, update each of the following skill files with project-specific data derived from the generated `core-essentials.md`. Use `Edit` for each targeted section.

### Data to derive from core-essentials.md before updating skill files

| Variable | Derived From |
|----------|-------------|
| `{framework_name}` | Technology stack (e.g., "Laravel", "Next.js", "Django") |
| `{source_dir}` | Primary source directory (e.g., `app`, `src`, `lib`) |
| `{test_dir}` | Test directory (e.g., `tests`, `__tests__`, `spec`) |
| `{test_runner_cmd}` | Test execution command from Validation Commands section |
| `{db_approach}` | Schema change strategy from Critical Rules (migrations / manual SQL / Prisma) |
| `{extension_points}` | Framework's override/extension mechanisms (e.g., Service Providers, Middleware) |
| `{base_test_class}` | Framework's base test class (e.g., `Illuminate\Foundation\Testing\TestCase`) |

### testing/SKILL.md

Update the following sections:

**1. Frontmatter `scope`:**
Replace `"{test_dir}/"` placeholder with the actual test directory (e.g., `"tests/"`).

**2. H1 title:**
Replace `# Testing Skill` with `# {Framework Name} Testing Skill`.

**3. File classification table** — replace the placeholder with the actual project structure:

| File Location | Test Type | Base Class |
|---------------|-----------|------------|
| `{source_dir}/{service_layer}/` | Unit test | `{base_test_class}` |
| `{source_dir}/{model_layer}/` | Unit test | `{base_test_class}` |
| `{source_dir}/{controller_layer}/` | Feature/integration test | `{base_test_class}` |
| `{source_dir}/{repository_layer}/` | Integration test | `{base_test_class}` |
| `{template_dir}/` | Skip — templates | — |

Generate rows based on the actual project directory structure.

**4. Test run commands** — replace the placeholders in Step 5 with the actual test runner command from `core-essentials.md` Validation Commands:

```bash
# Unit tests
{test_runner_cmd} {test_dir}/{path}/{TestFile}

# Integration tests (if applicable)
{test_runner_cmd} {test_dir}/{path}/{TestFile}
```

**5. Reference: Test Infrastructure table** — populate with actual base test classes discovered from the project or inferred from the framework.

**6. Test Database Setup** — replace placeholder with the project-specific setup note from `core-essentials.md`.

### feature-development/SKILL.md

**1. Frontmatter `scope`:** Replace `"{source_dir}/"` with actual source directory.

**2. H1 title:** Replace `# Feature Development Skill` with `# {Framework Name} Feature Development Skill`.

**3. Standard Feature Structure** — replace the placeholder block with the actual project-specific structure derived from the framework:

For example, for **Laravel**:
```
app/
├── Models/
├── Repositories/
├── Services/
├── Http/
│   ├── Controllers/
│   └── Requests/       # Form validation
└── Providers/

resources/views/{feature}/
├── index.blade.php
├── create.blade.php
└── edit.blade.php

database/migrations/
routes/web.php or routes/api.php
```

Generate the appropriate structure for the detected framework.

### change-request/SKILL.md

**1. Frontmatter `scope`:** Replace `"{source_dir}/"` with actual source directory.

**2. H1 title:** Replace `# Change Request Implementation Skill` with `# {Framework Name} Change Request Implementation Skill`.

**3. Migration/schema approach note** — replace the generic placeholder with the project's actual schema change strategy from `core-essentials.md` Critical Rules:

- **If using Doctrine (no migrations):** `> ⚠️ This project does NOT use Doctrine migrations. Schema changes are applied via manual SQL scripts.`
- **If using Prisma:** `> ⚠️ Schema changes require updating \`schema.prisma\` and running \`npx prisma migrate dev\`.`
- **If using Laravel Eloquent:** `> ⚠️ Schema changes require creating a new migration: \`php artisan make:migration\`.`
- **If using Django:** `> ⚠️ Schema changes require running \`python manage.py makemigrations && migrate\`.`
- **Generic:** `> ⚠️ Schema changes — follow the approach defined in \`core-essentials.md\` Critical Rules.`

### bug-fixing/SKILL.md

**1. Frontmatter `scope`:** Replace `"{source_dir}/"` with actual source directory.
**2. Frontmatter `role`:** Replace with `"Diagnose and fix {Framework} bugs using the project's override and extension patterns"`.
**3. H1 title:** Replace `# Bug Fixing Skill` with `# {Framework Name} Bug Fixing Skill`.

### refactoring/SKILL.md

**1. Frontmatter `scope`:** Replace `"{source_dir}/"` with actual source directory.
**2. Frontmatter `role`:** Replace with `"Modernize legacy {Framework} code — extract services, reduce cyclomatic complexity, enforce patterns"`.
**3. H1 title:** Replace `# Code Refactoring Skill` with `# {Framework Name} Code Refactoring Skill`.

### investigation/SKILL.md

**1. Frontmatter `scope`:** Replace `"{source_dir}/"` with the full scope pattern for the project (include all relevant directories, e.g., `"app/, config/, resources/"` for Laravel).
**2. Frontmatter `role`:** Replace with `"Read-only specialist for tracing code paths, mapping dependencies, and assessing blast radius in {Framework} environments"`.
**3. H1 title:** Replace `# Investigation & Impact Analysis Skill` with `# {Framework Name} Investigation & Impact Analysis Skill`.

---

### Success Message Template
```
✅ Generated 2 core skill files + updated CLAUDE.md + updated 6 individual skill files:

1. **core-essentials.md** (~{N} lines) — Auto-loaded rules, directories, conventions
2. **core-full.md** (~{N} lines) — Full architecture, edge cases, patterns

🔧 Updated individual skill files:
3. **testing/SKILL.md** — scope, title, file classification table, run commands
4. **feature-development/SKILL.md** — scope, title, Standard Feature Structure
5. **change-request/SKILL.md** — scope, title, migration approach
6. **bug-fixing/SKILL.md** — scope, role, title
7. **refactoring/SKILL.md** — scope, role, title
8. **investigation/SKILL.md** — scope, role, title

📁 Location: `.claude/skills/`
🔄 Updated: `CLAUDE.md` Critical Rules + Key Directories, `SKILL.md` header

Please review all files and adjust any rules or conventions to match your team's preferences.
```
