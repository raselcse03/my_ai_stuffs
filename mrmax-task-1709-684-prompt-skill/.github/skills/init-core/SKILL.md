---
name: "Core Skill Generator"
role: "Generate core-essentials.md and core-full.md coding guideline skill files for any project"
primary_tools: [vscode_askQuestions, read_file, create_file, replace_string_in_file, grep_search, list_dir, runSubagent]
scope: ".github/skills/"
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
Use `vscode_askQuestions` to ask:

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
Use `vscode_askQuestions` to collect the following (all in one question set):

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

### 3A. Multi-Source Discovery

Gather evidence from **three source categories** — project files are **truth**, SRS is **intent**:

**1. SRS / Requirement documents:**
```
file_search: **/*SRS*, **/*Requirement*, **/*requirement*, **/*spec*
file_search: **/*srs*, **/*specification*
```

**2. Project manifest files (if any exist — confirms an existing codebase):**
```
file_search: **/composer.json, **/package.json, **/requirements.txt
file_search: **/go.mod, **/Cargo.toml, **/pom.xml, **/build.gradle
file_search: **/Gemfile, **/*.csproj, **/pyproject.toml
file_search: **/pubspec.yaml                          → Flutter/Dart
file_search: **/Podfile, **/*.xcodeproj, **/*.pbxproj  → iOS (Swift/ObjC)
file_search: **/build.gradle.kts, **/settings.gradle   → Android (Kotlin/Java)
file_search: **/app.json, **/metro.config.js            → React Native
```

**3. Infrastructure / deployment files:**
```
file_search: **/Dockerfile*, **/docker-compose*
file_search: **/taskdef*.json, **/buildspec*, **/appspec*
file_search: **/.github/workflows/*, **/serverless.yml
file_search: **/terraform/*.tf, **/k8s/*.yaml
```

Read and cross-reference all found sources. If project manifest files exist, extract **actual** versions and dependencies from them — these override any SRS assumptions.

---

### 3B. Structured Analysis Framework (7 Dimensions)

Analyze every source against these 7 technology dimensions:

| Dimension | What to detect | SRS signals | Project file signals |
|-----------|---------------|-------------|---------------------|
| **Language & Version** | Primary language + runtime version | "built with Python 3.11", "PHP application" | `composer.json` → PHP, `package.json` → JS/TS, `go.mod` → Go, `pubspec.yaml` → Dart |
| **Framework** | Web/app framework + version | "Django REST API", "React frontend", "Flutter app" | Framework packages in dependency files |
| **Database** | Primary + secondary DB | "relational data", "600K members", "document store" | DB driver packages, Docker DB service images |
| **ORM / Data Layer** | How data is accessed | "complex queries", "NoSQL", "raw SQL", "local storage" | ORM packages (Doctrine, Prisma, Eloquent, SQLAlchemy, Drift/Isar) |
| **Frontend / Client** | Rendering approach + platform | "SPA", "server-rendered", "mobile app", "iOS + Android", "cross-platform" | React/Vue/Angular in deps, Twig/Blade templates, Flutter/RN/SwiftUI in deps |
| **Infrastructure** | Where and how it runs | "AWS", "scalable", "containerized", "serverless" | Dockerfile, taskdef.json, buildspec.yml, terraform files |
| **Integrations** | External services and APIs | "payment gateway", "SFTP", "email", "push notifications" | SDK packages, API client libraries in dependencies |
| **Mobile Platform** | Target platforms + distribution | "iOS and Android", "App Store", "Play Store", "barcode scan", "camera" | `pubspec.yaml`, `Podfile`, `build.gradle.kts`, `app.json` (RN) |

For each dimension, assign a **confidence level**:
- **High** — directly confirmed by project files (e.g., `composer.json` lists `"php": "^8.2"`)
- **Medium** — explicitly stated in SRS (e.g., "the system will use PostgreSQL")
- **Low** — inferred from requirements patterns (e.g., "real-time updates" → WebSockets)
- **Unknown** — no evidence found; needs user input

---

