---
name: feature-development
description: "Builds new EC-Cube features end-to-end following the Entity → Service → Controller → Template pattern in app/Customize/. Use when creating functionality that does not exist yet. Triggered by the [Feature] tag or /feature."
---

# EC-Cube Feature Development Skill

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

## When to Use

- Adding new functionality to EC-Cube system
- Custom product attributes or variations
- Advanced search and filtering
- Third-party API integrations (payment, shipping, CRM)
- Custom reporting and analytics
- Admin dashboard widgets

## Expected Outcome

- Complete feature module: Entity, Repository, Service, Controller, Form, Template
- Database schema changes via manual SQL scripts (no migrations)
- Proper routing and admin integration
- Comprehensive test coverage
- Documentation updated

---

## Discovery Phase (for multi-file tasks)

If the feature touches >3 existing files, dispatch an **Explore subagent** first:
1. `Agent("Explore")` — find all related entities, services, templates, and routes
2. Subagent returns: file paths + key method signatures + existing patterns
3. Implement with clean context using only the subagent's summary

This prevents context overflow on large features.

---

## Standard Feature Structure

```
app/Customize/
├── Entity/
│   └── MyFeature.php                    # Data model
├── Repository/
│   └── MyFeatureRepository.php          # Data access
├── Service/
│   └── MyFeatureService.php             # Business logic
├── Controller/
│   ├── MyFeatureController.php          # Frontend
│   └── Admin/
│       └── MyFeatureController.php      # Admin panel
├── Form/
│   └── Type/
│       └── MyFeatureType.php            # Form validation

app/template/default/MyFeature/
├── index.twig                           # List view
├── detail.twig                          # Detail view
└── edit.twig                            # Edit form

app/config/eccube/
├── routes/
│   └── my_feature.yaml                  # Route definitions
└── packages/
    └── eccube_nav.yaml                  # Admin menu (update)
```

---

## Implementation Steps

### Phase 1: Planning

**1. Define Requirements**
- Functional requirements (what it does)
- Non-functional requirements (performance, security)
- User stories and acceptance criteria

**2. Design Database Schema**
```
MyFeature Entity:
- id (PK)
- name (varchar 255)
- description (text, nullable)
- status (boolean)
- created_at (datetime)
- updated_at (datetime)
- Relations: OneToMany, ManyToOne, etc.
```

**3. Map Dependencies**
- Required services (EntityManager, Repositories)
- External APIs or libraries
- Events to trigger/listen to

---

### Phase 2: Entity & Repository

Create Entity in `app/Customize/Entity/` with ORM annotations, lifecycle callbacks (`@PrePersist`, `@PreUpdate`).
Create Repository extending `AbstractRepository` in `app/Customize/Repository/`.

**For full code templates**, see `.claude/skills/examples/feature-templates.md` → "Entity Example" and "Repository Example"

---

### Phase 3: Service Layer

Create Service in `app/Customize/Service/` with:
- Constructor injection of EntityManager + Repository
- Transaction wrapping for create/delete operations
- Business logic methods

**For full code template**, see `.claude/skills/examples/feature-templates.md` → "Service Example"

---

### Phase 4: Form & Controller

**Form Type** in `app/Customize/Form/Type/` — use Symfony constraints (`NotBlank`, `Length`, etc.)
**Controller** in `app/Customize/Controller/` — thin, delegates to service layer

**For full code templates**, see `.claude/skills/examples/feature-templates.md` → "Form Type Example" and "Controller Example"

---

### Phase 5: Configuration

1. **Routes** — `app/config/eccube/routes/{feature}.yaml`
2. **Services** — register in `app/config/eccube/services.yaml`
3. **Admin Menu** — update `app/config/eccube/packages/eccube_nav.yaml`

**For YAML templates**, see `.claude/skills/examples/feature-templates.md` → "Routes Configuration" and "Service Registration"

---

### Phase 6: Database Schema (Manual SQL Script)

> ⚠️ This project does NOT use Doctrine migrations. Apply schema changes via manual SQL scripts.

**For SQL template**, see `.claude/skills/examples/feature-templates.md` → "SQL Schema Script"

---

## Validation Checklist

### Coding Convention
- [ ] PSR-12 compliant
- [ ] Proper namespacing: `Customize\{Layer}\{Feature}`
- [ ] Type hints and return types declared
- [ ] DocBlocks for all public methods

### Security
- [ ] CSRF protection on forms (auto-applied by Symfony)
- [ ] Input validation in Form Type
- [ ] Output escaping in templates (auto-escape enabled)
- [ ] Authorization checks if needed

### Performance
- [ ] Indexes on frequently queried columns
- [ ] Lazy loading for associations
- [ ] Pagination for large result sets

### Code Quality
- [ ] 80%+ test coverage for service
- [ ] No code duplication
- [ ] Meaningful names for classes/methods

### Architecture
- [ ] Services registered in DI container
- [ ] Business logic in service layer
- [ ] Data access through repository
- [ ] Thin controllers (orchestration only)

---

## Testing the Feature

```bash
# Clear cache
bin/console cache:clear

# Run tests
bin/phpunit tests/Customize/Service/MyFeatureServiceTest.php

# Test in browser
symfony serve
# Navigate to: http://localhost:8000/my_feature
```

---

## Return Contract

After completing the feature, return **only**:
1. **What was built** — 1-sentence summary of the feature
2. **Files created/modified** — list of file paths (no raw content)
3. **Verification** — cache cleared + tests run, result (pass/fail)

Do NOT paste full file contents or unchanged code blocks in the response.

---

## Related Skills

- **`core-essentials`** - Critical rules and architecture
- **`testing`** - Write comprehensive tests
- **`code-review`** - Self-review before committing
