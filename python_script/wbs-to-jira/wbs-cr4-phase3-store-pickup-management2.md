# Work Breakdown Structure — JIRA Import Ready
## CR4 Phase 3 — Store Pickup Order Management

**Generated:** 2026-05-21
**Last Updated:** 2026-06-05
**Source:** CR4_Phase3/CR4-Phase3-final-wbs.xlsx, docs/srs-cr4-phase3-store-pickup-management.md
**Total Stories:** 15
**Total Development Effort:** 292 man-hours

---

## Epic: CR4 Phase 3 — Store Pickup Order Management

**Epic Description:**
> Reduce EC HQ↔Store communication overhead for store pickup orders by enabling EC request management, regional Excel exports, authority-based access control, pre-order lifecycle support, and enhanced admin UX.

---

### Story 1: EC Request Database Schema & Entity Extension

**Type:** Story | **Priority:** High | **Effort:** 8h | **Sprint:** 1

#### Story Overview
Add two new columns (`is_ec_requested` and `output_datetime`) to `dtb_order_item` to support EC request tracking and Excel export audit. Add ORM annotations to `OrderItemTrait.php`, regenerate proxies, and add DB performance indexes. Manual SQL scripts only — no Doctrine migrations.

- **Linked Requirements:** REQ1_COL_001, REQ1_COL_002
- **Affected Components:** `app/Customize/Entity/OrderItemTrait.php`, `init-sql/`, `app/proxy/entity/`
- **Scope:** Backend

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 1.1 | Add `is_ec_requested` and `output_datetime` to dtb_order_item | Backend | 4h |
| 1.2 | ORM mapping in OrderItemTrait.php | Backend | 2h |
| 1.3 | Regenerate proxy and add DB index | Backend | 2h |

#### Sub-task Details

##### Sub-task 1.1: Add `is_ec_requested` and `output_datetime` to dtb_order_item
**Estimate:** 4h

Prepare idempotent manual SQL scripts:
- `ALTER TABLE dtb_order_item ADD COLUMN is_ec_requested BOOLEAN DEFAULT FALSE;`
- `ALTER TABLE dtb_order_item ADD COLUMN output_datetime DATETIME DEFAULT NULL;`

**Acceptance Criteria:**
- [ ] Columns exist in `dtb_order_item` with correct types and defaults
- [ ] Scripts are idempotent (safe to re-run)

##### Sub-task 1.2: ORM mapping in OrderItemTrait.php
**Estimate:** 2h

Add Doctrine ORM annotations:
- `is_ec_requested`: `@ORM\Column(type="boolean", options={"default": false})`
- `output_datetime`: `@ORM\Column(type="datetime", nullable=true)`
- Add getters and setters following existing trait conventions (e.g., `lack_count`, `is_backordered`).

**Acceptance Criteria:**
- [ ] `getIsEcRequested()` / `setIsEcRequested()` work correctly
- [ ] `getOutputDatetime()` / `setOutputDatetime()` work correctly
- [ ] Defaults: `is_ec_requested=false`, `output_datetime=null`

##### Sub-task 1.3: Regenerate proxy and add DB index
**Estimate:** 2h

- Run `bin/console eccube:generate:proxies`
- Create performance indexes:
  - `CREATE INDEX idx_order_item_ec_requested ON dtb_order_item (is_ec_requested);`
  - `CREATE INDEX idx_order_item_output_datetime ON dtb_order_item (output_datetime);`

**Acceptance Criteria:**
- [ ] Proxies regenerated without errors
- [ ] Both indexes created

---

### Story 2: EC Request Checkbox in Order Detail

**Type:** Story | **Priority:** High | **Effort:** 21h | **Sprint:** 1

#### Story Overview
Display an "EC依頼" checkbox per order item row on the admin order detail page, visible only for store pickup orders (order_type ∈ {11, 21, 31}) AND only for out-of-stock items. Checkbox state maps to `is_ec_requested` on `dtb_order_item`. Saved only on explicit Update click.

- **Linked Requirements:** REQ2_ECREQ_001, REQ2_ECREQ_002, REQ2_ECREQ_003
- **Affected Components:** `app/Customize/Form/Type/Admin/OrderType.php`, `app/template/admin/Order/edit.twig`, `app/Customize/Controller/Admin/Order/EditController.php`
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 2.1 | Register `is_ec_requested` in OrderItemType.php form | Backend | 4h |
| 2.2 | EC Request checkbox column in edit.twig | Frontend | 4h |
| 2.3 | Conditional enable/disable logic | Full-stack | 4h |
| 2.4 | Translation label for EC Request column header | Frontend | 1h |
| 2.5 | Unit test case writing | Backend | 4h |
| 2.6 | BAT | QA | 4h |

#### Sub-task Details

##### Sub-task 2.1: Register `is_ec_requested` in OrderItemType.php form
**Estimate:** 4h

Add `CheckboxType` field for `is_ec_requested` per order item in the admin form. Field mapped to entity property via Symfony form data binding.

**Acceptance Criteria:**
- [ ] `is_ec_requested` field exists as `CheckboxType` in OrderItem sub-form
- [ ] Form submission with `is_ec_requested=1` sets entity property to `true`

##### Sub-task 2.2: EC Request checkbox column in edit.twig
**Estimate:** 4h

Render EC依頼 checkbox per order item row using `{{ form_widget(orderItemForm.is_ec_requested) }}`.

**Acceptance Criteria:**
- [ ] Checkbox visible for order_type ∈ {11, 21, 31} and out-of-stock items
- [ ] Checkbox hidden for non-pickup order types and in-stock items

