# Work Breakdown Structure — JIRA Import Ready
## CR4 Phase 3 — Store Pickup Order Management

**Generated:** 2026-05-21
**Source:** docs/srs-cr4-phase3-store-pickup-management.md
**Total Stories:** 14
**Total Story Points:** 79

---

## Epic: CR4 Phase 3 — Store Pickup Order Management

**Epic Description:**
> Reduce EC HQ↔Store communication overhead for store pickup orders by enabling EC request management, regional Excel exports, authority-based access control, pre-order lifecycle support, and enhanced admin UX.

---

### Story 1: DB Schema & Entity Extensions for EC Request Tracking

**Type:** Story | **Priority:** High | **Points:** 3 | **Sprint:** 1

#### Story Overview
Add two new columns (`is_ec_requested` and `output_datetime`) to `dtb_order_item` to support EC request tracking and Excel export audit. The `is_ec_requested` boolean flag indicates whether a store has requested EC HQ to fulfill an out-of-stock item. The `output_datetime` column records the timestamp of the first Excel export containing that order item — it is write-once and never overwritten. Corresponding Doctrine ORM annotations must be added to `OrderItemTrait.php`. Performance indexes are required for both columns since they back radio filter queries on the order list. Manual SQL scripts must be prepared — no Doctrine migrations. The master data CSV for `mtb_authority` must also be updated to include the new authority_id=6 record, though the authority behavioral logic is covered in a separate story. This story is the foundational data layer that all other stories depend on.

- **Linked Requirements:** REQ1_COL_001, REQ1_COL_002, REQ7_AUTH_001 (data only)
- **Affected Components:** `app/Customize/Entity/OrderItemTrait.php`, `init-sql/`, `app/Customize/DataFixture/Master/csv/mtb_authority.csv`
- **Scope:** Backend

#### Sub-task List
- [ ] 1.1 — Add `is_ec_requested` and `output_datetime` properties to OrderItemTrait (Backend, 4h)
- [ ] 1.2 — Prepare manual SQL scripts for schema, indexes, and master data (Backend, 4h)
- [ ] 1.3 — Unit tests for entity properties and defaults (Backend, 2h)

---

#### Sub-tasks:

##### Sub-task 1.1: Add `is_ec_requested` and `output_datetime` properties to OrderItemTrait
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Extend `OrderItemTrait.php` with two new Doctrine ORM-annotated properties: `is_ec_requested` (boolean, default false) and `output_datetime` (datetime, nullable). Add getters and setters following existing trait conventions (e.g., `lack_count`, `is_backordered`).

###### Requirement Details
- `is_ec_requested`: `@ORM\Column(type="boolean", options={"default": false})` — stores per-item EC request flag. Only set via explicit admin Update click.
- `output_datetime`: `@ORM\Column(type="datetime", nullable=true)` — write-once timestamp set on first Excel export. Must default to null.
- **Linked Requirements:** REQ1_COL_001, REQ1_COL_002
- **Affected Files:** `app/Customize/Entity/OrderItemTrait.php`
- **Scope:** Entity layer

###### Acceptance Criteria
- [ ] **Given** the `OrderItemTrait` is loaded, **When** a new OrderItem is created, **Then** `is_ec_requested` defaults to `false` and `output_datetime` defaults to `null`
- [ ] **Given** an OrderItem entity, **When** `setIsEcRequested(true)` is called, **Then** `getIsEcRequested()` returns `true`
- [ ] **Given** an OrderItem entity, **When** `setOutputDatetime($datetime)` is called, **Then** `getOutputDatetime()` returns that datetime

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| None | — | Foundation task; no upstream dependencies |

###### Definition of Done
- [ ] Two new properties with ORM annotations added to `OrderItemTrait.php`
- [ ] Getters and setters implemented
- [ ] `app/proxy/entity/` regenerated if required by project build
- [ ] No regressions in existing OrderItem functionality

---

##### Sub-task 1.2: Prepare manual SQL scripts for schema, indexes, and master data
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Create idempotent SQL scripts for: (1) adding `is_ec_requested` and `output_datetime` columns to `dtb_order_item`, (2) creating performance indexes, (3) inserting authority_id=6 into `mtb_authority`. Update the `mtb_authority.csv` master data fixture.

###### Requirement Details
- ALTER TABLE for two columns with proper defaults
- CREATE INDEX for `is_ec_requested` and `output_datetime` for search filter performance (NFR-003)
- INSERT authority_id=6 record: `(6, '店舗受取担当', 6, 'authority')`
- **Linked Requirements:** REQ1_COL_001, REQ1_COL_002, REQ7_AUTH_001
- **Affected Files:** `init-sql/` (new SQL file), `app/Customize/DataFixture/Master/csv/mtb_authority.csv`
- **Scope:** Database / Master data

###### Acceptance Criteria
- [ ] **Given** the SQL script is executed, **When** `dtb_order_item` is described, **Then** `is_ec_requested` (BOOLEAN DEFAULT FALSE) and `output_datetime` (DATETIME DEFAULT NULL) columns exist
- [ ] **Given** the SQL script is executed, **When** indexes are queried, **Then** `idx_order_item_ec_requested` and `idx_order_item_output_datetime` exist
- [ ] **Given** the SQL script is executed, **When** `mtb_authority` is queried, **Then** id=6, name='店舗受取担当' exists

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| None | — | Independent DB script |

###### Definition of Done
- [ ] SQL scripts created and verified on local DB
- [ ] `mtb_authority.csv` updated
- [ ] Scripts are idempotent (safe to re-run)
- [ ] No Doctrine migrations generated

---

##### Sub-task 1.3: Unit tests for entity properties and defaults
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Write PHPUnit tests verifying `is_ec_requested` and `output_datetime` property defaults, getters, and setters on OrderItem entities using the trait.

###### Requirement Details
- Test default values on new entity instances
- Test setter/getter round-trips
- Test null handling for `output_datetime`
- **Linked Requirements:** REQ1_COL_001, REQ1_COL_002
- **Affected Files:** `codeception/unit/` or `tests/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** a new OrderItem, **When** no setter called, **Then** `isEcRequested` is false and `outputDatetime` is null
- [ ] **Given** an OrderItem, **When** `setIsEcRequested(true)` then `setIsEcRequested(false)`, **Then** value toggles correctly

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 1.1 | Blocked-by | Entity properties must exist |

###### Definition of Done
- [ ] Tests pass in CI
- [ ] Edge cases for null datetime covered

---

### Story 2: EC依頼 Checkbox on Order Detail Page

**Type:** Story | **Priority:** High | **Points:** 8 | **Sprint:** 1

#### Story Overview
Display an "EC依頼" checkbox per order item row on the admin order detail page, visible only for store pickup orders (order_type ∈ {11, 21, 31}) AND only for out-of-stock items. The checkbox state maps to the `is_ec_requested` field on `dtb_order_item`. Changes are persisted ONLY when the admin clicks the "Update" button — no auto-save behavior. Checking the out-of-stock checkbox and clicking Update must NOT trigger a confirmation popup. The form type (`OrderType.php`) needs a new `is_ec_requested` field mapped to the entity. The controller (`EditController.php`) handles the save logic. The template (`edit.twig`) renders the conditional checkbox with JavaScript to show/hide based on order type and stock status.

- **Linked Requirements:** REQ2_ECREQ_001, REQ2_ECREQ_002, REQ2_ECREQ_003, REQ5_DETAIL_001, REQ5_DETAIL_002, US-001, US-005
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/Customize/Form/Type/Admin/OrderType.php`, `app/template/admin/Order/edit.twig`
- **Scope:** Full-stack

#### Sub-task List
- [ ] 2.1 — Add `is_ec_requested` field to OrderType form (Backend, 4h)
- [ ] 2.2 — Update EditController to persist EC依頼 flag on Update (Backend, 4h)
- [ ] 2.3 — Render EC依頼 checkbox in order detail template (Frontend, 4h)
- [ ] 2.4 — Remove auto-save behavior and enforce Update-only persistence (Full-stack, 4h)
- [ ] 2.5 — Tests for EC依頼 checkbox logic (Backend, 4h)

---

#### Sub-tasks:

##### Sub-task 2.1: Add `is_ec_requested` field to OrderType form
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Add a `CheckboxType` field for `is_ec_requested` per order item in the admin `OrderType` form. The field should be mapped to the `OrderItem` entity's `is_ec_requested` property. It must be optional (not required) and default to the entity's current value.

###### Requirement Details
- Add `is_ec_requested` as `CheckboxType` in the OrderItem sub-form within `OrderType`
- Field mapped to entity property via Symfony form data binding
- Must not be `required` — unchecked checkboxes submit no value
- **Linked Requirements:** REQ2_ECREQ_001, REQ2_ECREQ_003
- **Affected Files:** `app/Customize/Form/Type/Admin/OrderType.php`
- **Scope:** Form layer

###### Acceptance Criteria
- [ ] **Given** the OrderType form is built, **When** the form contains an order item sub-form, **Then** `is_ec_requested` field exists as CheckboxType
- [ ] **Given** the form is submitted with `is_ec_requested=1`, **When** processed, **Then** the entity property is set to `true`

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 (Sub-task 1.1) | Blocked-by | Entity property must exist |

###### Definition of Done
- [ ] Form field added and data-binds correctly
- [ ] No regression on existing OrderType form submissions

---

##### Sub-task 2.2: Update EditController to persist EC依頼 flag on Update
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Modify `EditController.php` to persist the `is_ec_requested` flag from form data when the admin clicks "Update". Ensure no auto-save AJAX calls modify this field. The save must only happen in the existing form-submit handler.

###### Requirement Details
- The `is_ec_requested` value flows through the Symfony form binding to the entity
- Ensure existing auto-save endpoints (if any) do NOT persist this field
- Verify the Update action flushes the entity with the updated flag
- **Linked Requirements:** REQ2_ECREQ_003, REQ5_DETAIL_001, US-001
- **Affected Files:** `app/Customize/Controller/Admin/Order/EditController.php`
- **Scope:** Controller layer

