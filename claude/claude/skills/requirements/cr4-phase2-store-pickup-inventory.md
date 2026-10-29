---
name: "cr4-phase2-store-pickup-inventory"
description: "CR4-Phase2 Store Pickup Inventory — store stock deduction, new shipping status, store backorder columns, admin UI (order list/detail, picking, packing, shop memo)"
---

# CR4-Phase2: Store Pickup Inventory & Operations Skill

**Prerequisites:** Review `core-essentials` for critical rules. Review `change-request` for CR methodology.

## When to Use

- Adding store-level backorder columns (`store_is_backordered`, `store_lack_count`)
- Working on the new "商品手配中" (Arranging) shipping status
- Modifying stock deduction logic for store pickup orders (types 11, 21, 31)
- Updating admin order list search/bulk update/CSV for new status
- Adding store/online toggle in order detail for store pickup orders
- Modifying total picking list (authority, store stock column, PDF)
- Adding barcodes (JAN8/JAN13) to packing list PDF/HTML
- Updating shop memo (accordion, popup, append behavior)
- Authority enforcement for `authority_id = 6` (store staff)

## Expected Outcome

- Store pickup orders deduct stock from **receiving store** (not EC warehouse)
- Store-level backorder fields correctly populated for store pickup orders
- EC-level backorder fields remain `false`/`0` for store pickup orders
- "商品手配中" status integrates into existing shipping status flow
- Admin UI correctly filters, displays, and exports new data
- Barcodes are scannable when printed from PDF
- Authority_id=6 enforced server-side (not CSS-only)

---

## Requirement Groups Overview

| Req | Title | Category | Priority |
|-----|-------|----------|----------|
| 1 | Add columns: `store_is_backordered`, `store_lack_count` | Table | Foundation |
| 2 | Add shipping status: 商品手配中 (ID=4) | Table | Foundation |
| 3 | Change stock deduction for store pickup to store inventory | Logic | **Critical** |
| 4 | Admin order list: search, bulk update, missing CSV | Admin | Medium |
| 5 | Admin order detail: store/online toggle, authority_id=6 | Admin | Medium |
| 6 | Total picking list: authority enforcement, store stock column | Admin | Medium |
| 7 | Packing list: JAN barcode, store stock column, CSV | Admin | Medium |
| 8 | Shop memo: accordion, popup edit, append behavior | Admin | Low |

### Dependency Chain

```
Req 1 (DB columns) ──────► Req 3 (Inventory logic uses store columns)
         │                             │
         ├──► Req 5 (Order detail shows store backorder data)
         │                             │
         ▼                             ▼
Req 2 (New status) ──────► Req 4 (Search/bulk update with new status)
                                       │
                    ┌──────────────────┤
                    ▼                  ▼
              Req 6 (Picking)    Req 7 (Packing)
                                       │
                                       ▼
                                 Req 8 (Shop Memo)
```

### Implementation Order

```
Phase 2A (Foundation): Req 1 → Req 2
Phase 2B (Core Logic): Req 3
Phase 2C (Admin UI):   Req 4, 5, 6, 7, 8 (parallelizable)
```

---

## File Map (Key Files)

