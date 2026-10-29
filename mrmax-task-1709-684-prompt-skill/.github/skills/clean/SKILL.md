---
name: "Project Cleaner"
role: "Clean project-specific data and core files for fresh installation on a new codebase — triggered by [Clean] tag"
primary_tools: [vscode_askQuestions, run_in_terminal, read_file, replace_string_in_file, list_dir, grep_search]
scope: ".github/"
---

# Project Cleaner Skill

**Purpose:** Remove all project-specific data, requirement specs, generated outputs, and core configuration files — preparing the AI-Skills framework for installation on a new codebase. Optionally delegates to `[Init-Core]` to regenerate core files for the new project.

## Usage

```
@workspace [Clean]
@workspace [Clean] I want to install this on a new Laravel project
```

---

## Step 1: Discover Project-Specific Files

Scan the workspace to identify all files that need cleaning. Group into categories:

### 1a. Core Configuration Files (project-specific rules)

```
check_exists: .github/skills/core-essentials.md
check_exists: .github/skills/core-full.md
check_exists: .github/instructions/core-essentials.instructions.md
```

### 1b. Requirement Specification Files

```
list_dir: .github/skills/requirements/
```

All files inside `requirements/` are project-specific.

### 1c. Generated Documents

```
list_dir: docs/           → SRS, maturity reports
list_dir: docs/wbs/       → WBS markdown
list_dir: docs/wbs/excel/ → WBS Excel files
```

All files inside `docs/` are generated outputs.

### 1d. Project Tag Routing (in copilot-instructions.md)

```
grep_search: "Project Tag Routing" in .github/copilot-instructions.md
```

All rows in the Project Tag Routing table are project-specific.

### 1e. Project-Specific Critical Rules (in copilot-instructions.md)

```
grep_search: "Critical Rules" in .github/copilot-instructions.md
```

Rules referencing specific framework paths (e.g., `src/Eccube/`, `app/Customize/`) are project-specific.

### 1f. SKILL.md Project-Specific Entries

```
grep_search: "Requirement-Specific Skills" in .github/skills/SKILL.md
```

Sections:
- `🏗️ Requirement-Specific Skills (requirements/)` — entire section
- Rows in `📚 All Available Skills` table referencing `requirements/*`
- Rows in the scenario routing table referencing `requirements/*`
- File listing under `### Requirements (requirements/)` section
- SKILL.md header/description referencing EC-Cube or project name

### 1g. Project-Specific Sections in Individual Skill Files

The following skill files contain hardcoded project-specific references (framework name in title, project paths in `scope`, framework-specific tables and commands) that must be reset:

```
check: .github/skills/testing/SKILL.md        → scope, title, file classification table, base test classes, run commands
check: .github/skills/feature-development/SKILL.md → scope, title, Standard Feature Structure
check: .github/skills/change-request/SKILL.md → scope, title, migration/schema approach note
check: .github/skills/bug-fixing/SKILL.md     → scope, role, title
check: .github/skills/refactoring/SKILL.md    → scope, role, title
check: .github/skills/investigation/SKILL.md  → scope, role, title
```

---

## Step 2: Show Cleanup Plan & Confirm

Present the full list of files to be cleaned using `vscode_askQuestions`:

```
Header: "Project Cleanup Plan"
Question: "The following project-specific files will be removed. Proceed?"
Message: |
  **Core files (will be deleted):**
  - .github/skills/core-essentials.md
  - .github/skills/core-full.md
  - .github/instructions/core-essentials.instructions.md

  **Requirement specs (all files in requirements/):**
  {list each file found}

  **Generated docs (all files in docs/):**
  {list each file found}

  **Config sections to clean:**
  - copilot-instructions.md → Project Tag Routing rows
  - copilot-instructions.md → Critical Rules (project-specific)
  - SKILL.md → Requirement-Specific Skills section
  - SKILL.md → Project-specific entries in tables
  - SKILL.md → Header description (EC-Cube → generic)
  - testing/SKILL.md → scope, title, file classification table, run commands
  - feature-development/SKILL.md → scope, title, Standard Feature Structure
  - change-request/SKILL.md → scope, title, migration approach note
  - bug-fixing/SKILL.md → scope, role, title
  - refactoring/SKILL.md → scope, role, title
  - investigation/SKILL.md → scope, role, title

Options:
  - "Yes, clean everything" (recommended)
  - "No, cancel"
```

