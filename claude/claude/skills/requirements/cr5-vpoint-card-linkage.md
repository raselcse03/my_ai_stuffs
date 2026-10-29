---
name: cr5-vpoint-card-linkage
description: "CR5 V-Point & Credit Card Linkage — CCCMK sp101/sp201 API, AES-256-CBC encryption, card linkage (barcode/birthday), V-Point coupon exchange (EC checkout + Native app), single-attempt cancel with BAT3/BAT5 recovery, 30,000pt/month limit, admin screens, POS API, Karte events. Loaded by the [CR5] project tag."
---

# CR5: V-Point & Credit Card Linkage Integration Skill

**Deep context (load on demand):** for CCCMK API payloads (sp101/sp201), BAT1–BAT5 batch internals, and AES-256-CBC details read `cr5-vpoint-card-linkage-deep.md`. Do not load it unless the task touches those areas.

**Prerequisites:** Review `core-essentials` for critical rules. Review `change-request` for CR methodology.

---

## When to Use

- Implementing CCCMK API client (sp101 balance inquiry, sp201 point usage/cancel)
- Working on AES-256-CBC encryption/decryption with MD5 key expansion
- Building card linkage flow (barcode scan, birthday auth, link/unlink/withdrawal)
- Processing SMCC daily file import (SFTP → EBCDIC→UTF-8 → 5 data types)
- Implementing V-Point coupon exchange in EC checkout (STEP1-1 → STEP3)
- Building Native App V-Point balance/exchange API endpoints
- Modifying `CouponDiscountProcess` for dynamic discount (coupon_id=999999990001)
- Modifying `ShoppingController` for V-Point checkout integration
- Adding `serial_no` column to `CouponTarget` entity
- Creating BAT3 SP recovery file (783 bytes/record, Shift_JIS, CRLF, ZIP compression)
- Creating BAT4 SE result file processor (794 bytes/record)
- Creating BAT5 automated cancel processing (status=2 → sp201 Cancel → status routing)
- Building admin screens (card linkage summary, member detail, cancel redemption search)
- Implementing single-attempt cancel logic (sp201 Cancel → status=6 recovery → BAT3/BAT5)
- Implementing 30,000pt/month exchange limit validation (cross-channel per app_member_id)
- Adding Karte event tracking for V-Point exchange/usage
- Modifying POS API for coupon_id=999999990001 barcode handling
- Working on error message mapping (30+ return codes across sp101/sp201/sp201Cancel)
- Implementing admin PG button disable / Payment Status List filtering for V-Point orders

---

## Expected Outcome

- sp101/sp201 API calls work with correct AES-256-CBC encryption (MD5 key expansion)
- Card linkage stores in `dtb_customer_card_info` with only 1 valid link per `app_member_id`
- V-Point coupons issued only on sp201 `return_cd=00`; removed on successful cancel
- Cancel logic: **Single attempt** (v23) → if code_type=2 → `status=6` (Recovery/Resend) → BAT3/BAT5 recovery
  if code_type=3 → `status=5` (Failed). **NO retries in EC/Native/Admin flows.**
- **BAT5:** Automated cancel processing for approved refunds (point_kbn=74, status=2)
  BAT5 calls sp201(Cancel) → code_type=1→status=4, code_type=2→status=6, code_type=3→status=5
- **Monthly limit:** 30,000pt/month per account across EC+Native channels (v25)
- **Status 6 (Recovery/Resend):** sp201 Code Type 2 errors OR BAT4 resendable errors (521..550).
  BAT3 queries `status=6` for SP file generation
- **Status 7 (CheckOut NG):** EC-only status when sp201 succeeded but GMO payment failed
- **BAT3 ZIP:** SP file compressed to standard ZIP (PKZIP) before S3 upload (v23)
- **Payment method:** `dtb_order.payment_method` = Null for full V-Point coupon orders
- **Retry columns:** `retry_kbn`, `retry_cnt` kept in schema for future use (confirmed by client)
- SP file format: 783 bytes/record, Shift_JIS, CRLF, 13 validation checks
- SE file parsing: 794 bytes/record, error_cd classification (resendable→status=6 vs permanent→status=5)
- `CouponDiscountProcess` reads dynamic discount from `kangen_point` for coupon_id=999999990001
- EC checkout: sp201 called at STEP2 (not STEP1-1); GMO skipped for full V-Point
- serial_no format: `[ServiceID:3][YYMMDD:6][Seq:11]` (A03=Native, A04=EC)
- All timestamps: shori_date/shori_time in UTC; serial_no date in JST; SP file header in JST

