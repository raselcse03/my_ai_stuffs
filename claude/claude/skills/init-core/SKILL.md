---
name: init-core
description: "Generates core-essentials.md and core-full.md coding-guideline skill files tailored to any project's tech stack — from provided guidelines, interactive answers, or SRS inference. Use when setting up the skill framework on a new project or refreshing coding guidelines. Triggered by the [Init-Core] tag or /init-core."
---

# Core Skill File Generator

**Purpose:** Interactive multi-step command that generates `core-essentials.md` and `core-full.md` skill files tailored to any project's technology stack and coding conventions.

---

## Execution Flow

```
START
  │
  ▼
[Step 1] Ask: "Do you have an existing coding guideline?"
  │
  ├── YES → User provides/attaches document
  │         → Parse guideline → Extract rules, stack, conventions
  │         → Generate both skill files
  │         → DONE
  │
  ├── NO (but knows tech stack) → Go to Step 2
  │
  └── NO (tech undecided) → Go to Step 3
  │
[Step 2] Ask about technology stack (framework, language, DB, ORM, etc.)
  │       → User provides answers
  │       → Generate both skill files
  │       → DONE
  │
[Step 3] Read project SRS/requirement documents
  │       → Analyze and suggest technology stack
  │       → Ask user to confirm or modify
  │       → Generate both skill files
  │       → DONE
```

---

## Step 1: Check for Existing Coding Guidelines

### Action
Use `AskUserQuestion` to ask:

```
Question 1: "Do you have an existing coding guideline document for this project?"
Options: ["Yes, I'll provide it", "No, but I know our tech stack", "No, suggest based on our SRS"]
```

### If "Yes, I'll provide it"
1. Ask user to attach or paste the guideline document
2. Parse the document thoroughly — extract:
   - **Technology stack** (language, framework, database, ORM, templating, etc.)
   - **Critical rules** (what to never do, what to always do)
   - **Directory structure** and file organization conventions
   - **Naming conventions** (services, controllers, models, routes, etc.)
   - **Security rules** (input validation, auth, injection prevention)
   - **Testing strategy** (tools, coverage expectations, commands)
   - **Deployment architecture** (cloud provider, CI/CD, containers)
   - **Coding standards** (style guide, linting, formatting)
   - **Business logic patterns** (domain-specific workflows)
   - **Edge cases** and known architectural pitfalls
3. Proceed to **Generation Phase**

### If "No, but I know our tech stack"
→ Go to **Step 2**

### If "No, suggest based on our SRS"
→ Go to **Step 3**

---

## Step 2: Gather Technology Details Interactively

### Action
Use `AskUserQuestion` to collect the following (all in one question set):

```
Q1: "What programming language does your project use?"
    Options: ["PHP", "TypeScript", "JavaScript", "Python", "Java", "C#", "Go", "Ruby", "Rust"]
    (allow freeform)

Q2: "What is your primary framework?"
    (freeform — e.g., "Laravel 11", "Next.js 14", "Django 5", "Spring Boot 3", "EC-Cube 4.x")

Q3: "What database do you use?"
    Options: ["MySQL", "PostgreSQL", "MongoDB", "SQLite", "SQL Server", "DynamoDB"]
    (allow freeform, multiSelect)

Q4: "What ORM or data access layer?"
    (freeform — e.g., "Doctrine", "Prisma", "Eloquent", "SQLAlchemy", "TypeORM", "None/raw SQL")

Q5: "What is your deployment target?"
    Options: ["AWS (ECS/EC2)", "Vercel", "Docker/K8s", "Azure", "GCP", "On-premise", "Other"]
    (allow freeform)

Q6: "Any additional tools or conventions?"
    (freeform — e.g., "Redis for caching, Jest for testing, ESLint + Prettier, monorepo with Turborepo")
```

### After answers
1. Build a complete technology profile from user responses
2. Proceed to **Generation Phase**

---

## Step 3: Infer Technology from SRS

