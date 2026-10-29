---
name: cr4-phase3-store-pickup-preorder-deep
description: "Deep companion to cr4-phase3-store-pickup-preorder: EC-request Excel export internals, out-of-stock Excel generation details, verbose entity/validation matrices, long SQL/query examples, extended business rules, and edge-case testing walkthroughs. Load on demand only — the [CR4-Phase3] project tag loads the lean main file."
---

# CR4-Phase3 Store Pickup Order Management — Deep Companion

Verbatim overflow of `cr4-phase3-store-pickup-preorder.md`. Load only when a task touches EC-request export internals, out-of-stock Excel generation, verbose matrices, long SQL/query examples, or edge-case walkthroughs.

---

## Expected Outcome

- ✅ New columns in `dtb_order_item`: `is_ec_requested` (bool, default false), `output_datetime` (datetime, nullable)
- ✅ EC依頼 checkbox visible only for OOS items in pickup orders (order_type ∈ {11, 21, 31})
- ✅ EC依頼 flag persisted ONLY on explicit Update click — no auto-save
- ✅ Server-side validation rejects `is_ec_requested=true` for non-pickup/in-stock items
- ✅ Auto-reset `is_ec_requested=false` when item restocked
- ✅ EC依頼 checkbox disabled on cancelled orders; cancelled excluded from export
- ✅ Excel export: .xlsx with 2 sheets per HQ (by Order No / JAN code), via PhpSpreadsheet
- ✅ `output_datetime` set on first export only — write-once, never overwritten
- ✅ Batch007 processes pickup orders at delivery-installation SC連携 timing
- ✅ Auto-save removed from order detail; client-side subtotal recalculation; dirty-form warning
- ✅ Popup on shipping→商品手配中 with opt-in email (default unchecked); popup persists if email skipped
- ✅ Pre-order order_type=31 shows barcode at CAN_RECEIVE=3 and sends email
- ✅ authority_id=6 cannot see PG payment info, Member ID Link, Customer Flag — server-side enforced
- ✅ authority_id=6 filtered to pickup order types only (11, 21, 31)
- ✅ 商品受渡処理 screen: rename, barcode scan → immediate popup confirmation
- ✅ Two new radio filters on order list: EC依頼, ファイル出力済み
- ✅ Export timing: cutoff at 8:30/12:30, export at 10:15/15:15
- ✅ All changes backward compatible; existing orders unaffected

---

## WBS Story Map (Finalized — 16 Stories, 259.5h)

| Story | Title | Effort | Assignee |
|-------|-------|--------|----------|
| 1 | EC Request Database Schema & Entity Extension | 9h | Adib San |
| 2 | EC Request Checkbox in Order Detail | 10.5h | Adib San |
| 3 | EC Request Excel Export — Core Engine | 35h | Adib San |
| 4 | SC Collaboration for Store Pickup Orders | 46h | Shahriar San |
| 5 | Pre-Order Pickup Support (Type 31) | 30h | Adib San |
| 6 | Auto-Save Removal from Order Edit | 36h | Shahriar San |
| 7 | Server-Side EC Request Validation & Business Rules | 6h | Adib San |
| 8 | Products List Template Update | 4h | Shahriar San |
| 9 | Cancelled Order EC Request Handling | 3h | Adib San |
| 10 | Integration Testing | 16h | DEV-3 |
| 11 | Change Pop-up behavior | 12h | Adib San |
| 12 | Controll Screen permission in order details | 24h | Adib San |
| 13 | Additional Search Condition in Order List Page | 7h | Shahriar San |
| 14 | 商品受渡処理 Screen — Rename & Barcode Confirmation | 21h | Shahriar San |
| 15 | Make Memo editable for Store Staff | 9h | Adib San |
| 16 | Modify Batch007/008 for SC collaboration | 16h | Shahriar San |

---

## Key Entities

### OrderType (dcm_order_type)
| Constant | Value | Description |
|----------|-------|-------------|
| STANDARD_KEEP_IN_STORE | 11 | Store pickup |
| EXPRESS_KEEP_IN_STORE | 21 | Express store pickup |
| BOOKING_ORDER_KEEP_IN_STORE | 31 | Pre-order in-store pickup |
| **PICKUP_TYPES** | {11, 21, 31} | All pickup types |