```
Entity / Schema:
  app/Customize/Entity/OrderItemTrait.php       → store_is_backordered, store_lack_count (Req 1)
  app/Customize/Entity/ShippingStatus.php        → ARRANGING = 4 constant (Req 2)
  app/Customize/Entity/LocationStock.php         → ec_stock_reservable (store stock)
  app/Customize/Entity/OrderType.php             → PICKUP_TYPE = [11, 21, 31]

Business Logic:
  app/Customize/Service/OrderHelper.php          → processStockCheckout(), updateBackorderedProductItem(), recalculateBackOrdered() (Req 3)
  app/Customize/Service/PurchaseFlow/Processor/StockReduceProcessor.php → Stock reduce for store (Req 3)
  app/Customize/EventListener/OrderCompleteListener.php → Redis lock for store stock (Req 3)
  app/Customize/Service/OrderState/Rule.php      → Transition rules for ARRANGING status (Req 2, 3)
  app/Customize/Service/Admin/OrderService.php   → Status transitions, CSV export, mail (Req 2, 4)

Admin Controllers:
  app/Customize/Controller/Admin/Order/OrderController.php       → Order list, bulk ops (Req 4)
  app/Customize/Controller/Admin/Order/EditController.php        → Order detail/edit (Req 5, 8)
  app/Customize/Controller/Admin/Order/TotalPickingController.php → Picking list, PDF (Req 6)
  app/Customize/Controller/Admin/Order/PackingController.php     → Packing list, PDF, CSV (Req 7)

Form Types:
  app/Customize/Form/Type/Admin/SearchOrderType.php        → Search with new status (Req 4)
  app/Customize/Form/Type/Admin/StockBulkUpdateType.php    → Bulk update (Req 4)
  app/Customize/Form/Type/Admin/SearchTotalPickingType.php → Authority enforcement (Req 6)
  app/Customize/Form/Type/Admin/OrderPackingSearchType.php → Authority enforcement (Req 7)
  app/Customize/Form/Type/Admin/OrderType.php              → Memo form handling (Req 8)

Templates:
  app/template/admin/Order/index.twig                        → Order list UI (Req 4)
  app/template/admin/Order/edit.twig                         → Order detail UI (Req 5, 8)
  app/template/admin/Order/Shipping/products_list.twig       → Store backorder display (Req 5)
  app/template/admin/Order/Shipping/memo.twig                → Memo accordion/popup (Req 8)
  app/template/admin/Order/Shipping/standard_keep_in_store.twig → Store pickup view (Req 5)
  app/template/admin/Order/Picking/                          → Picking HTML templates (Req 6)
  app/template/admin/Order/Export/Picking/                   → Picking PDF templates (Req 6)
  app/template/admin/Order/Packing/Sections/order_item_list.twig → Packing HTML (Req 7)
  app/template/admin/Order/Export/Packing/order_item_list.twig   → Packing PDF (Req 7)

Data Fixtures:
  app/Customize/DataFixture/Master/ShippingStatusFixture.php      → Seed ARRANGING (Req 2)
  app/Customize/DataFixture/Master/csv/shipping_status.csv        → CSV seed data (Req 2)

Repositories:
  app/Customize/Repository/PickingRepository.php    → Store stock query (Req 6)

Downstream (Cascade Impact from Req 3):
  app/Customize/Service/Admin/InvoiceService.php    → realQty = quantity - storeLackCount
  app/Customize/Service/Admin/PackingService.php    → SUM(store_lack_count)
  app/Customize/Command/Batch007Command.php         → QTY = quantity - storeLackCount
```

---

## Req 1 — Database Schema: Store Backorder Columns

### New Columns on `dtb_order_item`

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `store_is_backordered` | boolean | false | Store-level out-of-stock flag |
| `store_lack_count` | integer | 0 | Store-level missing item count |

### Existing EC-Level Counterparts (DO NOT MODIFY)

| Column | Type | Default | Purpose |
|--------|------|---------|---------|
| `is_backordered` | boolean | false | EC-level backorder flag |
| `lack_count` | integer | 0 | EC-level missing item count |

### Implementation

1. Add ORM-annotated properties to `OrderItemTrait.php`
2. Add getters/setters: `getStoreIsBackordered()`, `setStoreIsBackordered()`, `getStoreLackCount()`, `setStoreLackCount()`
3. Apply manual SQL: `ALTER TABLE dtb_order_item ADD store_is_backordered BOOLEAN DEFAULT FALSE, ADD store_lack_count INT DEFAULT 0`
4. Run `bin/console eccube:generate:proxies`

---

## Req 2 — New Shipping Status: 商品手配中 (ARRANGING)

### Status Definition

| ID | Name (JP) | Name (EN) | Constant | sort_no |
|----|-----------|-----------|----------|---------|
| 4 | 商品手配中 | Arranging | `ARRANGING` | Between PREPARING(1) and READY(2) |

### Updated Shipping Status Flow

