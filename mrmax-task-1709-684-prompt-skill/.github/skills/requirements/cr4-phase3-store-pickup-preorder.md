---
title: CR4 Phase 3 — Store Pickup Order Management (EC Request, Excel Export, Authority, Pre-Order)
phase: 3
applyTo: "app/Customize/**, app/template/admin/Order/**"
version: 2.0
createdAt: 2026-05-21
updatedAt: 2026-06-05
---

# CR4-Phase3: Store Pickup Order Management Skill

**Prerequisites:** Review `core-essentials.md` for critical rules. Review `change-request.md` for CR methodology.

## When to Use This Skill

This skill is invoked when implementing or extending CR4 Phase 3 features:
- Adding/modifying EC request flag logic (`is_ec_requested`, `output_datetime` columns on `dtb_order_item`)
- Building Excel export for out-of-stock EC-requested items (Munakata/Isesaki HQ split)
- Modifying Batch007Command SC連携 timing for store pickup orders
- Removing auto-save behavior from order detail page; enforcing explicit Update
- Implementing popup logic for shipping status → 商品手配中 transition
- Supporting pre-order in-store pickup (order_type=31) barcode display + email
- Configuring authority_id=6 (店舗受取担当) permissions and deny_urls
- Redesigning 商品受渡処理 screen (barcode scan, confirmation popup)
- Adding EC依頼 / ファイル出力済み search filters to order list
- Server-side EC Request validation and auto-reset on restock
- EC Request status display in products list template
- Cancelled order EC Request handling (export exclusion + checkbox disable)
- Export timing (cutoff) configuration for 8:30/12:30 windows

**Do NOT use this skill for:**
- Regular EC-CUBE core development (use `core-essentials.md`)
- Modifying `src/Eccube/` files (NEVER — use `app/Customize/` only)
- Generating or running Doctrine migrations (`app/DoctrineMigrations/`)
- CR5 V-Point card linkage features (use `cr5-vpoint-card-linkage.md`)
- CR4-Phase2 store pickup inventory (use `cr4-phase2-store-pickup-inventory.md`)

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

## File Map

### Database & Entity

```
app/Customize/Entity/OrderItemTrait.php
  - ADD: $is_ec_requested (bool, default false)
  - ADD: $output_datetime (datetime, nullable)
  - ADD: getIsEcRequested() / setIsEcRequested()
  - ADD: getOutputDatetime() / setOutputDatetime()
  - Pattern: @EntityExtension("Eccube\Entity\OrderItem")
  - Convention: follows existing isXxx() / setXxx() patterns (see isInstallFee() L23, isRemovalFee() L31)
```

### Controllers

```
app/Customize/Controller/Admin/Order/EditController.php
  - index() at L330 — Main order edit/save (GET + POST)
  - Route: /%eccube_admin_route%/order/{id}/edit
  - Mode check: $request->get('mode') === 'register'
  - Transaction: $this->entityManager->beginTransaction()
  - MODIFY: Persist is_ec_requested from form on Update
  - MODIFY: Remove auto-save AJAX triggers
  - MODIFY: Add popup trigger on shipping→商品手配中
  - MODIFY: Add email dispatch conditional on popup checkbox
  - MODIFY: Add server-side validation for is_ec_requested eligibility
  - MODIFY: Block PG payment info for authority_id=6

app/Customize/Controller/Admin/Order/OrderController.php
  - index() at L196 — Order list with search/filter
  - Route: /%eccube_admin_route%/order
  - Uses SearchOrderType form
  - Session-based search: $this->session->set('eccube.admin.order.search', $formData)
  - MODIFY: Add EC依頼 / ファイル出力済み filter conditions to query
  - MODIFY: Filter order category for authority_id=6 (pickup types only)

NEW: app/Customize/Controller/Admin/Order/ExcelExportController.php
  - GET /%eccube_admin_route%/order/ec-request-export/east → Isesaki HQ export
  - GET /%eccube_admin_route%/order/ec-request-export/west → Munakata HQ export
  - Inject: ExcelExportService, OrderRepository
  - Returns: StreamedResponse with .xlsx

app/Customize/Controller/Admin/Order/ShippingExpressController.php
  - index() at L75 — Store pickup management (商品受渡処理)
  - Route: /%eccube_admin_route%/order/shipping-express
  - Uses ShippingExpressType form
  - MODIFY: Rename menu label from 店舗受取管理 to 商品受渡処理
  - MODIFY: Add barcode scan → immediate popup confirmation flow
  - MODIFY: Add scan timestamp in popup
  - Dependencies: ExportPdfService, ShopService, ShippingExpressService, QrCodeService
```