**Repository Constants** (OrderRepository.php L68-72):
```php
const TYPE_RECEIVE_AT_STORE = '11, 21, 31';
const TYPE_RECEIVE_AT_HOME = '10, 20, 30, 40';
const ORDER_TYPE_PRODUCT = [1, 10, 11];
const ORDER_EXPRESS = [20, 21];
const ORDER_NOT_EXPRESS = [10, 11, 30, 31];
```

### OrderItem — New Columns (dtb_order_item via OrderItemTrait)
| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| is_ec_requested | BOOLEAN | FALSE | Store requests EC HQ for OOS product |
| output_datetime | DATETIME | NULL | First Excel export timestamp (write-once) |

### ShippingStatus (dcm_shipping_status)
| ID | Name | Notes |
|----|------|-------|
| 0 | 未出荷 | |
| 1 | 出荷準備中 | |
| 2 | 出荷準備完了 | |
| 3 | SC連携 | |
| 4 | 商品手配中 | Added in CR4-Phase2 |
| 9 | 出荷済み | |

### DeliveryStatus (dcm_delivery_status)
| ID | Name | Notes |
|----|------|-------|
| 0 | 未配達 | |
| 3 | 受取可能 (CAN_RECEIVE) | Triggers barcode display + email |
| 9 | 配達完了 (DONE) | Set on Store Pickup Complete |

### Authority (mtb_authority)
| ID | Name | Notes |
|----|------|-------|
| 0 | システム管理者 | Full access |
| 1 | 店舗オーナー | |
| 6 | 店舗受取担当 | NEW — restricted role |

---

## Business Rules (Extended)

*Rules 5 and 7 remain in the main file; the remaining rules are reproduced below in original numeric order.*

### Rule 1: EC Request Flag Lifecycle (Stories 2, 7, 9)

```
Precondition:
  order_type IN (11, 21, 31)
  AND item is out of stock (is_backordered = true OR lack_count > 0)
  AND order is NOT cancelled

Toggle Action:
  Admin checks EC依頼 checkbox → clicks Update button
  → Controller receives form with is_ec_requested = true
  → Server-side validation:
      IF order_type NOT IN (11, 21, 31) → REJECT (ignore field)
      IF item is in stock → REJECT (ignore field)
      IF order is cancelled → REJECT (ignore field)
  → Persist is_ec_requested to dtb_order_item

Auto-Reset:
  When item stock status changes from OOS to available:
    → Service-level: SET is_ec_requested = false
    → output_datetime preserved (audit trail)

Cancelled Order:
  → EC依頼 checkbox disabled (greyed out) in UI
  → is_ec_requested excluded from form submission
  → Cancelled orders excluded from Excel export queries
```

### Rule 2: Output DateTime Write-Once Atomicity (Story 3)

```
On First Export:
  UPDATE dtb_order_item
  SET output_datetime = NOW()
  WHERE is_ec_requested = 1
    AND output_datetime IS NULL
    AND order_item_id IN (:exportedIds)

On Subsequent Exports:
  output_datetime already set → SKIP update for those rows
  出力済み column in Excel shows original timestamp

Guarantee:
  output_datetime only set once, never updated
  Enforced at service level (SQL WHERE output_datetime IS NULL)
  Not just UI guard — concurrent export safe
```

### Rule 3: Auto-Save Removal & Manual Update (Story 6)

```
AS-IS (Before):
  Field change → AJAX auto-save → DB persisted immediately
  Subtotals recalculated server-side on each change

TO-BE (After):
  Field change → held in browser memory ONLY
  Subtotals recalculated client-side via JavaScript
  Click Update → form POST → server validates → DB persisted
  Navigate away without Update → browser confirmation dialog
  Changes discarded if user confirms navigation
```

### Rule 4: Shipping Status Popup (Story 11)