### 3C. Inference Rules (When SRS Has No Explicit Tech Mentions)

If SRS describes requirements without naming specific technologies, apply these inference patterns:

| SRS Requirement Pattern | Inferred Technology | Rationale |
|------------------------|--------------------|-----------| 
| "real-time updates", "live notifications", "chat" | WebSocket (Socket.IO / Pusher / Mercure) | Push-based communication needed |
| "mobile app + web", "REST API", "cross-platform" | API-first backend + React Native / Flutter | Multi-client architecture |
| "e-commerce", "payments", "cart", "checkout" | Payment SDK (Stripe/GMO/PayPal), session/Redis cart | Transactional integrity required |
| "high concurrency", "1M+ users", "throughput" | Async runtime (Go/Node) or queue-based (SQS/RabbitMQ) | Horizontal scaling |
| "file upload", "image processing", "media" | S3 + CDN + image processing (Imagick/Sharp) | Scalable blob storage |
| "batch processing", "scheduled jobs", "cron" | ECS Batch / Celery / Bull / Laravel Scheduler | Async background processing |
| "multi-language", "i18n", "localization" | Framework i18n (gettext, react-intl, next-intl) | Translation management |
| "audit trail", "compliance", "history tracking" | Event sourcing or append-only log tables | Immutable traceability |
| "search", "filtering", "full-text search" | Elasticsearch / Algolia / Meilisearch | Search performance at scale |
| "encryption", "PII", "sensitive data", "GDPR" | AES-256, bcrypt, Vault/KMS, field-level encryption | Security compliance |
| "PDF generation", "reports", "invoices" | DomPDF / Puppeteer / WeasyPrint / TCPDF | Document rendering |
| "email notifications", "transactional email" | SES / SendGrid / Mailgun + queue | Reliable delivery |
| "SFTP", "file transfer", "EDI", "partner integration" | phpseclib / paramiko / SFTP client + batch job | B2B file exchange |
| "role-based access", "admin panel", "permissions" | RBAC middleware, admin framework (Filament/AdminBro) | Authorization layer |
| "iOS and Android", "cross-platform mobile", "single codebase" | Flutter (Dart) or React Native (TypeScript) | Cross-platform mobile |
| "native iOS", "Swift", "Apple", "ARKit", "HealthKit" | Swift + SwiftUI/UIKit + Xcode | iOS-exclusive APIs or App Store focus |
| "native Android", "Kotlin", "Google Play", "Jetpack" | Kotlin + Jetpack Compose + Android Studio | Android-exclusive APIs or Play Store focus |
| "barcode scan", "camera", "NFC", "biometrics", "GPS" | Flutter (camera/NFC plugins) or Native SDK | Hardware access requirements |
| "push notifications", "FCM", "APNs" | Firebase Cloud Messaging + APNs | Mobile push delivery |
| "offline-first", "local database", "sync" | SQLite (Drift/sqflite) or Hive/Isar + sync layer | Connectivity-resilient architecture |
| "app store", "play store", "OTA updates" | Flutter + CodePush / EAS Update, or native CI/CD | Mobile distribution pipeline |
| "deep links", "universal links", "app links" | Flutter go_router / iOS Universal Links / Android App Links | Cross-platform navigation |

---

### 3D. Compose Structured Recommendation

Present the recommendation as a **formatted table with confidence levels and rationale**, not a text paragraph:

```
Based on analysis of [N] SRS documents, [N] project files, and [N] infrastructure files:

| Layer | Technology | Version | Confidence | Source | Rationale |
|-------|-----------|---------|------------|--------|-----------|
| Language | PHP | 8.2 | High | composer.json | Existing project dependency |
| Framework | Laravel | 11 | Medium | SRS | "REST API" + "queue" requirements |
| Database | PostgreSQL | 16 | High | docker-compose.yml | DB service defined |
| ORM | Eloquent | - | High | composer.json | Laravel default, present in deps |
| Frontend | React | 18 | Medium | SRS | "interactive dashboard" requirement |
| Build Tool | Vite | 5 | Low | Inferred | Modern default for React |
| Infra | AWS ECS Fargate | - | High | taskdef.json | Task definition present |
| Cache | Redis | 7 | High | docker-compose.yml | Redis service defined |
| Search | Elasticsearch | 8 | Medium | SRS | "full-text search" requirement |

Sources analyzed: CR5-Requirement-Specification.md, composer.json, Dockerfile, docker-compose.yml
```

