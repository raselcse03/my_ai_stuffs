# Change Request — Code Templates & Examples

> Loaded on-demand by `change-request.md`. Do NOT read unless implementing a CR.

---

## Specification Document Template

```markdown
## CR-XXX: [Feature Name]

### Business Need
[Why is this needed?]

### Requested By
[Stakeholder name/team]

### Priority
Critical / High / Medium / Low

### Target Date
[YYYY-MM-DD]

### Functional Requirements
1. System shall...
2. User shall be able to...
3. When X happens, system shall...

### Non-Functional Requirements
- Performance: [e.g., < 2s response time]
- Security: [e.g., Admin-only access]
- Compatibility: [e.g., Must work with existing API]

### Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

---

## Impact Assessment Template

```markdown
## Impact Assessment: CR-XXX

### Code Impact
**Files to Modify:**
- app/Customize/Service/OrderService.php
- app/Customize/Entity/Order.php

**New Files:**
- app/Customize/Service/DiscountCalculator.php
- app/Customize/Form/Type/DiscountType.php

### Database Impact
**Schema Changes:** Yes
- Add column: dtb_order.custom_discount (decimal)
- Add table: dtb_discount_rule

**Data Backfill:** Required (manual SQL script)
- Backfill existing discount data

### API Impact
**Breaking Changes:** No
**New Endpoints:**
- POST /api/discount/calculate

### Integration Impact
**Affected Systems:**
- Payment gateway integration
- Reporting system

### Performance Impact
**Expected Load:** +10% order processing time
**Mitigation:** Add caching for discount rules

### Security Impact
**New Attack Surfaces:** Discount calculation logic
**Mitigation:** Input validation, authorization checks

### Risk Assessment
**Technical Risks:**
- Data backfill complexity
- Backward compatibility

**Mitigation:**
- Thorough testing
- Rollback plan

### Estimated Effort
- Development: 16 hours
- Testing: 8 hours
- Documentation: 4 hours
- **Total:** 28 hours (3.5 days)
```

---

## SQL Schema Script Example

```sql
-- CR-123: Add custom discount fields

-- Add new column
ALTER TABLE dtb_order 
ADD custom_discount DECIMAL(12,2) DEFAULT 0 
COMMENT 'Custom discount amount';

