---
name: clean
description: "Removes project-specific data, requirement skills, and generated outputs to prepare the AI-skills framework for a fresh install on a new codebase; optionally regenerates core files via init-core. Use when resetting the framework for a new project. Triggered by the [Clean] tag or /clean."
---

# Project Cleaner Skill

**Purpose:** Remove all project-specific data, requirement specs, generated outputs, and core configuration files — preparing the AI-Skills framework for installation on a new codebase. Optionally delegates to `[Init-Core]` to regenerate core files for the new project.

## Usage

```
[Clean]
[Clean] I want to install this on a new Laravel project
```

---

## Step 1: Discover Project-Specific Files

Scan the workspace and group findings into categories:

| # | Category | How to Find | What Is Project-Specific |
|---|----------|-------------|--------------------------|
| 1a | Core config files | `check_exists: .claude/skills/core-essentials.md`, `.claude/skills/core-full.md` | Both files. `CLAUDE.md` is never deleted — only its project-specific sections are reset (1d/1e, Step 4) |
| 1b | Requirement specs | `Glob: .claude/skills/requirements/` | All files inside |
| 1c | Generated docs | `Glob: docs/`, `docs/wbs/`, `docs/wbs/excel/` | All files (SRS, maturity reports, WBS markdown/Excel) |
| 1d | Project Tag Routing | `Grep: "Project Tag Routing" in CLAUDE.md` | All rows in the table |
| 1e | Critical Rules | `Grep: "Critical Rules" in CLAUDE.md` | Rules referencing specific framework paths (e.g., `src/Eccube/`, `app/Customize/`) |
| 1f | SKILL.md entries | `Grep: "Requirement-Specific Skills" in .claude/skills/SKILL.md` | Requirement-Specific Skills section; `requirements/*` rows in the All Available Skills and scenario routing tables; `### Requirements (requirements/)` file listing; header/description referencing EC-Cube or project name |
| 1g | Individual skill files | Check table below | Hardcoded framework name in title, project paths in `scope`, framework-specific tables and commands |

**1g — skill files with project-specific sections to reset:**

| File | Sections |
|------|----------|
| `testing/SKILL.md` | scope, title, file classification table, base test classes, run commands |
| `feature-development/SKILL.md` | scope, title, Standard Feature Structure |
| `change-request/SKILL.md` | scope, title, migration/schema approach note |
| `bug-fixing/SKILL.md` | scope, role, title |
| `refactoring/SKILL.md` | scope, role, title |
| `investigation/SKILL.md` | scope, role, title |

---

## Step 2: Show Cleanup Plan & Confirm

Present the full list of files to be cleaned using `AskUserQuestion`:

```
Header: "Project Cleanup Plan"
Question: "The following project-specific files will be removed. Proceed?"
Message: |
  **Core files (will be deleted):**
  - .claude/skills/core-essentials.md
  - .claude/skills/core-full.md

  **Requirement specs (all files in requirements/):**
  {list each file found}

  **Generated docs (all files in docs/):**
  {list each file found}

  **Config sections to clean:**
  - CLAUDE.md → Project Tag Routing rows
  - CLAUDE.md → Critical Rules (project-specific)
  - SKILL.md → Requirement-Specific Skills section
  - SKILL.md → Project-specific entries in tables
  - SKILL.md → Header description (EC-Cube → generic)
  - {each 1g skill file → its sections, per the 1g table}

Options:
  - "Yes, clean everything" (recommended)
  - "No, cancel"
```

If **cancel**: stop immediately.

---

## Step 3: Delete Project-Specific Files

### 3a. Delete Core Configuration Files

```bash
rm -f .claude/skills/core-essentials.md
rm -f .claude/skills/core-full.md
```

`CLAUDE.md` itself is not deleted — Step 4 resets its Project Tag Routing and Critical Rules sections in place.

### 3b. Delete All Requirement Specs

```bash
# Delete all files inside requirements/ but keep the directory
find .claude/skills/requirements/ -type f -delete
```

### 3c. Delete All Generated Documents

```bash
# Delete all files inside docs/ recursively but keep directory structure
find docs/ -type f -delete
```

### 3d. Reset Project-Specific Sections in Individual Skill Files

For each file in the 1g table, use `Edit` to replace the project-specific content with a generic placeholder. Do NOT delete the files — only reset the identified sections.

→ Read `references/cleanup-templates.md` (section "Step 3d") for the exact per-file replacement blocks when you reach this step.

---

## Step 4: Clean CLAUDE.md

- **4a. Project Tag Routing table** — remove all data rows, keep the table header, append the *"(No project tags registered. Use `[Register-Skill]` to add project-specific requirement skills.)"* placeholder.
- **4b. Critical Rules** — replace project-specific rules with the generic rule set plus the `[Init-Core]` placeholder note.