---

## Implementation Status

> ⚠️ **All CR5 files are greenfield** — no V-Point-specific code exists in the codebase yet.

| Status | Requirement | Notes |
|--------|------------|-------|
| ✅ Done | T1: VpointRedeemResult Entity | `Entity/VpointRedeemResult.php` — 32 columns |
| ✅ Done | T2: VpointExchange Entity | `Entity/VpointExchange.php` — 9 seed rows |
| ⚠️ Modify | T3: CouponTarget serial_no | `Entity/CouponTarget.php` exists — add `serial_no VARCHAR(20)` |
| ✅ Done | T4: VpointApiClient + Encryption | `Service/Vpoint/VpointApiClient.php`, `VpointEncryptionService.php`, `Sp201Request.php`, `Sp201Result.php` |
| ✅ Done | T5: SerialNoGenerator | `Service/Vpoint/SerialNoGenerator.php` |
| ⚠️ Missing | T6: VpointRedemptionService | `Service/Vpoint/VpointRedemptionService.php` |
| ⚠️ Missing | T7: VpointCouponService | `Service/Vpoint/VpointCouponService.php` |
| ⚠️ Missing | T8: VpointController | `Controller/Api/VpointController.php` |
| ⚠️ Modify | T9: ShoppingController V-Point | `Controller/ShoppingController.php` exists — add STEP2 integration |
| ⚠️ Modify | T10: CouponDiscountProcess | `Service/PurchaseFlow/Processor/CouponDiscountProcess.php` exists — add coupon_id=999999990001 |
| ⚠️ Missing | T11: Checkout Twig templates | V-Point exchange UI (Pu2→Pu7) |
| ⚠️ Missing | T12-T14: Native API endpoints | Balance, exchanges, redeem |
| ⚠️ Missing | T15: POS API modification | Existing POS controller — modify for coupon_id=999999990001 |
| ⚠️ Missing | T16: VpointErrorMessageService | `Service/Vpoint/VpointErrorMessageService.php` |
| ⚠️ Missing | T17: Karte Event Integration | `Service/Vpoint/VpointKarteEventService.php` + Twig tracker |
| ⚠️ Missing | T18: Structured Logging | Modify VpointApiClient, VpointCouponService |
| ⚠️ Modify | T19: CouponTargetRepository | `Repository/CouponTargetRepository.php` exists — combined date sort |
| ⚠️ Missing | T20: VpointBannerService | `Service/Vpoint/VpointBannerService.php` |
| ⚠️ Missing | T21: Purchase history cancel status | Twig template modification |
| ⚠️ Missing | BAT1-BAT4 | 4 batch commands — none exist |
| ⚠️ Missing | Admin screens | Card linkage summary, member detail, cancel redemption |

---

## File Map (Key Files)