-- Add new table
CREATE TABLE dtb_discount_rule (
    id INT UNSIGNED AUTO_INCREMENT NOT NULL,
    name VARCHAR(255) NOT NULL,
    discount_rate DECIMAL(5,2) NOT NULL,
    min_amount DECIMAL(12,2) DEFAULT 0,
    valid_from DATETIME NOT NULL,
    valid_to DATETIME DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    PRIMARY KEY(id)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ENGINE = InnoDB;

CREATE INDEX idx_active ON dtb_discount_rule (is_active);
CREATE INDEX idx_dates ON dtb_discount_rule (valid_from, valid_to);
```

---

## Entity Extension (Proxy Pattern)

**Trait: `app/Customize/Entity/OrderTrait.php`**
```php
<?php
namespace Customize\Entity;

use Doctrine\ORM\Mapping as ORM;
use Eccube\Annotation\EntityExtension;

/**
 * @EntityExtension("Eccube\\Entity\\Order")
 */
trait OrderTrait
{
    /**
     * @var float|null
     * @ORM\Column(name="custom_discount", type="decimal", precision=12, scale=2, options={"default":0})
     */
    private $customDiscount = 0;

    public function getCustomDiscount(): ?float
    {
        return $this->customDiscount;
    }

    public function setCustomDiscount(?float $customDiscount): self
    {
        $this->customDiscount = $customDiscount;
        return $this;
    }
    
    public function getTotalWithCustomDiscount(): float
    {
        return max(0, $this->getTotal() - $this->getCustomDiscount());
    }
}
```

---

## New Service Example

**Service: `app/Customize/Service/DiscountCalculatorService.php`**
```php
<?php
namespace Customize\Service;

use Customize\Repository\DiscountRuleRepository;
use Eccube\Entity\Order;
use Psr\Log\LoggerInterface;

class DiscountCalculatorService
{
    private DiscountRuleRepository $discountRuleRepository;
    private LoggerInterface $logger;

    public function __construct(
        DiscountRuleRepository $discountRuleRepository,
        LoggerInterface $logger
    ) {
        $this->discountRuleRepository = $discountRuleRepository;
        $this->logger = $logger;
    }

    public function calculateDiscount(Order $order): float
    {
        $rules = $this->discountRuleRepository->findActiveRules();
        
        $discount = 0;
        foreach ($rules as $rule) {
            if ($this->isRuleApplicable($rule, $order)) {
                $ruleDiscount = $order->getTotal() * $rule->getDiscountRate();
                $discount = max($discount, $ruleDiscount);
                
                $this->logger->info('Discount rule applied', [
                    'rule' => $rule->getName(),
                    'order_id' => $order->getId(),
                    'discount' => $ruleDiscount,
                ]);
            }
        }
        
        return $discount;
    }

    private function isRuleApplicable($rule, Order $order): bool
    {
        if ($order->getTotal() < $rule->getMinAmount()) {
            return false;
        }
        $now = new \DateTime();
        if ($rule->getValidFrom() > $now) {
            return false;
        }
        if ($rule->getValidTo() !== null && $rule->getValidTo() < $now) {
            return false;
        }
        return true;
    }
}
```

---

## Modify Existing Service Example

```php
<?php
namespace Customize\Service;

class OrderProcessingService
{
    private DiscountCalculatorService $discountCalculator;

    public function __construct(
        EntityManagerInterface $entityManager,
        OrderRepository $orderRepository,
        DiscountCalculatorService $discountCalculator  // NEW
    ) {
        $this->entityManager = $entityManager;
        $this->orderRepository = $orderRepository;
        $this->discountCalculator = $discountCalculator;
    }

    public function confirmOrder(int $orderId): Order
    {
        $order = $this->orderRepository->find($orderId);
        
        // Apply custom discount
        $discount = $this->discountCalculator->calculateDiscount($order);
        $order->setCustomDiscount($discount);
        
        $this->entityManager->flush();
        return $order;
    }
}
```

---

## Service Registration (services.yaml)

```yaml
services:
    Customize\Service\DiscountCalculatorService:
        arguments:
            - '@Customize\\Repository\\DiscountRuleRepository'
            - '@logger'

    Customize\Service\OrderProcessingService:
        arguments:
            - '@doctrine.orm.entity_manager'
            - '@Eccube\\Repository\\OrderRepository'
            - '@Customize\\Service\\DiscountCalculatorService'
```

---

## Unit Test Example

```php
<?php
namespace Tests\Customize\Service;

use PHPUnit\Framework\TestCase;
use Customize\Service\DiscountCalculatorService;

class DiscountCalculatorServiceTest extends TestCase
{
    private $service;
    
    protected function setUp(): void
    {
        $mockRepo = $this->createMock(DiscountRuleRepository::class);
        $mockLogger = $this->createMock(LoggerInterface::class);
        $this->service = new DiscountCalculatorService($mockRepo, $mockLogger);
    }
    
    public function testCalculateDiscount_AppliesRuleWhenEligible()
    {
        $order = new Order();
        $order->setTotal(10000);
        $discount = $this->service->calculateDiscount($order);
        $this->assertGreaterThan(0, $discount);
    }
    
    public function testCalculateDiscount_NoRuleAppliedBelowMinimum()
    {
        $order = new Order();
        $order->setTotal(500);
        $discount = $this->service->calculateDiscount($order);
        $this->assertEquals(0, $discount);
    }
}
```

---

## Backward Compatibility Pattern

```php
// Support both old and new behavior
if ($order->hasCustomDiscount()) {
    $total = $order->getTotalWithCustomDiscount();
} else {
    $total = $order->getTotal();
}
```

---

## Stakeholder Status Update Template

```markdown
## CR-123 Implementation Status

### Completed (Week of 2026-02-18)
- ✅ Requirements analysis
- ✅ Impact assessment
- ✅ Database schema design
- ✅ Entity and service implementation
- ✅ Unit tests (coverage: 85%)

### In Progress
- 🔄 UAT with stakeholders
- 🔄 User documentation

### Upcoming
- ⏳ Production deployment (2026-02-25)
- ⏳ Training session (2026-02-26)

### Blockers
None
```

---

## Deployment Checklist

```bash
# 1. Backup database
mysqldump eccube_db > backup_$(date +%Y%m%d).sql

# 2. Apply SQL schema changes (manual script — no Doctrine migrations)
mysql eccube_db < sql/cr-xxx-schema-changes.sql

# 3. Clear cache
bin/console cache:clear --env=prod

# 4. Warm up cache
bin/console cache:warmup --env=prod

# 5. Run tests
bin/phpunit

# 6. Verify in staging → Deploy to production → Monitor logs
```