---

### 3E. Iterative Confirmation

Use `vscode_askQuestions` with **multi-select** so the user can pinpoint exactly what to change:

```
Q1: "Here's the recommended stack. Select any items you want to change (or select 'All looks good'):"
Options (multiSelect):
  - "Language: PHP 8.2"
  - "Framework: Laravel 11"
  - "Database: PostgreSQL 16"
  - "ORM: Eloquent"
  - "Frontend: React 18 + Vite"
  - "Infrastructure: AWS ECS Fargate"
  - "Cache: Redis 7"
  - "Search: Elasticsearch 8"
  - "All looks good ✅" (recommended)
```

**If user selects "All looks good":**
→ Proceed to **Generation Phase**

**If user selects specific items to change:**
→ For each selected item, ask a follow-up freeform question:
```
"What should [Layer: Current Choice] be instead? (e.g., 'MySQL 8' or 'MongoDB 7')"
```
→ Incorporate all modifications into the technology profile
→ Proceed to **Generation Phase**

---

### 3F. Fallback: Zero-Signal SRS (Greenfield Project)

If the SRS has **no tech clues** AND **no project files exist** (truly greenfield):

Use `vscode_askQuestions` to gather minimum viable context:

```
Q1: "What type of application is this?"
    Options: ["Web application", "REST/GraphQL API backend", 
              "Mobile app (cross-platform — Flutter/React Native)",
              "Mobile app (native iOS — Swift)",
              "Mobile app (native Android — Kotlin)",
              "Mobile app + Web (full stack)",
              "CLI / Data pipeline", "Desktop application", "Microservices"]

Q2: "What scale do you expect?"
    Options: ["Small (< 1K users)", "Medium (1K–100K users)", 
              "Large (100K–1M users)", "Enterprise (1M+ users)"]

Q3: "Does your team have experience with any language/framework?"
    (freeform — e.g., "We know Python and React", "No preference")

Q4: "Any infrastructure constraints?"
    Options: ["AWS", "GCP", "Azure", "Vercel/Netlify", "On-premise/Docker", "No preference"]
```

From these answers, compose a technology recommendation using sensible defaults:

| App Type + Scale | Default Stack |
|-----------------|---------------|
| Web app, small/medium | Next.js (TypeScript) + PostgreSQL + Prisma + Vercel |
| Web app, large/enterprise | Laravel/Django + PostgreSQL + Redis + AWS ECS |
| API backend, any scale | Express/Fastify (TS) or Laravel + PostgreSQL + Redis |
| Mobile cross-platform, small/medium | Flutter (Dart) + Firebase (Auth/Firestore/FCM) + Cloud Functions |
| Mobile cross-platform, large/enterprise | Flutter (Dart) + REST/GraphQL API backend + PostgreSQL + Redis + S3 + FCM |
| Mobile native iOS | Swift + SwiftUI + Core Data/Realm + CloudKit or custom API backend |
| Mobile native Android | Kotlin + Jetpack Compose + Room + Firebase or custom API backend |
| Mobile + Web (full stack) | Flutter (mobile) + Next.js/React (web) + shared API (NestJS/Laravel) + PostgreSQL |
| CLI / Data pipeline | Python + SQLite/PostgreSQL + Click/Typer |
| Microservices | Go or Node.js + PostgreSQL + RabbitMQ/SQS + K8s |

Present recommendation → user confirms or modifies → proceed to **Generation Phase**

---

## Generation Phase: Create Both Skill Files

### Pre-Generation: Discover Project Structure
Before generating, scan the workspace to understand the actual directory layout:
```
list_dir: project root
list_dir: src/ (or app/, lib/, etc.)
grep_search: "composer.json" OR "package.json" OR "requirements.txt" OR "go.mod" OR "Cargo.toml"
```