##### Sub-task 2.3: Conditional enable/disable logic
**Estimate:** 4h

JavaScript/Twig logic to conditionally show/hide checkbox based on order type and stock status. Ensure checkbox state is only persisted via Update button.

**Acceptance Criteria:**
- [ ] Checkbox enabled only for OOS items in pickup orders
- [ ] No auto-save — changes only persist on Update click

##### Sub-task 2.4: Translation label for EC Request column header
**Estimate:** 1h

Add translation key for "EC依頼" column header in messages files.

##### Sub-task 2.5: Unit test case writing
**Estimate:** 4h

Test form submission, conditional visibility, and persistence behavior.

**Acceptance Criteria:**
- [ ] Form submitted for order_type=11 with is_ec_requested=1 → flag persisted
- [ ] Form submitted for order_type=1 with is_ec_requested=1 → field ignored

##### Sub-task 2.6: BAT (Business Acceptance Test)
**Estimate:** 4h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity properties must exist |

---

### Story 3: EC Request Excel Export — Core Engine

**Type:** Story | **Priority:** High | **Effort:** 44h | **Sprint:** 2

#### Story Overview
Build the Excel export engine for EC-requested out-of-stock items. Generate .xlsx with 2 sheets (by Order No, by JAN code) per regional HQ (Munakata/Isesaki). Track first-export timestamp via `output_datetime` (write-once). Split by `uketori_location_cd`.

- **Linked Requirements:** REQ3_EXCEL_001–005, NFR-001, NFR-005, NFR-010, NFR-013, NFR-014
- **Affected Components:** `app/Customize/Service/ExcelExportService.php` (NEW), `app/Customize/Controller/Admin/Order/ExcelExportController.php` (NEW), `app/Customize/Repository/OrderRepository.php`, `app/template/admin/Order/index.twig`
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 3.1 | Repository query for EC Request export data | Backend | 4h |
| 3.2 | Excel generation service with PhpSpreadsheet | Backend | 8h |
| 3.3 | Export controller with location routing | Backend | 8h |
| 3.4 | `output_datetime` stamp logic | Backend | 4h |
| 3.5 | Download buttons on order list template | Frontend | 2h |
| 3.6 | Closing time (締日時) calculation | Backend | 4h |
| 3.7 | Sort by JANCODE/Order No. | Backend | 2h |
| 3.8 | Unit test case writing | Backend | 8h |
| 3.9 | BAT | QA | 4h |

#### Sub-task Details

##### Sub-task 3.1: Repository query for EC Request export data
**Estimate:** 4h

Query `dtb_order_item` for items where `is_ec_requested=1`, joined with order data, filtered by `uketori_location_cd` for East/West HQ split.

**Acceptance Criteria:**
- [ ] Query returns only EC-requested items
- [ ] Results filterable by HQ region (Munakata/Isesaki)
- [ ] Uses parameterized queries

##### Sub-task 3.2: Excel generation service with PhpSpreadsheet
**Estimate:** 8h

Create `ExcelExportService` using PhpSpreadsheet v1.24+:
- Sheet_1 【注文番号別】: sorted by Order No ASC
- Sheet_2 【商品別】: sorted by JAN code ASC
- Columns: 注文番号, 店舗名, 分類コード, 分類名, 商品CD, 商品名, EC依頼数, 締日時, 出力済み

**Acceptance Criteria:**
- [ ] .xlsx generated with 2 sheets, correct columns, correct sort order
- [ ] Export completes within 10s for up to 1,000 items (NFR-001)

##### Sub-task 3.3: Export controller with location routing
**Estimate:** 8h

Create `ExcelExportController` with two endpoints — one for East (Isesaki), one for West (Munakata).

**Acceptance Criteria:**
- [ ] Two endpoints functional, each downloads correct regional data
- [ ] Uses dependency injection

##### Sub-task 3.4: `output_datetime` stamp logic
**Estimate:** 4h

Write-once guard at service level: set `output_datetime = NOW()` only when currently NULL.

**Acceptance Criteria:**
- [ ] First export sets timestamp
- [ ] Subsequent exports preserve original timestamp
- [ ] Guard enforced at service level (not just UI)

##### Sub-task 3.5: Download buttons on order list template
**Estimate:** 2h

Add download action buttons/links for EC依頼リスト on the order list page.

##### Sub-task 3.6: Closing time (締日時) calculation
**Estimate:** 4h

Implement cutoff time logic: orders cut off at 8:30 / 12:30 for export windows.

##### Sub-task 3.7: Sort by JANCODE/Order No.
**Estimate:** 2h

Sheet_1 sorted by 注文番号 ASC, Sheet_2 sorted by JAN code ASC.

##### Sub-task 3.8: Unit test case writing
**Estimate:** 8h

Test export generation, write-once guard, HQ split, sort order, empty/large data sets.

##### Sub-task 3.9: BAT
**Estimate:** 4h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | `is_ec_requested` and `output_datetime` columns must exist |
| Q-02 | Blocked-by | East/West `uketori_location_cd` mapping needed |
| Q-09 | Info-needed | EC依頼数 = `lack_count` or separate field? |

---

### Story 4: SC Collaboration for Store Pickup Orders

**Type:** Story | **Priority:** High | **Effort:** 26h | **Sprint:** 2

#### Story Overview
Align SC連携 (Batch007Command) timing for store pickup orders to use the same timing as delivery-installation orders. Existing type mapping (11→2, 21→4, 31→6) is preserved — only timing/filter conditions change. Store pickup orders must proceed even with out-of-stock items.