###### Acceptance Criteria
- [ ] **Given** admin checks EC依頼 and clicks Update, **When** the form is submitted, **Then** `is_ec_requested=true` is persisted in `dtb_order_item`
- [ ] **Given** admin checks EC依頼 but navigates away, **When** the page reloads, **Then** `is_ec_requested` remains `false` (no auto-save)

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 2.1 | Blocked-by | Form field must exist |

###### Definition of Done
- [ ] EC依頼 flag persisted only on explicit Update
- [ ] Auto-save endpoints verified to exclude `is_ec_requested`

---

##### Sub-task 2.3: Render EC依頼 checkbox in order detail template
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Add the EC依頼 checkbox to each order item row in `edit.twig`. The checkbox is conditionally visible: shown only when the order's `order_type` ∈ {11, 21, 31} AND the item is out of stock. Use JavaScript or Twig conditions for visibility. The label should read "EC依頼".

###### Requirement Details
- Checkbox rendered per order item row using `{{ form_widget(orderItemForm.is_ec_requested) }}`
- Visibility condition: `order.OrderType.id in [11, 21, 31]` AND item is out of stock
- Hidden for in-stock items and non-pickup order types
- **Linked Requirements:** REQ2_ECREQ_001, REQ2_ECREQ_002
- **Affected Files:** `app/template/admin/Order/edit.twig`
- **Scope:** Template layer

###### Acceptance Criteria
- [ ] **Given** order_type=11 and item is out of stock, **When** order detail loads, **Then** EC依頼 checkbox is visible
- [ ] **Given** order_type=1 (standard delivery), **When** order detail loads, **Then** EC依頼 checkbox is NOT visible
- [ ] **Given** order_type=11 and item is in stock, **When** order detail loads, **Then** EC依頼 checkbox is NOT visible

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 2.1 | Blocked-by | Form field must exist for Twig rendering |

###### Definition of Done
- [ ] Checkbox renders correctly for all pickup order types
- [ ] Checkbox hidden for non-pickup types and in-stock items

---

##### Sub-task 2.4: Remove auto-save behavior and enforce Update-only persistence
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Full-stack

###### Summary
Remove or disable any existing AJAX auto-save behavior on the order detail page so that field changes (including EC依頼) are held in memory and only persisted on explicit Update click. Ensure OOS checkbox + Update does not trigger a confirmation popup.

###### Requirement Details
- Identify and remove/disable auto-save AJAX calls on the order detail page
- Verify that checking the out-of-stock checkbox and clicking Update saves directly without popup
- Changes discarded if user navigates away without clicking Update
- **Linked Requirements:** REQ5_DETAIL_001, REQ5_DETAIL_002, US-005
- **Affected Files:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/template/admin/Order/edit.twig` (JS)
- **Scope:** Full-stack

###### Acceptance Criteria
- [ ] **Given** admin changes any field, **When** no Update click occurs, **Then** changes are NOT persisted
- [ ] **Given** admin checks OOS checkbox + clicks Update, **When** form submits, **Then** save completes without confirmation popup

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 2.2 | Blocked-by | Controller save logic must be in place |

###### Definition of Done
- [ ] Auto-save disabled/removed
- [ ] OOS + Update path confirmed popup-free
- [ ] Manual regression test on order detail save flow

---

##### Sub-task 2.5: Tests for EC依頼 checkbox logic
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Write functional tests covering EC依頼 form submission, conditional visibility logic, auto-save removal verification, and no-popup on OOS update.

###### Requirement Details
- Test form submission with `is_ec_requested=true` and verify DB state
- Test that non-pickup order types do not include `is_ec_requested` in response
- Test that navigating away without Update discards changes
- **Linked Requirements:** REQ2_ECREQ_001–003, REQ5_DETAIL_001–002
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** form submitted for order_type=11 with is_ec_requested=1, **When** DB queried, **Then** flag is true
- [ ] **Given** form submitted for order_type=1 with is_ec_requested=1, **When** processed, **Then** field is ignored or rejected

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 2.1–2.4 | Blocked-by | Feature complete before testing |

###### Definition of Done
- [ ] All test cases pass
- [ ] Coverage for positive and negative scenarios

---

### Story 3: Order Detail Popup Flow for Shipping Status Changes

**Type:** Story | **Priority:** High | **Points:** 5 | **Sprint:** 1

#### Story Overview
Restructure the confirmation popup behavior on the order detail page. A confirmation popup must appear ONLY when the admin changes the shipping status to "商品手配中" and clicks Update — not when just toggling the OOS or EC依頼 checkboxes. The popup includes a "Send notification email" checkbox that defaults to unchecked (opt-in). If the admin updates without sending the email, the popup must re-appear on the next status-changing update. This requires JavaScript changes for popup trigger detection, controller changes for email dispatch conditional logic, and template changes for the popup HTML with the email checkbox.

- **Linked Requirements:** REQ5_DETAIL_003, REQ5_DETAIL_004, REQ5_DETAIL_005, US-006
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/template/admin/Order/edit.twig`, `app/Customize/Service/OrderState/OrderStateHelper.php`
- **Scope:** Full-stack

#### Sub-task List
- [ ] 3.1 — Implement popup trigger on shipping→商品手配中 status change (Full-stack, 8h)
- [ ] 3.2 — Add email notification opt-in checkbox in popup (Frontend, 4h)
- [ ] 3.3 — Backend email dispatch conditional on popup checkbox (Backend, 4h)
- [ ] 3.4 — Tests for popup flow and email dispatch (Backend, 4h)

---

#### Sub-tasks:

##### Sub-task 3.1: Implement popup trigger on shipping→商品手配中 status change
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Full-stack

###### Summary
Add JavaScript logic to intercept the Update button click, detect if shipping status was changed to 商品手配中, and display a confirmation popup instead of directly submitting the form. The popup must persist — if the previous update was done without sending email, the popup re-appears on the next status-changing update.

###### Requirement Details
- Detect shipping status field change to 商品手配中 value on Update click
- Show modal/popup with confirmation message before form submit
- Popup must NOT appear for OOS checkbox changes (REQ5_DETAIL_002)
- Popup persists across updates if email was not sent (REQ5_DETAIL_005)
- **Linked Requirements:** REQ5_DETAIL_003, REQ5_DETAIL_005
- **Affected Files:** `app/template/admin/Order/edit.twig` (JS), `app/Customize/Controller/Admin/Order/EditController.php`
- **Scope:** Full-stack

###### Acceptance Criteria
- [ ] **Given** shipping status changed to 商品手配中, **When** Update clicked, **Then** confirmation popup appears
- [ ] **Given** shipping status NOT changed, **When** Update clicked, **Then** form submits directly (no popup)
- [ ] **Given** previous update skipped email, **When** status changed again + Update, **Then** popup re-appears

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 2 (Sub-task 2.4) | Relates-to | Auto-save removal must be complete |
| Q-01 (Blocker) | Blocked-by | 商品手配中 must exist in `dcm_shipping_status` |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---|---|
| 1 | 商品手配中 not in `dcm_shipping_status` | Cannot implement — pending Q-01 resolution |
| 2 | Multiple shipping status changes before Update | Popup shown once based on final state |

###### Definition of Done
- [ ] Popup triggers only on 商品手配中 transition
- [ ] Popup persists on subsequent updates if email not sent
- [ ] No popup on OOS-only changes

---

##### Sub-task 3.2: Add email notification opt-in checkbox in popup
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Add a "Send notification email" checkbox inside the confirmation popup. The checkbox must default to unchecked. When the admin confirms, the checkbox value is submitted with the form as a hidden field or request parameter.

###### Requirement Details
- Checkbox label: "通知メールを送信する" or equivalent
- Default: unchecked (opt-in model)
- Value submitted as part of the form POST (e.g., hidden input set by JS)
- **Linked Requirements:** REQ5_DETAIL_004
- **Affected Files:** `app/template/admin/Order/edit.twig`
- **Scope:** Template / JS

###### Acceptance Criteria
- [ ] **Given** popup is displayed, **When** admin sees email checkbox, **Then** it is unchecked by default
- [ ] **Given** admin checks the email checkbox and confirms, **When** form submits, **Then** email flag is sent in request

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 3.1 | Blocked-by | Popup must exist |

###### Definition of Done
- [ ] Checkbox renders in popup with correct default state
- [ ] Value correctly transmitted to backend

---

##### Sub-task 3.3: Backend email dispatch conditional on popup checkbox
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Modify `EditController.php` to read the email notification flag from the request and conditionally dispatch the notification email only when the flag is true. Record whether email was sent in session/entity state to support popup persistence logic.

###### Requirement Details
- Read `send_notification_email` (or equivalent) from request
- Dispatch email only if flag is `true`
- Track email-sent status per order/shipping to support popup persistence
- **Linked Requirements:** REQ5_DETAIL_004, REQ5_DETAIL_005
- **Affected Files:** `app/Customize/Controller/Admin/Order/EditController.php`
- **Scope:** Controller / Service

###### Acceptance Criteria
- [ ] **Given** email flag is true in request, **When** Update processes, **Then** notification email is sent
- [ ] **Given** email flag is false/absent, **When** Update processes, **Then** no email is sent

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 3.2 | Blocked-by | Frontend must submit email flag |

###### Definition of Done
- [ ] Email dispatched conditionally
- [ ] No email sent when checkbox unchecked

---

##### Sub-task 3.4: Tests for popup flow and email dispatch
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Write tests verifying popup trigger conditions and email dispatch logic. Cover: status change triggers popup, OOS does not trigger popup, email sent only when checkbox checked, popup re-appears when email skipped.

###### Requirement Details
- **Linked Requirements:** REQ5_DETAIL_002–005
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** status→商品手配中 + email flag=true, **When** controller processes, **Then** email dispatched
- [ ] **Given** status→商品手配中 + email flag=false, **When** controller processes, **Then** no email dispatched

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 3.1–3.3 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] All popup and email dispatch tests pass

