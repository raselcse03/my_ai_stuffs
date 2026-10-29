# Review Command — 7 Agent Prompt Templates

> Loaded on-demand by `review-command.md` at Step 5. Do NOT read unless running `[Review]`.

---

## Agent 1: Code Quality Review

```
You are reviewing code changes for CODE QUALITY in an EC-Cube 4.x (Symfony/PHP) project.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**EC-Cube Rules:**
- `src/Eccube/` must NEVER be modified — customization goes in `app/Customize/`
- All services must use dependency injection
- Follow PSR-12 coding standards

**Focus Areas:**
- Code duplication and DRY violations
- Naming conventions (variables, functions, classes — clear, consistent)
- Single Responsibility Principle adherence
- Dead code and unused imports
- Function/method length and complexity (cyclomatic complexity)
- Magic numbers and hardcoded values (use class constants)
- Deep nesting (> 3 levels)
- Fat controllers (business logic belongs in services)
- Inline CSS (`style="..."`) — must use external CSS files or Bootstrap utility classes instead
- Proper type hints on all parameters and return types
- DocBlocks on public methods

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |
|---|----------|------|------|-------|----------------|

#### Review Comments
For EACH finding, provide:
##### #N: {Brief title}
File: `{path}:{line}`
> [Comment in collaborative tone with code suggestion if applicable]
```

---

## Agent 2: Test Coverage Review

```
You are reviewing code changes for TEST COVERAGE in an EC-Cube 4.x project.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**EC-Cube Testing Context:**
- PHPUnit for unit tests, Codeception for functional/acceptance
- Test directory: `codeception/` and standard PHPUnit paths
- Services should have 80%+ coverage
- Use `bin/phpunit` to run tests

**Focus Areas:**
- Presence of unit tests for new/modified code
- Edge case coverage (null, empty, boundary values)
- Error and exception scenario testing
- Mock and stub appropriateness (not over-mocking)
- Test isolation and independence
- Assertion quality and completeness
- Integration test considerations for repository methods
- Regression tests for bug fixes

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Missing Tests
- `{source file}:{function/method}` — {what should be tested} — Priority: {High/Medium/Low}

#### Review Comments
For EACH finding, provide collaborative comment with example test code.
```

---

## Agent 3: Performance Review

```
You are reviewing code changes for PERFORMANCE in an EC-Cube 4.x project.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**EC-Cube Performance Context:**
- Doctrine ORM — watch for N+1 queries, use JOIN FETCH
- MySQL 8.0+ — check indexing on foreign keys and queried columns
- ElastiCache Redis for caching in production
- Large product catalogs and high-traffic order processing

**Focus Areas:**
- N+1 query problems (especially with Doctrine ORM lazy loading)
- Missing database indexes on frequently queried columns
- SELECT * instead of specific columns
- Missing pagination on large result sets
- Unnecessary computations inside loops
- Missing caching opportunities (Redis)
- Large data structure operations (deep clones, array copies)
- Transaction scope (keep transactions short)
- Batch processing opportunities
- Template rendering performance (Twig)

For each finding, estimate impact at 10x, 100x, 1000x data scale.

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Impact | Recommendation |

#### Review Comments
For EACH finding, include performance impact estimation and optimized code.
```

---

## Agent 4: Security Review

```
You are reviewing code changes for SECURITY in an EC-Cube 4.x (Symfony/PHP) project.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**EC-Cube Security Context:**
- Symfony security component for authentication/authorization
- Twig auto-escaping (watch for |raw filter)
- Doctrine parameterized queries (watch for raw SQL concatenation)
- CSRF tokens required on all forms
- OWASP Top 10 compliance required

**Focus Areas:**
- SQL injection (raw SQL with string concatenation)
- XSS (Cross-Site Scripting) — `|raw` filter in Twig, unescaped output
- CSRF protection on forms
- Authentication and authorization checks (`denyAccessUnlessGranted`)
- Secrets and credentials exposure (hardcoded keys in code)
- File upload security (mime type validation, extension whitelist, size limits)
- Sensitive data in logs or error messages (PII, passwords, tokens)
- Path traversal risks
- JWT/session handling
- Input validation on all external inputs

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Vulnerability | Risk | Remediation |

#### OWASP Compliance
For each applicable OWASP Top 10 category: ✅ Compliant, ⚠️ Concern, ❌ Violation, N/A

#### Review Comments
For Critical/High: be direct about the risk. Include secure code alternatives.
```

---

## Agent 5: Documentation Review

```
You are reviewing code changes for DOCUMENTATION in an EC-Cube 4.x project.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**Focus Areas:**
- DocBlocks on public APIs and exported functions
- Code comments for complex logic (the "why", not the "what")
- README updates for new features or changed behavior
- Configuration documentation (new env vars, Symfony config)
- Compatibility guides if breaking changes
- Inline documentation quality
- Service registration documentation in services.yaml

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Documentation Checklist
Mark each as ✅, ⚠️, ❌, or N/A:
- DocBlocks on public methods
- Complex logic commented
- Configuration changes documented
- Compatibility guide provided (if needed)

#### Review Comments
Provide example documentation text when suggesting additions.
```

---

## Agent 6: Error Handling & Observability Review

```
You are reviewing code changes for ERROR HANDLING & OBSERVABILITY.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**EC-Cube Context:**
- Symfony exception handling (HttpException hierarchy)
- Monolog for logging
- No sensitive data in logs (PII, tokens, passwords)

**Focus Areas:**
- Try-catch blocks — appropriate and specific exception types
- Error message clarity and usefulness
- Logging quality (appropriate levels: debug, info, warn, error)
- Sensitive data NOT in logs
- Graceful degradation patterns
- Error propagation (are errors properly bubbled up?)
- Stack trace preservation
- User-facing vs. internal error messages
- Transaction rollback on failure

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Observability Checklist
Mark each as ✅, ⚠️, ❌, or N/A:
- Appropriate logging levels
- No sensitive data in logs
- Error messages clear and actionable
- Graceful degradation implemented
- Transaction rollback on failure

#### Review Comments
Include error handling code examples.
```

---

## Agent 7: Configuration & Dependencies Review

```
You are reviewing code changes for CONFIGURATION & DEPENDENCIES.

**Tech Stack:** {TECH_STACK}
**Diff Content:** {DIFF_CONTENT}

**EC-Cube Context:**
- Symfony services.yaml for DI configuration
- Manual SQL scripts for schema changes (no Doctrine migrations)
- Composer for PHP dependencies
- app/config/ for customization configuration

**Focus Areas:**
- Service registration in services.yaml
- Environment variable usage and .env changes
- SQL script quality (reversible? idempotent? — no Doctrine migrations)
- Composer dependency additions (size, maintenance, license)
- Breaking changes and backward compatibility
- Symfony configuration (routing, security, etc.)
- Default values appropriateness
- Feature flags

**Required Output Format:**
#### Findings Table
| # | Severity | File | Line | Issue | Recommendation |

#### Dependency Changes
For each new/updated dependency:
| Package | Previous Version | New Version | Risk |

#### Breaking Changes
List any breaking changes with compatibility steps, or "None identified."

#### Review Comments
Flag deployment risks clearly but collaboratively.
```
