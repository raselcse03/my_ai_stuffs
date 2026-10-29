---
name: change-request
description: "Implements client change requests to existing features while preserving backward compatibility. Use when a stakeholder asks to modify, add, or remove behavior in an existing flow. Triggered by the [CR] tag or /cr."
---

# EC-Cube Change Request Implementation Skill

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

## When to Use

- Business rule modifications (pricing, discounts, workflows)
- UI/UX changes and template modifications
- New field additions to existing entities
- Integration with new third-party services
- Regulatory compliance updates
- Performance optimization requests

## Expected Outcome

- Complete impact assessment documented
- Backward compatibility maintained
- Database schema changes applied via manual SQL scripts (no migrations)
- All affected areas updated
- Stakeholder requirements validated
- Documentation updated

---

## Discovery Phase (for multi-file CRs)

If the CR touches >3 existing files, dispatch an **Explore subagent** first:
1. `Agent("Explore")` — map all affected entities, services, templates, and routes
2. Subagent returns: file paths + key method signatures + existing patterns
3. Implement with clean context using only the subagent's summary

This prevents context overflow on complex CRs.

---

## Implementation Process

### Phase 1: Requirements Analysis

**1. Clarify Requirements** — Meet with stakeholders, document exact needs, define success criteria, get sign-off.

**2. Create Specification Document** — For template, see `.claude/skills/examples/cr-templates.md` → "Specification Document Template"

---

### Phase 2: Impact Assessment

Assess all dimensions: Code, Database, API, Integration, Performance, Security, Risk.

**For the full impact assessment template**, see `.claude/skills/examples/cr-templates.md` → "Impact Assessment Template"

---

### Phase 3: Implementation

> ⚠️ This project does NOT use Doctrine migrations. Schema changes are applied via manual SQL scripts.

Follow this order:
1. **Database Changes** — Manual SQL script (ALTER TABLE, CREATE TABLE, indexes)
2. **Entity Extension** — Proxy pattern with `@EntityExtension` trait in `app/Customize/Entity/`
3. **New/Modified Services** — Business logic in `app/Customize/Service/`, inject via constructor
4. **Service Registration** — Update `app/config/eccube/services.yaml`
5. **Controller/Form** — Thin controllers, form validation via Symfony Form Types

**For code examples** (Entity Trait, Service, SQL, services.yaml), see `.claude/skills/examples/cr-templates.md`

---

### Phase 4: Testing

- Write unit tests in `tests/Customize/Service/`
- Mock dependencies, use AAA pattern
- Run: `bin/phpunit tests/Customize/Service/{ServiceName}Test.php`

---

### Phase 5: Documentation & Deployment

- Create technical docs in `docs/`
- Prepare deployment checklist (backup → SQL → cache clear → tests → verify)

**For documentation and deployment templates**, see `.claude/skills/examples/cr-templates.md`

---

## Backward Compatibility

### Non-Breaking Changes (Preferred)
- Add new nullable columns
- Add new routes/endpoints
- Extend existing functionality

### Breaking Changes (Requires Data Backfill)
- Rename/remove columns
- Change data types
- Modify API contracts

**For backward compatibility code pattern**, see `.claude/skills/examples/cr-templates.md`

---

## Validation Checklist

### Requirements
- [ ] All functional requirements met
- [ ] Non-functional requirements satisfied
- [ ] Acceptance criteria validated
- [ ] Stakeholder sign-off obtained

### Technical
- [ ] Code follows PSR-12
- [ ] Services properly injected
- [ ] Database schema changes applied and tested (manual SQL)
- [ ] 80%+ test coverage
- [ ] Performance benchmarked

### Security
- [ ] Input validation implemented
- [ ] Authorization checks added
- [ ] No SQL injection risks
- [ ] Security review completed

### Documentation
- [ ] Technical docs updated
- [ ] User guide created
- [ ] API docs updated
- [ ] CHANGELOG.md updated

### Deployment
- [ ] Staging deployment successful
- [ ] UAT completed
- [ ] Rollback plan documented
- [ ] Monitoring configured

---

## Return Contract

After completing the CR, return **only**:
1. **What changed** — 1-sentence summary of the implementation
2. **Files changed** — list of file paths created/modified (no raw content)
3. **Verification** — cache cleared + tests run, result (pass/fail)

Do NOT paste full file contents or unchanged code blocks in the response.

---

## Related Skills

- **`core-essentials`** - Critical rules and architecture
- **`feature-development`** - Follow development patterns
- **`testing`** - Comprehensive test coverage
- **`code-review`** - Self-review before submission
