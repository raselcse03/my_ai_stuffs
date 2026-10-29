---
name: "cr2-phase2-ac-installation"
description: "CR2-Phase2 AC Installation Queries - conditional form fields, cost estimation, outlet pattern logic, and drilling validation"
---

# CR2-Phase2: AC Installation Queries Skill

**Prerequisites:** Review `core-essentials` for critical rules. Review `change-request` for CR methodology.

## When to Use

- Modifying AC installation checkout form fields or visibility logic
- Changing cost estimation/calculation (attach goods AC001-AC034)
- Fixing conditional show/hide behavior for installation queries
- Working on outlet pattern logic (P1-P6)
- Modifying drilling cost validation chain
- Updating estimation modal or PDF generation
- Responsive design changes for installation checkout
- Adding/modifying translation keys for installation fields

## Expected Outcome

- Form field visibility correctly follows parent-child hierarchy
- Cost estimation accurately maps to attach goods codes
- Pattern logic (P1-P6) correctly determines electrical work fields
- Frontend (JS) and backend (PHP) validation stay synchronized
- Responsive design works on both desktop (≥768px) and mobile (<768px)

---

## File Map (Key Files)

```
Frontend:
  app/template/default/Shopping/InstallationCheckout/Sections/
    ac_installation_queries.twig          → Main form template
    payment_price_infor.twig              → Cost display (desktop)
    noted.twig                            → Cost display (mobile)
    installation_service_query.twig       → Constants template

  app/template/default/Shopping/Dialog/
    installation_modal.twig               → Estimation modal + calculateACCosts()
    installation_query_pdf.html.twig      → PDF generation template

  html/template/default/assets/dest/js/
    001_001_checkout_installation.js       → Main JS (show/hide, pattern logic)

  markup/source/sass/
    001_001_checkout_install.scss          → SCSS styles (BEM methodology)

Backend:
  app/Customize/Entity/
    InstallationQuery.php                 → Entity + field constants

  app/Customize/Form/Type/Front/
    InstallationQueryType.php             → Symfony form type

  app/Customize/Service/
    InstallationCostCalculationService.php → Backend cost calculation

  app/Customize/Repository/
    InstallationQueryRepository.php       → DB persistence + validation
```

---

## Field Hierarchy (5 Levels)

### LEVEL 1 - Always Visible & Required
| # | Field ID | Type | Options |
|---|----------|------|---------|
| 1 | `installation_type` | Radio | New Install / Replacement |
| 2 | `residence_type_ac` | Radio grid | 12 residence options |
| 3 | `room_size` | Radio grid | 7 room sizes (tatami) |
| 4 | `wall_structure` | Radio grid | Mortar(1)/Concrete(2)/Block(3)/MudWall(4)/Other(5) |
| 5 | `pipe_hole` | Radio | Available(1) / Not Available(2) |

### LEVEL 2 - Conditionally Required
| Condition | Field ID | Options |
|-----------|----------|---------|
| `installation_type = REPLACEMENT` | `removal_option` | Disposal(AC001) / Reuse(AC002) |
| `pipe_hole = AVAILABLE` | `dedicated_outlet` | Available(1)/NotAvailable(2)/Other(3) |
| `pipe_hole = NOT_AVAILABLE` | `hole_drilling` | Possible(1) / Impossible(2) |

### LEVEL 3 - Grandchild Dependencies
| Path | Field ID | Notes |
|------|----------|-------|
| `hole_drilling = POSSIBLE` | `hole_drilling_possible` | Before/After 2006 → AC008/AC009+AC010 |
| `hole_drilling = IMPOSSIBLE` | `hole_drilling_not_possible` | 4 options → AC032/AC033/AC034 |
| Both drilling paths | `dedicated_outlet` | Same 3 options as Level 2 |

### LEVEL 4 - Outlet Shape Fields
| Condition | Fields Shown |
|-----------|-------------|
| `dedicated_outlet = AVAILABLE` | `current_outlet_shape`(COS1-5) + `purchased_outlet_shape`(POS1-5) |
| `dedicated_outlet = NOT_AVAILABLE` | `purchased_outlet_shape`(POS1-5) only |
| `dedicated_outlet = OTHER` | `dedicated_outlet_note` (textarea) |