```
NOT_SHIPPED (0)
    ↓ [orderStatus == IN_PROGRESS]
PREPARING_TO_SHIP (1)
    ├──► ARRANGING (4) [store items backordered] ← NEW
    │        ↓ [stock fulfilled]
    └──► READY_TO_SHIP (2) [no backordered items]
             ↓ [trackingNumber exists]
         SHIPPED (9)
```

### Frontend Display Mapping

| Shipping Status | Customer-Facing Display |
|----------------|------------------------|
| 出荷準備中 (Preparing) | 準備中 |
| **商品手配中 (Arranging)** | **準備中** (same as Preparing) |
| 出荷準備完了 (Ready) | 準備中 |

### Key Rule
If no product is out of stock at the store → skip "商品手配中" → go directly to "出荷準備完了".

---

## Req 3 — Stock Deduction Logic Change (CRITICAL)

### Stock Deduction Rule

| Stock Type | Online Delivery (Type 10) | Store Pickup (Type 11, 21, 31) |
|---|---|---|
| EC warehouse `ec_stock_reservable` | ✅ Deducted | ❌ **Not deducted** |
| Receiving store `ec_stock_reservable` | Not used | ✅ **Deducted** |
| EC `is_backordered` / `lack_count` | ✅ Used | ❌ Always false / 0 |
| Store `store_is_backordered` / `store_lack_count` | Not used | ✅ **Used** |

### Location Code Mapping

| Delivery Type | Order Types | Location Source | Stock Deducted From |
|---|---|---|---|
| Normal delivery | 10, 30 | `shipping_location_cd` | Warehouse |
| Store pickup | 11, 21, 31 | `uketori_location_cd` | **Store** (NEW) |
| Express delivery | 20, 21 | `sokuhai_location_cd` | Store |

### Key Change Points in `OrderHelper.php`

1. **`processStockCheckout()`** (~line 1868): Change `increaseQuantity()` target from shipping warehouse to receiving store for `$isOrderKeepInStore == true`
2. **`updateBackorderedProductItem()`** (~line 1990): Write to `store_is_backordered`/`store_lack_count` instead of EC columns for store pickup. Set EC columns to `false`/`0`.
3. **`recalculateBackOrdered()`** (~line 1200): Use store-level stock for cart recalculation
4. **Redis lock**: Acquire lock on receiving store's LocationStock ID (not shipping warehouse)

### Cascade Impact (Must Update)

| System | File | Change |
|--------|------|--------|
| Status transition | `Rule.php` | Check `store_is_backordered`/`store_lack_count` for store pickup |
| Invoice | `InvoiceService.php` | `realQty = quantity - storeLackCount` for store pickup |
| Packing totals | `PackingService.php` | `SUM(store_lack_count)` for store pickup |
| Batch007 CSV | `Batch007Command.php` | `QTY = quantity - storeLackCount` for store pickup |
| Mail notification | `OrderService.php` | Use `storeLackCount` in mail body for store pickup |
| Wait list | `OrderController.php` | Include `store_is_backordered` for store pickup |
| Frontend display | `is_back_ordered_label.twig` | Check `store_is_backordered` for store pickup |

### Race Condition (Client Confirmed Acceptable)

Store stock may go negative between cart check and purchase. Shortage recorded in `store_lack_count`. Store staff arranges missing items manually.

---

## Req 4 — Admin Order List Updates

### D.2.1 — Search with "商品手配中"
- Add to `shipping_status` field in `SearchOrderType.php`
- Conditional: only active when "Store pick up" is checked in Order Categories

### D.2.2 — Bulk Update
- Add "商品手配中" to bulk status update options

### D.2.3 — Missing CSV: New Columns

| # | Label | Source | Status |
|---|-------|--------|--------|
| 1-5 | (existing columns) | | Existing |
| **6** | **店舗名** | Store relation | **NEW** |
| **7** | **店舗欠品** | `store_is_backordered` | **NEW** |
| **8** | **店舗欠品数** | `store_lack_count` | **NEW** |

Update `exportOrderProductStockInfoCsv()` in `OrderService.php`.

---