→ Read `references/cleanup-templates.md` (section "Step 4") for the verbatim before/after blocks when you reach this step.

---

## Step 5: Clean SKILL.md

- **5a. Header description** — reset EC-Cube-specific title and Agent Role line to generic.
- **5b. Requirement-Specific Skills section** — delete the entire `## 🏗️ Requirement-Specific Skills (requirements/)` section (all CR entries) up to the next `## ✅` section; insert the placeholder.
- **5c. All Available Skills table** — remove rows referencing `requirements/*`; renumber remaining rows if needed to keep sequential numbering.
- **5d. Scenario routing table** — remove rows referencing `requirements/*` (e.g., `AC installation form changes`, `Fix estimation cost bug`, `Outlet pattern logic`, `Store pickup stock deduction`, `New shipping status`, `Picking/packing barcode`).
- **5e. Requirements file listing** — replace the `### Requirements (requirements/)` section with the placeholder.
- **5f. Core Principles section** — make generic (remove EC-Cube references) and add the `[Init-Core]` note.

→ Read `references/cleanup-templates.md` (section "Step 5") for the verbatim before/after and placeholder blocks when you reach this step.

---

## Step 6: Ask About Core File Generation

After cleaning, ask via `AskUserQuestion`:

```
Header: "Generate Core Files"
Question: "Do you want to generate new core files for a new codebase?"
Message: |
  This will run `[Init-Core]` to create:
  - **core-essentials.md** — Critical rules, directories, naming conventions
  - **core-full.md** — Full architecture, edge cases, patterns
  - Update **CLAUDE.md** Critical Rules and Key Directories for the new project
  - Update **SKILL.md** header description for the new project
  - Update the six 1g skill files (scope/title/role and framework-specific sections)

Options:
  - "Yes, generate for new project" (recommended)
  - "No, just keep it clean"
```

- **Yes** → Delegate to `[Init-Core]` — read `.claude/skills/init-core.md` and follow its full workflow (Step 1 → Step 2/3 → Generation Phase → Post-Generation).
- **No** → Skip to Step 7.

---

## Step 7: Summary Report

Present the final summary:

```
✅ Project cleanup complete!

**Deleted:** {N} core config files, {N} requirement specs, {N} generated docs
**Cleaned:** CLAUDE.md (Project Tag Routing cleared, Critical Rules reset),
SKILL.md (Requirement-Specific section cleared, project rows removed, header reset),
and the six 1g skill files (sections reset to generic placeholders)
**Core Files:** {Generated via [Init-Core] for {project} / Not generated — run [Init-Core] later}

📁 The framework is ready for {new project name / a new project}.
```

---

## What Gets Cleaned vs What Stays

| Category | Action | Files |
|----------|--------|-------|
| **Core config** | 🗑️ Delete | `core-essentials.md`, `core-full.md` |
| **Requirements** | 🗑️ Delete all | Everything in `.claude/skills/requirements/` |
| **Generated docs** | 🗑️ Delete all | Everything in `docs/` |
| **Project tags** | ✏️ Clear rows | `CLAUDE.md` → Project Tag Routing |
| **Critical rules** | ✏️ Reset | `CLAUDE.md` → generic rules only |
| **SKILL.md** | ✏️ Clean entries | Remove CR entries, reset header, clean tables |
| **testing/SKILL.md** | ✏️ Reset sections | scope, title, file classification table, run commands |
| **feature-development/SKILL.md** | ✏️ Reset sections | scope, title, Standard Feature Structure |
| **change-request/SKILL.md** | ✏️ Reset sections | scope, title, migration approach note |
| **bug-fixing/SKILL.md** | ✏️ Reset sections | scope, role, title |
| **refactoring/SKILL.md** | ✏️ Reset sections | scope, role, title |
| **investigation/SKILL.md** | ✏️ Reset sections | scope, role, title |
| **Other skill files** | ✅ Keep | Workflow logic untouched |
| **22 slash commands** | ✅ Keep | All `.claude/commands/*.md` files untouched |
| **4 example files** | ✅ Keep | All templates untouched |
| **Support scripts** | ✅ Keep | Python generators, converters, venv |
| **Samples** | ✅ Keep | BAT/WBS sample Excel files |
| **Agents** | ✅ Keep | Requirement analyst/reviewer/assessor agents |

---

## Related Skills

- **`init-core`** — Generate core skill files for any project (delegated from Step 6)
- **`register-skill`** — Register new project-specific skills after cleanup
- **`requirement-analysis`** — Analyze requirements for the new project