```
On Update button click:
  IF shipping_status changed to 商品手配中:
    → SHOW confirmation popup (modal)
    → Popup contains:
      - Confirmation message
      - "通知メールを送信する" checkbox (DEFAULT: unchecked)
      - Confirm / Cancel buttons
    → On Confirm:
      - Read send_notification_email flag from popup
      - Submit form with flag
      - Controller: IF flag=true → dispatch email via MailService
      - Controller: Track email-sent status per order/shipping
    → On Cancel:
      - Form not submitted; return to edit page

  IF shipping_status NOT changed to 商品手配中:
    → Submit form directly (no popup)

  IF previous update: status was 商品手配中 but email NOT sent:
    → Popup RE-APPEARS on next status-changing update

  IF only OOS checkbox or EC依頼 checkbox changed:
    → NO popup — direct save
```


### Rule 6: SC連携 Timing Alignment (Story 4)

```
Batch007Command timing change:
  Store pickup orders (11, 21, 31) → use delivery-installation cutoff timing
  Type mapping UNCHANGED: 11→2, 21→4, 31→6

OOS Non-Blocking:
  Store pickup orders with out-of-stock items
  → SC連携 proceeds regardless
  → OOS items handled via EC request flow (separate pipeline)

Backward Compatibility:
  Existing delivery-installation orders → timing UNCHANGED
  Only store pickup orders affected by this change
```


### Rule 8: Barcode Scan Completion (Story 14)

```
On barcode scan in 商品受渡処理:
  1. Validate barcode format
  2. Look up order from barcode value
  3. IF order not found → show error "Barcode not found"
  4. IF delivery_status already DONE (9) → show warning "Already completed" (idempotent)
  5. ELSE:
     a. Show confirmation popup immediately (<500ms per NFR-004)
     b. Popup content: customer name, order no, store, scan timestamp
     c. Warning text: "この操作は取り消せません" (irreversible)
     d. Cancel / Execute buttons
     e. On Execute: set delivery_status=DONE(9), record scan_datetime
     f. On Cancel: dismiss popup, barcode input cleared
```

### Rule 9: Excel Export HQ Split & Timing (Story 3)

```
HQ Assignment:
  uketori_location_cd → West locations → Munakata HQ list
  uketori_location_cd → East locations → Isesaki HQ list
  (Mapping pending Q-02 resolution)

Cutoff Timing:
  Morning: orders before 8:30 → export available at 10:15
  Afternoon: orders 8:30-12:30 → export available at 15:15

Export Structure:
  Sheet_1 【注文番号別】: sorted by Order No ASC
  Sheet_2 【商品別】: sorted by JAN code ASC
  Columns: 注文番号, 店舗名, 分類コード, 分類名, 商品CD, 商品名, EC依頼数, 締日時, 出力済み

Admin Menu:
  "EC依頼リスト_伊勢崎拠点" (East) → ExcelExportController east endpoint
  "EC依頼リスト_宗像拠点" (West) → ExcelExportController west endpoint
```


---

## Key Functions/Methods

### OrderItemTrait.php — New Properties

```php
/**
 * @ORM\Column(type="boolean", options={"default": false})
 * @var bool
 */
private $is_ec_requested = false;

/**
 * @ORM\Column(type="datetime", nullable=true)
 * @var \DateTime|null
 */
private $output_datetime;

public function getIsEcRequested(): bool
{
    return $this->is_ec_requested;
}

public function setIsEcRequested(bool $is_ec_requested): self
{
    $this->is_ec_requested = $is_ec_requested;
    return $this;
}

public function getOutputDatetime(): ?\DateTime
{
    return $this->output_datetime;
}

public function setOutputDatetime(?\DateTime $output_datetime): self
{
    $this->output_datetime = $output_datetime;
    return $this;
}
```

### OrderItemType.php — Add EC Request Checkbox

```php
// In buildForm(), after existing is_backordered field:
->add('is_ec_requested', CheckboxType::class, [
    'label' => 'EC依頼',
    'required' => false,
    'attr' => ['class' => 'ec-request-checkbox'],
])
```

### ExcelExportService.php — Core Export Logic