```
Entity / Schema:
  app/Customize/Entity/VpointRedeemResult.php       → sp201 request/response (31 cols)
  app/Customize/Entity/VpointExchange.php            → Exchange denominations (9 rows)
  app/Customize/Entity/CouponTarget.php              → MODIFY: add serial_no column
  app/Customize/Entity/AffiliatedCardInfo.php        → SMCC card master (30+ cols)
  app/Customize/Entity/CustomerCardInfo.php          → Card linkage history
  app/Customize/Entity/CardApplicationInfo.php       → Daily import tracking

Repository:
  app/Customize/Repository/VpointRedeemResultRepository.php
  app/Customize/Repository/VpointExchangeRepository.php
  app/Customize/Repository/CouponTargetRepository.php  → MODIFY: combined date sort (T19)
  app/Customize/Repository/AffiliatedCardInfoRepository.php
  app/Customize/Repository/CustomerCardInfoRepository.php

Services (app/Customize/Service/Vpoint/):
  VpointApiClient.php              → sp101/sp201 API wrapper, XML parsing, timeout 3s
  VpointEncryptionService.php      → AES-256-CBC + MD5 key expansion
  VpointRedemptionService.php      → Orchestration: sp101→sp201→cancel→coupon
  VpointCouponService.php          → Temp reservation (session/Redis) + real coupon issuance
  SerialNoGenerator.php            → A03/A04 + YYMMDD(JST) + 11-digit sequence
  VpointErrorMessageService.php    → Return code → JP error message mapping
  VpointKarteEventService.php      → Karte event payload builder
  VpointBannerService.php          → Dynamic coupon banner generation

Controllers:
  app/Customize/Controller/Api/VpointController.php       → EC + Native API endpoints
  app/Customize/Controller/ShoppingController.php         → MODIFY: STEP2 V-Point integration
  app/Customize/Controller/Admin/CardLinkageSummaryController.php
  app/Customize/Controller/Admin/MemberCardDetailController.php
  app/Customize/Controller/Admin/CancelRedemptionController.php

Batch Commands:
  app/Customize/Command/SmccFileRetrieveCommand.php       → BAT1: SFTP every 30min
  app/Customize/Command/SmccDataImportCommand.php         → BAT2: Validate + import 5 types
  app/Customize/Command/SpRecoveryFileCommand.php         → BAT3: SP file (783 bytes/record, ZIP)
  app/Customize/Command/SpResultProcessCommand.php        → BAT4: SE file (794 bytes/record)
  app/Customize/Command/AutoCancelProcessingCommand.php       → BAT5: Automated cancel (status=2 → sp201 Cancel via VpointApiClient)

Purchase Flow:
  app/Customize/Service/PurchaseFlow/Processor/CouponDiscountProcess.php → MODIFY: coupon_id=999999990001

Frontend:
  app/template/default/Shopping/vpoint_exchange.twig      → EC checkout V-Point modal
  app/template/default/Block/Tracker/vpoint_tracker.twig  → Karte event template
  app/template/admin/Vpoint/                              → Admin V-Point screens
```

---

> Requirement groups, dependency chain & implementation order → deep file § Requirement Groups Overview

---

## Card Linkage — Key Rules

### Barcode Validation
- **Format:** Code128, 8-digit
- **Check digit:** Modulus 10 (weight 2/1 from left)
- **Birthday auth:** 3 attempts max → escalation to support

### Status Decision Matrix

| Credit Card Status | EC Member Status | Action |
|-------------------|-----------------|--------|
| New (data_type=10) | Not registered | Store in `dtb_affiliated_card_info` only |
| New (data_type=10) | Registered | Store + allow barcode linkage |
| New (data_type=10) | Withdrawn | Store; re-enrollment = new registration (new `app_member_id`) |
| Cancel (data_type=20) | Registered + Linked | `is_card_cancelled=1`; `is_valid=0` |
| Change (data_type=30) | Any | Update address/name fields only |
| Reissue (data_type=40) | Registered + Linked | Old card `is_valid→0`; new `is_valid→1` |
| Update (data_type=50) | Any | Update expiry/renewal info |

### Constraint
Only **1 record** with `is_valid=1` per `app_member_id` at any time.

> sp101 return-code routing during card linkage → deep file § sp101 Routing — During Card Linkage Flow

### Customer Flow — Unlink Card
1. Customer navigates to membership card settings → taps "Unlink card"
2. System checks for active V-Point coupons
3. If coupons exist: show warning "You have N active V-Point coupons. Unlinking will not delete them but new points cannot be exchanged."
4. Customer confirms via code authentication
5. System sets `dtb_customer_card_info.is_valid = 0`, records `card_dislinkaged_dt`

### Customer Flow — Member Withdrawal
1. Customer initiates app/web membership withdrawal
2. System checks: App member, Web member, or both?
3. If App member + card linked: check for active V-Point coupons → show warning
4. Set `dtb_customer_card_info.is_valid = 0`
5. Update `dtb_customer` withdrawal status
6. Re-enrollment treated as **new registration** (new `app_member_id`)

### Member ID Source
`dtb_customer.ext_attr_text3` = `app_member_id` (VARCHAR(13), **immutable** once assigned). Used as FK by `dtb_customer_card_info` and `dct_vpoint_redeem_result`.

> Card/membership/coupon status combinations → deep file § Card Linkage / Membership / Coupon Status Combinations
> Card-linkage UI messages (M01–M07) → deep file § Frontend Messages (Card Linkage UI)

---

## CCCMK API — Key Specifications

### Endpoints