## Req 5 — Admin Order Details Updates

### Store/Online Toggle
- New toggle button, visible only for PICKUP_TYPE orders (11, 21, 31)
- "店舗" view shows `store_is_backordered`, `store_lack_count`
- "オンライン" view shows `is_backordered`, `lack_count`

### Authority_id=6 (Store Staff)
- **Enable editing** of the toggle area and store backorder fields
- Currently no authority_id=6 check exists — must be added
- Use `$this->getUser()->getChargeLocationCd()` as authority proxy

---

## Req 6 — Total Picking List Updates

### Authority Enforcement
- Server-side restriction for `authority_id = 6` — prevent store change
- Current: CSS-only hiding via `d-none` class (insufficient)
- Add proper validation in `TotalPickingController.php` and `SearchTotalPickingType.php`

### Store Stock Column
- Column header: `[store name] + 在庫数`
- Value: `dct_location_stock.ec_stock_reservable` for the **pickup store**
- Already displayed in current UI — verify if existing query returns correct store
- Update both HTML and PDF templates

---

## Req 7 — Packing List Updates

### Barcode Addition
- JAN code 8 digits → **JAN8 barcode** (EAN-8)
- JAN code 13 digits → **JAN13 barcode** (EAN-13)
- Must be scannable when printed
- Requires new Composer dependency (e.g., `picqer/php-barcode-generator`)

### Store Stock Column
- Same as Req 6: `[store name] + 在庫数`
- Add to HTML, PDF, and CSV

### CSV Update
- Add "店舗在庫数" column from `dct_location_stock.ec_stock_reservable`

---

## Req 8 — Shop Memo Updates

### Current State
- Simple textarea in `memo.twig`
- Max length: 4000 chars (`OrderType::NOTE_LENGTH`)
- Field: `Order.note` (string, length=4000)

### Required Changes
1. **Accordion UI**: Wrap note display in collapsible component
2. **Read-only display**: Lighter text color, not directly editable
3. **Edit button**: "メモ追加" button opens popup modal
4. **Popup editor**: Modal dialog with "保存" (Save) and placeholder "ここにメモを追加…"
5. **Append logic**: New text appended to existing note with line break (not replace)
6. **Character limit**: Validate total length before append (4000 chars)

---

## Store Pickup Order Types Reference

```php
STANDARD_KEEP_IN_STORE = 11       // Standard Store Pickup
EXPRESS_KEEP_IN_STORE  = 21       // Express Store Pickup
BOOKING_ORDER_KEEP_IN_STORE = 31  // Booking Store Pickup
PICKUP_TYPE = [11, 21, 31]        // All pickup types
ORDER_TYPE_IN_HOUSE = [11, 31]    // In-house / non-express pickup
```

---

## Shipping Status Constants Reference

```php
NOT_SHIPPED = 0          // 未出荷
PREPARING_TO_SHIP = 1    // 出荷準備中
READY_TO_SHIP = 2        // 出荷準備完了
SC_OPTION = 3            // SC連携
ARRANGING = 4            // 商品手配中 ← NEW
SHIPPED = 9              // 出荷済み
```

---

## Authority / Permission Reference

| Area | Current Implementation | Required Change |
|------|----------------------|-----------------|
| Order Edit (Req 5) | No authority check | Enable editing for authority_id=6 |
| Total Picking (Req 6) | CSS-only hiding | Server-side enforcement |
| Packing List (Req 7) | Server-side query filtering | Maintain + add authority check |

**Recommendation:** Create centralized authority check service/helper.

---

## Open Questions

| # | Question | Req | Status |
|---|----------|-----|--------|
| Q2 | Should "商品手配中" auto-trigger or be manually set? | 2 | Open |
| Q3 | How does status ID=4 interact with SC_OPTION (ID=3)? | 2 | Open |
| Q5 | "店舗名" in Missing CSV — receiving store or shipping location? | 4 | Open |
| Q7 | What exactly is the "red area" in order details Figma? | 5 | Open |
| Q8 | What data changes between store/online toggle modes? | 5 | Open |
| Q9 | How should authority_id=6 be formalized? | 5,6,7 | Open |
| Q10 | Is existing `ec_stock_reservable` query sufficient for store stock column? | 6,7 | Open |
| Q11 | Barcode format: embedded image (PNG/SVG) in PDF? | 7 | Open |
| Q12 | Which barcode library is preferred? | 7 | Open |
| Q13 | Character limit for shop memo: 4000 or 3000? | 8 | Open |
| Q14 | Should memo append include timestamp/author? | 8 | Open |

