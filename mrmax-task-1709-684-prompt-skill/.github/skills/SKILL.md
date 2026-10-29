---
name: "Master Skill Index"
role: "Route untagged prompts to the correct Specialist Agent skill file"
primary_tools: [read_file]
scope: ".github/skills/"
---

# EC-Cube Agent Skills - Quick Reference

**Agent Role:** Principal Software Engineer and PR Reviewer specializing in EC-Cube 4.x

This is the **master index** for EC-Cube development skills. Each skill is optimized for Claude Agent performance (~300-400 lines, focused, actionable).

---

## 🎯 Which Skill Should You Use?

### **Core Principles** - Start Here First
**Skill:** `core`  
**Use when:** Need architecture overview, core rules, AWS setup, or validation commands

📋 **Contains:**
- EC-Cube 4.x architecture and directory structure
- AWS production environment setup
- Critical rules (NEVER violate)
- Pre-implementation checklist
- Business logic patterns
- Naming conventions

---

## 🛠️ Development Skills

### **1. Refactoring Legacy Code**
**Skill:** `refactoring`  
**Use when:** Modernizing fat controllers, replacing raw SQL, extracting services

✨ **You'll Learn:**
- Extract business logic to services
- Replace raw SQL with Doctrine ORM
- Implement Strategy pattern for complex conditionals
- Use Decorators to enhance core services
- Test refactored code

---

### **2. Building New Features**
**Skill:** `feature-development`  
**Use when:** Creating new functionality from scratch

✨ **You'll Learn:**
- Complete feature structure (Entity → Controller → Template)
- Database schema changes (manual SQL scripts)
- Service registration and DI
- Routing and admin integration
- Form validation
- Frontend templates

---

### **3. Fixing Bugs**
**Skill:** `bug-fixing`  
**Use when:** Diagnosing and fixing defects without modifying core

✨ **You'll Learn:**
- Debug with logs and Symfony Profiler
- Event Subscribers to intercept core behavior
- Service Decorators to wrap core services
- Repository overrides for query fixes
- Write regression tests

---

### **4. Implementing Change Requests**
**Skill:** `change-request`  
**Use when:** Implementing stakeholder/business requirements

✨ **You'll Learn:**
- Requirements analysis and impact assessment
- Backward compatibility strategies
- Database schema changes (manual SQL, no migrations)
- Entity extensions with Proxy pattern
- Stakeholder communication
- Deployment procedures

---

### **5. Requirement Analysis (3-Agent Pipeline)**
**Skill:** `requirement-analysis`  
**Trigger:** `[Req-Analysis]`  
**Use when:** Analyzing client requirement documents (Excel/Word/PDF/images) to produce SRS and WBS

✨ **You'll Get:**
- 3-agent pipeline (Maturity Assessor + Analyst + Reviewer) with maturity gate
- Automated PDF text extraction and page-to-image rendering
- Structured SRS document with requirements, impact analysis, corner cases, test cases
- JIRA-ready WBS with stories, sub-tasks, and sprint allocation
- Auto-generation of core-essentials.md + core-full.md if missing (via Init-Core delegation)
- Temporary files auto-cleaned after processing

---

### **6. WBS Generation (from SRS)**
**Skill:** `wbs-generation`  
**Trigger:** `[WBS]`  
**Use when:** You already have an SRS document and need to generate a detailed, JIRA-ready Work Breakdown Structure

✨ **You'll Get:**
- Fully detailed Stories with Summary, Requirement Details, Acceptance Criteria (Gherkin), Corner Cases, Risks
- Sub-tasks with specific file paths, Definition of Done, and hour estimates
- Cross-story dependency mapping and sprint allocation
- Traceability Matrix ensuring every SRS requirement is covered
- Auto-detected codebase context for accurate file references

---

### **7. Excel WBS Generation (from WBS Markdown)**
**Skill:** `excel-wbs-generation`  
**Trigger:** `[Excel-WBS]`  
**Use when:** You have a WBS markdown file and need a formatted Excel (.xlsx) matching WBS-Sample.xlsx