---

### Story 4: Excel Export Service for EC依頼 Items

**Type:** Story | **Priority:** High | **Points:** 13 | **Sprint:** 2

#### Story Overview
Build a new Excel export feature using PhpSpreadsheet that generates .xlsx files for EC-requested order items, split into two regional HQ lists: Munakata (West) and Isesaki (East). Each export produces a workbook with two sheets — Sheet_1 sorted by Order No ASC, Sheet_2 sorted by JAN code ASC. Both sheets contain 9 columns: 注文番号, 店舗名, 分類コード, 分類名, 商品CD, 商品名, EC依頼数, 締日時, 出力済み. The `output_datetime` column is set on first export only (write-once). Two admin menu items trigger the export: "EC依頼リスト_伊勢崎拠点" (East) and "EC依頼リスト_宗像拠点" (West). Regional assignment is determined by `uketori_location_cd`. The export follows cutoff times (8:30/12:30) with generation at 10:15/15:15. A new `ExcelExportService` class handles the PhpSpreadsheet logic following the existing `CsvExportService` pattern. A new `ExcelExportController` handles the admin route and response.

- **Linked Requirements:** REQ3_EXCEL_001–005, US-002, US-003, US-004
- **Affected Components:** NEW `app/Customize/Service/ExcelExportService.php`, NEW `app/Customize/Controller/Admin/Order/ExcelExportController.php`, `app/Customize/Repository/OrderRepository.php` or `OrderItemRepository.php`, admin nav template
- **Scope:** Backend + Frontend (menu)

#### Sub-task List
- [ ] 4.1 — Create ExcelExportService with PhpSpreadsheet (Backend, 8h)
- [ ] 4.2 — Implement output_datetime write-once logic (Backend, 4h)
- [ ] 4.3 — Create ExcelExportController with East/West endpoints (Backend, 8h)
- [ ] 4.4 — Add repository query for EC-requested items by region (Backend, 4h)
- [ ] 4.5 — Add admin menu items for EC依頼リスト (Frontend, 2h)
- [ ] 4.6 — Tests for Excel export (Backend, 8h)

---

#### Sub-tasks:

##### Sub-task 4.1: Create ExcelExportService with PhpSpreadsheet
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Create `ExcelExportService.php` that generates .xlsx workbooks containing two sheets. Sheet_1 lists EC-requested items sorted by 注文番号 ASC. Sheet_2 lists the same data sorted by JAN code (商品CD) ASC. Both sheets contain 9 columns. The service accepts a collection of order items and an HQ region identifier. Follow the `CsvExportService` pattern for DI and structure.

###### Requirement Details
- Use PhpSpreadsheet v1.24+ to create Xlsx writer
- Sheet_1: sorted by 注文番号 ASC
- Sheet_2: sorted by JAN code ASC
- 9 columns: 注文番号, 店舗名, 分類コード, 分類名, 商品CD, 商品名, EC依頼数, 締日時, 出力済み
- EC依頼数 maps to `lack_count` (pending Q-09 confirmation)
- 出力済み column shows `output_datetime` formatted or empty
- **Linked Requirements:** REQ3_EXCEL_002, REQ3_EXCEL_003, NFR-001, NFR-013
- **Affected Files:** NEW `app/Customize/Service/ExcelExportService.php`
- **Scope:** Service layer

###### Acceptance Criteria
- [ ] **Given** a collection of EC-requested OrderItems, **When** `generateExcel()` is called, **Then** a valid .xlsx workbook is returned with 2 sheets
- [ ] **Given** Sheet_1, **When** rows inspected, **Then** sorted by 注文番号 ASC
- [ ] **Given** Sheet_2, **When** rows inspected, **Then** sorted by JAN code ASC
- [ ] **Given** >1,000 items, **When** export runs, **Then** completes within 10s (NFR-001)

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity properties must exist |
| PhpSpreadsheet | Available | Already in composer.json |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---|---|
| 1 | Zero EC-requested items | Generate Excel with headers only (empty data rows) |
| 2 | >5,000 items | Memory management via chunked processing if needed |

###### Definition of Done
- [ ] Service class created following `CsvExportService` pattern
- [ ] Both sheets generate correctly with 9 columns
- [ ] Sorting verified for both sheets

---

##### Sub-task 4.2: Implement output_datetime write-once logic
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
In the export flow, set `output_datetime` to the current timestamp for each order item where `output_datetime IS NULL`. Items that already have a timestamp must NOT be overwritten. This must be enforced at the service/repository level, not just UI.

###### Requirement Details
- Check `output_datetime` before setting — only set if null
- Use a single UPDATE query with `WHERE output_datetime IS NULL` for atomicity
- Prevent race conditions from simultaneous exports
- **Linked Requirements:** REQ3_EXCEL_004, NFR-010, NFR-014
- **Affected Files:** `app/Customize/Service/ExcelExportService.php`, `app/Customize/Repository/OrderItemRepository.php`
- **Scope:** Service / Repository

###### Acceptance Criteria
- [ ] **Given** OrderItem with `output_datetime=NULL`, **When** first export runs, **Then** `output_datetime` is set to current timestamp
- [ ] **Given** OrderItem with `output_datetime='2026-05-20 10:15:00'`, **When** subsequent export runs, **Then** `output_datetime` remains unchanged

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 4.1 | Blocked-by | Service must exist |

###### Definition of Done
- [ ] Write-once enforced at service/repository level
- [ ] Race condition handled via SQL WHERE clause

---

##### Sub-task 4.3: Create ExcelExportController with East/West endpoints
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Create a new controller with two routes — one for Munakata (West) HQ and one for Isesaki (East) HQ. Each route calls `ExcelExportService` with the appropriate region filter and returns a StreamedResponse with the .xlsx content. The controller resolves the region using `uketori_location_cd` mapping.