### LEVEL 5 - AC Pattern Logic (P1-P6)
See **Pattern Decision Matrix** section below.

### Independent Parent Fields (Always Visible)
| # | Field ID | Cost Code | Options |
|---|----------|-----------|---------|
| 11 | `vertical_beam` | AC016 | Required / Not Required |
| 12 | `grounding_work` | AC017 | Required / Not Required |
| 13 | `installation_location` | AC018-AC026 | 10 location options with images |
| 14 | `pipe_length` | AC027/AC031 | Within 4m / Over 4m / Unknown |
| 15 | `outdoor_pipe_cover` | AC028/AC029 | Not Required / Within 2m / Over 2m / Unknown |
| 15.1 | `outdoor_pipe_cover_color` | - | Ivory/Gray/Brown/Black (when cover selected) |
| 16 | `indoor_pipe_cover` | AC030 | Required / Not Required |
| 17 | `recycling` | - | Yes(→recycle_note) / No |
| 18 | `parking_space` | - | Yes(→parking_space_note) / No |

### Optional Fields (Not Required)
- `elevator_loading` - Loadable/Not Loadable/Unknown
- `floor_level` - 2F-5F+/Not Applicable (AC003-AC006)

---

## Pattern Decision Matrix (P1-P6)

Controls which electrical work fields appear based on outlet shape combinations.

| Pattern | Condition | Fields Shown | AC Costs |
|---------|-----------|-------------|----------|
| **P1** | `AVAILABLE` + COS==POS (same shape) | outlet_shape_change (optional) | AC015 if selected |
| **P2** | `NOT_AVAILABLE` + POS1-4 | circuit_work + outlet_shape_change | AC011/AC012 + AC015 |
| **P3** | `AVAILABLE` + voltage mismatch (100V↔200V) | voltage_work + outlet_shape_change(req) | AC013/AC014 + AC015 |
| **P4** | `NOT_AVAILABLE`+POS5 or `OTHER` | Info fields only (disabled) | None |
| **P5** | `AVAILABLE` + amperage mismatch (15A↔20A) | outlet_shape_change (required) | AC015 |
| **P6** | `AVAILABLE` + COS5 or POS5 | Info fields only (disabled) | None |

### P3 Voltage Mismatch Combinations
```
COS3(200V)→POS1(100V), COS4(200V)→POS1(100V)
COS3(200V)→POS2(100V), COS4(200V)→POS2(100V)
COS1(100V)→POS3(200V), COS2(100V)→POS3(200V)
COS1(100V)→POS4(200V), COS2(100V)→POS4(200V)
```

### P5 Amperage Mismatch Combinations
```
COS2(20A)→POS1(15A), COS1(15A)→POS2(20A)
COS4(20A)→POS3(15A), COS3(15A)→POS4(20A)
```

### Auto-Set Values (only on user interaction, NOT on initial load)
- P1, P2: `outlet_shape_change = NOT_REQUIRED`
- P3, P5: `outlet_shape_change = REQUIRED`

---

## Drilling Cost Validation (Critical v2.1)

**ALL 4 conditions MUST be true** for drilling costs (AC008/AC009/AC010):

```
1. wall_structure = MORTAR(1) or CONCRETE(2)
2. pipe_hole = NOT_AVAILABLE(2)
3. hole_drilling = POSSIBLE(1)
4. hole_drilling_possible = BEFORE_2006(1) or AFTER_2006(2) ← MANDATORY
```

### Cost Rules
| Wall Type | Base Cost | + Before 2006 |
|-----------|-----------|---------------|
| Mortar(1) | AC008 | + AC010 (combined, not shown separately) |
| Concrete(2) | AC009 | + AC010 (combined, not shown separately) |
| Block/MudWall/Other | No estimation | - |