### Services

```
NEW: app/Customize/Service/ExcelExportService.php
  - generateEcRequestExcel(string $hqLocation): StreamedResponse
  - filterByHqLocation(string $uketoriLocationCd): array
  - updateOutputDatetime(array $orderItemIds): void — atomic, write-once
  - Pattern: Follow existing CsvExportService.php (extends \Eccube\Service\CsvExportService)
  - Library: PhpSpreadsheet v1.24+ (already in composer.json)
  - 2 sheets: Sheet_1 【注文番号別】 by Order No ASC, Sheet_2 【商品別】 by JAN code ASC
  - 9 columns: 注文番号, 店舗名, 分類コード, 分類名, 商品CD, 商品名, EC依頼数, 締日時, 出力済み

app/Customize/Service/OrderState/OrderStateHelper.php
  - do() — Handle state switches/transitions
  - endPoint() — Get from/to state points
  - ALLOW_SIGNATURES constant (L30-47): tracks allowed state transitions
  - MODIFY: Add pre-order (type 31) status transition logic
  - MODIFY: Support delivery_status → CAN_RECEIVE(3) → DONE(9) for type 31
  - Dependencies: PaymentService, OrderService, MessageBusInterface, OrderItemRepository,
    EntityManagerInterface, ProductStockService, OrderRepository, CommandService

app/Customize/Service/MailService.php
  - Pattern: MailerInterface + Twig_Environment for rendering
  - Uses: MailTemplateRepository, MailHistoryRepository
  - MODIFY: Add email dispatch for delivery_status → 受取可能 (type 31)
  - MODIFY: Conditional email on shipping→商品手配中 popup checkbox

app/Customize/Service/CsvExportService.php
  - getOrderQueryBuilder(Request $request, $chargeLocationArray): array
  - Pattern reference for new ExcelExportService
  - Uses SearchOrderType form + customOrderRepository query builder
```

### Batch

```
app/Customize/Command/Batch007Command.php
  - mapOrderTypeToOmniChannelType() at L530-545
  - Existing mapping: 11→2, 21→4, 31→6 (UNCHANGED)
  - MODIFY: Timing/filter conditions only — align pickup with delivery-installation timing
  - VERIFY: OOS items do NOT block SC連携 for pickup orders
```

### Forms

```
app/Customize/Form/Type/Admin/OrderType.php
  - buildForm() at L~180
  - OrderItems registered as CollectionType with entry_type=OrderItemType::class (L~239-245)
  - MODIFY: No changes here (checkbox added in OrderItemType)

app/Customize/Form/Type/Admin/OrderItemType.php
  - buildForm() at L82
  - Existing fields: is_backordered (checkbox), is_returned (checkbox), lack_count
  - Form events: addPrice(L226), addQuantity(L259), addLackCount(L290), addTaxRule(L323), verifyData(L369)
  - ADD: 'is_ec_requested' as CheckboxType (follow is_backordered pattern)
  - Convention: POST_SET_DATA + POST_SUBMIT event listeners

app/Customize/Form/Type/Admin/SearchOrderType.php
  - MODIFY: Add EC依頼 radio (ChoiceType, expanded=true): すべて / 依頼あり
  - MODIFY: Add ファイル出力済み radio (ChoiceType, expanded=true): すべて / 未出力のみ
```

### Repository

```
app/Customize/Repository/OrderRepository.php
  - getQueryBuilderBySearchDataForAdmin() at L707 — Admin order list query builder
  - getOrderItems() at L190 — Raw SQL for order items
  - MODIFY: Add is_ec_requested=1 filter condition (when 依頼あり selected)
  - MODIFY: Add output_datetime IS NULL filter condition (when 未出力のみ selected)
  - MODIFY: Add cancelled order exclusion in EC export queries
  - Pattern: QueryBuilder with ->andWhere(), parameterized queries via ->setParameter()
```

### Templates