###### Requirement Details
- Route 1: `/admin/order/ec-request-export/west` → Munakata
- Route 2: `/admin/order/ec-request-export/east` → Isesaki
- Response: `StreamedResponse` with `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Filename: `EC依頼リスト_{region}_{date}.xlsx`
- **Linked Requirements:** REQ3_EXCEL_001, REQ3_EXCEL_005, US-002, US-003
- **Affected Files:** NEW `app/Customize/Controller/Admin/Order/ExcelExportController.php`
- **Scope:** Controller layer

###### Acceptance Criteria
- [ ] **Given** admin clicks West export menu, **When** request processed, **Then** .xlsx file downloads with Munakata-region items
- [ ] **Given** admin clicks East export menu, **When** request processed, **Then** .xlsx file downloads with Isesaki-region items

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 4.1 | Blocked-by | Service must exist |
| Sub-task 4.4 | Blocked-by | Repository query must exist |
| Q-02 (Blocker) | Blocked-by | East/West uketori_location_cd mapping required |

###### Definition of Done
- [ ] Two routes created and functional
- [ ] Proper HTTP response headers for Excel download
- [ ] Admin-only access enforced

---

##### Sub-task 4.4: Add repository query for EC-requested items by region
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Add a query method to `OrderItemRepository` (or `OrderRepository`) that fetches EC-requested order items (`is_ec_requested=true`) filtered by HQ region (determined by `uketori_location_cd`). The query must support cutoff time filtering.

###### Requirement Details
- Filter: `is_ec_requested = true` AND region-based `uketori_location_cd`
- Support cutoff time windows (orders before 8:30 → export at 10:15; orders before 12:30 → export at 15:15)
- Return OrderItem entities with their parent Order data for Excel columns
- **Linked Requirements:** REQ3_EXCEL_001, REQ9_SEARCH_001
- **Affected Files:** `app/Customize/Repository/OrderItemRepository.php` or `app/Customize/Repository/OrderRepository.php`
- **Scope:** Repository layer

###### Acceptance Criteria
- [ ] **Given** EC-requested items exist for West region, **When** queried with region=west, **Then** only West items returned
- [ ] **Given** cutoff time is 8:30, **When** queried, **Then** only items from orders created before 8:30 returned

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | DB columns must exist |
| Q-02 (Blocker) | Blocked-by | uketori_location_cd mapping needed |

###### Definition of Done
- [ ] Query method returns correct filtered results
- [ ] Parameterized queries (no SQL injection)
- [ ] Proper use of indexes

---

##### Sub-task 4.5: Add admin menu items for EC依頼リスト
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

###### Summary
Add two new admin navigation menu items: "EC依頼リスト_伊勢崎拠点" (East/Isesaki) and "EC依頼リスト_宗像拠点" (West/Munakata). Each links to its respective export controller route.

###### Requirement Details
- Menu items appear in admin navigation sidebar
- Each links to the corresponding export route
- Positioned in the order management section
- **Linked Requirements:** REQ3_EXCEL_005
- **Affected Files:** Admin navigation template (e.g., `app/template/admin/nav.twig` or equivalent)
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** admin logs in, **When** viewing sidebar, **Then** both EC依頼リスト menu items are visible
- [ ] **Given** admin clicks "EC依頼リスト_伊勢崎拠点", **When** route resolves, **Then** East HQ export triggers

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 4.3 | Blocked-by | Routes must exist |

###### Definition of Done
- [ ] Both menu items visible and functional
- [ ] Correct route linking

---

##### Sub-task 4.6: Tests for Excel export
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Write tests for: ExcelExportService (sheet generation, sorting, columns), output_datetime write-once, controller response, regional filtering, and edge cases (empty data, large datasets).

###### Requirement Details
- **Linked Requirements:** REQ3_EXCEL_001–005, NFR-001, NFR-010
- **Affected Files:** `codeception/` or `tests/` (new test files)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** known test data, **When** Excel generated, **Then** all 9 columns present and sorting correct
- [ ] **Given** zero items, **When** export runs, **Then** valid Excel with headers only

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 4.1–4.5 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] Unit tests for ExcelExportService
- [ ] Functional tests for controller endpoints
- [ ] Edge case coverage

---

### Story 5: Batch007 SC連携 Timing Alignment for Store Pickup Orders

**Type:** Story | **Priority:** High | **Points:** 5 | **Sprint:** 2

#### Story Overview
Adjust `Batch007Command.php` to align the SC連携 timing for store pickup orders (order_type ∈ {11, 21, 31}) with the existing delivery-installation timing. The existing type mapping (11→2, 21→4, 31→6) is preserved — only the timing/filter conditions change. Store pickup orders must proceed through SC連携 even if they contain out-of-stock items, unlike standard delivery orders which may block. This requires modifying the batch command's query filters and timing logic, while maintaining backward compatibility with existing delivery-installation SC連携. AMS coordination is required (JIRA: MRMAX_ECOPE-3335).

- **Linked Requirements:** REQ4_SC_001, REQ4_SC_002, REQ4_SC_003, US-014
- **Affected Components:** `app/Customize/Command/Batch007Command.php`
- **Scope:** Backend

#### Sub-task List
- [ ] 5.1 — Modify Batch007 timing/filter for store pickup orders (Backend, 8h)
- [ ] 5.2 — Allow OOS items through SC連携 for store pickup (Backend, 4h)
- [ ] 5.3 — Tests for Batch007 timing and backward compatibility (Backend, 8h)

---

#### Sub-tasks:

##### Sub-task 5.1: Modify Batch007 timing/filter for store pickup orders
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Update `Batch007Command.php` to apply delivery-installation SC連携 timing to store pickup orders. The existing mapping (11→2, 21→4, 31→6) must remain unchanged. The change is in which timing bucket/filter conditions apply to store pickup order types.

###### Requirement Details
- Store pickup orders (order_type ∈ {11, 21, 31}) use delivery-installation timing
- Existing mapping preserved: 11→2, 21→4, 31→6
- No changes to delivery-installation order processing
- **Linked Requirements:** REQ4_SC_001, REQ4_SC_002
- **Affected Files:** `app/Customize/Command/Batch007Command.php`
- **Scope:** Batch / Command

###### Acceptance Criteria
- [ ] **Given** a store pickup order (type=11), **When** Batch007 runs, **Then** SC連携 uses delivery-installation timing
- [ ] **Given** a delivery-installation order, **When** Batch007 runs, **Then** existing timing is unchanged

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| AMS coordination | External | JIRA: MRMAX_ECOPE-3335 |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---|---|
| 1 | In-flight delivery-installation orders during deploy | Unaffected — backward compatibility maintained |

###### Definition of Done
- [ ] Store pickup orders processed with aligned timing
- [ ] Delivery-installation orders unaffected
- [ ] No mapping changes

---

##### Sub-task 5.2: Allow OOS items through SC連携 for store pickup
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Modify Batch007 to not block SC連携 processing for store pickup orders that contain out-of-stock items. Standard delivery orders may still block on OOS, but store pickup orders proceed — the EC request flow handles fulfillment separately.

###### Requirement Details
- Add condition: if `order_type ∈ {11, 21, 31}`, skip OOS blocking check
- Standard delivery orders retain existing OOS blocking behavior
- **Linked Requirements:** REQ4_SC_003
- **Affected Files:** `app/Customize/Command/Batch007Command.php`
- **Scope:** Batch / Command

###### Acceptance Criteria
- [ ] **Given** store pickup order with OOS items, **When** Batch007 runs, **Then** order proceeds through SC連携
- [ ] **Given** standard delivery order with OOS items, **When** Batch007 runs, **Then** existing blocking behavior maintained

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 5.1 | Relates-to | Same file, can be done in parallel |

###### Definition of Done
- [ ] OOS non-blocking for pickup types only
- [ ] Standard delivery OOS blocking preserved

---

##### Sub-task 5.3: Tests for Batch007 timing and backward compatibility
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Write tests covering: (1) store pickup orders use delivery-installation timing, (2) mapping 11→2, 21→4, 31→6 preserved, (3) OOS non-blocking for pickup, (4) backward compatibility for existing delivery-installation orders.

###### Requirement Details
- **Linked Requirements:** REQ4_SC_001–003, NFR-012
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** test store pickup order, **When** Batch007 executed, **Then** correct timing applied and mapping preserved
- [ ] **Given** test delivery-installation order, **When** Batch007 executed, **Then** no behavioral change

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 5.1–5.2 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] All Batch007 tests pass
- [ ] Backward compatibility verified

---

### Story 6: Pre-order In-Store Pickup Lifecycle (order_type=31)

**Type:** Story | **Priority:** High | **Points:** 8 | **Sprint:** 2

#### Story Overview
Implement the full lifecycle for pre-order in-store pickup (order_type=31). The flow mirrors regular store pickup until `delivery_status` reaches `CAN_RECEIVE` (3), at which point: (1) a barcode is displayed to the customer, (2) an automated email notification is sent, (3) from that point the regular store pickup flow applies (scan → confirm → complete). Status transitions: order_status 1→4→5→8, preorder_status 1→9, shipping 0→1→2→9, delivery 0→3→9. The `OrderStateHelper` must support these transitions. The email template for 受取可能 notification must be created or identified. The customer-facing barcode display is triggered at delivery_status=3.

- **Linked Requirements:** REQ6_PREORDER_001–005, US-010, US-011
- **Affected Components:** `app/Customize/Service/OrderState/OrderStateHelper.php`, Barcode display template, Email template, controllers
- **Scope:** Full-stack

#### Sub-task List
- [ ] 6.1 — Implement pre-order status transition logic in OrderStateHelper (Backend, 8h)
- [ ] 6.2 — Trigger email on delivery_status → CAN_RECEIVE (Backend, 4h)
- [ ] 6.3 — Display barcode at delivery_status=CAN_RECEIVE (Frontend, 4h)
- [ ] 6.4 — Tests for pre-order lifecycle (Backend, 8h)

---

#### Sub-tasks:

##### Sub-task 6.1: Implement pre-order status transition logic in OrderStateHelper
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Add or update `OrderStateHelper.php` to handle the complete status transition chain for order_type=31: order_status 1→4→5→8, preorder_status 1→9, shipping 0→1→2→9, delivery 0→3→9. Enforce no-skip transitions. The pre-order follows regular store pickup logic until delivery_status reaches CAN_RECEIVE.

###### Requirement Details
- Status chain: order_status 1(New)→4(Processing)→5(Shipped)→8(Completed)
- preorder_status: 1(Active)→9(Fulfilled)
- shipping: 0(Initial)→1(Preparing)→2(Shipped)→9(Completed)
- delivery: 0(Initial)→3(CAN_RECEIVE)→9(Completed)
- Validate no states are skipped
- **Linked Requirements:** REQ6_PREORDER_001, REQ6_PREORDER_004
- **Affected Files:** `app/Customize/Service/OrderState/OrderStateHelper.php`
- **Scope:** Service layer

###### Acceptance Criteria
- [ ] **Given** order_type=31 at order_status=1, **When** transition triggered, **Then** moves to order_status=4 (not 5 or 8)
- [ ] **Given** delivery transitions 0→3→9, **When** any skip attempted (e.g., 0→9), **Then** transition rejected

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity layer foundation |

###### Definition of Done
- [ ] All pre-order status transitions implemented
- [ ] No-skip validation in place

---

##### Sub-task 6.2: Trigger email on delivery_status → CAN_RECEIVE
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Dispatch an automated email to the customer when `delivery_status` transitions to CAN_RECEIVE (3) for order_type=31. The email notifies the customer their pre-order is ready for pickup. Identify or create the email template.

###### Requirement Details
- Email sent when delivery_status changes: any → 3 (CAN_RECEIVE)
- Only for order_type=31
- Use existing mail service patterns (e.g., `MailService`)
- **Linked Requirements:** REQ6_PREORDER_005, US-010
- **Affected Files:** `app/Customize/Service/OrderState/OrderStateHelper.php`, mail service, email template
- **Scope:** Service / Template

###### Acceptance Criteria
- [ ] **Given** order_type=31 delivery_status changes to 3, **When** transition processed, **Then** email sent to customer
- [ ] **Given** order_type=11 delivery_status changes to 3, **When** transition processed, **Then** regular flow applies (no duplicate email logic)

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 6.1 | Blocked-by | Transition logic must exist |
| Q-11 | Pending | Email template exists or needs creation |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---|---|
| 1 | Email service fails at CAN_RECEIVE | Barcode still displayed; email retry or manual notification needed |

###### Definition of Done
- [ ] Email dispatched on CAN_RECEIVE transition
- [ ] Template created or identified
- [ ] Error handling for email failure

---

##### Sub-task 6.3: Display barcode at delivery_status=CAN_RECEIVE
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Show a barcode on the customer-facing order page when `delivery_status` reaches CAN_RECEIVE (3) for order_type=31. After barcode display, the regular store pickup flow applies: store staff scans barcode → confirmation → completion.

###### Requirement Details
- Barcode visible to customer on mypage/order detail when delivery_status=3
- Barcode format: Code128 (existing infrastructure assumed)
- After barcode display, same flow as order_type=11 completion
- **Linked Requirements:** REQ6_PREORDER_002, REQ6_PREORDER_003, US-011
- **Affected Files:** Customer-facing order/mypage template
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** order_type=31 with delivery_status=3, **When** customer views order page, **Then** barcode is displayed
- [ ] **Given** order_type=31 with delivery_status<3, **When** customer views order page, **Then** no barcode shown

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 6.1 | Blocked-by | Status transition must support CAN_RECEIVE |

###### Definition of Done
- [ ] Barcode renders at delivery_status=3
- [ ] Hidden at earlier statuses

---

##### Sub-task 6.4: Tests for pre-order lifecycle
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Write tests for: complete status transition chain (order_status, preorder_status, shipping, delivery), email dispatch at CAN_RECEIVE, barcode display condition, no-skip validation, and edge cases (email failure, double transition).

###### Requirement Details
- **Linked Requirements:** REQ6_PREORDER_001–005
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** order_type=31, **When** full lifecycle simulated, **Then** all status transitions correct
- [ ] **Given** email fails, **When** delivery→CAN_RECEIVE, **Then** error logged but barcode still available

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 6.1–6.3 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] Full lifecycle tests pass
- [ ] Edge cases covered

---

### Story 7: Authority ID=6 — Store Pickup Staff Role

**Type:** Story | **Priority:** High | **Points:** 8 | **Sprint:** 2

#### Story Overview
Implement a new admin authority role (authority_id=6, "店舗受取担当") with restricted access. Users with this authority: (1) CANNOT view PG Multi-Payment payment info — enforced server-side, not just UI; (2) have Member ID Link and Customer Flag features inactivated; (3) see only store pickup order types (11, 21, 31) in the order category filter; (4) these restrictions apply regardless of entry point (商品受渡処理 or 受注一覧). The deny_url configuration MUST NOT include '/order' as this would block total-picking and packing pages. The access restrictions must be enforced at controller/service level (NFR-008, NFR-009).

- **Linked Requirements:** REQ7_AUTH_001–006, US-007, US-008
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/Customize/Controller/Admin/Order/OrderController.php`, `app/Customize/DataFixture/Master/csv/authority_role.csv`, admin templates
- **Scope:** Full-stack