```php
/**
 * Generate Excel for EC-requested items by HQ location
 * @param string $hqLocation 'east' or 'west'
 * @return StreamedResponse .xlsx download
 */
public function generateEcRequestExcel(string $hqLocation): StreamedResponse
{
    // 1. Query: is_ec_requested=1, matching HQ by uketori_location_cd
    $items = $this->orderRepository->findEcRequestedItemsByHq($hqLocation);

    // 2. Create workbook with PhpSpreadsheet
    $spreadsheet = new Spreadsheet();

    // 3. Sheet_1 【注文番号別】 — sorted by order_no ASC
    $sheet1 = $spreadsheet->getActiveSheet();
    $sheet1->setTitle('注文番号別');
    $this->writeHeaders($sheet1);
    $this->writeData($sheet1, $this->sortByOrderNo($items));

    // 4. Sheet_2 【商品別】 — sorted by JAN code ASC
    $sheet2 = $spreadsheet->createSheet();
    $sheet2->setTitle('商品別');
    $this->writeHeaders($sheet2);
    $this->writeData($sheet2, $this->sortByJanCode($items));

    // 5. Atomically set output_datetime for exported items (write-once)
    $this->updateOutputDatetime($this->extractItemIds($items));

    // 6. Return as StreamedResponse
    return $this->createExcelResponse($spreadsheet, $hqLocation);
}

/**
 * Atomic update: set output_datetime only if currently NULL (write-once)
 */
private function updateOutputDatetime(array $orderItemIds): void
{
    if (empty($orderItemIds)) return;

    $this->entityManager->getConnection()->executeStatement(
        'UPDATE dtb_order_item SET output_datetime = NOW()
         WHERE id IN (?) AND output_datetime IS NULL',
        [$orderItemIds],
        [Connection::PARAM_INT_ARRAY]
    );
}
```

### EditController.php — EC Request Validation & Authority Check

```php
// Inside index() method, after form validation:

// Server-side EC request validation (Story 7)
foreach ($Order->getOrderItems() as $orderItem) {
    if ($orderItem->getIsEcRequested()) {
        $orderType = $Order->getOrderType()->getId();
        $isPickupType = in_array($orderType, [11, 21, 31]);
        $isOos = $orderItem->getIsBackordered() || $orderItem->getLackCount() > 0;

        if (!$isPickupType || !$isOos) {
            $orderItem->setIsEcRequested(false); // silently reject
        }
    }
}

// Authority id=6 PG payment restriction (Story 12)
$authority = $this->getUser()->getAuthority();
$authorityId = $authority ? $authority->getId() : null;
if ($authorityId === 6) {
    // Strip payment info from view data
    // Return 403 if accessing payment-specific endpoints
}
```

### EditController.php — Popup Email Dispatch Logic

```php
// Inside index() method, handle popup email flag:
$sendNotificationEmail = $request->request->get('send_notification_email', false);

if ($shippingStatusChangedToArranging && $sendNotificationEmail) {
    // Dispatch notification email via MailService
    $this->mailService->sendArrangingNotification($Order);
}

// Track email-sent status for popup persistence
if ($shippingStatusChangedToArranging && !$sendNotificationEmail) {
    // Store in session/entity that email was not sent
    // Popup will re-appear on next status-changing update
}
```

### OrderRepository.php — Search Filter Extensions

```php
// In getQueryBuilderBySearchDataForAdmin(), add filter conditions:

// EC依頼 filter
if (isset($searchData['ec_request_filter']) && $searchData['ec_request_filter'] === 'requested') {
    $qb->andWhere('oi.is_ec_requested = :ecRequested')
       ->setParameter('ecRequested', true);
}

// ファイル出力済み filter
if (isset($searchData['output_filter']) && $searchData['output_filter'] === 'not_output') {
    $qb->andWhere('oi.output_datetime IS NULL');
}

// Authority id=6 order type filter
if ($authorityId === 6) {
    $qb->andWhere('ot.id IN (:pickupTypes)')
       ->setParameter('pickupTypes', [11, 21, 31]);
}
```

### Batch007Command.php — Timing Alignment

```php
// Existing mapping (Lines 530-545) — DO NOT CHANGE:
protected function mapOrderTypeToOmniChannelType($orderType)
{
    $orderTypeMap = [
        OrderType::STANDARD => 1,
        OrderType::STANDARD_KEEP_IN_STORE => 2,       // 11→2
        OrderType::EXPRESS => 3,
        OrderType::EXPRESS_KEEP_IN_STORE => 4,          // 21→4
        OrderType::BOOKING_ORDER => 5,
        OrderType::BOOKING_ORDER_KEEP_IN_STORE => 6,    // 31→6
        OrderType::SC_OPTION => 7,
    ];
    return $orderTypeMap[$orderType] ?? null;
}

// MODIFY: Filter/timing conditions — pickup orders use delivery-installation timing
// Ensure OOS items do NOT block SC連携 for pickup order types
```