```
app/template/admin/Order/edit.twig
  - Extends: @admin/default_frame.twig
  - Form theme: bootstrap_4_horizontal_layout.html.twig
  - MODIFY: Add EC依頼 checkbox per order item row (Twig: {{ form_widget(orderItemForm.is_ec_requested) }})
  - MODIFY: Visibility: order.OrderType.id in [11, 21, 31] AND item OOS
  - MODIFY: Remove auto-save AJAX triggers (JS)
  - MODIFY: Add client-side subtotal recalculation (JS)
  - MODIFY: Add dirty-form warning on navigation (JS)
  - MODIFY: Add popup trigger on shipping→商品手配中 (JS modal intercept)
  - MODIFY: Add email opt-in checkbox in popup (default unchecked)
  - MODIFY: Hide PG payment area for authority_id=6 (Twig conditional)

app/template/admin/Order/index.twig
  - Extends: @admin/default_frame.twig
  - Form theme: bootstrap_4_layout.html.twig
  - MODIFY: Add EC依頼 radio filter ({{ form_widget(searchForm.ec_request_filter) }})
  - MODIFY: Add ファイル出力済み radio filter ({{ form_widget(searchForm.output_filter) }})
  - MODIFY: Add export download buttons/links for EC依頼リスト

app/template/admin/Order/shipping_express.twig (or equivalent)
  - MODIFY: Rename screen title to 商品受渡処理
  - MODIFY: Add barcode input field with auto-focus
  - MODIFY: Add confirmation popup on scan (order details + irreversibility warning + timestamp)
  - MODIFY: Ensure receipt status filter (未/済み/全て), store dropdown, date range, results table

Admin navigation template (investigate exact path)
  - MODIFY: Rename menu: 店舗受取管理 → 商品受渡処理
  - ADD: EC依頼リスト_伊勢崎拠点 menu item
  - ADD: EC依頼リスト_宗像拠点 menu item
```

### Master Data (CSV)

```
app/Customize/DataFixture/Master/csv/ja/mtb_authority.csv
  - ADD: id=6, name='店舗受取担当', sort_no=6

app/Customize/DataFixture/Master/csv/authority_role.csv
  - ADD: deny_url entries for authority_id=6
  - CONSTRAINT: MUST NOT include '/order' (blocks total-picking and packing)
```

---

## Business Rules & Logic

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

### Rule 5: Pre-Order State Machine (Story 5, order_type=31)

```
Status Transitions:
  order_status:    1 (New) → 4 (Processing) → 5 (Shipped) → 8 (Completed)
  preorder_status: 1 (Active) → 9 (Fulfilled)
  shipping:        0 (Initial) → 1 (Preparing) → 2 (Shipped) → 9 (Completed)
  delivery:        0 (Initial) → 3 (CAN_RECEIVE) → 9 (DONE)

Barcode Display Condition:
  delivery_status = CAN_RECEIVE (3)
  → Generate and display barcode to customer
  → Barcode format: Code128

Email Trigger:
  On transition delivery_status → CAN_RECEIVE (3):
    → sendEmail(customer, subject: "受取可能のお知らせ")
    → Use MailService pattern with Twig template

Post-Barcode Flow:
  Barcode scan at store → confirmation popup → delivery_status = DONE (9)
  Same as order_type=11 from this point
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

### Rule 7: Authorization Enforcement (Story 12)

```
For authority_id = 6 (店舗受取担当):

Server-Side (Controller Level):
  EditController.index():
    IF authority_id = 6:
      ✗ Strip/hide PG Multi-Payment payment info from response
      ✗ Return 403 on direct URL access to payment endpoints
    Pattern: $authority = $this->getUser()->getAuthority(); $authorityId = $authority->getId();

  OrderController.index():
    IF authority_id = 6:
      ✗ Filter order list: only order_type IN (11, 21, 31)
      ✗ Hide non-pickup order types from category filter

  Template Level (complementary):
    {% if app.user.authority.id != 6 %}
      {{ payment_info_block }}
    {% endif %}

  Features Inactivated:
    ✗ Member ID Link — hidden/disabled
    ✗ Customer Flag — hidden/disabled

  deny_url Configuration:
    MUST NOT include '/order' (blocks total-picking and packing)
    Use specific paths instead

  Entry Point Agnostic:
    Same restrictions from 商品受渡処理 entry
    Same restrictions from 受注一覧 entry
    Same restrictions from direct URL
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

## Implementation Checklist

### Phase 1: Database & Entity (Sprint 1 — Stories 1, 7)
- [ ] Prepare manual SQL: `ALTER TABLE dtb_order_item ADD COLUMN is_ec_requested BOOLEAN DEFAULT FALSE`
- [ ] Prepare manual SQL: `ALTER TABLE dtb_order_item ADD COLUMN output_datetime DATETIME DEFAULT NULL`
- [ ] Create indexes: `idx_order_item_ec_requested`, `idx_order_item_output_datetime`
- [ ] Add ORM annotations in OrderItemTrait.php (`@ORM\Column`)
- [ ] Add getters/setters following existing trait conventions
- [ ] Run `bin/console eccube:generate:proxies`
- [ ] Verify: `composer show phpoffice/phpspreadsheet` (must be v1.24+)
- [ ] ❌ NO Doctrine migrations generated