### Validation Locations (Must Stay Synchronized)
- **Frontend**: `installation_modal.twig` → `calculateACCosts()` (outer `if` on `holeDrillingPossibleValue`)
- **Backend**: `InstallationCostCalculationService.php` → `isset($data['hole_drilling_possible'])`
- **Persistence**: `InstallationQueryRepository.php` → validates before saving costs

---

## Cost Estimation Modal

### Element IDs
- Shopping page: `shopping-page-estimation-grand-total`
- Confirm page: `price-info-estimation-grand-total`
- Modal grand total: `complete-cost-grand-total`

### Show/Hide Conditions
```javascript
// Show when ALL true:
hasInstallationProducts && serviceType == SERVICE_TYPE_INSTALL 
  && policyAgreed == YES && grandTotal > 0

// CSS class toggle (NO inline styles):
$('.checkout-installation__total-estimation__price-info')
  .removeClass('checkout-installation__total-estimation__price-info--hidden');
```

### Update Triggers
1. `$(document).ready()` with 500ms delay
2. Form field change → `updateCompleteCostModal()`
3. `show.bs.modal` event on `#completeCostModal`

### Calculation Functions
- **AC products**: `calculateACCosts(orderItemId, savedData, mainKindCd, isGrandModal)`
- **Non-AC products**: `calculateNonACCosts(orderItemId, savedData, mainKindCd, isGrandModal)`
- Return: `{ html: string, total: number, hasCosts: boolean }`

---

## Attach Goods Code Reference

| Code | Name (JP) | Trigger |
|------|-----------|---------|
| AC001 | 取外し処分 | removal_option = Disposal |
| AC002 | 取外し再利用 | removal_option = Reuse |
| AC003-006 | 階数別費用 | floor_level = 2F-5F+ |
| AC008 | モルタル穴あけ | wall=Mortar + drilling possible |
| AC009 | コンクリート穴開け | wall=Concrete + drilling possible |
| AC010 | 2006年以前追加 | hole_drilling_possible = Before 2006 |
| AC011 | 回路増設 1F | P2: circuit_addition_1f |
| AC012 | 回路増設 2F | P2: circuit_addition_2f |
| AC013 | 切替(ブレーカーなし) | P3: voltage_switch_no_breaker |
| AC014 | 切替(ブレーカーあり) | P3: voltage_switch_with_breaker |
| AC015 | コンセント形状変更 | P1-P5: outlet_shape_change = REQUIRED |
| AC016 | 縦桟 | vertical_beam = Required |
| AC017 | アース工事 | grounding_work = Required |
| AC018-026 | 設置場所別 | installation_location options |
| AC027 | 配管4m超(2分3分) | pipe_length = Over 4m (small) |
| AC028 | 化粧カバー2m以内 | outdoor_pipe_cover = Within 2m |
| AC029 | 化粧カバー2m超 | outdoor_pipe_cover = Over 2m |
| AC030 | 室内化粧カバー | indoor_pipe_cover = Required |
| AC031 | 配管4m超(2分4分) | pipe_length = Over 4m (large) |
| AC032-034 | アルミパネル S/M/L | hole_drilling_not_possible options 1-3 |

---

## Key JavaScript Functions

| Function | Purpose |
|----------|---------|
| `handleConditionalFields()` | Main dispatcher for field type changes |
| `handlePipeHoleField()` | Pipe hole → hole_drilling / dedicated_outlet |
| `handleHoleDrillingField()` | Drilling possible/impossible child fields |
| `handleDedicatedOutletField()` | Outlet → shape fields / note / pattern |
| `handleACPatternLogic()` | Determines P1-P6 based on COS+POS combo |
| `P1LogicHandler()` - `P6LogicHandler()` | Individual pattern handlers |
| `hideHoleDrillingAndChilds()` | Cascading hide for drilling tree |
| `hideDedicatedOutletAndChilds()` | Cascading hide for outlet tree |
| `resetACPatternLogicHandler()` | Reset all patterns to hidden |
| `updateCompleteCostModal()` | Recalculate and display estimation |
| `calculateACCosts()` | AC-specific cost calculation |

---

## CSS Architecture (BEM)

