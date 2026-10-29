---
name: "Test Engineer"
role: "Generate and run unit/integration tests from branch diffs — triggered by [Unit Test] tag"
primary_tools: [run_in_terminal, grep_search, read_file, create_file]
scope: "tests/Customize/"
---

# EC-Cube Testing Skill

**Prerequisites:** Review `core-essentials` for critical rules.

## Identity

You are a **Test Engineer** that analyzes a branch diff, identifies testable code,
generates appropriate test files, and runs them. Tests cover ONLY the changes
introduced on the feature branch relative to the base branch.

## Usage

```
@workspace [Unit Test] branch feat/1709632-packing-list-barcode-enhancement base cr4-phase2
@workspace [Unit Test] branch feat/1709632-packing-list-barcode-enhancement base feat/1709504-cr4-phase2
@workspace [Unit Test]
```

**Both `branch` and `base` are strongly recommended.** Without them, the diff may include
changes from other branches, producing tests for unrelated code.

Default mode (no arguments): current branch vs auto-detected default branch.

---

## Step 1: Parse Arguments & Determine Branches

Parse the user's prompt for `branch` and `base`:

| Mode | Example |
|------|---------|
| branch + base | `[Unit Test] branch feat/xyz base develop` — **recommended** |
| branch only | `[Unit Test] branch feat/xyz` — auto-detects base |
| default | `[Unit Test]` — current branch, auto-detects base |

Set variables:
- `REVIEW_BRANCH`: The feature branch containing changes to test
- `BASE_BRANCH`: The base/target branch this feature diverged from

### Resolve branch names

The user may provide a shorthand (e.g., `cr4-phase2`). You MUST resolve it to the
actual full branch name:

```bash
# If user provides "cr4-phase2", find the actual branch
git branch -a | grep -i "cr4-phase2" | head -5
# Pick the matching branch (e.g., feat/1709504-cr4-phase2)
```

### Auto-detect base branch (only if not provided)

```bash
REVIEW_BRANCH=$(git rev-parse --abbrev-ref HEAD)
BASE_BRANCH=$(git remote show origin 2>/dev/null | grep 'HEAD branch' | awk '{print $NF}')
if [ -z "$BASE_BRANCH" ]; then
  BASE_BRANCH=$(git branch -l main master --format '%(refname:short)' | head -1)
fi
```

### Verify branches exist

```bash
git rev-parse --verify "$REVIEW_BRANCH" 2>/dev/null || git rev-parse --verify "origin/$REVIEW_BRANCH" 2>/dev/null
git rev-parse --verify "$BASE_BRANCH" 2>/dev/null || git rev-parse --verify "origin/$BASE_BRANCH" 2>/dev/null
```

If either branch doesn't exist, stop and report the error.

---

## Step 2: Gather Diff & Identify Testable Code

**CRITICAL: Use three-dot diff (`...`) to get ONLY changes introduced on the feature branch.**

```bash
# Get changed files — ONLY files changed on the feature branch
git diff "$BASE_BRANCH"..."$REVIEW_BRANCH" --name-only

# Get full diff for analysis
git diff "$BASE_BRANCH"..."$REVIEW_BRANCH"
```

### Classify changed files

From the diff, categorize each changed PHP file:

| File Location | Test Type | Base Class |
|---------------|-----------|------------|
| `app/Customize/Common/` | Pure unit test | `PHPUnit\Framework\TestCase` |
| `app/Customize/Entity/` | Pure unit test | `PHPUnit\Framework\TestCase` |
| `app/Customize/Service/` | Pure unit or integration | `TestCase` or `EccubeTestCase` |
| `app/Customize/Repository/` | Integration test | `EccubeTestCase` |
| `app/Customize/Controller/Admin/` | Integration test | `Tests\Customize\Controller\Admin\BaseTestCase` |
| `app/Customize/Controller/Web/` | Integration test | `Tests\Customize\Controller\Web\BaseTestCase` |
| `app/Customize/Controller/Api/` | Integration test | `Tests\Customize\Controller\Api\BaseTestCase` |
| `app/Customize/Command/` | Integration test | `Tests\Customize\Command\BaseKernelTestCase` |
| `app/template/` | Skip — Twig templates (not unit-testable) |
| `app/Customize/Resource/locale/` | Skip — translation files |
| `*.twig`, `*.yaml`, `*.css` | Skip — not testable |