### edit.twig — JavaScript: Auto-Save Removal & Popup

```javascript
// Remove existing auto-save triggers
// BEFORE: $(document).on('change', '.auto-save-field', function() { $.ajax({...}); });
// AFTER: Remove all auto-save AJAX handlers

// Client-side subtotal recalculation
$(document).on('change', '.quantity-input, .price-input', function() {
    recalculateSubtotals(); // Pure JS, no server call
});

// Dirty-form warning
let formDirty = false;
$(document).on('change', 'form input, form select', function() { formDirty = true; });
$(window).on('beforeunload', function(e) {
    if (formDirty) {
        e.preventDefault();
        return '';
    }
});

// Popup on shipping→商品手配中
$('#order-update-btn').on('click', function(e) {
    const newShippingStatus = $('#shipping_status_select').val();
    const ARRANGING_STATUS = 4; // 商品手配中

    if (newShippingStatus == ARRANGING_STATUS) {
        e.preventDefault();
        $('#arranging-popup-modal').modal('show');
    }
    // No popup for OOS checkbox or EC依頼 checkbox changes
});

// Popup confirm → submit form with email flag
$('#arranging-popup-confirm').on('click', function() {
    const sendEmail = $('#send_notification_email').is(':checked');
    $('<input>').attr({type:'hidden', name:'send_notification_email', value: sendEmail ? '1' : '0'})
        .appendTo('form');
    $('form').submit();
});
```

---

## Validation Rules

| # | Rule | When | Condition | Action |
|---|------|------|-----------|--------|
| V1 | EC request eligibility | Toggle is_ec_requested | `order_type NOT IN (11,21,31)` | Server silently resets to false |
| V2 | EC request stock check | Toggle is_ec_requested | Item is in stock | Server silently resets to false |
| V3 | EC request cancelled | Toggle is_ec_requested | Order is cancelled | Checkbox disabled in UI; server rejects |
| V4 | Auto-reset on restock | Item stock changes | `is_backordered=false AND lack_count=0` | Auto-set `is_ec_requested=false` at service level |
| V5 | output_datetime write-once | Excel export | `output_datetime IS NOT NULL` | Skip update; preserve original |
| V6 | Authority 6 payment | View order detail | `authority_id = 6` | Strip payment info server-side; 403 on direct access |
| V7 | Authority 6 order type | View order list | `authority_id = 6` | Filter to order_type IN (11, 21, 31) at query level |
| V8 | Barcode idempotency | Barcode scan | `delivery_status = DONE (9)` | Show info warning, not error; no double-processing |
| V9 | Pre-order barcode guard | Display barcode | `delivery_status != CAN_RECEIVE (3)` | Don't render barcode; show waiting status |
| V10 | Auto-save prevention | Field change | Any field change | Changes held in memory; NOT persisted until Update click |
| V11 | Export timing | Excel export query | Cutoff times 8:30/12:30 | Filter orders by time window |

---

## Open Questions (Blockers)

| # | Question | Impact | Status |
|---|----------|--------|--------|
| Q-01 | 商品手配中 shipping status — already added in CR4-Phase2? | Popup trigger logic (Story 11) | VERIFY |
| Q-02 | East/West HQ mapping for uketori_location_cd | Excel export split (Story 3) | BLOCKER |
| Q-03 | 4 Excel views vs 2 sheets — relationship | Export UI design (Story 3) | PENDING |
| Q-06 | Complete deny_url list for authority_id=6 | Auth configuration (Story 12) | PENDING |
| Q-09 | EC依頼数 = lack_count or separate field? | Excel column data (Story 3) | PENDING |

---

## Common Bug Patterns & Prevention

### Bug 1: `output_datetime` Overwritten on Re-Export
**Pattern:** Multiple exports update `output_datetime` repeatedly.
**Prevention:**
```sql
-- Atomic condition: only set if NULL
UPDATE dtb_order_item SET output_datetime = NOW()
WHERE id IN (?) AND output_datetime IS NULL
```
Test with multiple concurrent exports; verify first timestamp preserved.