#### Sub-task List
- [ ] 7.1 — Configure deny_url entries for authority_id=6 (Backend, 4h)
- [ ] 7.2 — Server-side PG payment info restriction (Backend, 4h)
- [ ] 7.3 — Order category filter restriction for authority_id=6 (Backend, 4h)
- [ ] 7.4 — Inactivate Member ID Link and Customer Flag for authority_id=6 (Backend, 2h)
- [ ] 7.5 — Template-level hiding for authority_id=6 (Frontend, 4h)
- [ ] 7.6 — Tests for authority restrictions (Backend, 8h)

---

#### Sub-tasks:

##### Sub-task 7.1: Configure deny_url entries for authority_id=6
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Define and insert deny_url entries in `authority_role.csv` for authority_id=6. The entries must restrict access to sensitive areas while NOT including '/order' (which would block total-picking and packing). Use more specific deny paths to block payment info and other restricted areas.

###### Requirement Details
- Insert deny_url entries into `authority_role.csv`
- MUST NOT include '/order' — blocks total-picking and packing
- Must deny: PG payment info URLs, Member ID Link, Customer Flag URLs
- Must allow: order list, order detail, total-picking, packing, 商品受渡処理
- **Linked Requirements:** REQ7_AUTH_005
- **Affected Files:** `app/Customize/DataFixture/Master/csv/authority_role.csv`
- **Scope:** Configuration / Master data

###### Acceptance Criteria
- [ ] **Given** authority_id=6 deny_url list, **When** reviewed, **Then** '/order' is NOT present
- [ ] **Given** authority_id=6, **When** accessing total-picking page, **Then** access is allowed

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 (Sub-task 1.2) | Blocked-by | mtb_authority record must exist |
| Q-06 | Pending | Complete deny_url list from business |

###### Definition of Done
- [ ] deny_url entries inserted
- [ ] '/order' confirmed absent from deny list

---

##### Sub-task 7.2: Server-side PG payment info restriction
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Add server-side checks to `EditController.php` (and/or relevant service) to block authority_id=6 users from accessing PG Multi-Payment payment info. This must not rely solely on template hiding — the controller must refuse to render/return payment data.

###### Requirement Details
- Check `$this->getUser()->getAuthority()->getId() === 6` in payment info endpoints/render paths
- Return 403 or omit payment data for authority_id=6
- Enforcement regardless of entry point (URL direct access, API, etc.)
- **Linked Requirements:** REQ7_AUTH_002, REQ7_AUTH_004, NFR-008, NFR-009
- **Affected Files:** `app/Customize/Controller/Admin/Order/EditController.php`
- **Scope:** Controller / Security

###### Acceptance Criteria
- [ ] **Given** authority_id=6 user, **When** accessing order detail, **Then** PG payment info is NOT present in response
- [ ] **Given** authority_id=6 user, **When** directly requesting payment info URL, **Then** access denied (403 or redirect)

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 7.1 | Relates-to | deny_url provides first layer; server-side is defense-in-depth |

###### Definition of Done
- [ ] Server-side enforcement implemented
- [ ] Verified via direct URL access test

---

##### Sub-task 7.3: Order category filter restriction for authority_id=6
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Modify `OrderController.php` to filter the order category dropdown to show only store pickup types (11, 21, 31) when the current user has authority_id=6. The query must also filter results to only return orders of these types.

###### Requirement Details
- Filter the order type choices in the search form for authority_id=6
- Filter the query results to exclude non-pickup order types
- Applied on both 受注一覧 and 商品受渡処理 entry points
- **Linked Requirements:** REQ7_AUTH_006, US-007
- **Affected Files:** `app/Customize/Controller/Admin/Order/OrderController.php`, `app/Customize/Form/Type/Admin/OrderType.php`
- **Scope:** Controller / Form

###### Acceptance Criteria
- [ ] **Given** authority_id=6 user, **When** viewing order list, **Then** only order types 11, 21, 31 appear in filter
- [ ] **Given** authority_id=6 user, **When** search executed, **Then** only pickup orders returned

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 7.1 | Blocked-by | Authority must be configured |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---|---|
| 1 | authority_id=6 accesses order detail via direct URL for non-pickup order | Server-side rejection; redirect to order list |

###### Definition of Done
- [ ] Order type filter restricted for authority_id=6
- [ ] No non-pickup orders accessible

---

##### Sub-task 7.4: Inactivate Member ID Link and Customer Flag for authority_id=6
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Ensure Member ID Link and Customer Flag features are inactivated (not accessible) for authority_id=6 users. This may involve deny_url entries and/or additional checks in relevant controllers.

###### Requirement Details
- Member ID Link feature inaccessible for authority_id=6
- Customer Flag feature inaccessible for authority_id=6
- **Linked Requirements:** REQ7_AUTH_003
- **Affected Files:** Relevant controllers or deny_url configuration
- **Scope:** Controller / Configuration

###### Acceptance Criteria
- [ ] **Given** authority_id=6 user, **When** attempting Member ID Link access, **Then** blocked
- [ ] **Given** authority_id=6 user, **When** attempting Customer Flag access, **Then** blocked

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 7.1 | Blocked-by | deny_url config in place |

###### Definition of Done
- [ ] Both features confirmed inaccessible for authority_id=6

---

##### Sub-task 7.5: Template-level hiding for authority_id=6
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Update admin templates (order detail, order list, navigation) to conditionally hide UI elements for authority_id=6: PG payment info section, Member ID Link, Customer Flag, non-pickup order type options. This is a presentation-layer complement to server-side enforcement.

###### Requirement Details
- Use Twig condition: `{% if app.user.authority.id != 6 %}` or equivalent
- Hide: PG payment section, Member ID Link, Customer Flag, non-pickup order types
- **Linked Requirements:** REQ7_AUTH_002–006
- **Affected Files:** `app/template/admin/Order/edit.twig`, `app/template/admin/Order/index.twig`
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** authority_id=6 user, **When** viewing order detail, **Then** PG payment section not rendered
- [ ] **Given** non-auth-6 user, **When** viewing order detail, **Then** all sections visible as before

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 7.2 | Relates-to | Server-side must also enforce |

###### Definition of Done
- [ ] UI elements hidden for authority_id=6
- [ ] No visual regression for other authorities

---

##### Sub-task 7.6: Tests for authority restrictions
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

###### Summary
Write tests covering: PG payment info blocked server-side, order type filter restricted, deny_url validation (no '/order'), Member ID Link/Customer Flag blocked, entry point agnostic enforcement, direct URL access for non-pickup orders rejected.

###### Requirement Details
- **Linked Requirements:** REQ7_AUTH_001–006, NFR-008, NFR-009
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** authority_id=6 simulated login, **When** accessing payment info, **Then** 403 or data omitted
- [ ] **Given** authority_id=6, **When** searching orders, **Then** only pickup types returned

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 7.1–7.5 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] All authority restriction tests pass
- [ ] Server-side enforcement verified (not just template hiding)

---

### Story 8: 商品受渡処理 Screen — Rename & Barcode Confirmation

**Type:** Story | **Priority:** High | **Points:** 5 | **Sprint:** 3

#### Story Overview
Rename the "店舗受取管理" admin screen to "商品受渡処理". Implement the barcode scan → immediate confirmation popup flow. The popup shows order details, scan timestamp, and an irreversibility warning. The screen contains: barcode input field, store dropdown, receipt status filter (未/済み/全て), date range picker, and results table. Scanning a barcode triggers the confirmation popup without intermediate steps. The scan timestamp is recorded and displayed in the popup.

- **Linked Requirements:** REQ8_SCREEN_001–005, US-009
- **Affected Components:** `app/Customize/Controller/Admin/Order/ShippingController.php` (or equivalent), 商品受渡処理 template, admin nav template
- **Scope:** Full-stack

#### Sub-task List
- [ ] 8.1 — Rename menu label and screen title (Frontend, 2h)
- [ ] 8.2 — Implement barcode scan → confirmation popup flow (Full-stack, 8h)
- [ ] 8.3 — Add scan timestamp display and irreversibility warning (Frontend, 4h)
- [ ] 8.4 — Verify screen elements: filters, dropdown, date range (Frontend, 4h)
- [ ] 8.5 — Tests for barcode scan and popup flow (Backend, 4h)

---

#### Sub-tasks:

##### Sub-task 8.1: Rename menu label and screen title
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

###### Summary
Update the admin navigation menu item from "店舗受取管理" to "商品受渡処理". Also update the page title/heading on the screen itself. The URL route may remain unchanged.