### Phase 2: Forms & EC Request Checkbox (Sprint 1 — Stories 2, 6)
- [ ] Add `is_ec_requested` as `CheckboxType` in OrderItemType.php (follow `is_backordered` pattern)
- [ ] Render EC依頼 checkbox in edit.twig per order item (conditional: pickup type + OOS)
- [ ] Add translation key for "EC依頼" column header
- [ ] Remove auto-save AJAX triggers from edit.twig JavaScript
- [ ] Add client-side subtotal recalculation JavaScript
- [ ] Add dirty-form navigation warning
- [ ] Server-side EC request validation in EditController (reject non-eligible)
- [ ] Auto-reset `is_ec_requested` on restock (service-level hook)

### Phase 3: Excel Export (Stories 3, 9)
- [ ] Create ExcelExportService (PhpSpreadsheet, 2-sheet output)
- [ ] Create ExcelExportController with East/West endpoints
- [ ] Add repository query: EC-requested items by HQ region
- [ ] Implement output_datetime write-once logic (atomic SQL)
- [ ] Add cutoff time filtering (8:30/12:30 windows) and 締日時 calculation
- [ ] Add admin menu items: "EC依頼リスト_伊勢崎拠点", "EC依頼リスト_宗像拠点"
- [ ] Add download buttons on order list template
- [ ] Exclude cancelled orders from export queries
- [ ] Sort by JANCODE/Order No.

### Phase 4: Batch & Pre-Order (Stories 4, 5, 8, 16)
- [ ] State machine modification for SC_OPTION in pickup flow (Story 4)
- [ ] Verify and update Batch007 for pickup order types (Story 4)
- [ ] Modify Batch007/008 for SC collaboration (Story 16, MRMAX_ECOPE-3335)
- [ ] Verify OOS items do NOT block SC連携 for pickup
- [ ] Implement pre-order (type 31) status transitions in OrderStateHelper
- [ ] Add email on delivery_status → CAN_RECEIVE via MailService
- [ ] Add barcode display at CAN_RECEIVE
- [ ] Add barcode scan → DONE transition
- [ ] Add EC Request status display in products list template

### Phase 5: Popup, Authority, Screen & Memo (Stories 11, 12, 13, 14, 15)
- [ ] Checkbox behavior update (Story 11)
- [ ] Pop-up show condition change (Story 11)
- [ ] Configure deny_url entries for authority_id=6 (Story 12)
- [ ] Server-side PG payment info restriction (Story 12)
- [ ] Order category filter restriction for authority_id=6 (Story 12)
- [ ] Inactivate Member ID Link, Customer Flag for authority_id=6 (Story 12)
- [ ] Template-level hiding for authority_id=6 (Story 12)
- [ ] Add 2 new search filter UI elements on order list page (Story 13)
- [ ] Backend search filter logic for additional conditions (Story 13)
- [ ] Rename menu: 店舗受取管理 → 商品受渡処理 (Story 14)
- [ ] Implement barcode scan → confirmation popup on 商品受渡処理 (Story 14)
- [ ] Add scan timestamp + irreversibility warning (Story 14)
- [ ] Verify screen elements: filters, dropdown, date range (Story 14)
- [ ] Make memo editable for store staff / authority_id=6 (Story 15)

### Phase 6: Testing (Sprint 4 — Story 10)
- [ ] Unit tests for entity properties and defaults
- [ ] Unit tests for form submission and validation
- [ ] Unit tests for EC request server-side validation
- [ ] Unit tests for export service (write-once, sort, HQ split)
- [ ] Unit tests for Batch007 backward compatibility
- [ ] Integration tests for full EC request → export flow
- [ ] Integration tests for authority_id=6 restrictions (direct URL)
- [ ] Integration tests for pre-order lifecycle
- [ ] Performance tests: export <10s for 1000 items, search <1s, barcode <500ms
- [ ] Run PHPStan: `vendor/bin/phpstan analyse`
- [ ] Run full test suite: `vendor/bin/phpunit`

---

## Related Documents

- [SRS](../docs/srs-cr4-phase3-store-pickup-management.md)
- [WBS](../docs/wbs-cr4-phase3-store-pickup-management.md)
- [Analysis Report](../aigenerated-report/CR4-Phase3-Requirement-Analysis.md)
- [CR4-Phase2 Skill](cr4-phase2-store-pickup-inventory.md) — predecessor phase
- [Finalized WBS Excel](../docs/wbs/excel/cr4-phase3-store-pickup-management-wbs.xlsx)