✨ **You'll Get:**
- Formatted Excel with colored story/subtask rows (green/light-green)
- Status, Assignee, and Review dropdowns
- Auto-parsed stories and sub-tasks from WBS markdown
- Output at `docs/wbs/excel/{feature}-wbs.xlsx`

---

### **8. WBS Import (from Excel/CSV → WBS Markdown)**
**Skill:** `wbs-import`  
**Trigger:** `[WBS-Import]`  
**Use when:** You have an Excel-WBS (.xlsx) or CSV export and need to reverse-generate a full WBS markdown enriched with SRS details

✨ **You'll Get:**
- Full WBS markdown reconstructed from Excel/CSV skeleton
- Stories and sub-tasks enriched with SRS requirement details, acceptance criteria (Gherkin), corner cases, risks
- Preserved Excel metadata (assignee, status, dev effort hours)
- Traceability Matrix cross-referencing every FR-*/US-* from the SRS
- Import Metadata section tracking source files and counts

---

### **9. Requirement Conversion (Excel/Word → PDF + PNG)**
**Skill:** `requirement-conversion`  
**Trigger:** `[Req-Convert]`  
**Use when:** You have Excel (.xlsx) or Word (.docx) requirement documents with visual diagrams and need PDF + PNG output

✨ **You'll Get:**
- One PDF per worksheet preserving all visuals (shapes, arrows, charts, formatting)
- One PNG per worksheet (multi-page PDFs stitched vertically)
- Output at `.github/docs/requirement-conversion/{excel-name}/pdf/` + `images/`
- Auto-install of all dependencies (Python venv + LibreOffice AppImage) on first run
- No system dependencies required beyond Python 3

---

### **10. Initialize Core Skill Files**
**Skill:** `init-core`  
**Trigger:** `[Init-Core]`  
**Use when:** Setting up a new project and need to generate `core-essentials.md` + `core-full.md` coding guideline skill files

✨ **You'll Get:**
- Interactive 3-path flow: from existing guidelines, manual tech input, or SRS-based inference
- `core-essentials.md` (~50-70 lines) — auto-loaded rules, directories, naming conventions
- `core-full.md` (~200-250 lines) — full architecture, edge cases, patterns, validation commands
- YAML frontmatter + markdown format matching the existing skill file structure
- Technology-specific rules and patterns (not generic boilerplate)

---

### **11. Register New Skill**
**Skill:** `register-skill`  
**Trigger:** `[Register-Skill]`  
**Use when:** Adding a new skill, action tag, or slash command to the orchestrator

✨ **You'll Get:**
- Interactive questionnaire to gather skill details
- Skill workflow file (`.github/skills/{name}.md`) from template
- Slash command file (`.github/prompts/{slug}.prompt.md`)
- Automatic routing table and SKILL.md registration
- Verification checks to confirm everything is wired correctly

---

### **12. Project Cleaner**
**Skill:** `clean`  
**Trigger:** `[Clean]`  
**Use when:** Preparing the AI-Skills framework for installation on a new codebase — removes all project-specific data

✨ **You'll Get:**
- Deletion of core config files (`core-essentials.md`, `core-full.md`, `core-essentials.instructions.md`)
- Cleanup of all requirement specs in `requirements/`
- Cleanup of all generated docs in `docs/`
- Reset of `copilot-instructions.md` project tags and critical rules
- Reset of `SKILL.md` project-specific entries and header
- Optional `[Init-Core]` delegation to generate core files for the new project

---

## 🏗️ Requirement-Specific Skills (requirements/)

Stored in `requirements/` subdirectory. Use `[Project-Tag]` in prompts to auto-load.

### **CR2-Phase2: AC Installation Queries**
**Skill:** `requirements/cr2-phase2-ac-installation`  
**Use when:** Working on AC installation checkout form, cost estimation, outlet pattern logic, or drilling validation

✨ **You'll Learn:**
- 5-level field hierarchy with conditional show/hide
- Pattern logic P1-P6 for electrical work fields
- Attach goods codes AC001-AC034 and cost calculation
- Drilling cost validation chain (4 mandatory conditions)
- Frontend/backend sync for estimation modal
- Responsive design (desktop/mobile)
- BEM CSS architecture

