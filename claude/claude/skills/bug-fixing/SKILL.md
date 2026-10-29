---
name: bug-fixing
description: "Diagnoses and fixes EC-Cube defects without touching core, using app/Customize/, Event Subscribers, and Repository Decorators. Use when something is broken, throws an error, or behaves unexpectedly. Triggered by the [Bug] tag or /bug."
---

# EC-Cube Bug Fixing Skill

**Prerequisites:** Review `core-essentials` for critical rules. For full architecture details, see `core-full`.

## When to Use

- Order processing failures
- Payment gateway errors
- Display issues in templates
- Data inconsistency problems
- Performance degradation

## Expected Outcome

- Root cause identified through logs/debugging
- Fix applied in `app/Customize/` (never in core)
- Regression test written to prevent recurrence
- Related areas checked for similar issues
- Documentation updated if needed

---

## Diagnostic Process

### Phase 1: Reproduce & Check Logs

1. Identify exact steps to trigger the bug
2. Check `var/log/prod.log` — grep for `ERROR`, `CRITICAL`, `Exception`
3. Note environment (dev/staging/prod) and user input that causes it

### Phase 2: Isolate Component

Identify which layer is broken:
- Controller → Service → Repository → Entity → Template → Form

### Phase 3: Search First

`Grep` for error messages, class names, and subscriber patterns before reading any files.

---

## Fix Strategies

### Strategy 1: Event Subscriber (Intercept Core Behavior)

**Use when:** Need to modify core behavior without changing core files.
- Create class in `Customize\EventListener\` implementing `EventSubscriberInterface`
- Subscribe to template events (`'Product/list.twig'`) or kernel events
- Register in `app/config/eccube/services.yaml` with `kernel.event_subscriber` tag

### Strategy 2: Service Decorator (Wrap Core Service)

**Use when:** Need to modify core service behavior.
- Create class in `Customize\Service\` extending or wrapping the core service
- Register with `decorates:` in services.yaml, inject `.inner` decorated service

### Strategy 3: Repository Override

**Use when:** Need to fix query logic.
- Extend the core repository in `Customize\Repository\`
- Override the specific method, call `parent::` then apply fix

### Strategy 4: Twig Extension (Template Bug)

**Use when:** Need to fix template rendering.
- Create extension in `Customize\Twig\Extension\` extending `AbstractExtension`

---

## Verification

1. Write a regression test in `tests/Customize/` that fails before fix and passes after
2. Run `bin/phpunit` to confirm no regressions
3. `bin/console cache:clear` and verify in browser

---

## Common Bug Patterns

| Pattern | Symptom | Fix |
|---------|---------|-----|
| N+1 Query | Slow page, many DB queries | Add JOIN FETCH to query |
| Race Condition | Intermittent failures under load | Use DB locks or transactions |
| Null Pointer | "Call to member function on null" | Add null checks + defaults |
| Cache Staleness | Old data after update | Clear cache after entity changes |
| Session Issues | User logged out unexpectedly | Check session config and Redis |

---

## Validation Checklist

- [ ] Fix uses Event Subscriber or Decorator (no `src/Eccube/` modifications)
- [ ] Minimal changes — only what's necessary
- [ ] Regression test added
- [ ] No new security vulnerabilities or N+1 queries
- [ ] `bin/console cache:clear` + `bin/phpunit` pass

---

## Return Contract

After completing the fix, return **only**:
1. **Root cause** — 1-sentence description of what was wrong
2. **Files changed** — list of file paths modified (no raw content)
3. **Verification** — command run + result (pass/fail)

Do NOT paste full file contents or unchanged code blocks in the response.

---

## Related Skills

- **`core-essentials`** - Critical rules and patterns
- **`testing`** - Write regression tests
- **`code-review`** - Self-review fix