- **Linked Requirements:** REQ4_SC_001–003, NFR-012
- **Affected Components:** `app/Customize/Command/Batch007Command.php`, state machine configuration
- **Scope:** Backend / Integration

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 4.1 | State machine modification for SC_OPTION in pickup flow | Backend | 8h |
| 4.2 | Verify and update Batch007 for pickup order types | Backend | 4h |
| 4.3 | Verify SC status reuse (no new status) | Backend | 2h |
| 4.4 | Unit test case writing | Backend | 8h |
| 4.5 | BAT | QA | 4h |

#### Sub-task Details

##### Sub-task 4.1: State machine modification for SC_OPTION in pickup flow
**Estimate:** 8h

Modify state machine to align store pickup order SC連携 timing with delivery-installation timing.

**Acceptance Criteria:**
- [ ] Store pickup orders processed at delivery-installation cutoff timing
- [ ] Existing delivery-installation logic unaffected (backward compatible)

##### Sub-task 4.2: Verify and update Batch007 for pickup order types
**Estimate:** 4h

Verify Batch007Command Lines 533-537 mapping (11→2, 21→4, 31→6) is preserved. Update filter conditions.

**Acceptance Criteria:**
- [ ] Type mapping unchanged: 11→2, 21→4, 31→6
- [ ] Pickup orders included in SC連携 batch at correct timing

##### Sub-task 4.3: Verify SC status reuse (no new status)
**Estimate:** 2h

Confirm no new `dcm_shipping_status` values needed.

##### Sub-task 4.4: Unit test case writing
**Estimate:** 8h

Test timing alignment, backward compatibility, OOS non-blocking.

##### Sub-task 4.5: BAT
**Estimate:** 4h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| AMS coordination | Relates-to | JIRA: MRMAX_ECOPE-3335 |

---

### Story 5: Pre-Order Pickup Support (Type 31)

**Type:** Story | **Priority:** High | **Effort:** 28h | **Sprint:** 2

#### Story Overview
Full lifecycle support for pre-order in-store pickup (order_type=31). Status transitions: order_status 1→4→5→8, preorder_status 1→9, shipping 0→1→2→9, delivery 0→3(CAN_RECEIVE)→9(DONE). Barcode displayed at delivery_status=CAN_RECEIVE(3), email sent at that transition. After barcode display, follows regular store pickup flow.

- **Linked Requirements:** REQ6_PREORDER_001–005
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/Customize/Service/OrderState/OrderStateHelper.php`, templates, email templates
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 5.1 | Type 31 pickup flow integration in controllers/services | Backend | 8h |
| 5.2 | Pre-order status mapping | Backend | 4h |
| 5.3 | Email notification at delivery_status=3 for type 31 | Backend | 4h |
| 5.4 | Barcode display at delivery_status=3 for type 31 | Frontend | 4h |
| 5.5 | Barcode scan → delivery_status=9 for type 31 | Full-stack | 4h |
| 5.6 | Arranging(4) access for type 31 with backorder | Backend | 4h |

#### Sub-task Details

##### Sub-task 5.1: Type 31 pickup flow integration
**Estimate:** 8h

Integrate order_type=31 into existing pickup flow. Same flow as regular store pickup until delivery_status → CAN_RECEIVE.

**Acceptance Criteria:**
- [ ] order_type=31 follows status transitions: order 1→4→5→8, preorder 1→9, shipping 0→1→2→9, delivery 0→3→9

##### Sub-task 5.2: Pre-order status mapping
**Estimate:** 4h

Map pre-order specific statuses (preorder_status 1→9) alongside standard order status transitions.

##### Sub-task 5.3: Email notification at delivery_status=3
**Estimate:** 4h

Send automated email to customer when delivery_status changes to CAN_RECEIVE(3).

**Acceptance Criteria:**
- [ ] Email sent on delivery_status transition to 3
- [ ] Email follows existing `MailService` patterns

##### Sub-task 5.4: Barcode display at delivery_status=3
**Estimate:** 4h

Show barcode to customer after delivery_status reaches 受取可能(3).

**Acceptance Criteria:**
- [ ] Barcode visible at CAN_RECEIVE status
- [ ] Code128 format

##### Sub-task 5.5: Barcode scan → delivery_status=9
**Estimate:** 4h

Scanning barcode completes pickup: delivery_status → DONE(9).

##### Sub-task 5.6: Arranging(4) access for type 31 with backorder
**Estimate:** 4h

Handle 商品手配中(Arranging) status access for type 31 when items have backorder.

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity changes required |

---

### Story 6: Auto-Save Removal from Order Edit

**Type:** Story | **Priority:** High | **Effort:** 14h | **Sprint:** 1

#### Story Overview
Remove existing auto-save AJAX behavior from the order detail page. Changes must only persist on explicit Update button click. Add client-side subtotal recalculation, form validation on explicit submit, and dirty-form warning on navigation away.

- **Linked Requirements:** REQ5_DETAIL_001, REQ5_DETAIL_002
- **Affected Components:** `app/template/admin/Order/edit.twig` (JS), `app/Customize/Controller/Admin/Order/EditController.php`
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 6.1 | Remove auto-submit triggers from edit.twig | Frontend | 4h |
| 6.2 | Client-side subtotal recalculation | Frontend | 4h |
| 6.3 | Form validation on explicit submit | Full-stack | 4h |
| 6.4 | Dirty-form warning on navigation | Frontend | 2h |

#### Sub-task Details

##### Sub-task 6.1: Remove auto-submit triggers from edit.twig
**Estimate:** 4h

Identify and remove/disable all AJAX auto-save calls in order detail page JavaScript.

**Acceptance Criteria:**
- [ ] No field changes trigger automatic persistence
- [ ] All saves require explicit Update click

##### Sub-task 6.2: Client-side subtotal recalculation
**Estimate:** 4h

Subtotal calculations happen client-side in JavaScript without server round-trips.

**Acceptance Criteria:**
- [ ] Subtotals update correctly in browser as fields change
- [ ] No server requests until Update click

##### Sub-task 6.3: Form validation on explicit submit
**Estimate:** 4h

Form validation runs on Update button click.

**Acceptance Criteria:**
- [ ] Validation errors displayed on Update click
- [ ] Invalid forms not submitted

##### Sub-task 6.4: Dirty-form warning on navigation
**Estimate:** 2h

Browser warning when navigating away with unsaved changes.

**Acceptance Criteria:**
- [ ] Confirmation dialog on navigate away with dirty form
- [ ] No warning when form is clean

---

### Story 7: Server-Side EC Request Validation & Business Rules

**Type:** Story | **Priority:** High | **Effort:** 8h | **Sprint:** 1

#### Story Overview
Implement server-side validation for EC request operations. Ensure `is_ec_requested` can only be set for eligible items (pickup orders + OOS). Auto-reset the flag when backorder condition is cleared.

- **Linked Requirements:** REQ2_ECREQ_002, NFR-011
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/Customize/Service/` (new or existing)
- **Scope:** Backend

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 7.1 | Server-side EC Request validation | Backend | 4h |
| 7.2 | Auto-reset `is_ec_requested` when backorder cleared | Backend | 4h |