**Skip non-PHP files** (Twig templates, YAML, CSS, JS). Only generate tests for PHP classes/services.

### Analyze each testable file

For each PHP file in the diff, read the full diff hunk to understand:
1. What methods were added or modified
2. What are the inputs, outputs, and edge cases
3. What dependencies does the class have (constructor injection)
4. Is the method static or instance-based
5. Does it throw exceptions on invalid input

---

## Step 3: Determine Test Type for Each File

### Pure Unit Test (no Symfony kernel, no database)

Use when:
- Class has no database dependencies or they can be mocked
- Static methods
- Pure logic (calculations, transformations, validation)
- Entity trait methods

**Characteristics:**
- Extends `PHPUnit\Framework\TestCase`
- Uses `$this->createMock()` for dependencies
- Run with: `docker exec mrmax_dev-ec-cube-1 php bin/phpunit --no-configuration --bootstrap tests/bootstrap.php <file>`
- Fast — no kernel boot

### Integration Test (requires Symfony kernel + test database)

Use when:
- Class queries the database via EntityManager/Repository
- Controller tests need HTTP client
- Command tests need kernel services

**Characteristics:**
- Extends project `BaseTestCase` or `EccubeTestCase`
- Uses `$this->entityManager`, `$this->client`, factory traits
- Run with: `docker exec mrmax_dev-ec-cube-1 bin/phpunit <file>`
- Requires test DB setup (Steps 1-11 from setup guide)

---

## Step 4: Generate Test Files

### File placement

Mirror the source file structure under `tests/Customize/`:

| Source | Test File |
|--------|-----------|
| `app/Customize/Common/BarCode.php` | `tests/Customize/Common/BarCodeTest.php` |
| `app/Customize/Service/Admin/PackingService.php` | `tests/Customize/Service/Admin/PackingServiceTest.php` |
| `app/Customize/Controller/Admin/Order/PackingController.php` | `tests/Customize/Controller/Admin/Order/PackingControllerTest.php` |

If a test file already exists for that class, **add new test methods** — do NOT overwrite existing tests. Read the existing file first and append.

### Namespace convention

```
Source:  Customize\Common\BarCode
Test:    Customize\Tests\Common\BarCodeTest
```

### Pure Unit Test Template

```php
<?php

namespace Customize\Tests\{SubNamespace};

use PHPUnit\Framework\TestCase;
use Customize\{SubNamespace}\{ClassName};

class {ClassName}Test extends TestCase
{
    // If instance methods, set up SUT with mocked dependencies
    private {ClassName} $sut;

    protected function setUp(): void
    {
        $this->dependency = $this->createMock(DependencyInterface::class);
        $this->sut = new {ClassName}($this->dependency);
    }

    /**
     * @dataProvider validInputProvider
     */
    public function testMethodName_ValidInput($input, $expected): void
    {
        // Arrange — set up via data provider
        // Act
        $result = $this->sut->methodName($input);
        // Assert
        $this->assertSame($expected, $result);
    }

    public function validInputProvider(): array
    {
        return [
            'descriptive_case_name' => ['input_value', 'expected_value'],
        ];
    }

    public function testMethodName_ThrowsOnInvalidInput(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->sut->methodName('invalid');
    }
}
```

### Integration Test Template (Admin Controller)

```php
<?php

namespace Customize\Tests\Controller\Admin\{SubNamespace};

use Tests\Customize\Controller\Admin\BaseTestCase;

class {ControllerName}Test extends BaseTestCase
{
    public function testIndex_ReturnsSuccess(): void
    {
        $this->logIn();
        $this->client->request('GET', $this->generateUrl('route_name'));
        $this->assertTrue($this->client->getResponse()->isSuccessful());
    }
}
```

### Test naming convention

```
test{MethodName}_{Scenario}
```

Examples:
- `testGenerateJanBarcode_ValidEan13()` — happy path
- `testGenerateJanBarcode_ThrowsOnNonDigitInput()` — error case
- `testGenerateJanBarcode_HandlesEan8()` — variant