### Bug 2: EC依頼 Checkbox Shows for Non-Pickup Orders
**Pattern:** Missing `order_type` guard in template.
**Prevention:**
```twig
{% if order.OrderType.id in [11, 21, 31] and orderItem.isBackordered %}
    {{ form_widget(orderItemForm.is_ec_requested) }}
{% endif %}
```
Also enforce server-side in EditController (V1).

### Bug 3: EC依頼 Set on Cancelled Order
**Pattern:** User manipulates DOM to enable disabled checkbox.
**Prevention:** Server-side validation in EditController. Never trust frontend-only disabling.
```php
if ($Order->getOrderStatus()->getId() === OrderStatus::CANCEL) {
    $orderItem->setIsEcRequested(false);
}
```

### Bug 4: Authority 6 Sees PG Payment via Direct URL
**Pattern:** Frontend hides field, but controller returns full data.
**Prevention:**
```php
$authorityId = $this->getUser()->getAuthority()?->getId();
if ($authorityId === 6) {
    // Strip payment fields BEFORE template rendering
    // Or return 403 for payment-specific endpoints
}
```
Server-side check ALWAYS; test via direct URL access.

### Bug 5: Auto-Save Still Active After Removal
**Pattern:** Missed AJAX handler in JavaScript; partial removal.
**Prevention:** Search for ALL `$.ajax`, `$.post`, `$.get` calls in edit.twig and related JS files. Remove/disable each one. Test by changing field → checking network tab → verifying no requests.

### Bug 6: Popup Shows on OOS Checkbox Instead of Status Change
**Pattern:** Wrong trigger condition; popup fires on any change.
**Prevention:**
```javascript
// CORRECT: Only check shipping status value
const newStatus = $('#shipping_status_select').val();
if (newStatus == ARRANGING_STATUS) { showPopup(); }
// WRONG: Checking any form change
```

### Bug 7: Batch007 Breaks Delivery-Installation Orders
**Pattern:** Timing change not backward-compatible.
**Prevention:** Only modify filter conditions for pickup types. Do NOT alter timing for existing delivery-installation flow. Test both paths.

### Bug 8: Pre-order Barcode Displayed Prematurely
**Pattern:** Barcode shown before `delivery_status = CAN_RECEIVE (3)`.
**Prevention:**
```php
if ($order->getDeliveryStatus() !== DeliveryStatus::CAN_RECEIVE) {
    // Don't render barcode; show "Awaiting" message
}
```

### Bug 9: EC依頼 Still Active After Restock
**Pattern:** Missing auto-reset logic when stock status changes.
**Prevention:** Add event/service hook: when `is_backordered` changes to false or `lack_count` drops to 0, auto-set `is_ec_requested = false`.

### Bug 10: Subtotals Wrong After Auto-Save Removal
**Pattern:** Client-side recalculation misses edge cases (tax, discounts).
**Prevention:** Port all server-side calculation logic to JavaScript. Test with various price/quantity/tax combinations.

### Bug 11: Email Popup Shows Incorrectly on Non-Status Updates
**Pattern:** Popup triggers on any form submit, not just status change.
**Prevention:** Track original shipping status on page load. Compare on submit. Only show popup if status actually changed TO 商品手配中.

---

## Testing Scenarios

### Scenario 1: EC Request Checkbox Visibility
```
Given: Order with order_type=11 (store pickup)
  And: Item A is out of stock (is_backordered=true)
  And: Item B is in stock
When: Admin opens order detail page
Then:
  ✓ EC依頼 checkbox visible for Item A
  ✗ EC依頼 checkbox NOT visible for Item B

Given: Order with order_type=1 (standard delivery)
  And: Item C is out of stock
When: Admin opens order detail page
Then:
  ✗ EC依頼 checkbox NOT visible for any item
```

### Scenario 2: EC Request Persistence (No Auto-Save)
```
Given: Order type=21, item out of stock, EC依頼 unchecked
When: Admin checks EC依頼 checkbox
  And: Does NOT click Update
  And: Navigates away
Then:
  ✓ Browser shows dirty-form confirmation dialog
  ✓ is_ec_requested remains FALSE in DB

When: Admin checks EC依頼 checkbox
  And: Clicks Update
Then:
  ✓ is_ec_requested = TRUE in DB
  ✓ No confirmation popup shown (OOS checkbox → direct save)
```