Read the main dependency file to confirm versions and dependencies.

### File 1: `core-essentials.md`

**Target path:** `.github/skills/core-essentials.md`
**Size target:** ~50-70 lines (compact, auto-loaded every task)

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

### File 2: `core-full.md`

**Target path:** `.github/skills/core-full.md`
**Size target:** ~200-250 lines (comprehensive reference)

**Required sections (in order):**

```markdown
---
name: "Core Architecture"
role: "Foundational {Framework} architecture rules, technical stack, and critical constraints"
primary_tools: [grep_search, list_dir, read_file]
scope: "{primary_source_directory}/"
---

# {Project/Framework Name} Core Principles & Architecture

## Role

I am a **Principal Software Engineer and PR Reviewer** specializing in {Framework/Stack}.

**Core Responsibilities:**
- Architecture guidance using {framework}-specific patterns
- Code quality enforcement ({coding standard})
- Security assessment ({relevant threats})
- Performance optimization ({relevant concerns})
- Testing strategy ({test types})

---

## Technical Stack

**Framework:** {name and version}
**Language:** {language and version}
**Database:** {DB and version}
**ORM:** {ORM and version}
**Templating:** {template engine if applicable}
**DI:** {dependency injection mechanism}

### Directory Structure
{Detailed ASCII tree with annotations}

### Request Flow
{Detailed ASCII diagram of request lifecycle}

---

## {Deployment/Infrastructure} Architecture

{ASCII diagram of production architecture}
{Cloud services, containers, databases, caches, CDN, etc.}

**Key Services:**
{Bulleted list of infrastructure components}

---

## Edge Cases

### 1. {Domain-Specific Edge Case}
**Issue:** {description}
**Solution:** {approach}
**Pattern:** {pattern name}

### 2. {Performance Edge Case}
**Issue:** {description}
**Solution:** {approach}
**Pattern:** {pattern name}

### 3. {Integration Edge Case}
**Issue:** {description}
**Solution:** {approach}
**Pattern:** {pattern name}

### 4. {Data/State Edge Case}
**Issue:** {description}
**Solution:** {approach}
**Pattern:** {pattern name}

---

## Critical Rules (NEVER VIOLATE)

{Same rules as core-essentials.md, expanded with more detail — 7-9 rules}

---

## Pre-Implementation Check (MANDATORY)

**BEFORE any code changes:**

### Step 1: Context Discovery
{4-5 search/check actions specific to the framework}

### Step 2: Compliance Check
{5-6 checkbox items for validation}

### Step 3: Implementation Plan
{4 planning steps}

### Step 4: Execute with Validation
{CLI commands for cache, tests, static analysis}

---

## Business Logic Patterns

### {Domain Pattern 1 — e.g., Order Processing, Data Pipeline, API Design}
{4-5 bullet points of best practices}

### {Domain Pattern 2}
{4-5 bullet points}

### {Domain Pattern 3}
{4-5 bullet points}

### {Domain Pattern 4}
{4-5 bullet points}

---

## Naming Conventions

{Full naming convention table with pattern → example format}

---

## Standard Rule Categories

### Coding Convention
{4-5 rules}

### Security
{4-5 rules}

### Performance
{4-5 rules}

### Code Quality
{4-5 rules}

### Architecture
{4-5 rules}

---

## Validation Commands

{6-8 CLI commands with comments explaining each}

---

## Implementation Workflow

{ASCII flow diagram: Request → Discovery → Plan → Execute → Validate → Report}

{Link back to related skills}
```

---

## Post-Generation Checklist

After generating both files:

1. **Validate format** — Ensure YAML frontmatter has `name`, `role`, `scope` (and `primary_tools` for core-full)
2. **Verify consistency** — Critical rules must match between both files
3. **Check paths** — `scope` field must reference actual project directories
4. **Confirm placement** — Files are at `.github/skills/core-essentials.md` and `.github/skills/core-full.md`
5. **Generate `core-essentials.instructions.md`** — See below
6. **Update `copilot-instructions.md` Critical Rules** — Replace project-specific rules with new project's rules
7. **Update individual skill files** — See "Post-Generation Step: Update Individual Skill Files" below
8. **Summary** — Tell the user what was generated and suggest they review the files

---

## Post-Generation Step: Generate `core-essentials.instructions.md`

After generating `core-essentials.md` and `core-full.md`, also generate the VS Code instructions file that auto-loads core rules when editing project source files.

**Target path:** `.github/instructions/core-essentials.instructions.md`

### Template

```markdown
---
applyTo: "{source_directories_glob}"
---

# {Project/Framework Name} Core Essentials (Auto-Loaded)

{Copy the "Critical Rules" section from core-essentials.md — same ❌/✅ rules}
```

### `applyTo` Pattern Rules

Derive the `applyTo` glob from the project's source directories discovered during generation:

| Project Type | Typical `applyTo` Pattern |
|-------------|--------------------------|
| EC-Cube | `app/Customize/**,app/Plugin/**,app/config/**,app/template/**` |
| Laravel | `app/**,config/**,routes/**,resources/**,database/**` |
| Next.js | `src/**,app/**,pages/**,components/**,lib/**` |
| Django | `apps/**,config/**,templates/**,static/**` |
| Express/NestJS | `src/**,lib/**,config/**` |
| Flutter | `lib/**,test/**` |
| Spring Boot | `src/main/**,src/test/**` |
| Generic | `src/**` |

### Update `copilot-instructions.md` Critical Rules

Replace the **Critical Rules** section at the bottom of `copilot-instructions.md` with rules derived from the new `core-essentials.md`. These should be the 3-5 most important rules from the new project.

---

## Post-Generation Step: Update SKILL.md

After generating core files, update the SKILL.md master index:

1. **Header description** — Replace `EC-Cube Agent Skills` with `{Project Name} Agent Skills` (line ~10)
2. **Core Principles section** — Update the description to reference the new framework/stack
3. **Verify entry #19** (`init-core`) is present in the All Available Skills table

---

## Post-Generation Step: Update Individual Skill Files

After updating SKILL.md, update each of the following skill files with project-specific data derived from the generated `core-essentials.md`. Use `replace_string_in_file` for each targeted section.

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
✅ Generated 3 core skill files + updated 6 individual skill files:

1. **core-essentials.md** (~{N} lines) — Auto-loaded rules, directories, conventions
2. **core-full.md** (~{N} lines) — Full architecture, edge cases, patterns
3. **core-essentials.instructions.md** — VS Code auto-loader (applyTo: {pattern})

🔧 Updated individual skill files:
4. **testing/SKILL.md** — scope, title, file classification table, run commands
5. **feature-development/SKILL.md** — scope, title, Standard Feature Structure
6. **change-request/SKILL.md** — scope, title, migration approach
7. **bug-fixing/SKILL.md** — scope, role, title
8. **refactoring/SKILL.md** — scope, role, title
9. **investigation/SKILL.md** — scope, role, title

📁 Location: `.github/skills/` and `.github/instructions/`
🔄 Updated: `copilot-instructions.md` Critical Rules, `SKILL.md` header

Please review all files and adjust any rules or conventions to match your team's preferences.
```

---

## Key Principles for Generation

1. **Be specific, not generic** — Rules must reference actual framework APIs, not vague best practices
2. **Use real paths** — Directory structures must match the actual project layout
3. **Framework-idiomatic** — Patterns must follow the framework's recommended approach (e.g., Laravel uses Eloquent, not raw PDO)
4. **Actionable rules** — Every rule should be something an AI agent can verify programmatically
5. **Correct versions** — Read `composer.json`, `package.json`, etc. to get actual versions
6. **No placeholder text** — Every section must contain real, usable content
7. **Match existing format exactly** — YAML frontmatter, markdown headers, ASCII diagrams, emoji markers (❌/✅) must follow the template structure shown above