If **cancel**: stop immediately.

---

## Step 3: Delete Project-Specific Files

### 3a. Delete Core Configuration Files

```bash
rm -f .github/skills/core-essentials.md
rm -f .github/skills/core-full.md
rm -f .github/instructions/core-essentials.instructions.md
```

### 3b. Delete All Requirement Specs

```bash
# Delete all files inside requirements/ but keep the directory
find .github/skills/requirements/ -type f -delete
```

### 3c. Delete All Generated Documents

```bash
# Delete all files inside docs/ recursively but keep directory structure
find docs/ -type f -delete
```

### 3d. Reset Project-Specific Sections in Individual Skill Files

For each file below, use `replace_string_in_file` to replace the project-specific content with a generic placeholder. Do NOT delete the files — only reset the identified sections.

#### testing/SKILL.md

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

#### feature-development/SKILL.md

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

#### change-request/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **H1 title** → `# Change Request Implementation Skill`
3. **Migration/schema note** (the `> ⚠️ This project does NOT use Doctrine migrations.` line in Phase 3) → replace with:

```markdown
> ⚠️ Follow the project's schema change approach defined in `core-essentials.md`. Run `[Init-Core]` if not yet generated.
```

#### bug-fixing/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **Frontmatter `role`** → `"Diagnose and fix bugs using the project's extension and override patterns"`
3. **H1 title** → `# Bug Fixing Skill`

#### refactoring/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **Frontmatter `role`** → `"Modernize legacy code — extract services, reduce cyclomatic complexity, enforce patterns"`
3. **H1 title** → `# Code Refactoring Skill`

#### investigation/SKILL.md

1. **Frontmatter `scope`** → `"{source_dir}/"`
2. **Frontmatter `role`** → `"Read-only specialist for tracing code paths, mapping dependencies, and assessing blast radius"`
3. **H1 title** → `# Investigation & Impact Analysis Skill`

---

## Step 4: Clean copilot-instructions.md

### 4a. Clean Project Tag Routing Table

Remove all data rows from the Project Tag Routing table, keeping the table header:

