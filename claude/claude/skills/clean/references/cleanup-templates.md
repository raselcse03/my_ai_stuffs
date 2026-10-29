# Cleanup Replacement Templates

Verbatim replacement and before/after blocks for the Project Cleaner skill — loaded on demand by Steps 3d, 4, and 5 of `.claude/skills/clean/SKILL.md`.

---

## Step 3d: Reset Templates for Individual Skill Files

### testing/SKILL.md

1. **Frontmatter `scope`** → `"{test_dir}/"` (placeholder)
2. **H1 title** → `# Testing Skill`
3. **File classification table** (the `| File Location | Test Type | Base Class |` table under "Classify changed files") → replace with:

```markdown
| File Location | Test Type | Base Class |
|---------------|-----------|------------|
| *(Run `[Init-Core]` to populate with project-specific paths and base classes)* | — | — |
```

4. **Test type detail sections** — replace `EccubeTestCase` references with `{ProjectBaseTestCase}` placeholder
5. **Run commands** in Step 5 — replace `docker exec mrmax_dev-ec-cube-1 php bin/phpunit ...` and `docker exec mrmax_dev-ec-cube-1 bin/phpunit ...` with:

```bash
# Run command will be project-specific — see core-essentials.md after [Init-Core]
# {test_runner} {test_file}
```

6. **Reference: Test Infrastructure table** (Existing Base Test Classes) → replace with:

```markdown
| Base Class | Location | For |
|------------|----------|-----|
| *(Run `[Init-Core]` to populate with project-specific base test classes)* | — | — |
```

7. **Test Database Setup** paragraph → replace with:
```
*(Test database setup is project-specific — see project documentation after [Init-Core].)*
```

### feature-development/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **H1 title** → `# Feature Development Skill`
3. **Standard Feature Structure** code block (the ASCII tree under `## Standard Feature Structure`) → replace with:

```
{source_dir}/
├── {model_layer}/        # Data model (run [Init-Core] to populate)
├── {repository_layer}/   # Data access
├── {service_layer}/      # Business logic
├── {controller_layer}/   # Request handling
└── {form_layer}/         # Input validation

{template_dir}/
└── {feature}/            # View templates
```

### change-request/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **H1 title** → `# Change Request Implementation Skill`
3. **Migration/schema note** (the `> ⚠️ This project does NOT use Doctrine migrations.` line in Phase 3) → replace with:

```markdown
> ⚠️ Follow the project's schema change approach defined in `core-essentials.md`. Run `[Init-Core]` if not yet generated.
```

### bug-fixing/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **Frontmatter `role`** → `"Diagnose and fix bugs using the project's extension and override patterns"`
3. **H1 title** → `# Bug Fixing Skill`

### refactoring/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **Frontmatter `role`** → `"Modernize legacy code — extract services, reduce cyclomatic complexity, enforce patterns"`
3. **H1 title** → `# Code Refactoring Skill`

### investigation/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **Frontmatter `role`** → `"Read-only specialist for tracing code paths, mapping dependencies, and assessing blast radius"`
3. **H1 title** → `# Investigation & Impact Analysis Skill`

---

## Step 4: Clean CLAUDE.md

### 4a. Clean Project Tag Routing Table

Remove all data rows from the Project Tag Routing table, keeping the table header:

**Before:**
```markdown
## Project Tag Routing

| Project Tag | Skill File |
|-------------|-----------|
| `[CR2-Phase2]` | `.claude/skills/requirements/cr2-phase2-ac-installation.md` |
| `[CR4-Phase2]` | `.claude/skills/requirements/cr4-phase2-store-pickup-inventory.md` |
| ... |
```

**After:**
```markdown
## Project Tag Routing

| Project Tag | Skill File |
|-------------|-----------|

*(No project tags registered. Use `[Register-Skill]` to add project-specific requirement skills.)*
```

### 4b. Reset Critical Rules to Generic

Replace project-specific critical rules with framework-generic rules:

**Before:**
```markdown
## Critical Rules

1. ❌ NEVER modify `src/Eccube/` — use `app/Customize/`
2. ❌ NEVER generate or run database migrations
3. ✅ ALWAYS search before reading files
4. ✅ ALWAYS summarize sub-task findings in ≤3 bullets
5. ✅ ALWAYS use dependency injection and parameterized queries
```

**After:**
```markdown
## Critical Rules

1. ✅ ALWAYS search before reading files
2. ✅ ALWAYS summarize sub-task findings in ≤3 bullets
3. ✅ ALWAYS use dependency injection and parameterized queries

*(Project-specific rules will be added when `[Init-Core]` generates core files.)*
```

---

## Step 5: Clean SKILL.md

### 5a. Reset Header Description

Replace project-specific header with generic:

**Before:**
```markdown
# EC-Cube Agent Skills - Quick Reference

**Agent Role:** Principal Software Engineer and PR Reviewer specializing in EC-Cube 4.x
```

**After:**
```markdown
# Agent Skills - Quick Reference

**Agent Role:** Principal Software Engineer and PR Reviewer
```

### 5b. Remove Requirement-Specific Skills Section

Delete the entire `## 🏗️ Requirement-Specific Skills (requirements/)` section including all CR entries (CR2-Phase2, CR4-Phase2, CR5, CR4-Phase3, etc.) up to the next `## ✅` section.

Replace with a placeholder:

```markdown
## 🏗️ Requirement-Specific Skills (requirements/)

Stored in `requirements/` subdirectory. Use `[Project-Tag]` in prompts to auto-load.

*(No project-specific requirement skills registered. Use `[Register-Skill]` to add them.)*

---
```

### 5e. Clean Requirements File Listing

Replace the `### Requirements (requirements/)` section under the file listing:

**After:**
```markdown
### Requirements (requirements/)
*(No project-specific requirement files. Add via `[Register-Skill]`.)*
```

### 5f. Reset Core Principles Section

Update the Core Principles section to be generic (remove EC-Cube references):

**Before:**
```markdown
### **Core Principles** - Start Here First
**Skill:** `core`  
**Use when:** Need architecture overview, core rules, AWS setup, or validation commands

📋 **Contains:**
- EC-Cube 4.x architecture and directory structure
- AWS production environment setup
- Critical rules (NEVER violate)
...
```

**After:**
```markdown
### **Core Principles** - Start Here First
**Skill:** `core`  
**Use when:** Need architecture overview, core rules, infrastructure setup, or validation commands

📋 **Contains:**
- Project architecture and directory structure
- Production environment setup
- Critical rules (NEVER violate)
- Pre-implementation checklist
- Business logic patterns
- Naming conventions

*(Run `[Init-Core]` to generate project-specific core files.)*
```