###### Requirement Details
- Menu label: '店舗受取管理' → '商品受渡処理'
- Page heading updated to match
- **Linked Requirements:** REQ8_SCREEN_001, NFR-006
- **Affected Files:** Admin navigation template, 商品受渡処理 page template
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** admin logged in, **When** viewing navigation, **Then** menu reads '商品受渡処理'
- [ ] **Given** admin opens the screen, **When** page loads, **Then** heading reads '商品受渡処理'

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| None | — | Independent label change |

###### Definition of Done
- [ ] Menu label updated
- [ ] Page heading updated

---

##### Sub-task 8.2: Implement barcode scan → confirmation popup flow
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Full-stack

###### Summary
Implement the flow where scanning a barcode (or entering a barcode value and pressing Enter) in the barcode input field triggers a confirmation popup immediately without intermediate steps. The popup shows order details and requires explicit confirmation to complete the handover. The controller backend validates the barcode and returns order data for the popup.

###### Requirement Details
- Barcode input: text field captures scan input (Code128)
- On scan/Enter: AJAX call to backend to validate barcode and fetch order details
- Backend returns order info → popup displayed immediately
- Confirmation in popup → marks order as completed
- **Linked Requirements:** REQ8_SCREEN_002, US-009, NFR-004
- **Affected Files:** `app/Customize/Controller/Admin/Order/ShippingController.php`, 商品受渡処理 template (JS)
- **Scope:** Full-stack

###### Acceptance Criteria
- [ ] **Given** barcode scanned on 商品受渡処理, **When** scan detected, **Then** confirmation popup appears within 500ms
- [ ] **Given** popup confirmed, **When** processing completes, **Then** order marked as completed

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| None | — | Builds on existing scan infrastructure |

###### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---|---|
| 1 | Barcode for already-completed order | Warning shown; action rejected |
| 2 | Invalid barcode | Error message; no popup |

###### Definition of Done
- [ ] Scan → popup flow works end-to-end
- [ ] Response time < 500ms

---

##### Sub-task 8.3: Add scan timestamp display and irreversibility warning
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Enhance the confirmation popup to display the scan timestamp (captured at the moment of scan) and show a clear irreversibility warning message indicating the handover action cannot be undone.

###### Requirement Details
- Scan timestamp captured via JavaScript `new Date()` or server timestamp
- Displayed in popup: "スキャン日時: YYYY-MM-DD HH:mm:ss"
- Irreversibility warning: clear, prominent text
- **Linked Requirements:** REQ8_SCREEN_003, REQ8_SCREEN_005
- **Affected Files:** 商品受渡処理 template (JS/HTML)
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** barcode scanned, **When** popup appears, **Then** scan timestamp is displayed
- [ ] **Given** popup displayed, **When** admin views content, **Then** irreversibility warning is clearly visible

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 8.2 | Blocked-by | Popup must exist |

###### Definition of Done
- [ ] Timestamp displayed in popup
- [ ] Warning text present and prominent

---

##### Sub-task 8.4: Verify screen elements: filters, dropdown, date range
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Ensure all required UI elements are present on the 商品受渡処理 screen: barcode input, store dropdown, receipt status filter (未/済み/全て), date range picker, results table. Verify existing elements if already implemented; add missing ones.

###### Requirement Details
- Barcode input field
- Store dropdown (filterable)
- Receipt status filter: 未 (not received) / 済み (received) / 全て (all)
- Date range: start date – end date pickers
- Results table with order list
- **Linked Requirements:** REQ8_SCREEN_004
- **Affected Files:** 商品受渡処理 template
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** admin opens 商品受渡処理, **When** page loads, **Then** all 5 UI elements are present and functional

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 8.1 | Relates-to | Screen rename should be done first |

###### Definition of Done
- [ ] All screen elements verified present
- [ ] Filters functional

---

##### Sub-task 8.5: Tests for barcode scan and popup flow
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Write tests for: barcode validation endpoint, popup data response, completion on confirmation, already-completed order rejection, invalid barcode handling.

###### Requirement Details
- **Linked Requirements:** REQ8_SCREEN_002–005
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** valid barcode, **When** API called, **Then** order data returned
- [ ] **Given** already-completed order barcode, **When** scanned, **Then** rejection response

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 8.1–8.4 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] All barcode/popup tests pass

---

### Story 9: EC依頼 Search Filter on Order List

**Type:** Story | **Priority:** Medium | **Points:** 3 | **Sprint:** 3

#### Story Overview
Add an "EC依頼" radio filter to the order list search form with two options: すべて (all — no filter) and 依頼あり (is_ec_requested=1). The filter extends the `OrderType` search form and the `OrderRepository` query builder. When "依頼あり" is selected, the search returns only orders containing items with `is_ec_requested=true`.

- **Linked Requirements:** REQ9_SEARCH_001, US-012
- **Affected Components:** `app/Customize/Form/Type/Admin/OrderType.php`, `app/Customize/Repository/OrderRepository.php`, `app/template/admin/Order/index.twig`
- **Scope:** Full-stack

#### Sub-task List
- [ ] 9.1 — Add EC依頼 radio to OrderType search form (Backend, 2h)
- [ ] 9.2 — Extend OrderRepository for EC依頼 filter query (Backend, 4h)
- [ ] 9.3 — Render EC依頼 radio in order list template (Frontend, 2h)
- [ ] 9.4 — Tests for EC依頼 search filter (Backend, 2h)

---

#### Sub-tasks:

##### Sub-task 9.1: Add EC依頼 radio to OrderType search form
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Add a `ChoiceType` field with `expanded=true` (radio buttons) for EC依頼 filter in the admin OrderType form. Choices: すべて (value=null), 依頼あり (value=1).

###### Requirement Details
- **Linked Requirements:** REQ9_SEARCH_001
- **Affected Files:** `app/Customize/Form/Type/Admin/OrderType.php`
- **Scope:** Form

###### Acceptance Criteria
- [ ] **Given** the order list search form, **When** rendered, **Then** EC依頼 radio options are present

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | is_ec_requested column must exist |

###### Definition of Done
- [ ] Radio field added to form type

---

##### Sub-task 9.2: Extend OrderRepository for EC依頼 filter query
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Add query condition in `OrderRepository.php` to join/filter by `is_ec_requested=true` on order items when the EC依頼 filter is set to "依頼あり". Use the existing index for performance.

###### Requirement Details
- Join `dtb_order_item` and filter `is_ec_requested = true`
- Only applied when filter value is "依頼あり"
- Must use `idx_order_item_ec_requested` index (NFR-003)
- **Linked Requirements:** REQ9_SEARCH_001, NFR-003
- **Affected Files:** `app/Customize/Repository/OrderRepository.php`
- **Scope:** Repository

###### Acceptance Criteria
- [ ] **Given** EC依頼=依頼あり, **When** search executed, **Then** only orders with EC-requested items returned
- [ ] **Given** EC依頼=すべて, **When** search executed, **Then** all orders returned (no EC依頼 filter)

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 9.1 | Blocked-by | Form field must supply filter value |

###### Definition of Done
- [ ] Query builds correct condition
- [ ] Search completes < 1s with index

---

##### Sub-task 9.3: Render EC依頼 radio in order list template
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

###### Summary
Render the EC依頼 radio buttons in the order list search form on `index.twig`.

###### Requirement Details
- **Linked Requirements:** REQ9_SEARCH_001
- **Affected Files:** `app/template/admin/Order/index.twig`
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** order list page loads, **When** search form displayed, **Then** EC依頼 radio is visible

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 9.1 | Blocked-by | Form field must exist |

###### Definition of Done
- [ ] Radio buttons render correctly

---

##### Sub-task 9.4: Tests for EC依頼 search filter
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Write tests verifying EC依頼 filter query logic: "依頼あり" returns only matching orders, "すべて" returns all.

###### Requirement Details
- **Linked Requirements:** REQ9_SEARCH_001
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** test data with mixed EC request states, **When** filter=依頼あり, **Then** correct subset returned

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 9.1–9.3 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] Filter tests pass

---

### Story 10: ファイル出力済み Search Filter on Order List

**Type:** Story | **Priority:** Medium | **Points:** 3 | **Sprint:** 3

#### Story Overview
Add a "ファイル出力済み" radio filter to the order list search form with two options: すべて (all — no filter) and 未出力のみ (output_datetime IS NULL). When "未出力のみ" is selected, the search returns only orders containing items that have NOT been exported yet. This enables admins to identify items not yet included in Excel exports.

- **Linked Requirements:** REQ9_SEARCH_002, US-013
- **Affected Components:** `app/Customize/Form/Type/Admin/OrderType.php`, `app/Customize/Repository/OrderRepository.php`, `app/template/admin/Order/index.twig`
- **Scope:** Full-stack

#### Sub-task List
- [ ] 10.1 — Add ファイル出力済み radio to OrderType search form (Backend, 2h)
- [ ] 10.2 — Extend OrderRepository for output_datetime filter query (Backend, 4h)
- [ ] 10.3 — Render ファイル出力済み radio in order list template (Frontend, 2h)
- [ ] 10.4 — Tests for ファイル出力済み search filter (Backend, 2h)

---

#### Sub-tasks:

##### Sub-task 10.1: Add ファイル出力済み radio to OrderType search form
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Add a `ChoiceType` field with `expanded=true` for ファイル出力済み filter. Choices: すべて (value=null), 未出力のみ (value=1).

###### Requirement Details
- **Linked Requirements:** REQ9_SEARCH_002
- **Affected Files:** `app/Customize/Form/Type/Admin/OrderType.php`
- **Scope:** Form

###### Acceptance Criteria
- [ ] **Given** the order list search form, **When** rendered, **Then** ファイル出力済み radio options are present

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | output_datetime column must exist |

###### Definition of Done
- [ ] Radio field added to form type

---

##### Sub-task 10.2: Extend OrderRepository for output_datetime filter query
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Add query condition in `OrderRepository.php` to join/filter by `output_datetime IS NULL` when the filter is set to "未出力のみ". Use the existing index.