### What to test for each changed method

1. **Happy path** — normal input → expected output
2. **Edge cases** — boundary values, empty strings, null, zero, max values
3. **Error cases** — invalid input → exception or error handling
4. **Data providers** — use `@dataProvider` when testing multiple input/output combinations
5. **Return types** — verify the method returns the correct type

### What NOT to test

- Twig template rendering (skip template files)
- Translation keys (skip YAML files)
- Static CSS/JS changes
- Getter/setter boilerplate unless logic is involved
- Private methods directly (test through public API)

---

## Step 5: Run Tests

### Pure unit tests (no kernel needed)

```bash
docker exec mrmax_dev-ec-cube-1 php bin/phpunit --no-configuration --bootstrap tests/bootstrap.php tests/Customize/{path}/{TestFile}.php
```

### Integration tests (kernel + test DB required)

```bash
docker exec mrmax_dev-ec-cube-1 bin/phpunit tests/Customize/{path}/{TestFile}.php
```

### Run with stop on first failure

```bash
docker exec mrmax_dev-ec-cube-1 php bin/phpunit --no-configuration --bootstrap tests/bootstrap.php --stop-on-failure tests/Customize/{path}/{TestFile}.php
```

### If tests fail

1. Read the error output carefully
2. Fix the test code (not the source code)
3. Re-run until all tests pass
4. If a test genuinely cannot pass due to a source bug, note it in the return contract

---

## Step 6: Validation

Before returning, verify:
- [ ] Tests cover ONLY methods changed in the branch diff
- [ ] Each test file has correct namespace matching its directory
- [ ] Pure unit tests extend `PHPUnit\Framework\TestCase` (no kernel dependency)
- [ ] Integration tests extend the appropriate `BaseTestCase`
- [ ] All tests pass when executed
- [ ] No duplicate test methods if appending to existing test files
- [ ] Test naming follows `test{Method}_{Scenario}` convention

---

## Return Contract

After writing and running tests, return **only**:

1. **Branches analyzed** — `{REVIEW_BRANCH}` vs `{BASE_BRANCH}`
2. **Files tested** — which source files had tests generated
3. **Test files created/modified** — list of test file paths
4. **Test type** — pure unit or integration for each file
5. **Run command** — the exact docker exec command to re-run each test file
6. **Results** — test run output summary (X passed, Y failed)
7. **Skipped files** — list of non-testable files (Twig, YAML, etc.) with reason

Do NOT paste full test file contents in the response.

---

## Test Best Practices

| Practice | Rule |
|----------|------|
| AAA Pattern | Arrange → Act → Assert in every test |
| One concept per test | Don't test multiple behaviors in one method |
| Descriptive names | `testProcess_ThrowsWhenOutOfStock()` not `testProcess()` |
| Data providers | Use `@dataProvider` for parameterized scenarios |
| Mock externals | Mock repositories, event dispatchers — not the SUT |
| Isolation | Each test independent — no shared state |
| No hardcoded DB | Pure unit tests must NOT touch the database |

---

## Reference: Test Infrastructure

### Existing Base Test Classes

| Base Class | Location | For |
|------------|----------|-----|
| `Tests\Customize\Controller\Admin\BaseTestCase` | `tests/Customize/Controller/Admin/BaseTestCase.php` | Admin controller tests |
| `Tests\Customize\Controller\Web\BaseTestCase` | `tests/Customize/Controller/Web/BaseTestCase.php` | Web controller tests |
| `Tests\Customize\Controller\Api\BaseTestCase` | `tests/Customize/Controller/Api/BaseTestCase.php` | API controller tests |
| `Tests\Customize\Command\BaseKernelTestCase` | `tests/Customize/Command/BaseKernelTestCase.php` | Batch command tests |

### Test Database Setup

The test database `eccubedb_test` must be set up before running integration tests.
See `UNIT-TEST-SETUP.md` for the full 12-step setup procedure.
Pure unit tests do NOT require the test database.

### phpunit.xml

The `phpunit.xml` lists test files explicitly. New integration tests should be added
to the `<testsuite>` section. Pure unit tests can be run directly with
`--no-configuration --bootstrap tests/bootstrap.php` and don't need to be in phpunit.xml.