### **CR4-Phase2: Store Pickup Inventory & Operations**
**Skill:** `requirements/cr4-phase2-store-pickup-inventory`  
**Use when:** Working on store pickup stock deduction, new shipping status (商品手配中), store backorder columns, admin order list/detail, picking, packing, or shop memo

✨ **You'll Learn:**
- Store vs EC stock deduction logic (order types 11, 21, 31)
- Store backorder columns (`store_is_backordered`, `store_lack_count`)
- New shipping status ARRANGING (ID=4) and transition rules
- Authority_id=6 server-side enforcement
- JAN8/JAN13 barcode generation for packing PDF
- Shop memo accordion/popup append behavior
- Cascade impact on invoice, packing, batch, mail, wait list

### **CR5: V-Point & Credit Card Linkage Integration**
**Skill:** `requirements/cr5-vpoint-card-linkage`  
**Use when:** Working on CCCMK API integration (sp101/sp201), AES-256-CBC encryption, card linkage (barcode/birthday), V-Point coupon exchange (EC checkout + Native app), cancel retry logic, BAT1-BAT4 batch processing, admin V-Point screens, POS API for coupon_id=999999990001

✨ **You'll Learn:**
- sp101 balance inquiry + sp201 point usage/cancel API integration
- AES-256-CBC encryption with MD5 key expansion
- Card linkage flow (barcode scan, birthday auth, 5 data types)
- EC checkout STEP1-1→STEP3 with temp coupon reservation (session/Redis)
- Cancel retry logic (3 attempts → cancel_status state machine → BAT3/BAT4)
- SP/SE file format (783/794 bytes, Shift_JIS, fixed-length)
- 30+ return code classification and error message mapping
- Admin cancel redemption (365-day window, audit log)
- CouponDiscountProcess modification for dynamic discount
- Serial number generation (A03/A04 + YYMMDD(JST) + 11-digit sequence)

---

## ✅ Quality Assurance Skills

### **5. Quick Review (Single Agent)**
**Skill:** `code-review`  
**Trigger:** `[Quick Review]`  
**Use when:** Lightweight single-agent code review — faster than `[Review]`, one pass through 6 dimensions

✨ **You'll Get:**
- Single-agent review across 6 dimensions (Security, Performance, Architecture, Quality, Testing, Error Handling)
- `QUICK-REVIEW-*.md` report with verdict (APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES)
- Same modes as `[Review]`: PR, branch, staged, diff
- Faster turnaround — no sub-agent orchestration overhead

---

### **5b. Code Review Command (Automated)**
**Skill:** `review-command`  
**Use when:** Running a comprehensive automated review with parallel agents
**Trigger:** `@workspace [Review] pr 123` / `[Review] branch feature-x` / `[Review] staged` / `[Review] diff file.diff`

✨ **You'll Get:**
- 7 parallel review agents (Quality, Tests, Performance, Security, Docs, Error Handling, Config)
- Auto-detected tech stack with EC-Cube-specific rules
- Structured `CODE-REVIEW-*.md` report with severity ratings
- Executive summary with APPROVE / APPROVE WITH COMMENTS / REQUEST CHANGES verdict
- Deduplicated findings with prioritized action items

---

### **5c. PR Link Review (Remote GitHub PRs)**
**Skill:** `pr-review`  
**Trigger:** `[PR-Review]`  
**Use when:** Reviewing a GitHub PR by URL — works with any repo you have access to in VS Code