| API | PROD | STG | Timeout | Purpose |
|-----|------|-----|---------|---------|
| sp101 | `https://api.tpoint.jp/sp101.do` | `https://stg.api.tpoint.jp/sp101.do` | 3s | **Member Balance Inquiry** — Verifies card validity and returns current V-Point balance. Used at STEP1-1 (display), STEP2 (re-check), and Native app (refresh). |
| sp201 | `https://api.tpoint.jp/sp201.do` | `https://stg.api.tpoint.jp/sp201.do` | 3s | **Point Operations** — Deducts V-Points (point_kbn=73) or cancels a prior deduction (point_kbn=74). Called at STEP2 for EC checkout, Native redeem, and admin cancel. |

**Method:** POST | **Content-Type:** `application/x-www-form-urlencoded` | **Encoding:** UTF-8 | **Response:** XML (`return_cd`, balance) | **Encryption:** AES-256-CBC on ALL fields (No.2–15 for sp101, No.2–21 for sp201) — `alliance_cd` (No.1) is unencrypted in request; `return_cd` is unencrypted in response

> AES-256-CBC encryption + sp101/sp201 request & response payloads + field formatting → deep file § CCCMK API — Encryption & Payloads

---

## EC Checkout Flow (STEP1-1 → STEP3)

### Key Design Decision
sp201 point deduction called at **STEP2** (purchase completion), NOT at STEP1-1 (Exchange button).

### Flow Summary

> **CRITICAL RULE:** INSERT `dct_vpoint_redeem_result` with `return_cd=NULL` **BEFORE** sp201 API call. UPDATE with `return_cd` **AFTER** API response. This prevents double deduction on timeout.

```
STEP1-1: sp101 balance → User inputs amount → "Exchange" button
           → Session/Redis reservation (NO sp201 call)
           → Discount applied visually to checkout total

STEP1-2: User reviews order → "Confirm order" → proceeds to STEP2

STEP2:   sp101 re-check → generate serial_no (A04+YYMMDD+seq)
           → INSERT dct_vpoint_redeem_result (return_cd=NULL)
           → Call sp201 (point_kbn=73) → UPDATE return_cd
           → If 00: issue real coupon → GMO or skip → STEP3
           → If NG (CodeType 3): show error MSG only (no cancel needed) → STEP1-1
           → If NG (CodeType 2): show error MSG, status=6 → BAT3 recovery
           → If GMO NG (after sp201 OK): status=7 → sp201 Cancel (single attempt)
             → cancel OK → status=4; cancel NG (Type2) → status=6 → BAT3

STEP3:   Order confirmation
```

### Special Cases
- Full V-Point payment → **skip GMO entirely**; `dtb_order.payment_method` = NULL
- **30,000 pt/month net exchange limit** per account per calendar month — validated server-side before sp201 call. Net limit: canceled/refunded points restore the available limit.
- Quantity decrease after V-Point coupon applied → return to STEP1-1 if discount > new total
- sp201 Cancel NG (Code Type 2) → status=6 → SPxxxxxx file via BAT3; user cannot retry until resolved

### CouponDiscountProcess Modification (T10)
When `coupon_id=999999990001`:
- During checkout: read discount from session/Redis clone (`getCouponClone()`)
- After order completion: read from `dct_vpoint_redeem_result.kangen_point`

### VpointCouponService Methods (T7)
- `storeCouponClone(customerId, amount)` → builds clone `{coupon_id: 999999990001, customer_id, discount_price, status: RESERVED, sp101_balance, reserved_at}` → writes to session/Redis
- `getCouponClone(customerId)` → reads clone (used by `CouponDiscountProcess`)
- `clearCouponClone(customerId)` → deletes clone from session/Redis
- `issueCoupon(customerId, amount, serialNo)` → inserts real `dct_coupon_target` with `status=ACTIVE` + `serial_no`
- **Redis key:** `vpoint_reserve:{customer_id}` (TTL configurable, e.g. 30 min)
- **Coupon barcode format:** Code128

### STEP2 sp101 Re-check Failure Handling
- sp101 NG (return_cd ≠ 00) → show error MSG, clear reservation (session/Redis), return to STEP1-1
- Balance < reserved amount → show "Vポイントが足りません。", clear reservation, return to STEP1-1
- GMO NG (after sp201 OK) → set status=7 (CheckOut NG); call `VpointRedemptionService::cancelRedemption()` → sp201 Cancel (single attempt); if cancel NG → status=6 → BAT3/BAT5 recovery. Also revert coupon (`ACTIVE` → `CANCELLED`)

