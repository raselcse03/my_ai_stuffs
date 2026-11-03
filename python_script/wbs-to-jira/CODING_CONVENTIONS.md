# MrMax Coding Conventions

## 1. Scope and Architecture

This project follows EC-CUBE extension architecture.

- Do custom development in `app/Customize/`, `app/Plugin/`, `app/config/`, and `app/template/`.
- Do not modify `src/Eccube/` directly.
- Keep controllers thin; place business logic in service classes.
- Use repositories for data access and services for orchestration.

## 2. Non-Negotiable Rules

- Never modify `src/Eccube/`.
- Never generate or run Doctrine migrations in this project.
- Use manual SQL scripts for schema changes.
- Use dependency injection (constructor injection) for services.
- Use parameterized queries; never concatenate SQL strings.
- Validate input at system boundaries.
- Use transactions for multi-step write operations.
- Clear cache after configuration changes.

## 3. Directory and Layer Conventions

- Controllers: `app/Customize/Controller/`
- Services: `app/Customize/Service/`
- Repositories: `app/Customize/Repository/`
- Entities: `app/Customize/Entity/`
- Form Types / Validators: `app/Customize/Form/`
- Templates: `app/template/`
- Service wiring: `app/config/eccube/services.yaml`
- Security/firewall config: `app/config/eccube/packages/security.yaml`

## 4. Naming Conventions

- Service class: `{Domain}Service`
- Repository class: `{Domain}Repository`
- Controller class: `{Feature}Controller`
- Form class: `{Domain}Type`
- Route name: `{scope}_{feature}_{action}`

Examples:

- `SpFileDownloadService`
- `VpointRedeemResultRepository`
- `SpFileDownloadController`

## 5. Controller Conventions

- Keep controller responsibilities limited to:
  - authentication/authorization checks
  - request parsing
  - service delegation
  - HTTP response mapping
- Do not implement storage orchestration, heavy branching logic, or data workflows in controllers.
- For API endpoints, return deterministic status codes and response structure.

## 6. Service Conventions

- Service classes own business workflows and external storage/API orchestration.
- Keep service methods explicit and testable.
- Prefer small, focused methods for each workflow stage.
- Log meaningful context on failure paths.
- If failure should not block primary response, log and continue explicitly.

## 7. Security Conventions

- Keep sensitive values in environment variables.
- Use constant-time comparisons for credential checks.
- For firewall patterns, prefer exact route matching if endpoint must be isolated.
  - Example: `^/api/v1/vpoint/sp-file/download$`
- Do not allow accidental prefix route bypass for `security: false` firewalls.

## 8. Data and SQL Conventions

- Use Doctrine repositories/query builder where possible.
- Use parameter binding in all queries.
- No raw interpolated SQL.
- For schema evolution:
  - manual SQL only
  - no generated migrations under `app/DoctrineMigrations/`

## 9. API Conventions

- Standard API error format:

```json
{
  "error": {
    "message": "..."
  }
}
```

- Use consistent HTTP status semantics:
  - 200: success with payload
  - 204: success with no payload
  - 400: bad request
  - 401: auth failure
  - 403: forbidden
  - 500: internal failure
  - 503: temporary service unavailability

## 10. S3/File Handling Conventions

- Treat S3 paths as object keys; folders are virtual prefixes.
- Avoid folder marker files unless required by external integration.
- Use project FileService abstraction for reads/writes/deletes.
- For backup workflow, keep deterministic path format:
  - `backup/SPyyyymmdd/{filename}`

## 11. Logging Conventions

- Use structured context in logs (`file`, `source`, `backup`, `error`, `ip`, etc.).
- Log at appropriate level:
  - `info` for lifecycle milestones
  - `warning` for invalid requests/auth attempts
  - `error` for operation failure
  - `critical` for misconfiguration/security-impacting issues

## 12. Test Conventions

### 12.1 Location and Namespace

Mirror source path under `tests/Customize/`.

- Source: `app/Customize/Service/Vpoint/SpFileDownloadService.php`
- Test: `tests/Customize/Service/Vpoint/SpFileDownloadServiceTest.php`

### 12.2 Test Type Selection

- `app/Customize/Common/`, `Entity/`: pure unit tests
- `app/Customize/Service/`: unit or integration depending on dependencies
- `app/Customize/Repository/`: integration tests
- `app/Customize/Controller/Api/`: integration tests in full stack; unit tests only for isolated logic/delegation
- `app/Customize/Command/`: kernel/integration tests

### 12.3 Naming Pattern

- Method naming: `test{Method}_{Scenario}`
- Cover:
  - happy path
  - edge cases
  - error paths

## 13. Branch, Commit, and PR Conventions

### 13.1 Branch

Format:

- `(feat|fix|revert)/{ticketid}-short-title`

### 13.2 Commit Message

Format:

- `(revert: )?(feat|fix|docs|dx|refactor|perf|test|workflow|build|ci|chore|types|wip|release|deps)(scope)?: summary`

### 13.3 Pull Request Title

Format:

- `(feat|fix|revert|chore|refactor|cr|ut|doc)/{ticketid1},{ticketid2} summary`

## 14. Validation Commands

```bash
bin/console cache:clear
bin/phpunit
vendor/bin/phpstan analyze app/Customize/
```

## 15. Pull Request Review Checklist

- No changes in core EC-CUBE files (`src/Eccube/`).
- Controller remains thin and delegates to services.
- Service responsibilities are cohesive and test-covered.
- Security and firewall patterns are explicit and minimal.
- No SQL injection risk (parameterized queries only).
- Error handling/logging paths are explicit.
- Cache clear and tests executed for touched modules.