```scss
.checkout-installation {
  &__total-estimation {
    &__price-info { /* base container */ }
    &__price-info--hidden { display: none; }
    &__price-info-wrapper { /* clickable, orange bg, rounded */ }
    &__price-info__price { color: $danger; }
    &__details { /* scrollable modal content */ }
    &__product-section { }
    &__product-title { font-size: 13px; font-weight: 600; }
    &__product-price { font-size: 16px; color: orange; }
  }
  &__d-none-sp { /* hides element on mobile */ }
}
```

### Responsive Breakpoints
- Desktop: ≥768px → estimation in right sidebar
- Mobile: <768px → estimation at bottom of page
- Same CSS classes, different positioning via `.checkout-installation__d-none-sp`

---

## isInitialLoad Behavior

| Param | Field Visibility | Auto-Set Values |
|-------|-----------------|----------------|
| `true` (page load) | Executes normally | Skipped (preserves saved values) |
| `false` (user interaction) | Executes normally | Applied (P1→NOT_REQ, P3→REQ, etc.) |

Functions respecting this: `handleConditionalFields()`, `handlePipeHoleField()`, `handleDedicatedOutletField()`, `handleHoleDrillingField()`, `handleACPatternLogic()`, all P1-P6 handlers.

---

## State & Persistence

- **LocalStorage key**: `installation_form_data`
- Field values saved on change via `saveToLocalStorage()`
- Image uploads tracked separately
- Form restored on page load
- Hidden fields NOT validated for submission

---

## Implementation Checklist

### Before Changes
- [ ] Identify affected files from File Map
- [ ] Check if change affects frontend JS, backend PHP, or both
- [ ] Verify pattern logic sync between `001_001_checkout_installation.js` and `installation_modal.twig`

### During Changes
- [ ] Follow BEM naming for CSS classes
- [ ] Use translation keys (`installation.{field}.{option}`)
- [ ] Container IDs follow: `{field-name}-field-{orderItemId}`
- [ ] Respect `isInitialLoad` parameter
- [ ] No inline styles (use CSS classes for visibility)

### After Changes
- [ ] Frontend and backend calculation logic synchronized
- [ ] Drilling validation chain complete (4 conditions)
- [ ] Test all 5 scenarios from requirements
- [ ] Verify responsive behavior (desktop + mobile)
- [ ] Clear cache: `bin/console cache:clear`

---

## Testing Scenarios

1. **Standard Install + Existing Hole**: pipe_hole=Available → dedicated_outlet → outlet shapes → P1
2. **New Install + Drilling**: pipe_hole=None → hole_drilling=Possible → dedicated_outlet → P2
3. **Voltage Conversion**: dedicated_outlet=Available → COS1→POS3 → P3 (AC013/AC014+AC015)
4. **Other Outlet**: dedicated_outlet=Other → P4 (info only, no costs)
5. **Pipe Cover + Color**: outdoor_pipe_cover=Within2m → color selection

---

## Common Bug Patterns

| Bug | Root Cause | Fix Location |
|-----|-----------|-------------|
| Drilling cost shows without full selection | Missing `holeDrillingPossibleValue` check | `installation_modal.twig` calculateACCosts() |
| Pattern fields don't reset on parent change | Missing `resetACPatternLogicHandler()` call | `001_001_checkout_installation.js` |
| Auto-set values overwrite saved data on reload | `isInitialLoad` not checked | Pattern handler functions |
| Cost mismatch between modal and PDF | Frontend/backend calculation desync | Sync both `calculateACCosts()` implementations |
| Mobile estimation section duplicated | Missing `.checkout-installation__d-none-sp` | Template classes |

---

## Related Skills

- **`core`** - Architecture rules, never modify `src/Eccube/`
- **`change-request`** - CR implementation methodology
- **`testing`** - Write tests for calculation logic
- **`code-review`** - Security/performance review checklist
- **`bug-fixing`** - Debug conditional field issues

---

## Full Requirements Document

For complete field option lists, translation keys, and detailed specifications:  
`/home/pavel-11142/Desktop/MrMax/CR2-Phase2/ac-installation-queries-requirements.md` (2593 lines)