### EC Checkout UI Controls (Figma Pu2-Pu5)

| Screen | Control | Behavior |
|--------|---------|----------|
| Pu2 | Radio not selected | V-Point exchange area **disabled** |
| Pu3 | Radio selected | V-Point exchange area **active** |
| Pu4 | Input amount | **Numeric keyboard only**; max = available balance |
| Pu5 | Change radio selection | Keep input value but **disabled** |
| Pu4 (re-select) | Radio selected again | Re-enable with **preserved** input amount |

### Pre-validation Rule
If input amount > available balance → show **"Vポイントが足りません。"** client-side **BEFORE** calling sp201.

### Coupon Display Rule
- **EC checkout V-Point coupons**: NOT displayed in active EC Coupon List — shown on **Used/Expired Tab only**
- **Native App / Shop V-Point coupons**: follow existing display behavior (no change)
- Combined sort by `update_date DESC` (latest first), not separated by type

### Coupon Master Record (pre-seeded)
| Field | Value |
|-------|-------|
| coupon_id | 999999990001 |
| type1 | 3 (Automatic) |
| type2 | 1 (Normal) |
| scope | 1 (Common) |
| number_of_use | 1 |
| discount_type | 1 (DISCOUNT_PRICE) |
| discount_price | 0 (**dynamic** — read from `kangen_point`) |

---

## Cancel Logic & State Machine

### sp201 Cancel — Single Attempt (v23)

> **(v23) Updated 2026/5/14** — Cancel retry removed. Single cancel attempt; if NG → immediate BAT3/BAT5 recovery.

| Attempt | Action | If OK (00) | If NG (Code Type 2) | If NG (Code Type 3) |
|---------|--------|-----------|---------------------|---------------------|
| Cancel 1 | sp201 cancel (point_kbn=74, cancel_kbn=0) — **INSERT** cancel record | status=4 | status=6 (Recovery/Resend) → BAT3 | status=5 (Failed) |


> **Critical: BAT3 INSERTs a NEW record** with `type=2` (File Transfer), same `serial_no`, `status=3`. BAT4 then UPDATEs that type=2 record.
> The original type=1 (API Call) record retains its status=6. This means `dct_vpoint_redeem_result` may have **multiple rows per serial_no** (one type=1 + one type=2).
> **UPDATE fields on type=2 row:** `status`, `return_cd`, `error_cd`, `get_return_date`, `update_date`, `program_name`.
> **No retries in EC/Native/Admin flows.** Single sp201 Cancel attempt only.

### Status State Machine (0–7)

| Status | Name | Description | Next Transitions |
|--------|------|-------------|-----------------|
| 0 | Not Applied | Initial: redemption/cancellation request created, before sp201 API call | → 1 (admin refund) |
| 1 | Applied | Admin: Refund button clicked (0→1); waiting for approval | → 2 (approve) or → 0 (cancel application) or → 4 (sp201 OK direct) |
| 2 | Approved | Admin: Approve button clicked (1→2); waiting for BAT5 pickup | → 4/5/6 (BAT5 result) |
| 3 | Processing | BAT3 executed: SPxxx recovery file created and sent; waiting for BAT4 (SExxx) | → 4 (BAT4 no error) or → 5 (BAT4 error) |
| 4 | Success | Redeem/cancel success (sp201 return_cd=00, or BAT4 no error_cd) | Terminal (→7 if GMO NG after redeem) |
| 5 | Failed | Show error msg only (CodeType 3, or BAT4 non-resendable error_cd) | → 1 (admin retry) |
| 6 | Recovery/Resend | CodeType 2 or BAT4 resendable error (521..550) — waiting for BAT3 file recovery | → 3 (BAT3 picks up) |
| 7 | CheckOut NG | EC-only: Redemption succeeded but GMO payment failed; will call sp201 cancel | → 4/5/6 (cancel result) |

### sp201 Redemption (point_kbn=73) Return Code Routing (v23)

> **(v23)** Code Type 3 NO LONGER triggers sp201 Cancel. Points were NOT deducted for these errors.