#### Sub-task Details

##### Sub-task 7.1: Server-side EC Request validation
**Estimate:** 4h

Validate at controller/service level that `is_ec_requested` can only be set to `true` when order_type ∈ {11, 21, 31} AND item is out of stock. Server-side enforcement, not CSS-only.

**Acceptance Criteria:**
- [ ] Server rejects `is_ec_requested=true` for non-pickup orders
- [ ] Server rejects `is_ec_requested=true` for in-stock items

##### Sub-task 7.2: Auto-reset `is_ec_requested` when backorder cleared
**Estimate:** 4h

When an item's stock status changes from OOS to available, automatically reset `is_ec_requested=false`.

**Acceptance Criteria:**
- [ ] `is_ec_requested` automatically cleared when item restocked
- [ ] Reset happens at service level

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity properties must exist |

---

### Story 8: Products List Template Update

**Type:** Story | **Priority:** Medium | **Effort:** 4h | **Sprint:** 2

#### Story Overview
Display EC Request status information in the products list template so store staff can see which items have been EC-requested.

- **Linked Requirements:** REQ2_ECREQ_001
- **Affected Components:** `app/template/admin/Order/products_list.twig`
- **Scope:** Frontend

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 8.1 | EC Request status display in products_list.twig | Frontend | 4h |

#### Sub-task Details

##### Sub-task 8.1: EC Request status display in products_list.twig
**Estimate:** 4h

Add visual indicator (icon/badge/label) showing EC request status per product item in the products list view.

**Acceptance Criteria:**
- [ ] EC-requested items visually distinguishable in products list
- [ ] Status reflects current `is_ec_requested` value

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity property must exist |

---

### Story 9: Cancelled Order EC Request Handling

**Type:** Story | **Priority:** Medium | **Effort:** 3h | **Sprint:** 2

#### Story Overview
Handle edge cases for cancelled orders: exclude cancelled orders from EC Request Excel export, and disable EC Request checkbox on cancelled orders.

- **Linked Requirements:** REQ3_EXCEL_001 (edge case)
- **Affected Components:** `app/Customize/Repository/OrderRepository.php`, `app/template/admin/Order/edit.twig`
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 9.1 | Exclude cancelled orders from EC Request export | Backend | 2h |
| 9.2 | Disable EC Request checkbox on cancelled orders | Frontend | 1h |

#### Sub-task Details

##### Sub-task 9.1: Exclude cancelled orders from EC Request export
**Estimate:** 2h

Add filter to export repository query to exclude orders with cancelled status.

**Acceptance Criteria:**
- [ ] Cancelled orders not included in Excel export

##### Sub-task 9.2: Disable EC Request checkbox on cancelled orders
**Estimate:** 1h

Disable (grey out) EC依頼 checkbox when order is cancelled.

**Acceptance Criteria:**
- [ ] EC依頼 checkbox disabled for cancelled orders

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 2 | Blocked-by | EC checkbox must exist |
| Story 3 | Blocked-by | Export query must exist |

---

### Story 10: Integration Testing & Quality Assurance

**Type:** Story | **Priority:** High | **Effort:** 16h | **Sprint:** 4

#### Story Overview
End-to-end integration tests covering all EC Request flows, Excel export correctness, auto-save removal regression, and pre-order type 31 lifecycle.

- **Linked Requirements:** NFR-001–014
- **Affected Components:** `codeception/CR4_Phase-3/` (new test files)
- **Scope:** Test

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 10.1 | EC Request end-to-end test scenarios | QA | 4h |
| 10.2 | Excel export performance and correctness test | QA | 4h |
| 10.3 | Auto-save removal regression test | QA | 4h |
| 10.4 | Pre-order type 31 flow test | QA | 4h |

#### Sub-task Details

##### Sub-task 10.1: EC Request end-to-end test scenarios
**Estimate:** 4h

Test full flow: set EC依頼 → export → verify output_datetime → search filters.

##### Sub-task 10.2: Excel export performance and correctness test
**Estimate:** 4h