Runs only when the user chose "No, suggest based on our SRS". The branch, in summary:
- **3A. Multi-Source Discovery** — gather evidence from SRS/requirement docs, project manifest files, and infrastructure files (project files are truth, SRS is intent)
- **3B. 7-Dimension Analysis Framework** — Language, Framework, Database, ORM, Frontend/Client, Infrastructure, Integrations (+ Mobile Platform), each with a High/Medium/Low/Unknown confidence level
- **3C. Inference Rules** — map SRS requirement patterns to technologies when nothing is named explicitly
- **3D. Structured Recommendation** — present a table with technology, version, confidence, source, and rationale
- **3E. Iterative Confirmation** — multi-select `AskUserQuestion` so the user confirms or pinpoints changes
- **3F. Zero-Signal Fallback** — greenfield questionnaire plus sensible default stacks

→ Read `references/tech-inference.md` only if the user chose SRS-based inference.

After confirmation → proceed to **Generation Phase**

---

## Generation Phase: Create Both Skill Files

### Pre-Generation: Discover Project Structure
Before generating, scan the workspace to understand the actual directory layout:
```
Glob: project root
Glob: src/ (or app/, lib/, etc.)
Grep: "composer.json" OR "package.json" OR "requirements.txt" OR "go.mod" OR "Cargo.toml"
```

Read the main dependency file to confirm versions and dependencies.

### File 1: `core-essentials.md`

**Target path:** `.claude/skills/core-essentials.md`
**Size target:** ~50-70 lines (compact, auto-loaded every task)

→ Read `references/core-essentials-template.md` for the full File 1 generation template when generating this file.

### File 2: `core-full.md`

**Target path:** `.claude/skills/core-full.md`
**Size target:** ~200-250 lines (comprehensive reference)

→ Read `references/core-full-template.md` for the full File 2 generation template when generating this file.

---

## Post-Generation Checklist

After generating both files:

1. **Validate format** — Ensure YAML frontmatter has `name`, `role`, `scope` (and `primary_tools` for core-full)
2. **Verify consistency** — Critical rules must match between both files
3. **Check paths** — `scope` field must reference actual project directories
4. **Confirm placement** — Files are at `.claude/skills/core-essentials.md` and `.claude/skills/core-full.md`
5. **Update `CLAUDE.md`** — Replace Critical Rules and Key Directories with the new project's — see below
6. **Update individual skill files** — See "Post-Generation Step: Update Individual Skill Files" below
7. **Summary** — Tell the user what was generated and suggest they review the files

---

## Post-Generation Step: Update `CLAUDE.md`

Claude Code has no per-path auto-loader (no `applyTo` mechanism) — the root `CLAUDE.md` is loaded every session regardless of which files are touched. So instead of generating a separate instructions file, fold the new rules directly into the existing root `CLAUDE.md`.

**Target path:** `CLAUDE.md` (repo root)

Replace the **Critical Rules** section in `CLAUDE.md` with the 3-5 most important ❌/✅ rules copied from the new `core-essentials.md`, and update its **Key Directories** section to match the new project's layout.

---

## Post-Generation Step: Update SKILL.md

After generating core files, update the SKILL.md master index:

1. **Header description** — Replace `EC-Cube Agent Skills` with `{Project Name} Agent Skills` (line ~10)
2. **Core Principles section** — Update the description to reference the new framework/stack
3. **Verify entry #19** (`init-core`) is present in the All Available Skills table

---

## Post-Generation Step: Update Individual Skill Files

→ Read `references/post-generation-updates.md` for the per-file update instructions (testing, feature-development, change-request, bug-fixing, refactoring, investigation), the data-derivation table, and the Success Message Template.

---

## Key Principles for Generation

1. **Be specific, not generic** — Rules must reference actual framework APIs, not vague best practices
2. **Use real paths** — Directory structures must match the actual project layout
3. **Framework-idiomatic** — Patterns must follow the framework's recommended approach (e.g., Laravel uses Eloquent, not raw PDO)
4. **Actionable rules** — Every rule should be something an AI agent can verify programmatically
5. **Correct versions** — Read `composer.json`, `package.json`, etc. to get actual versions
6. **No placeholder text** — Every section must contain real, usable content
7. **Match existing format exactly** — YAML frontmatter, markdown headers, ASCII diagrams, emoji markers (❌/✅) must follow the template structure shown above