| Code Type | Return Codes | Status | Action |
|-----------|-------------|--------|--------|
| **Type 1** | 00 | 4 | Success — issue coupon |
| **Type 2** | 04, 98 | 6 | Show error MSG; wait for BAT3 (SPxxx recovery) |
| **Type 3** | 05, 10, 11, 14, 15, 16, 17, 18, 22, 23, 41, 42, 43, 44, 52, 53, 80, 90, 92, 99 | 5 | Show error MSG only (points NOT deducted; NO sp201 Cancel needed) |

### sp201 Cancel (point_kbn=74) Return Code Routing (v23)

| Code Type | Return Codes | Status | Action |
|-----------|-------------|--------|--------|
| **Type 1** | 00 | 4 | Cancel success |
| **Type 2** | 04, 11, 16, 18, 80, 92, 98, 99 | 6 | Show error MSG; wait for BAT3 (SPxxx recovery) |
| **Type 3** | 05, 10, 14, 15, 17, 22, 23, 41, 42, 43, 44, 52, 53, 90 | 5 | Show error MSG; cancel without connecting V-Point |

> Status transition case matrix (9 cases) → deep file § Status Transition Case Matrix

---

## Batch Processing (Schedule Reference)

| Batch | Schedule | Purpose |
|-------|----------|---------|
| BAT1 | Every 30 min | SFTP retrieval from SMCC; zero-record files valid |
| BAT2 | On file arrival | Import 5 data types (10/20/30/40/50); per-record error tolerance |
| BAT3 | 14:30 JST daily | SP recovery file (status=6 records); ZIP compressed; header-only heartbeat |
| BAT4 | 11:30 JST daily | SE result file; error_cd 521–550 → re-queue; others → permanent fail |
| BAT5 | ~16:00 JST daily | Automated cancel (status=2 → sp201 Cancel → code_type routing) |

> Full deep reference (load on demand from `cr5-vpoint-card-linkage-deep.md`):
> → deep file § Batch Processing
> → deep file § Database Schema — Core Tables
> → deep file § Admin Screens
> → deep file § Native App — Key Rules
> → deep file § Purchase History — Cancel Status Display (v4, updated v23)
> → deep file § Karte Event Tracking (v4)
> → deep file § Return Code Classification (Quick Reference)
> → deep file § Error Messages — Complete Reference (for VpointErrorMessageService)
> → deep file § Key Constants
> → deep file § Structured Logging Fields (T18)
> → deep file § Open Items

---

## Common Bug Patterns

| Bug | Root Cause | Fix Location |
|-----|-----------|-------------|
| Encryption mismatch (code 92) | MD5 hash not repeated to 32 bytes | `VpointEncryptionService::expandKey()` |
| Double deduction (code 05) | serial_no not stored before API call | `VpointRedemptionService::redeemPoints()` |
| Timezone mismatch in BAT3 | DB uses UTC, serial_no uses JST | BAT3 — force JST conversion |
| SP file byte-count off | Shift_JIS multibyte char width | SP file generation — count bytes not chars |
| Coupon not issued after sp201 OK | DB insert fails silently | Wrap in transaction |
| sp101 timeout not caught | HTTP client timeout not set | `VpointApiClient` — set 3s timeout |
| Cancel record missing | INSERT not executed before sp201 Cancel call | Cancel logic — INSERT cancel record first, then call API |
| CouponDiscountProcess reads 0 | `dcm_coupon.discount_price=0` used | Must read `kangen_point` for coupon_id=999999990001 |
| Barcode check digit wrong | Weight order reversed (2,1,2,1 from left) | BarcodeValidator — verify weight direction |
| BAT2 stops on first error | Catch too broad | BAT2Command — per-record try/catch |
| File merge creates duplicates | Day N status not tracked | BAT3 — check retrieval flag before merge |
| Admin dislinkage race | Concurrent withdrawal | CardLinkageService — check is_valid before update |

---

## Related Skills

- **`core-essentials`** — Architecture rules, never modify `src/Eccube/`
- **`change-request`** — CR implementation methodology
- **`bat-generation`** — Batch command patterns (BAT1-BAT4)
- **`testing`** — Write tests for API client, encryption, cancel logic
- **`code-review`** — Security/performance review checklist
- **`feature-development`** — Entity → Controller → Template pattern
