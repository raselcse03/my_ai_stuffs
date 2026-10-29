---
name: cr4-phase3-store-pickup-preorder
description: "CR4 Phase 3 store-pickup order management: EC-request flags on dtb_order_item, out-of-stock Excel export (Isesaki/Munakata HQ split), order_type=31 pre-order barcode flow, authority_id=6 (店舗受取担当) restrictions, Batch007 SC連携 timing, and 商品受渡処理 barcode confirmation. Loaded by the [CR4-Phase3] project tag."
---

# CR4-Phase3: Store Pickup Order Management Skill

**Prerequisites:** Review `core-essentials.md` for critical rules. Review `change-request.md` for CR methodology.

**Deep context (load on demand):** for EC-request export internals, out-of-stock Excel generation, and edge-case walkthroughs read `cr4-phase3-store-pickup-preorder-deep.md`. Do not load it unless the task touches those areas.

---

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

> **Moved to the deep companion** (see pointer above):
> - Expected Outcome → deep file § Expected Outcome
> - WBS Story Map → deep file § WBS Story Map (Finalized — 16 Stories, 259.5h)
> - Key Entities → deep file § Key Entities

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

*Rules 1–4 → deep file § Business Rules (Extended)*

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

*Rule 6 → deep file § Business Rules (Extended)*

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

*Rules 8–9 → deep file § Business Rules (Extended)*

---

## Key Functions/Methods

→ deep file § Key Functions/Methods (OrderItemTrait properties, OrderItemType checkbox, ExcelExportService export logic, EditController validation/authority/popup, OrderRepository search SQL, Batch007 timing, edit.twig JS).

---

> **Moved to the deep companion** (see pointer above):
> - Validation Rules → deep file § Validation Rules
> - Open Questions (Blockers) → deep file § Open Questions (Blockers)
> - Common Bug Patterns → deep file § Common Bug Patterns & Prevention
> - Testing Scenarios → deep file § Testing Scenarios

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