✨ **You'll Get:**
- Same 7-agent parallel review pipeline as `[Review]`
- 3-tier data fetch: GitKraken MCP → git merge ref → curl + PAT
- Zero manual credentials (uses VS Code's built-in GitHub auth)
- Auto-detected tech stack with EC-Cube rules for same-repo PRs
- Structured `CODE-REVIEW-PR-{owner}-{repo}-{number}.md` report
- Temporary branch cleanup after review

---

### **5d. Quick PR Link Review (Remote GitHub PRs, Single-Agent)**
**Skill:** `quick-pr-review`  
**Trigger:** `[Quick PR-Review]`  
**Use when:** Reviewing a GitHub PR by URL with a faster single-agent quick-review pipeline

✨ **You'll Get:**
- URL-based PR review flow with the same 3-tier fetch strategy as `[PR-Review]`
- Single-agent analysis using `[Quick Review]` review dimensions
- Zero manual credentials in normal flow (uses VS Code GitHub auth)
- Structured `QUICK-REVIEW-PR-{owner}-{repo}-{number}.md` report in `docs/quick-review/`
- Temporary branch cleanup after review

---

### **6. Testing**
**Skill:** `testing`  
**Trigger:** `[Unit Test]`  
**Use when:** Generating tests from branch diffs — auto-detects pure unit vs integration tests

✨ **You'll Learn:**
- Branch-diff-based test generation (`branch` + `base` args)
- Pure unit tests (no kernel) vs integration tests (kernel + test DB)
- Docker exec commands for both test types
- AAA pattern, data providers, mock strategies
- Correct base class selection per file location

---

### **7. Investigation & Impact Analysis**
**Skill:** `investigation`  
**Trigger:** `[Investigation]`  
**Use when:** Tracing code paths, mapping dependencies, assessing blast radius — **read-only, no code changes**

✨ **You'll Get:**
- Complete dependency map (services, subscribers, templates, batch jobs)
- Risk assessment with severity classification
- Blast radius analysis before risky CRs or refactors
- Structured impact report
- **Zero code changes** — strictly read-only

---

### **8. AI Code Disclosure**
**Skill:** `ai-disclosure`  
**Trigger:** `[Disclose]`  
**Use when:** Preparing a PR and need to disclose AI-generated or AI-assisted code

✨ **You'll Get:**
- Git diff analysis for AI-generated code indicators
- Structured `AI_GENERATED_CODE_DISCLOSURE_<branch>.md` file
- Per-file classification: Type, Function/Class, Line Range, AI Scope, Reason
- Strict output format — no prose, no tables, only list entries

---

### **9. BAT Test Case Generation**
**Skill:** `bat-generation`  
**Trigger:** `[BAT]`  
**Use when:** Preparing a PR and need Developer BAT (Basic Acceptance Test) Excel reports from code diffs

✨ **You'll Get:**
- Git diff analysis to identify affected routes, controllers, templates, services
- Structured Excel (`.xlsx`) files per module with Positive, Negative, and Impact Area test cases
- Strict format: `Verify [action] at [route] ([METHOD]) — should [expected]`
- Auto-extracted ticket ID from branch name
- **Auto-test execution** — optional HTTP smoke tests against dev server, pre-filling Result (Dev1) column with OK/NG/NE

---

### **10. PR Note Generation**
**Skill:** `pr-note`  
**Trigger:** `[PR-Note]`  
**Use when:** Preparing a GitHub PR and need a structured PR description with ticket link, summary, checklists, and AI disclosure

✨ **You'll Get:**
- Auto-extracted Jira ticket link from branch name
- Summary and impact range generated from diff analysis
- Unit test commands extracted from changed test files
- AI-generated code disclosure (via `ai-disclosure` sub-agent)
- Static checklists for performance, code quality, and screenshots
- GitHub-compatible markdown file at `~/Desktop/MrMax/PR-Note/`

---

### **11. WBS to JIRA Ticket Creator**
**Skill:** `wbs-to-jira`  
**Trigger:** `[WBS-to-JIRA]`  
**Use when:** You have a WBS markdown file (generated by `[WBS]`) and want to create JIRA Stories + Sub-tasks automatically

✨ **You'll Get:**
- Dry-run preview showing Stories and Sub-task count before any API calls
- Live creation of JIRA Stories + Sub-tasks via REST API v3
- Story descriptions with Overview, Affected Components, Acceptance Criteria
- Sub-task descriptions with Estimate, Summary, AC, Definition of Done, Corner Cases, Risks
- Confirmation prompt before live creation — never creates tickets without your approval
- One-time config setup (`jira_config.ini`) with auto-gitignore for security

---

## 📊 Skill Selection Matrix

| **Task** | **Primary Skill** | **Also Review** |
|----------|------------------|-----------------|
| Extract logic from controller | `refactoring` | `core`, `testing` |
| Add new product feature | `feature-development` | `core`, `testing` |
| Fix order processing bug | `bug-fixing` | `core`, `testing` |
| Quick review (single-agent, lightweight) | `code-review` | `core` |
| Full review (7 parallel agents, detailed report) | `review-command` | `core`, `code-review` |
| **Review GitHub PR by URL (remote)** | `pr-review` | `code-review`, `review-command` |
| **Quick review GitHub PR by URL (remote)** | `quick-pr-review` | `code-review`, `pr-review` |
| Write service tests | `testing` | `core` |
| Implement discount system | `change-request` | `feature-development` |
| Optimize query performance | `refactoring` | `code-review` |
| **Assess blast radius before a risky CR** | `investigation` | `core` |
| **Trace order flow end-to-end** | `investigation` | `core` |
| **Generate AI code disclosure for PR** | `ai-disclosure` | `review-command` |
| **Generate BAT test cases from diff** | `bat-generation` | `testing`, `review-command` |
| **Generate GitHub PR description** | `pr-note` | `ai-disclosure` |
| **Analyze client requirements (PDF/Excel/Word/images)** | `requirement-analysis` | `core`, `change-request` |
| **Generate WBS Excel from WBS markdown** | `excel-wbs-generation` | `wbs-generation` |
| **Convert Excel/Word requirements to PDF/PNG** | `requirement-conversion` | `requirement-analysis` |
| **Generate core skill files for new project** | `init-core` | `core` |
| **Clean project data for new codebase** | `clean` | `init-core` |
| **Create JIRA tickets from WBS markdown** | `wbs-to-jira` | `wbs-generation` |
| AC installation form changes | `requirements/cr2-phase2-ac-installation` | `core`, `change-request` |
| Fix estimation cost bug | `requirements/cr2-phase2-ac-installation` | `bug-fixing`, `testing` |
| Outlet pattern logic (P1-P6) | `requirements/cr2-phase2-ac-installation` | `core` |
| Store pickup stock deduction | `requirements/cr4-phase2-store-pickup-inventory` | `core`, `change-request` |
| New shipping status (商品手配中) | `requirements/cr4-phase2-store-pickup-inventory` | `core`, `change-request` |
| Picking/packing barcode or authority | `requirements/cr4-phase2-store-pickup-inventory` | `core`, `testing` |
| Shop memo accordion/append | `requirements/cr4-phase2-store-pickup-inventory` | `core` |

---

## 🚀 Quick Start Workflow

```
1. READ: core (understand principles)
        ↓
2. SELECT: Choose task-specific skill
        ↓
3. EXECUTE: Follow skill's step-by-step process
        ↓
4. VALIDATE: Use validation checklists
        ↓
5. REVIEW: Self-review with code-review
```

---

## 📚 All Available Skills

| # | Skill | Agent Name | Trigger Tag | Scope |
|:-:|-------|-----------|-------------|-------|
| 1 | **`core`** | Core Architecture | *(always loaded)* | Architecture rules, AWS, critical constraints |
| 2 | **`bug-fixing`** | Bug Fixer | `[Bug]` | Diagnose & fix using subscribers, decorators |
| 3 | **`change-request`** | CR Engineer | `[CR]` | Implement CRs with backward compatibility |
| 4 | **`feature-development`** | Feature Builder | `[Feature]` | Build new: Entity → Service → Controller → Template |
| 5 | **`refactoring`** | Refactoring Specialist | `[Refactor]` | Extract services, replace raw SQL |
| 6 | **`code-review`** | Quick Reviewer | `[Quick Review]` | Single-agent review (security, perf, architecture) |
| 7 | **`review-command`** | Review Commander | `[Review]` | 7-agent parallel automated review |
| 8 | **`pr-review`** | PR Link Reviewer | `[PR-Review]` | Review any GitHub PR by URL (7-agent, zero tokens) |
| 9 | **`quick-pr-review`** | Quick PR Link Reviewer | `[Quick PR-Review]` | Review any GitHub PR by URL (single-agent quick review) |
| 10 | **`testing`** | Test Engineer | `[Unit Test]` | Generate & run tests from branch diff |
| 11 | **`investigation`** | Impact Analyst | `[Investigation]` | Code tracing, blast radius — read-only |
| 12 | **`ai-disclosure`** | Disclosure Analyst | `[Disclose]` | Detect AI-generated code, produce disclosure report |
| 13 | **`bat-generation`** | BAT Generator | `[BAT]` | Generate Developer BAT Excel reports from diffs + auto-test execution |
| 14 | **`pr-note`** | PR Note Generator | `[PR-Note]` | Generate GitHub PR description from branch diffs |
| 15 | **`wbs-generation`** | WBS Generator | `[WBS]` | Generate JIRA-ready WBS from existing SRS document |
| 16 | **`requirements/cr2-phase2-*`** | *(project-specific)* | `[CR2-Phase2]` | AC installation queries, cost estimation |
| 17 | **`requirements/cr4-phase2-*`** | *(project-specific)* | `[CR4-Phase2]` | Store pickup inventory, shipping status |
| 18 | **`requirement-analysis`** | Requirement Analyst | `[Req-Analysis]` | 3-agent pipeline (maturity gate + analyst + reviewer) → SRS + WBS; auto-offers core skill generation |
| 19 | **`excel-wbs-generation`** | Excel WBS Generator | `[Excel-WBS]` | Generate formatted WBS Excel from markdown |
| 20 | **`wbs-import`** | WBS Importer | `[WBS-Import]` | Reverse-generate WBS markdown from Excel/CSV |
| 21 | **`requirement-conversion`** | Requirement Converter | `[Req-Convert]` | Convert Excel/Word requirements to PDF + PNG |
| 22 | **`init-core`** | Core Skill Generator | `[Init-Core]` | Generate core-essentials.md + core-full.md for any project |
| 23 | **`register-skill`** | Skill Registrar | `[Register-Skill]` | Register a new skill, tag, and slash command in the orchestrator |
| 24 | **`clean`** | Project Cleaner | `[Clean]` | Clean project-specific data, optionally regenerate core for new codebase |

---

## 💡 Best Practices

### Always Start With
1. Review `core-essentials` for critical rules (load `core-full` only when you need AWS/edge-case details)
2. Run pre-implementation checklist
3. Search for existing patterns in codebase

### Never
- Modify `src/Eccube/` directory
- Use raw SQL without parameterization
- Skip writing tests for business logic
- Forget to clear cache after config changes
- Generate or run Doctrine migrations (use manual SQL scripts)

### Always
- Use dependency injection
- Follow PSR-12 coding standards
- Write DocBlocks and type hints
- Test in dev environment first
- Document significant changes

---

## 2. Technical Background (Brief Overview)

---

## 2. Technical Background (Brief Overview)

**For complete technical details, see `core` skill.**

### Stack
- **Framework:** EC-Cube 4.x on Symfony 4/5
- **PHP:** 8.0+
- **Database:** MySQL 8.0+ / PostgreSQL 13+
- **ORM:** Doctrine 2.x
- **Templates:** Twig 3.x

### Key Directories
```
src/Eccube/          → Core (NEVER modify)
app/Customize/       → Your code (USE THIS)
app/Plugin/          → Plugin system
app/config/          → Configuration
app/template/        → Frontend templates
```

### AWS Production
- **Compute:** ECS/Fargate
- **Database:** RDS Aurora MySQL
- **Cache:** ElastiCache Redis
- **Storage:** S3
- **CDN:** CloudFront

---

## 3. Critical Rules (Preview)

**For complete rules, see `core` skill.**

1. ❌ **NEVER** modify `src/Eccube/`
2. ✅ **ALWAYS** use dependency injection
3. ✅ **ALWAYS** clear cache after config changes
4. ✅ **ALWAYS** use parameterized queries
5. ✅ **ALWAYS** write tests for business logic

---

## 4. Common Commands

```bash
# Cache
bin/console cache:clear

# Tests
bin/phpunit

# Static analysis
vendor/bin/phpstan analyze app/Customize/

# Functional tests
vendor/bin/codecept run functional
```

---

## 5. Skill File Structure

Each specialized skill file follows this format:

```markdown
---
name: "skill-name"
description: "Brief description"
---

# Skill Title

## When to Use
- Specific scenarios

## Expected Outcome
- What you'll achieve

## Execution Process
Step-by-step instructions

## Validation Checklist
- Coding Convention
- Security
- Performance
- Code Quality
- Architecture

## Related Skills
Cross-references
```

---

## 6. Getting Help

### If You're Unsure Which Skill to Use
1. Start with `core` for fundamentals
2. Check the **Skill Selection Matrix** above
3. Review the task description in each skill

### If Multiple Skills Apply
Example: Adding a new discount feature
1. `core` - Review architecture and rules
2. `feature-development` - Build the feature structure
3. `testing` - Write comprehensive tests
4. `code-review` - Self-review before committing

---

## 7. Skill Maintenance

**These skills are optimized for:**
- Claude Sonnet 4.5 Agent performance
- 200-400 lines per skill (focused and fast)
- Actionable, step-by-step guidance
- Real code examples
- Complete validation checklists

**Last Updated:** 2026-03-11

---

## 📖 Full Skill List

### Core & Architecture
- **core-essentials.md** - Critical rules, key directories, naming (~60 lines, always loaded)
- **core-full.md** - Full architecture: AWS, edge cases, business patterns (~250 lines, on-demand)

### Development
- **refactoring/SKILL.md** - Modernize legacy code
- **feature-development/SKILL.md** - Build new features from scratch
- **bug-fixing/SKILL.md** - Diagnose and fix bugs
- **change-request/SKILL.md** - Implement business requirements
- **wbs-generation/SKILL.md** - Generate JIRA-ready WBS from an existing SRS document
- **excel-wbs-generation/SKILL.md** - Convert WBS markdown to formatted Excel
- **wbs-import/SKILL.md** - Reverse-generate WBS markdown from Excel/CSV
- **requirement-analysis/SKILL.md** - 3-agent pipeline for requirement analysis (maturity gate + SRS + WBS)
  > Sub-agents invoked internally (not top-level tags): `agents/requirement-analyst.md`, `agents/requirement-maturity-assessor.md`, `agents/requirement-reviewer.md`
- **requirement-conversion/SKILL.md** - Convert Excel/Word requirements to PDF + PNG

### Requirements (requirements/)
- *(Project-specific requirement files. Add via `[Register-Skill]`.)*

### Quality & Testing
- **code-review/SKILL.md** - Systematic code review
- **review-command/SKILL.md** - 7-agent parallel automated review
- **pr-review/SKILL.md** - Review any GitHub PR by URL (7-agent, zero tokens)
- **quick-pr-review/SKILL.md** - Review any GitHub PR by URL (single-agent quick review)
- **testing/SKILL.md** - Unit, integration, functional testing
- **ai-disclosure/SKILL.md** - AI-generated code disclosure for PRs
- **bat-generation/SKILL.md** - Developer BAT Excel reports with auto-test execution
- **pr-note/SKILL.md** - Generate GitHub PR description from branch diffs
- **investigation/SKILL.md** - Code tracing, blast radius assessment (read-only)

### Framework Management
- **init-core/SKILL.md** - Generate core skill files for any project
- **register-skill/SKILL.md** - Register a new skill, tag, and slash command
- **clean/SKILL.md** - Clean project-specific data for new codebase install

---

## 🎓 Learning Path

### Beginner
1. Read `core` thoroughly
2. Practice with `refactoring` on simple controllers
3. Try `testing` to write your first tests

### Intermediate
4. Use `feature-development` to build complete features
5. Apply `bug-fixing` to real issues
6. Practice `code-review` on your own code

### Advanced
7. Handle `change-request` for complex business logic
8. Combine multiple skills for large-scale refactoring
9. Mentor others using these skills

---

**Ready to start? Choose your skill from the list above based on your current task!**
