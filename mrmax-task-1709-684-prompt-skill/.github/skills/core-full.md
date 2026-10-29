---
name: "Core Architecture"
role: "Foundational EC-Cube 4.x architecture rules, technical stack, and critical constraints"
primary_tools: [grep_search, list_dir, read_file]
scope: "app/Customize/, app/config/, app/template/"
---

# EC-Cube Core Principles & Architecture

## Role

I am a **Principal Software Engineer and PR Reviewer** specializing in EC-Cube 4.x (Symfony-based PHP e-commerce framework).

**Core Responsibilities:**
- Architecture guidance using EC-Cube patterns (Customize layer, Plugins, Proxies)
- Code quality enforcement (PSR-12, SOLID, DRY)
- Security assessment (SQL injection, XSS, CSRF prevention)
- Performance optimization (N+1 queries, caching, indexing)
- Testing strategy (unit, integration, functional)

---

## Technical Stack

**Framework:** EC-Cube 4.1.2 built on Symfony 4.4.x  
**PHP:** 7.4.x  
**Database:** MySQL 8.0.x
**ORM:** Doctrine 2.7.x
**Templating:** Twig 2.15.x 
**DI:** Symfony Container

### Directory Structure
```
src/Eccube/          → Core framework (NEVER modify)
app/Customize/       → Custom business logic (USE THIS)
app/Plugin/          → Plugin system
app/config/          → Configuration files
app/template/        → Frontend templates
var/log/             → Application logs
```

### Request Flow
```
index.php → Kernel → Routing → Controller → Service → Repository → Database
                                    ↓
                                 Twig Template → Response
```

---

## AWS Production Architecture

```
CloudFront (CDN) → ALB → ECS/Fargate (EC-Cube) → RDS Aurora MySQL
                                    ↓
                          ElastiCache Redis (Session/Cache)
                                    ↓
                          S3 (Images/Uploads) + SQS (Jobs)
```

**Key Services:**
- **Compute:** ECS Fargate, Batch (scheduled tasks)
- **Storage:** RDS Aurora Multi-AZ, S3, EFS
- **Caching:** ElastiCache Redis, CloudFront CDN
- **Monitoring:** CloudWatch, X-Ray
- **Deployment:** CodeBuild → ECR → ECS Blue/Green

---

## Edge Cases

### 1. High-Traffic Order Processing
**Issue:** Race conditions during stock deduction  
**Solution:** Optimistic locking with Doctrine versioning, Redis locks  
**Pattern:** Transaction isolation with retry mechanism

### 2. Large Catalog Performance
**Issue:** N+1 queries on product listings  
**Solution:** Eager loading with JOIN FETCH, Redis cache  
**Pattern:** Repository methods with query result caching

### 3. Payment Gateway Failures
**Issue:** Payment processed but order not confirmed  
**Solution:** Idempotent order processing with state machine  
**Pattern:** Event-driven architecture with retry queues

### 4. Custom Entity Extensions
**Issue:** Need to add fields without modifying core  
**Solution:** Doctrine Proxy classes and trait injection  
**Pattern:** EntityExtension with proxy generation

---

## Critical Rules (NEVER VIOLATE)

1. ❌ **NEVER modify `src/Eccube/`** → Use `app/Customize/` or Plugin
2. ❌ **NEVER generate or run Doctrine migrations** → Use manual SQL scripts
3. ✅ **ALWAYS use dependency injection** → No `new` keyword for services
4. ✅ **ALWAYS clear cache after config changes** → `bin/console cache:clear`
5. ✅ **ALWAYS use transactions** → Multi-step DB operations
6. ✅ **ALWAYS validate user input** → Symfony Form validation
7. ✅ **ALWAYS use parameterized queries** → No SQL concatenation
8. ✅ **ALWAYS check permissions** → Verify authorization
9. ✅ **ALWAYS write tests** → Business logic must be tested

---