Test with 0, 1, and 1,000+ items. Verify sort order, sheet structure, HQ split.

##### Sub-task 10.3: Auto-save removal regression test
**Estimate:** 4h

Verify no auto-save behavior remains. Test dirty-form warnings, client-side recalculations.

##### Sub-task 10.4: Pre-order type 31 flow test
**Estimate:** 4h

Test full lifecycle: order → status transitions → barcode → email → scan completion.

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Stories 1–9, 11–15 | Blocked-by | All features deployed to test environment |

---

### Story 11: Order Detail Popup Flow for Shipping Status Changes

**Type:** Story | **Priority:** High | **Effort:** 28h | **Sprint:** 3

#### Story Overview
Restructure confirmation popup behavior on order detail page. Popup appears ONLY when shipping status changes to 商品手配中 + Update clicked — NOT on OOS/EC依頼 checkbox changes. Popup includes "Send notification email" checkbox (default unchecked). If email not sent, popup re-appears on next status-changing update.

- **Linked Requirements:** REQ5_DETAIL_003–005
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/template/admin/Order/edit.twig`, `app/Customize/Service/OrderState/OrderStateHelper.php`
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 11.1 | Implement popup trigger on shipping→商品手配中 status change | Full-stack | 8h |
| 11.2 | Add email notification opt-in checkbox in popup (default unchecked) | Frontend | 4h |
| 11.3 | Backend email dispatch conditional on popup checkbox | Backend | 4h |
| 11.4 | Popup persistence logic (re-appears if email not sent) | Full-stack | 4h |
| 11.5 | Unit test case writing | Backend | 4h |
| 11.6 | BAT | QA | 4h |

#### Sub-task Details

##### Sub-task 11.1: Implement popup trigger on shipping→商品手配中 status change
**Estimate:** 8h

JavaScript intercept on Update: detect shipping status change to 商品手配中, show modal popup. Popup must NOT appear for OOS/EC依頼 checkbox changes only.

**Acceptance Criteria:**
- [ ] Popup triggers only when shipping status → 商品手配中
- [ ] No popup on OOS/EC依頼 checkbox-only changes
- [ ] Multiple status changes before Update → popup based on final state

##### Sub-task 11.2: Add email notification opt-in checkbox in popup
**Estimate:** 4h

Checkbox label: "通知メールを送信する" — default unchecked (opt-in). Value submitted via form POST.

**Acceptance Criteria:**
- [ ] Checkbox defaults to unchecked
- [ ] Checked value transmitted to backend

##### Sub-task 11.3: Backend email dispatch conditional on popup checkbox
**Estimate:** 4h

Read `send_notification_email` flag from request. Dispatch email only when flag is true.

**Acceptance Criteria:**
- [ ] Email sent when checkbox checked + confirmed
- [ ] No email when checkbox unchecked

##### Sub-task 11.4: Popup persistence logic
**Estimate:** 4h

Popup re-appears on next status-changing update if previous update did not send email.

**Acceptance Criteria:**
- [ ] Popup re-appears if email was skipped
- [ ] Email-sent state tracked per order/shipping

##### Sub-task 11.5: Unit test case writing
**Estimate:** 4h

##### Sub-task 11.6: BAT
**Estimate:** 4h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 6 | Blocked-by | Auto-save removal must be complete |
| Q-01 | Blocked-by | 商品手配中 must exist in `dcm_shipping_status` |

---

### Story 12: Authority ID=6 — Store Pickup Staff Role Configuration

**Type:** Story | **Priority:** High | **Effort:** 34h | **Sprint:** 3

#### Story Overview
Create authority_id=6 (店舗受取担当) with restricted access. Cannot view PG Multi-Payment payment info, Member ID Link, or Customer Flag. Filtered to store pickup order types only (11, 21, 31). Restrictions enforced server-side, not just template hiding. deny_url MUST NOT include '/order'.

- **Linked Requirements:** REQ7_AUTH_001–006, NFR-008, NFR-009
- **Affected Components:** `app/Customize/DataFixture/Master/csv/mtb_authority.csv`, `app/Customize/DataFixture/Master/csv/authority_role.csv`, `app/Customize/Controller/Admin/Order/EditController.php`, `app/Customize/Controller/Admin/Order/OrderController.php`, templates
- **Scope:** Full-stack / Security

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 12.1 | Insert authority_id=6 into mtb_authority + deny_url entries | Backend | 4h |
| 12.2 | Server-side PG Multi-Payment info restriction (EditController) | Backend | 4h |
| 12.3 | Order Category filter restriction for authority_id=6 | Backend | 4h |
| 12.4 | Inactivate Member ID Link and Customer Flag for authority_id=6 | Backend | 2h |
| 12.5 | Template-level hiding for restricted areas | Frontend | 4h |
| 12.6 | Entry-point agnostic enforcement (Order List + Store Pickup Mgmt) | Backend | 4h |
| 12.7 | Unit test case writing | Backend | 8h |
| 12.8 | BAT | QA | 4h |

#### Sub-task Details

##### Sub-task 12.1: Insert authority_id=6 + deny_url entries
**Estimate:** 4h

SQL: `INSERT INTO mtb_authority (id, name, sort_no, discriminator_type) VALUES (6, '店舗受取担当', 6, 'authority');`
deny_url entries MUST NOT include '/order'. Update CSV fixtures.

**Acceptance Criteria:**
- [ ] authority_id=6 exists in mtb_authority
- [ ] deny_url does NOT include '/order'

##### Sub-task 12.2: Server-side PG Multi-Payment info restriction
**Estimate:** 4h

Controller-level check in EditController: block PG payment info for authority_id=6. Return 403 on direct URL access.

**Acceptance Criteria:**
- [ ] PG payment area inaccessible for authority_id=6
- [ ] 403 on direct URL access attempt

##### Sub-task 12.3: Order Category filter restriction
**Estimate:** 4h

Filter order list for authority_id=6 to only show order_type ∈ {11, 21, 31}.

**Acceptance Criteria:**
- [ ] authority_id=6 sees only pickup order types
- [ ] Filter enforced at query level

##### Sub-task 12.4: Inactivate Member ID Link and Customer Flag
**Estimate:** 2h

Disable Member ID Link and Customer Flag features for authority_id=6.

##### Sub-task 12.5: Template-level hiding
**Estimate:** 4h

Hide restricted UI elements for authority_id=6 in templates (complementary to server-side).

##### Sub-task 12.6: Entry-point agnostic enforcement
**Estimate:** 4h

Same restrictions from 商品受渡処理, 受注一覧, and direct URL.

**Acceptance Criteria:**
- [ ] Restrictions identical regardless of entry point

##### Sub-task 12.7: Unit test case writing
**Estimate:** 8h

##### Sub-task 12.8: BAT
**Estimate:** 4h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Q-06 | Info-needed | Complete deny_url list pending |

---

### Story 13: 商品受渡処理 Screen — Rename & Barcode Confirmation

**Type:** Story | **Priority:** High | **Effort:** 30h | **Sprint:** 3

#### Story Overview
Rename store pickup management screen: '店舗受取管理' → '商品受渡処理'. Implement barcode scan → immediate confirmation popup with timestamp, order details, and irreversibility warning. Screen elements: barcode input, store dropdown, receipt status filter (未/済み/全て), date range, results table.

- **Linked Requirements:** REQ8_SCREEN_001–005, NFR-004, NFR-006, NFR-007
- **Affected Components:** Admin navigation templates, Store Pickup Management controller, templates
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 13.1 | Rename menu label from 店舗受取管理 to 商品受渡処理 | Frontend | 2h |
| 13.2 | Implement barcode scan → confirmation popup flow | Full-stack | 8h |
| 13.3 | Add scan timestamp display in popup | Frontend | 4h |
| 13.4 | Confirmation popup with order details + irreversibility warning | Frontend | 4h |
| 13.5 | Screen elements: barcode input, store dropdown, status filter, date range | Frontend | 4h |
| 13.6 | Unit test case writing | Backend | 4h |
| 13.7 | BAT | QA | 4h |

#### Sub-task Details

##### Sub-task 13.1: Rename menu label
**Estimate:** 2h

Update admin navigation and translation files.

##### Sub-task 13.2: Barcode scan → confirmation popup
**Estimate:** 8h

On barcode scan, immediately show confirmation popup. Response < 500ms (NFR-004).

**Acceptance Criteria:**
- [ ] Barcode scan triggers popup immediately
- [ ] Response time < 500ms
- [ ] Idempotent: if already DONE, show warning

##### Sub-task 13.3: Scan timestamp display
**Estimate:** 4h

Show timestamp of barcode scan in confirmation popup.

##### Sub-task 13.4: Confirmation popup content
**Estimate:** 4h

Order summary + irreversibility warning in popup.

**Acceptance Criteria:**
- [ ] Order details visible
- [ ] Irreversibility warning clearly displayed

##### Sub-task 13.5: Screen elements
**Estimate:** 4h

Barcode input, store dropdown, receipt status filter (未/済み/全て), date range, results table.

##### Sub-task 13.6: Unit test case writing
**Estimate:** 4h

##### Sub-task 13.7: BAT
**Estimate:** 4h

---

### Story 14: EC依頼 & ファイル出力済み Search Filters on Order List

**Type:** Story | **Priority:** Medium | **Effort:** 20h | **Sprint:** 3

#### Story Overview
Add two radio filter groups to order list:
1. EC依頼: すべて / 依頼あり (is_ec_requested=1)
2. ファイル出力済み: すべて / 未出力のみ (output_datetime IS NULL)

- **Linked Requirements:** REQ9_SEARCH_001, REQ9_SEARCH_002, NFR-003
- **Affected Components:** `app/Customize/Form/Type/Admin/OrderType.php`, `app/Customize/Repository/OrderRepository.php`, `app/template/admin/Order/index.twig`
- **Scope:** Full-stack

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 14.1 | Add EC依頼 radio to OrderType search form | Backend | 2h |
| 14.2 | Add ファイル出力済み radio to OrderType search form | Backend | 2h |
| 14.3 | Extend OrderRepository for `is_ec_requested` filter query | Backend | 4h |
| 14.4 | Extend OrderRepository for `output_datetime IS NULL` filter query | Backend | 4h |
| 14.5 | Render radio filters in order list template | Frontend | 2h |
| 14.6 | Unit test case writing | Backend | 4h |
| 14.7 | BAT | QA | 2h |

#### Sub-task Details

##### Sub-task 14.1: Add EC依頼 radio to search form
**Estimate:** 2h

`ChoiceType` with expanded=true: すべて (no condition) / 依頼あり (is_ec_requested=1).

##### Sub-task 14.2: Add ファイル出力済み radio to search form
**Estimate:** 2h

`ChoiceType` with expanded=true: すべて (no condition) / 未出力のみ (output_datetime IS NULL).

##### Sub-task 14.3: Extend OrderRepository for EC依頼 filter
**Estimate:** 4h

**Acceptance Criteria:**
- [ ] すべて = no additional condition
- [ ] 依頼あり = only items with is_ec_requested=1
- [ ] Search < 1s with proper indexing (NFR-003)
- [ ] Uses parameterized queries

##### Sub-task 14.4: Extend OrderRepository for output_datetime filter
**Estimate:** 4h

**Acceptance Criteria:**
- [ ] すべて = no additional condition
- [ ] 未出力のみ = only items where output_datetime IS NULL

##### Sub-task 14.5: Render radio filters in template
**Estimate:** 2h

##### Sub-task 14.6: Unit test case writing
**Estimate:** 4h

##### Sub-task 14.7: BAT
**Estimate:** 2h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Columns and indexes must exist |

---

### Story 15: Export Timing (Cutoff) Configuration

**Type:** Story | **Priority:** Medium | **Effort:** 8h | **Sprint:** 2

#### Story Overview
Implement cutoff time filtering in Excel export query (8:30/12:30 → 10:15/15:15) and add admin navigation menu items for the two regional EC依頼リスト exports.

- **Linked Requirements:** REQ3_EXCEL_005
- **Affected Components:** `app/Customize/Service/ExcelExportService.php`, admin navigation templates
- **Scope:** Backend / Frontend

#### Sub-task List
| # | Sub-task | Skill | Estimate |
|---|---------|-------|----------|
| 15.1 | Implement cutoff time filtering in export query (8:30/12:30) | Backend | 4h |
| 15.2 | Admin navigation for EC依頼リスト_伊勢崎拠点 / 宗像拠点 menu items | Frontend | 2h |
| 15.3 | Unit test case writing | Backend | 2h |

#### Sub-task Details

##### Sub-task 15.1: Cutoff time filtering
**Estimate:** 4h

Filter export data by cutoff windows: orders before 8:30 for morning export, between 8:30-12:30 for afternoon export.

**Acceptance Criteria:**
- [ ] Correct time window applied
- [ ] Orders outside window excluded

##### Sub-task 15.2: Admin navigation menu items
**Estimate:** 2h

Add two menu items:
- "EC依頼リスト_伊勢崎拠点" (East)
- "EC依頼リスト_宗像拠点" (West)

**Acceptance Criteria:**
- [ ] Both menu items visible and link to correct endpoints

##### Sub-task 15.3: Unit test case writing
**Estimate:** 2h

**Dependencies:**
| Dependency | Type | Details |
|---|---|---|
| Story 3 | Blocked-by | Export service must exist |

---

## Cross-Story Dependencies

```
Story 1 (DB/Entity) ──► Story 2 (EC依頼 Checkbox)
                    ──► Story 3 (Excel Export)
                    ──► Story 5 (Pre-order)
                    ──► Story 7 (Server-Side Validation)
                    ──► Story 8 (Products List)
                    ──► Story 14 (Search Filters)