###### Requirement Details
- Filter: `output_datetime IS NULL` on order items
- Only applied when filter = "未出力のみ"
- Must use `idx_order_item_output_datetime` index
- **Linked Requirements:** REQ9_SEARCH_002, NFR-003
- **Affected Files:** `app/Customize/Repository/OrderRepository.php`
- **Scope:** Repository

###### Acceptance Criteria
- [ ] **Given** ファイル出力済み=未出力のみ, **When** search executed, **Then** only orders with un-exported items returned
- [ ] **Given** ファイル出力済み=すべて, **When** search executed, **Then** no output_datetime filter applied

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 10.1 | Blocked-by | Form field must supply filter value |

###### Definition of Done
- [ ] Query condition correct
- [ ] Search < 1s with index

---

##### Sub-task 10.3: Render ファイル出力済み radio in order list template
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

###### Summary
Render the ファイル出力済み radio buttons in the order list template.

###### Requirement Details
- **Linked Requirements:** REQ9_SEARCH_002
- **Affected Files:** `app/template/admin/Order/index.twig`
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** order list page, **When** form displayed, **Then** ファイル出力済み radio is visible

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 10.1 | Blocked-by | Form field must exist |

###### Definition of Done
- [ ] Radio buttons render correctly

---

##### Sub-task 10.4: Tests for ファイル出力済み search filter
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Write tests verifying output_datetime filter logic: "未出力のみ" returns only items with null output_datetime, "すべて" returns all.

###### Requirement Details
- **Linked Requirements:** REQ9_SEARCH_002
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** test data with mixed output_datetime states, **When** filter=未出力のみ, **Then** correct subset returned

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-tasks 10.1–10.3 | Blocked-by | Feature complete |

###### Definition of Done
- [ ] Filter tests pass

---

### Story 11: Export Status Visibility on Order Detail

**Type:** Story | **Priority:** Medium | **Points:** 2 | **Sprint:** 3

#### Story Overview
Show the export status of each order item on the order detail page so store staff can see which items have already been included in an EC依頼 Excel export. Display the `output_datetime` value (or "未出力" if null) per order item row alongside the EC依頼 checkbox. This helps staff avoid duplicate processing.

- **Linked Requirements:** REQ3_EXCEL_004 (display aspect), US-004
- **Affected Components:** `app/template/admin/Order/edit.twig`
- **Scope:** Frontend

#### Sub-task List
- [ ] 11.1 — Display output_datetime status per order item on detail page (Frontend, 4h)

---

#### Sub-tasks:

##### Sub-task 11.1: Display output_datetime status per order item on detail page
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

###### Summary
Add a read-only display column or label per order item row on the order detail page showing the export status: formatted `output_datetime` if set, or "未出力" if null. Visible only for store pickup orders (order_type ∈ {11, 21, 31}).

###### Requirement Details
- Display as text (not an input): `{{ orderItem.outputDatetime|date('Y-m-d H:i') }}` or "未出力"
- Only visible for pickup order types
- Positioned near the EC依頼 checkbox
- **Linked Requirements:** REQ3_EXCEL_004, US-004
- **Affected Files:** `app/template/admin/Order/edit.twig`
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** order_type=11 with output_datetime set, **When** detail page loads, **Then** formatted timestamp displayed
- [ ] **Given** order_type=11 with output_datetime=null, **When** detail page loads, **Then** "未出力" displayed
- [ ] **Given** non-pickup order, **When** detail page loads, **Then** export status not shown

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 1 | Blocked-by | Entity property must exist |
| Story 4 | Relates-to | Export sets the timestamp |

###### Definition of Done
- [ ] Export status visible on order detail for pickup orders
- [ ] Correct formatting and conditional display

---

### Story 12: Admin Navigation Updates

**Type:** Story | **Priority:** Medium | **Points:** 1 | **Sprint:** 1

#### Story Overview
Update the admin navigation sidebar to reflect CR4 Phase 3 changes: (1) rename "店舗受取管理" to "商品受渡処理", and (2) add two new menu items for EC依頼リスト exports (Isesaki and Munakata). This is a template-only change that depends on routes being available.

- **Linked Requirements:** REQ3_EXCEL_005, REQ8_SCREEN_001
- **Affected Components:** Admin navigation template
- **Scope:** Frontend

#### Sub-task List
- [ ] 12.1 — Update admin nav template (Frontend, 2h)

---

#### Sub-tasks:

##### Sub-task 12.1: Update admin nav template
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

###### Summary
Modify the admin navigation template to: rename "店舗受取管理" to "商品受渡処理" and add "EC依頼リスト_伊勢崎拠点" and "EC依頼リスト_宗像拠点" menu items under the order management section.

###### Requirement Details
- **Linked Requirements:** REQ3_EXCEL_005, REQ8_SCREEN_001
- **Affected Files:** Admin navigation template (e.g., `app/template/admin/nav.twig` or block override)
- **Scope:** Template

###### Acceptance Criteria
- [ ] **Given** admin logged in, **When** viewing nav sidebar, **Then** "商品受渡処理" label shown (not "店舗受取管理")
- [ ] **Given** admin logged in, **When** viewing nav sidebar, **Then** both EC依頼リスト items visible

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 4 (Sub-task 4.3) | Relates-to | Export routes should exist for linking |

###### Definition of Done
- [ ] Navigation updated with all 3 changes
- [ ] No layout regression

---

### Story 13: Export Timing (Cutoff) Configuration

**Type:** Story | **Priority:** Medium | **Points:** 2 | **Sprint:** 2

#### Story Overview
Implement the cutoff time logic for EC依頼 Excel exports. Orders are cut off at 8:30 and 12:30, with Excel exports generated at 10:15 and 15:15 respectively. The export query must filter items based on these cutoff windows. This may be implemented as configurable parameters or constants in the ExcelExportService.

- **Linked Requirements:** REQ3_EXCEL_001 (timing aspect)
- **Affected Components:** `app/Customize/Service/ExcelExportService.php`, `app/Customize/Controller/Admin/Order/ExcelExportController.php`
- **Scope:** Backend

#### Sub-task List
- [ ] 13.1 — Implement cutoff time filtering in export query (Backend, 4h)
- [ ] 13.2 — Tests for cutoff time logic (Backend, 2h)

---

#### Sub-tasks:

##### Sub-task 13.1: Implement cutoff time filtering in export query
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Add cutoff time logic to the Excel export query: orders created before 8:30 are included in the 10:15 export; orders created before 12:30 are included in the 15:15 export. Define cutoff windows as constants or configurable parameters.

###### Requirement Details
- Cutoff 1: orders before 8:30 → export at 10:15
- Cutoff 2: orders before 12:30 → export at 15:15
- Query filters orders based on current time slot
- **Linked Requirements:** REQ3_EXCEL_001
- **Affected Files:** `app/Customize/Service/ExcelExportService.php`
- **Scope:** Service

###### Acceptance Criteria
- [ ] **Given** export triggered at 10:15, **When** query executes, **Then** only orders created before 8:30 included
- [ ] **Given** export triggered at 15:15, **When** query executes, **Then** only orders created before 12:30 included

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 4 (Sub-task 4.1) | Blocked-by | ExcelExportService must exist |

###### Definition of Done
- [ ] Cutoff logic implemented and configurable
- [ ] Correct windowing verified

---

##### Sub-task 13.2: Tests for cutoff time logic
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

###### Summary
Write tests verifying cutoff time windows filter orders correctly.

###### Requirement Details
- **Linked Requirements:** REQ3_EXCEL_001
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Test

###### Acceptance Criteria
- [ ] **Given** orders at various times, **When** 10:15 export runs, **Then** only pre-8:30 orders included

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Sub-task 13.1 | Blocked-by | Cutoff logic must exist |

###### Definition of Done
- [ ] Cutoff tests pass

---

### Story 14: Integration Testing & Edge Case Validation

**Type:** Story | **Priority:** High | **Points:** 13 | **Sprint:** 4

#### Story Overview
Comprehensive integration testing across all CR4 Phase 3 features. Covers end-to-end flows: EC依頼 → Excel export → status update → barcode completion. Validates authority restrictions, pre-order lifecycle, popup behavior, search filters, and cross-feature interactions. Includes edge case testing from SRS Section 9 (15 corner cases).

- **Linked Requirements:** All REQs, All USs, NFR-001 through NFR-014
- **Affected Components:** All CR4 Phase 3 components
- **Scope:** Full-stack

#### Sub-task List
- [ ] 14.1 — End-to-end EC依頼 + Export + Completion flow test (Full-stack, 8h)
- [ ] 14.2 — Authority id=6 integration tests (Full-stack, 4h)
- [ ] 14.3 — Pre-order lifecycle integration test (Full-stack, 4h)
- [ ] 14.4 — Edge case validation from SRS Corner Cases (Full-stack, 8h)
- [ ] 14.5 — Performance validation (NFR compliance) (Backend, 4h)

---

#### Sub-tasks:

##### Sub-task 14.1: End-to-end EC依頼 + Export + Completion flow test
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Full-stack

###### Summary
Test the full flow: store staff marks item as EC依頼 → admin exports Excel (output_datetime set) → EC HQ ships → store receives → status update → customer pickup with barcode scan → order completion.

###### Requirement Details
- **Linked Requirements:** US-001, US-002, US-003, US-004, US-009
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Integration test

###### Acceptance Criteria
- [ ] **Given** OOS item on pickup order, **When** full flow executed, **Then** order reaches completion with correct timestamps

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Stories 1–11 | Blocked-by | All features must be implemented |

###### Definition of Done
- [ ] End-to-end flow test passes

---

##### Sub-task 14.2: Authority id=6 integration tests
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Full-stack

###### Summary
Verify authority_id=6 restrictions across all entry points and features: order list filtering, order detail restrictions, export access, barcode scan access.

###### Requirement Details
- **Linked Requirements:** REQ7_AUTH_001–006
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Integration test