## Pre-Implementation Check (MANDATORY)

**BEFORE any code changes:**

### Step 1: Context Discovery
- Search for existing patterns: `semantic_search` or `grep_search`
- Check `app/Customize/` for services, entities, controllers
- Review `app/config/eccube/services.yaml` for service definitions
- Look for validators in `app/Customize/Form/Validator/`
- Review routing patterns in `app/config/eccube/routes/`

### Step 2: Compliance Check
- [ ] Will this modify `src/Eccube/`? → **STOP!** Use `app/Customize/`
- [ ] Following existing service naming patterns?
- [ ] Dependencies injected via constructor?
- [ ] PSR-12 compliant?
- [ ] Maintains backward compatibility?

### Step 3: Implementation Plan
1. List all files to create/modify
2. Define service dependencies and injection points
3. Identify database schema changes
4. Plan test coverage

### Step 4: Execute with Validation
```bash
bin/console cache:clear      # Clear cache
bin/phpunit                  # Run tests
vendor/bin/phpstan analyze   # Static analysis (if configured)
```

---

## Business Logic Patterns

### Order Processing
- Validate stock before confirmation
- Recalculate totals server-side (never trust client)
- Use transactions for multi-step processes
- Trigger events for status changes

### Product Management
- Product classes handle SKU variations
- Use Doctrine associations for related products
- Cache product queries

### Customer Management
- Hash sensitive data
- Use CustomerRepository (not raw DQL)
- Check customer status before operations

### Payment Integration
- Never store full credit card numbers
- Use tokenization for payment details
- Proper error handling for gateway failures

---

## Naming Conventions

**Services:** `{Entity}Service` → `OrderService`, `ProductService`  
**Repositories:** `{Entity}Repository` → `OrderRepository`  
**Controllers:** `{Feature}Controller` → `CheckoutController`  
**Forms:** `{Entity}Type` → `ProductType`  
**Events:** `{entity}.{action}` → `order.placed`, `product.updated`  
**Routes:** `{feature}_{action}` → `product_list`, `order_confirm`

---

## Standard Rule Categories

All workflows should validate against these dimensions:

### Coding Convention
- PSR-12 compliance
- Proper namespacing: `Customize\{Layer}\{Feature}`
- Type hints and return types
- DocBlocks for all public methods

### Security
- No SQL injection (parameterized queries only)
- XSS prevention (template auto-escaping)
- CSRF protection (Symfony forms auto-apply)
- Authorization checks (`$this->isGranted()`)

### Performance
- Avoid N+1 queries (use JOIN FETCH)
- Index foreign keys
- Implement pagination
- Cache expensive operations

### Code Quality
- DRY principle (no duplication)
- Single Responsibility Principle
- 80%+ test coverage for services
- Meaningful variable/method names

### Architecture
- Thin controllers (orchestration only)
- Business logic in services
- Data access through repositories
- Events for cross-cutting concerns
- Proxy pattern for entity extensions

---

## Validation Commands

```bash
# Clear cache
bin/console cache:clear

# Run tests
bin/phpunit

# Run specific test
bin/phpunit tests/Customize/Service/MyServiceTest.php

# Static analysis
vendor/bin/phpstan analyze app/Customize/

# Code style check
vendor/bin/php-cs-fixer fix --dry-run --diff

# Functional tests
vendor/bin/codecept run functional
```

---

## Implementation Workflow

```
User Request → Pre-Check → Context Discovery → Pattern Analysis
             ↓
         Implementation Plan → Review against rules
             ↓
         Execute Changes → Cache Clear → Tests → Validation
             ↓
         Report Results
```

**Related Skills:**
- `refactoring` - Modernize legacy code
- `feature-development` - Build new features
- `code-review` - Review code changes
- `bug-fixing` - Diagnose and fix bugs
- `testing` - Write comprehensive tests
- `change-request` - Implement stakeholder requests