---

## Implementation Checklist

### Before Changes
- [ ] Identify affected files from File Map
- [ ] Check dependency chain — Req 1 & 2 must be completed first
- [ ] Verify current `processStockCheckout()` flow for the specific order type
- [ ] Confirm which backorder columns (EC vs store) apply for the order type

### During Changes
- [ ] Store pickup orders: deduct from `uketori_location_cd` (receiving store)
- [ ] Store pickup orders: write to `store_is_backordered`/`store_lack_count`
- [ ] Store pickup orders: set EC columns to `false`/`0`
- [ ] Non-pickup orders: no changes to existing flow
- [ ] Authority checks enforced server-side
- [ ] All status transitions validated in `Rule.php`
- [ ] Use translation keys for new labels

### After Changes
- [ ] Verify stock deduction target for all order types (10, 11, 20, 21, 30, 31)
- [ ] Verify no regression on express delivery (type 20)
- [ ] Test concurrent store pickup orders (Redis lock)
- [ ] Verify CSV export includes new columns
- [ ] Test barcode scanning on printed PDF (Req 7)
- [ ] Test authority_id=6 access across all views
- [ ] Clear cache: `bin/console cache:clear`
- [ ] Generate proxies: `bin/console eccube:generate:proxies`

---

## Testing Scenarios

1. **Store pickup + stock available**: Type 11 order, store has enough stock → `store_is_backordered=false`, `store_lack_count=0`, EC stock unchanged
2. **Store pickup + partial stock**: Type 11, store has 2 of 5 → `store_is_backordered=true`, `store_lack_count=3`, EC stock unchanged
3. **Store pickup + no stock**: Type 11, store has 0 → `store_is_backordered=true`, `store_lack_count=quantity`, EC stock unchanged
4. **Online delivery unchanged**: Type 10 order → EC stock deducted, `is_backordered`/`lack_count` used as before
5. **Express store pickup**: Type 21 → deduction from store, express-specific backorder bypass preserved
6. **Status transition**: PREPARING → ARRANGING (store items backordered) → READY (stock fulfilled)
7. **Concurrent orders**: Two store pickup orders to same store simultaneously → Redis lock prevents double-deduction
8. **Missing CSV export**: New columns correctly populated
9. **Barcode scan**: JAN8 and JAN13 barcodes scannable from printed PDF
10. **Memo append**: New text appended with line break, total length ≤ 4000

---

## Common Bug Patterns

| Bug | Root Cause | Fix Location |
|-----|-----------|-------------|
| EC stock deducted for store pickup | `increaseQuantity()` using wrong LocationStock | `OrderHelper::processStockCheckout()` |
| Store backorder written to EC columns | Missing conditional for store vs EC columns | `OrderHelper::updateBackorderedProductItem()` |
| Status stuck in ARRANGING | Missing transition to READY_TO_SHIP | `Rule.php` + `OrderService.php` |
| Authority bypass via URL manipulation | CSS-only hiding, no server check | `TotalPickingController`, `SearchTotalPickingType` |
| Barcode not scannable | Low resolution or wrong format | Barcode library config, PDF DPI |
| Memo exceeds max length after append | No total length validation | `EditController` append logic |
| SC_OPTION conflict with ARRANGING | Adjacent IDs interacting | Verify `SC_OPTION=3` vs `ARRANGING=4` separation |

---

## Related Skills

- **`core`** — Architecture rules, never modify `src/Eccube/`
- **`change-request`** — CR implementation methodology
- **`testing`** — Write tests for stock deduction logic
- **`code-review`** — Security/performance review checklist