### Scenario 3: Excel Export with Write-Once Timestamp
```
Given: 20 orders with is_ec_requested=1, split between East/West HQ
When: Admin clicks "EC依頼リスト_宗像拠点" (West)
Then:
  ✓ .xlsx file downloaded with 10 West records
  ✓ Sheet_1 sorted by Order No ASC
  ✓ Sheet_2 sorted by JAN code ASC
  ✓ output_datetime set for all 10 records
When: Admin clicks same export again
Then:
  ✓ output_datetime UNCHANGED for previously exported records
  ✓ 出力済み column shows original timestamp
  ✓ New records (if any) get fresh timestamp
```

### Scenario 4: Shipping→商品手配中 Popup Flow
```
Given: Order detail page with auto-save removed
When: Admin changes shipping status to 商品手配中
  And: Clicks Update
Then:
  ✓ Confirmation popup appears
  ✓ "通知メールを送信する" checkbox is UNCHECKED by default
When: Admin clicks Confirm WITHOUT checking email
Then:
  ✓ Status saved; no email sent
When: Admin changes status again and clicks Update
Then:
  ✓ Popup RE-APPEARS (email was not sent previously)
When: Admin checks email checkbox and confirms
Then:
  ✓ Email dispatched via MailService
  ✓ Popup does NOT re-appear on subsequent updates
```

### Scenario 5: Authority ID=6 Permission Enforcement
```
Given: User logged in with authority_id=6
When: Navigate to order list (受注一覧)
Then:
  ✓ Only order_type 11, 21, 31 visible
  ✗ Other order types hidden
When: Open order detail for a pickup order
Then:
  ✓ PG Multi-Payment payment info area NOT visible
  ✓ Member ID Link NOT visible
  ✓ Customer Flag NOT visible
  ✓ EC request flag and memo editable
When: Direct URL access to payment endpoint as authority_id=6
Then:
  ✓ HTTP 403 Forbidden returned
When: Access same order via 商品受渡処理 entry point
Then:
  ✓ Same restrictions apply (entry-point agnostic)
```

### Scenario 6: Pre-Order Pickup Lifecycle (Type 31)
```
Given: Pre-order item (order_type=31), delivery_status=0
When: Processing through statuses:
  order_status: 1 → 4 → 5
  shipping: 0 → 1 → 2
Then:
  ✓ Same flow as order_type=11

When: delivery_status set to CAN_RECEIVE (3)
Then:
  ✓ Barcode generated and displayed to customer
  ✓ Email notification sent to customer
  ✓ Barcode in Code128 format

When: Store staff scans barcode on 商品受渡処理
Then:
  ✓ Confirmation popup appears immediately (<500ms)
  ✓ Popup shows: customer name, order no, timestamp, irreversibility warning
When: Staff clicks Execute
Then:
  ✓ delivery_status → DONE (9)
  ✓ order_status → 8 (Completed)
  ✓ preorder_status → 9 (Fulfilled)
```

### Scenario 7: Cancelled Order EC Request
```
Given: Order with is_ec_requested=true
When: Order is cancelled
Then:
  ✓ EC依頼 checkbox greyed out on order detail
  ✓ Order excluded from Excel export results
  ✓ is_ec_requested value preserved in DB (for audit)
```

### Scenario 8: Server-Side EC Request Validation
```
Given: Order type=1 (standard delivery), item out of stock
When: Malicious request sends is_ec_requested=true (DOM manipulation)
Then:
  ✓ Server silently resets is_ec_requested to false
  ✓ No error shown to user (graceful handling)
```

### Scenario 9: Barcode Scan Idempotency
```
Given: Order already completed (delivery_status=DONE)
When: Barcode scanned again
Then:
  ✓ Warning message: "Already completed"
  ✓ No state change
  ✓ No error thrown
```

### Scenario 10: Auto-Reset EC Request on Restock
```
Given: Item with is_ec_requested=true, output_datetime=2026-06-01
When: Item stock status changes to available (is_backordered=false, lack_count=0)
Then:
  ✓ is_ec_requested automatically set to false
  ✓ output_datetime preserved (audit trail)
```

---
