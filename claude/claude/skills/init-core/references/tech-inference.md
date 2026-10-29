# Step 3: SRS-Based Technology Inference (3A–3F)

Full Step 3 machinery — loaded by `init-core` SKILL.md Step 3 only when the user chose "No, suggest based on our SRS" in Step 1.

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

Use `AskUserQuestion` with **multi-select** so the user can pinpoint exactly what to change:

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

Use `AskUserQuestion` to gather minimum viable context:

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