Story 2 ──► Story 7 (Validation) — shared entity logic
       ──► Story 9 (Cancelled Orders) — checkbox prerequisite

Story 3 ──► Story 9 (Cancelled Export) — export query prerequisite
       ──► Story 15 (Cutoff Timing) — export service extension

Story 6 (Auto-Save) ──► Story 11 (Popup Flow) — auto-save removal prerequisite

Stories 1–9, 11–15 ──► Story 10 (Integration Tests)
```

---

## Suggested Sprint Allocation

| Sprint | Stories | Dev Effort | Focus |
|--------|---------|-----------|-------|
| Sprint 1 | Story 1 (DB), Story 2 (EC Checkbox), Story 6 (Auto-Save), Story 7 (Validation) | 51h | Foundation + Order Detail |
| Sprint 2 | Story 3 (Excel Export), Story 4 (SC連携), Story 5 (Pre-order), Story 8 (Products List), Story 9 (Cancelled), Story 15 (Cutoff) | 113h | Core Features + Export Engine |
| Sprint 3 | Story 11 (Popup), Story 12 (Authority), Story 13 (商品受渡処理), Story 14 (Filters) | 112h | Authority + Screen + Popup + Filters |
| Sprint 4 | Story 10 (Integration Testing) | 16h | Testing & Validation |
| **Total** | **15 Stories** | **292h** | — |

---

## Risk Summary

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R-01 | Q-01 blocker: 商品手配中 not in `dcm_shipping_status` | High | High — blocks Story 11 popup | Escalate immediately; fallback: use existing status value |
| R-02 | Q-02 blocker: East/West `uketori_location_cd` mapping unknown | High | High — blocks Story 3 Excel export | Request mapping table from business team ASAP |
| R-03 | AMS SC連携 coordination delay (MRMAX_ECOPE-3335) | Medium | Medium — blocks Story 4 | Begin dev with mock timing; integrate AMS response later |
| R-04 | Incomplete deny_url list for authority_id=6 (Q-06) | Medium | Medium — incomplete security config | Start with known restrictions; iterate when full list available |
| R-05 | EC依頼数 field mapping unclear (Q-09) | Low | Low — fallback to `lack_count` | Implement with `lack_count`; update if different field confirmed |
| R-06 | Simultaneous Excel export race conditions | Low | Medium — duplicate timestamps | Write-once SQL WHERE clause mitigates |

---

## Assumptions

1. PhpSpreadsheet v1.24+ is available in `composer.json` — no additional installation required
2. `is_ec_requested` checkbox visibility is determined by combination of `order_type` and item stock status fields already available in the entity
3. Existing barcode scan infrastructure on 商品受渡処理 supports Code128 format
4. `EC依頼数` maps to `lack_count` unless Q-09 resolution indicates otherwise
5. Email templates for pre-order 受取可能 notification follow existing `MailService` patterns
6. Authority access control follows existing EC-CUBE 4.x `mtb_authority` + `authority_role` pattern
7. All new files are created in `app/Customize/` — NEVER in `src/Eccube/`
8. Database changes are manual SQL only — NO Doctrine migrations
9. Export cutoff times (8:30/12:30 → 10:15/15:15) are fixed operational requirements
10. `ShippingController.php` is the controller for the 商品受渡処理 screen (or closest equivalent)

---

## Traceability Matrix

| SRS Requirement | Story | Sub-tasks | Status |
|-----------------|-------|-----------|--------|
| REQ1_COL_001 | Story 1 | 1.1, 1.2, 1.3 | Planned |
| REQ1_COL_002 | Story 1 | 1.1, 1.2, 1.3 | Planned |
| REQ2_ECREQ_001 | Story 2 | 2.1, 2.2, 2.3 | Planned |
| REQ2_ECREQ_002 | Story 2, Story 7 | 2.3, 7.1 | Planned |
| REQ2_ECREQ_003 | Story 2 | 2.1, 2.3 | Planned |
| REQ3_EXCEL_001 | Story 3 | 3.1, 3.3 | Planned — Blocked (Q-02) |
| REQ3_EXCEL_002 | Story 3 | 3.2, 3.7 | Planned |
| REQ3_EXCEL_003 | Story 3 | 3.2 | Planned |
| REQ3_EXCEL_004 | Story 3 | 3.4 | Planned |
| REQ3_EXCEL_005 | Story 3, Story 15 | 3.5, 15.2 | Planned |
| REQ4_SC_001 | Story 4 | 4.1 | Planned |
| REQ4_SC_002 | Story 4 | 4.2 | Planned |
| REQ4_SC_003 | Story 4 | 4.1 | Planned |
| REQ5_DETAIL_001 | Story 6 | 6.1, 6.2, 6.3 | Planned |
| REQ5_DETAIL_002 | Story 6 | 6.1 | Planned |
| REQ5_DETAIL_003 | Story 11 | 11.1 | Planned — Blocked (Q-01) |
| REQ5_DETAIL_004 | Story 11 | 11.2, 11.3 | Planned |
| REQ5_DETAIL_005 | Story 11 | 11.4 | Planned |
| REQ6_PREORDER_001 | Story 5 | 5.1 | Planned |
| REQ6_PREORDER_002 | Story 5 | 5.4 | Planned |
| REQ6_PREORDER_003 | Story 5 | 5.5 | Planned |
| REQ6_PREORDER_004 | Story 5 | 5.1, 5.2 | Planned |
| REQ6_PREORDER_005 | Story 5 | 5.3 | Planned |
| REQ7_AUTH_001 | Story 12 | 12.1 | Planned |
| REQ7_AUTH_002 | Story 12 | 12.2, 12.5 | Planned |
| REQ7_AUTH_003 | Story 12 | 12.4 | Planned |
| REQ7_AUTH_004 | Story 12 | 12.2, 12.6 | Planned |
| REQ7_AUTH_005 | Story 12 | 12.1 | Planned |
| REQ7_AUTH_006 | Story 12 | 12.3, 12.5 | Planned |
| REQ8_SCREEN_001 | Story 13 | 13.1 | Planned |
| REQ8_SCREEN_002 | Story 13 | 13.2 | Planned |
| REQ8_SCREEN_003 | Story 13 | 13.3 | Planned |
| REQ8_SCREEN_004 | Story 13 | 13.5 | Planned |
| REQ8_SCREEN_005 | Story 13 | 13.4 | Planned |
| REQ9_SEARCH_001 | Story 14 | 14.1, 14.3, 14.5 | Planned |
| REQ9_SEARCH_002 | Story 14 | 14.2, 14.4, 14.5 | Planned |
| US-001 | Story 2 | 2.1–2.6 | Planned |
| US-002 | Story 3 | 3.1–3.9 | Planned |
| US-003 | Story 3 | 3.1–3.9 | Planned |
| US-004 | Story 8 | 8.1 | Planned |
| US-005 | Story 6 | 6.1–6.4 | Planned |
| US-006 | Story 11 | 11.1–11.6 | Planned |
| US-007 | Story 12 | 12.3 | Planned |
| US-008 | Story 12 | 12.2, 12.5 | Planned |
| US-009 | Story 13 | 13.2 | Planned |
| US-010 | Story 5 | 5.3 | Planned |
| US-011 | Story 5 | 5.4 | Planned |
| US-012 | Story 14 | 14.1, 14.3, 14.5 | Planned |
| US-013 | Story 14 | 14.2, 14.4, 14.5 | Planned |
| US-014 | Story 4 | 4.1–4.5 | Planned |
| NFR-001 | Story 3 | 3.2 | Planned |
| NFR-002 | Story 2 | 2.2 | Planned |
| NFR-003 | Story 14 | 14.3, 14.4 | Planned |
| NFR-004 | Story 13 | 13.2 | Planned |
| NFR-005 | Story 3 | 3.2 | Planned |
| NFR-006 | Story 13 | 13.1 | Planned |
| NFR-007 | Story 13 | 13.4 | Planned |
| NFR-008 | Story 12 | 12.2 | Planned |
| NFR-009 | Story 12 | 12.2 | Planned |
| NFR-010 | Story 3 | 3.4 | Planned |
| NFR-011 | Story 7 | 7.1 | Planned |
| NFR-012 | Story 4 | 4.4 | Planned |
| NFR-013 | Story 3 | 3.2 | Planned |
| NFR-014 | Story 3 | 3.4 | Planned |
