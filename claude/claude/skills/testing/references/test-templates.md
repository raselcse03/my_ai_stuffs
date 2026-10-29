# Testing — Test Templates & Reference

> Loaded on-demand by `testing/SKILL.md`: at Step 4 for the test-code skeletons, naming conventions, and what-to-test guidance; at the Reference step for test best practices, base test classes, DB setup, and phpunit.xml notes. Do NOT load until you reach those steps.

## Test Templates & Authoring Guidance (Step 4)

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
