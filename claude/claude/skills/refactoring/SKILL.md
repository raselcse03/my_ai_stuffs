---
name: refactoring
description: "Improves existing EC-Cube code structure — extracts services, replaces raw SQL, reduces cyclomatic complexity — without changing behavior. Use when code works but needs structural cleanup. Triggered by the [Refactor] tag or /refactor."
---

# EC-Cube Code Refactoring Skill

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

## When to Use

- Fat Controllers with embedded business logic
- Raw SQL queries that should use Doctrine ORM
- Tight coupling between components
- Duplicated code across multiple files
- Legacy procedural code in OOP codebase

## Expected Outcome

- Services extracted to `app/Customize/Service/`
- Controllers thin (max 50 lines per method)
- Database queries in Repository classes
- Business logic properly unit tested
- Dependencies injected via constructor

---

## Execution Process

### 1. Analyze
**Identify refactoring targets:**
- Controllers with business logic
- Direct EntityManager usage in controllers
- Raw SQL queries
- Duplicated code patterns
- Complex conditional logic

**Tools:**
```bash
# Find fat controllers
grep -r "entityManager" app/Customize/Controller/

# Find raw SQL
grep -r "->query(" app/Customize/

# Find duplication
vendor/bin/phpcpd app/Customize/
```

### 2. Extract Business Logic to Services

**Pattern:** Fat Controller → Thin Controller + Service
- Move business logic from Controller methods to `Customize\Service\{Name}Service`
- Controller only orchestrates: parse request → call service → render response
- Service handles: validation, business rules, DB operations (within transactions)
- Register service in `app/config/eccube/services.yaml`
- Target: controller methods < 50 lines

### 3. Replace Raw SQL with Query Builder

**Never:** `"SELECT * FROM dtb_product WHERE name LIKE '%{$keyword}%'"`  
**Always:** `$qb->where('p.name LIKE :keyword')->setParameter('keyword', '%'.$keyword.'%')`

Extract complex queries into Repository methods.

### 4. Extract Strategy Pattern for Complex Conditionals

When you see long if/elseif chains on the same field → create interface + strategy classes.

### 5. Verify

```bash
bin/console cache:clear && bin/phpunit
```

---

## Validation Checklist

- [ ] Business logic in service layer (not controllers)
- [ ] All queries parameterized (no SQL concatenation)
- [ ] Dependencies injected via constructor
- [ ] Controller methods < 50 lines
- [ ] No code duplication
- [ ] `bin/console cache:clear` + `bin/phpunit` pass

---

## Key Refactoring Patterns

| Pattern | When to Use | Target Location |
|---------|-------------|-----------------|
| Service Extraction | Business logic in controller | `Customize\Service\` |
| Repository Method | Complex queries in services | `Customize\Repository\` |
| Event Dispatcher | Cross-cutting concerns (email, logging, analytics) | `Customize\EventListener\` |
| Decorator | Modify core service behavior | `Customize\Service\` + services.yaml `decorates:` |

---

## Return Contract

After completing the refactor, return **only**:
1. **What improved** — 1-sentence summary of the structural change
2. **Files changed** — list of file paths modified (no raw content)
3. **Verification** — all tests still pass, no regressions

Do NOT paste full file contents or unchanged code blocks in the response.

---

## Related Skills

- **`core-essentials`** - Critical rules and patterns
- **`testing`** - Write tests for refactored code
- **`code-review`** - Review refactored code quality