###### Acceptance Criteria
- [ ] **Given** auth=6 user, **When** navigating all accessible routes, **Then** restrictions consistent

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 7 | Blocked-by | Authority feature must be complete |

###### Definition of Done
- [ ] All authority integration tests pass

---

##### Sub-task 14.3: Pre-order lifecycle integration test
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Full-stack

###### Summary
Test the complete order_type=31 lifecycle: creation → status transitions → CAN_RECEIVE → email + barcode → scan → completion.

###### Requirement Details
- **Linked Requirements:** REQ6_PREORDER_001–005
- **Affected Files:** `codeception/` (new test file)
- **Scope:** Integration test

###### Acceptance Criteria
- [ ] **Given** order_type=31, **When** full lifecycle simulated, **Then** all statuses transition correctly and email/barcode triggered

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Story 6 | Blocked-by | Pre-order feature must be complete |

###### Definition of Done
- [ ] Lifecycle integration test passes

---

##### Sub-task 14.4: Edge case validation from SRS Corner Cases
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Full-stack

###### Summary
Validate all 15 corner cases from SRS Section 9: navigating away without save, duplicate export timestamps, direct URL access for auth=6, already-completed barcode scan, empty export, OOS→in-stock transition, pre-order OOS, Batch007 backward compat, simultaneous exports, incomplete deny_url, 商品手配中 status, email recall, email failure at CAN_RECEIVE, unmapped uketori_location_cd, large export dataset.

###### Requirement Details
- **Linked Requirements:** SRS Section 9, Corner Cases 1–15
- **Affected Files:** `codeception/` (new test files)
- **Scope:** Integration test

###### Acceptance Criteria
- [ ] **Given** each corner case scenario, **When** simulated, **Then** expected behavior matches SRS specification

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Stories 1–11 | Blocked-by | All features complete |

###### Definition of Done
- [ ] All 15 corner cases validated

---

##### Sub-task 14.5: Performance validation (NFR compliance)
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

###### Summary
Verify NFR compliance: Excel export < 10s for 1,000 items (NFR-001), order detail < 2s (NFR-002), search filters < 1s (NFR-003), barcode scan → popup < 500ms (NFR-004).

###### Requirement Details
- **Linked Requirements:** NFR-001, NFR-002, NFR-003, NFR-004
- **Affected Files:** Test scripts / profiling tools
- **Scope:** Performance test

###### Acceptance Criteria
- [ ] **Given** 1,000 order items, **When** Excel export runs, **Then** completes < 10s
- [ ] **Given** order detail page with EC依頼, **When** loaded, **Then** response < 2s
- [ ] **Given** order list with filters, **When** searched, **Then** response < 1s
- [ ] **Given** barcode scan, **When** popup triggered, **Then** response < 500ms

###### Dependencies
| Dependency | Type | Details |
|---|---|---|
| Stories 1–11 | Blocked-by | All features deployed to test environment |

###### Definition of Done
- [ ] All NFR thresholds met

---

## Cross-Story Dependencies

```
Story 1 (DB/Entity) ──► Story 2 (EC依頼 Checkbox)
                    ──► Story 4 (Excel Export)
                    ──► Story 5 (Batch007)
                    ──► Story 6 (Pre-order)
                    ──► Story 7 (Authority)
                    ──► Story 9 (EC依頼 Filter)
                    ──► Story 10 (Export Filter)
                    ──► Story 11 (Export Status Display)

Story 2 ──► Story 3 (Popup Flow) — auto-save removal shared
Story 4 ──► Story 11 (Export Status Display) — output_datetime set by export
Story 4 ──► Story 13 (Cutoff Timing) — export service extension

Stories 1–11 ──► Story 14 (Integration Tests)
```

---

## Suggested Sprint Allocation

| Sprint | Stories | Points | Focus |
|--------|---------|--------|-------|
| Sprint 1 | Story 1 (DB), Story 2 (EC依頼 Checkbox), Story 3 (Popup), Story 12 (Nav) | 17 | Foundation + Order Detail changes |
| Sprint 2 | Story 4 (Excel Export), Story 5 (Batch007), Story 6 (Pre-order), Story 7 (Authority), Story 13 (Cutoff) | 36 | Core features: export, batch, lifecycle, auth |
| Sprint 3 | Story 8 (商品受渡処理 Screen), Story 9 (EC依頼 Filter), Story 10 (Export Filter), Story 11 (Export Status) | 13 | Screen updates + search enhancements |
| Sprint 4 | Story 14 (Integration Tests) | 13 | Testing, validation, performance |
| **Total** | **14 Stories** | **79** | **~4–6 dev-weeks** |

---

## Risk Summary

| # | Risk | Likelihood | Impact | Mitigation |
|---|------|-----------|--------|-----------|
| R-01 | Q-01 blocker: 商品手配中 not in `dcm_shipping_status` | High | High — blocks Story 3 popup trigger | Escalate immediately; fallback: use existing status value |
| R-02 | Q-02 blocker: East/West `uketori_location_cd` mapping unknown | High | High — blocks Story 4 Excel export | Request mapping table from business team ASAP |
| R-03 | AMS SC連携 coordination delay (MRMAX_ECOPE-3335) | Medium | Medium — blocks Story 5 Batch007 | Begin dev with mock timing; integrate AMS response later |
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
| REQ2_ECREQ_001 | Story 2 | 2.1, 2.3 | Planned |
| REQ2_ECREQ_002 | Story 2 | 2.3 | Planned |
| REQ2_ECREQ_003 | Story 2 | 2.1, 2.2 | Planned |
| REQ3_EXCEL_001 | Story 4 | 4.3, 4.4 | Planned — Blocked (Q-02) |
| REQ3_EXCEL_002 | Story 4 | 4.1 | Planned |
| REQ3_EXCEL_003 | Story 4 | 4.1 | Planned |
| REQ3_EXCEL_004 | Story 4, Story 11 | 4.2, 11.1 | Planned |
| REQ3_EXCEL_005 | Story 4, Story 12 | 4.5, 12.1 | Planned |
| REQ4_SC_001 | Story 5 | 5.1 | Planned |
| REQ4_SC_002 | Story 5 | 5.1 | Planned |
| REQ4_SC_003 | Story 5 | 5.2 | Planned |
| REQ5_DETAIL_001 | Story 2 | 2.4 | Planned |
| REQ5_DETAIL_002 | Story 2 | 2.4 | Planned |
| REQ5_DETAIL_003 | Story 3 | 3.1 | Planned — Blocked (Q-01) |
| REQ5_DETAIL_004 | Story 3 | 3.2, 3.3 | Planned |
| REQ5_DETAIL_005 | Story 3 | 3.1, 3.3 | Planned |
| REQ6_PREORDER_001 | Story 6 | 6.1 | Planned |
| REQ6_PREORDER_002 | Story 6 | 6.3 | Planned |
| REQ6_PREORDER_003 | Story 6 | 6.3 | Planned |
| REQ6_PREORDER_004 | Story 6 | 6.1 | Planned |
| REQ6_PREORDER_005 | Story 6 | 6.2 | Planned |
| REQ7_AUTH_001 | Story 1, Story 7 | 1.2, 7.1 | Planned |
| REQ7_AUTH_002 | Story 7 | 7.2, 7.5 | Planned |
| REQ7_AUTH_003 | Story 7 | 7.4 | Planned |
| REQ7_AUTH_004 | Story 7 | 7.2, 7.3 | Planned |
| REQ7_AUTH_005 | Story 7 | 7.1 | Planned |
| REQ7_AUTH_006 | Story 7 | 7.3, 7.5 | Planned |
| REQ8_SCREEN_001 | Story 8, Story 12 | 8.1, 12.1 | Planned |
| REQ8_SCREEN_002 | Story 8 | 8.2 | Planned |
| REQ8_SCREEN_003 | Story 8 | 8.3 | Planned |
| REQ8_SCREEN_004 | Story 8 | 8.4 | Planned |
| REQ8_SCREEN_005 | Story 8 | 8.3 | Planned |
| REQ9_SEARCH_001 | Story 9 | 9.1, 9.2, 9.3 | Planned |
| REQ9_SEARCH_002 | Story 10 | 10.1, 10.2, 10.3 | Planned |
| US-001 | Story 2 | 2.1–2.5 | Planned |
| US-002 | Story 4 | 4.1–4.6 | Planned |
| US-003 | Story 4 | 4.1–4.6 | Planned |
| US-004 | Story 11 | 11.1 | Planned |
| US-005 | Story 2 | 2.4 | Planned |
| US-006 | Story 3 | 3.1–3.4 | Planned |
| US-007 | Story 7 | 7.3 | Planned |
| US-008 | Story 7 | 7.2, 7.5 | Planned |
| US-009 | Story 8 | 8.2 | Planned |
| US-010 | Story 6 | 6.2 | Planned |
| US-011 | Story 6 | 6.3 | Planned |
| US-012 | Story 9 | 9.1–9.4 | Planned |
| US-013 | Story 10 | 10.1–10.4 | Planned |
| US-014 | Story 5 | 5.1–5.3 | Planned |
| NFR-001 | Story 4 | 4.1 | Planned |
| NFR-002 | Story 2 | 2.3 | Planned |
| NFR-003 | Story 9, Story 10 | 9.2, 10.2 | Planned |
| NFR-004 | Story 8 | 8.2 | Planned |
| NFR-005 | Story 4 | 4.1 | Planned |
| NFR-006 | Story 8 | 8.1 | Planned |
| NFR-007 | Story 8 | 8.3 | Planned |
| NFR-008 | Story 7 | 7.2 | Planned |
| NFR-009 | Story 7 | 7.2 | Planned |
| NFR-010 | Story 4 | 4.2 | Planned |
| NFR-011 | Story 2 | 2.2, 2.4 | Planned |
| NFR-012 | Story 5 | 5.3 | Planned |
| NFR-013 | Story 4 | 4.1 | Planned |
| NFR-014 | Story 4 | 4.2 | Planned |