**Before:**
```markdown
## Project Tag Routing

| Project Tag | Skill File |
|-------------|-----------|
| `[CR2-Phase2]` | `.github/skills/requirements/cr2-phase2-ac-installation.md` |
| `[CR4-Phase2]` | `.github/skills/requirements/cr4-phase2-store-pickup-inventory.md` |
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

### 5c. Remove Project-Specific Rows from All Available Skills Table

Remove rows referencing `requirements/*` from the `📚 All Available Skills` table (entries like #13 `requirements/cr2-phase2-*`, #14 `requirements/cr4-phase2-*`, etc.).

Renumber remaining rows if needed to keep sequential numbering.

### 5d. Remove Project-Specific Scenario Routing

Remove rows from the scenario routing table that reference `requirements/*`:
- `AC installation form changes`, `Fix estimation cost bug`, `Outlet pattern logic`, etc.
- `Store pickup stock deduction`, `New shipping status`, `Picking/packing barcode`, etc.

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

---

## Step 6: Ask About Core File Generation

After cleaning, ask via `vscode_askQuestions`:

```
Header: "Generate Core Files"
Question: "Do you want to generate new core files for a new codebase?"
Message: |
  This will run `[Init-Core]` to create:
  - **core-essentials.md** — Critical rules, directories, naming conventions
  - **core-full.md** — Full architecture, edge cases, patterns
  - **core-essentials.instructions.md** — VS Code auto-loader for source files
  - Update **copilot-instructions.md** Critical Rules for the new project
  - Update **SKILL.md** header description for the new project
  - Update **testing/SKILL.md** — scope, file classification table, run commands
  - Update **feature-development/SKILL.md** — scope, Standard Feature Structure
  - Update **change-request/SKILL.md** — scope, migration approach note
  - Update **bug-fixing/SKILL.md**, **refactoring/SKILL.md**, **investigation/SKILL.md** — scope, title, role

Options:
  - "Yes, generate for new project" (recommended)
  - "No, just keep it clean"
```

### If "Yes, generate for new project"
→ Delegate to `[Init-Core]` skill — read `.github/skills/init-core.md` and follow its full workflow (Step 1 → Step 2/3 → Generation Phase → Post-Generation).

### If "No, just keep it clean"
→ Skip to Step 7.

---

## Step 7: Summary Report

Present the final summary:

```
✅ Project cleanup complete!

**Deleted:**
- {N} core configuration files
- {N} requirement spec files from requirements/
- {N} generated document files from docs/

**Cleaned:**
- copilot-instructions.md → Project Tag Routing (cleared)
- copilot-instructions.md → Critical Rules (reset to generic)
- SKILL.md → Requirement-Specific Skills (cleared)
- SKILL.md → Project-specific table entries (removed)
- SKILL.md → Header description (reset to generic)
- testing/SKILL.md → scope, title, file classification table, run commands (reset to generic)
- feature-development/SKILL.md → scope, title, Standard Feature Structure (reset to generic)
- change-request/SKILL.md → scope, title, migration approach (reset to generic)
- bug-fixing/SKILL.md → scope, role, title (reset to generic)
- refactoring/SKILL.md → scope, role, title (reset to generic)
- investigation/SKILL.md → scope, role, title (reset to generic)

**Core Files:**
- {Generated via [Init-Core] for {project} / Not generated — run [Init-Core] later}

📁 The framework is ready for {new project name / a new project}.
```

---

## What Gets Cleaned vs What Stays

| Category | Action | Files |
|----------|--------|-------|
| **Core config** | 🗑️ Delete | `core-essentials.md`, `core-full.md`, `core-essentials.instructions.md` |
| **Requirements** | 🗑️ Delete all | Everything in `.github/skills/requirements/` |
| **Generated docs** | 🗑️ Delete all | Everything in `docs/` |
| **Project tags** | ✏️ Clear rows | `copilot-instructions.md` → Project Tag Routing |
| **Critical rules** | ✏️ Reset | `copilot-instructions.md` → generic rules only |
| **SKILL.md** | ✏️ Clean entries | Remove CR entries, reset header, clean tables |
| **testing/SKILL.md** | ✏️ Reset sections | scope, title, file classification table, run commands |
| **feature-development/SKILL.md** | ✏️ Reset sections | scope, title, Standard Feature Structure |
| **change-request/SKILL.md** | ✏️ Reset sections | scope, title, migration approach note |
| **bug-fixing/SKILL.md** | ✏️ Reset sections | scope, role, title |
| **refactoring/SKILL.md** | ✏️ Reset sections | scope, role, title |
| **investigation/SKILL.md** | ✏️ Reset sections | scope, role, title |
| **Other skill files** | ✅ Keep | Workflow logic untouched |
| **20 prompt files** | ✅ Keep | All slash command prompts untouched |
| **4 example files** | ✅ Keep | All templates untouched |
| **Support scripts** | ✅ Keep | Python generators, converters, venv |
| **Samples** | ✅ Keep | BAT/WBS sample Excel files |
| **Agents** | ✅ Keep | Requirement analyst/reviewer/assessor agents |

---

## Related Skills

- **`init-core`** — Generate core skill files for any project (delegated from Step 6)
- **`register-skill`** — Register new project-specific skills after cleanup
- **`requirement-analysis`** — Analyze requirements for the new project
