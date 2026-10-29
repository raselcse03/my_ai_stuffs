---
name: cr5-vpoint-card-linkage-deep
description: "Deep companion to cr5-vpoint-card-linkage — CCCMK sp101/sp201 API payloads, AES-256-CBC details, BAT1–BAT5 batch internals, SP/SE file layouts, full database schemas, admin screens, Native app APIs, error-message catalogs, key constants, and edge-case matrices. Load on demand for CR5 deep-dive tasks; see cr5-vpoint-card-linkage.md for quick reference."
---

# CR5 Deep Reference

> **Extended reference for CR5.** For quick-reference rules, file map, implementation status, key flows, and cancel logic → see `cr5-vpoint-card-linkage.md` first.

---

## Requirement Groups Overview

| # | Module | Scope | Priority |
|---|--------|-------|----------|
| 1 | Card Linkage (barcode + birthday + SFTP import) | Entity + Service + BAT1/BAT2 | Foundation |
| 2 | CCCMK API Client (sp101 + sp201 + encryption) | Service | Foundation |
| 3 | V-Point EC Checkout (STEP1-1 → STEP3) | Controller + Service + Twig | **Critical** |
| 4 | V-Point Native App (balance + exchange + redeem) | API Controller | High |
| 5 | Coupon System (master 999999990001, dynamic discount) | Entity + Service + PurchaseFlow | **Critical** |
| 6 | Batch Processing (BAT3 SP file + BAT4 SE file) | Commands | High |
| 7 | Admin Screens (summary + member detail + cancel) | Controller + Twig | Medium |
| 8 | Cross-cutting (Karte, logging, POS API, error messages) | Service + Twig | Medium |

### Dependency Chain

```
Group 1 (Entity/Schema) ──────► Group 2 (API Client)
         │                              │
         ├──► Group 5 (Coupon System)   ├──► Group 3 (EC Checkout)
         │                              │
         │                              ├──► Group 4 (Native App)
         │                              │
         ▼                              ▼
Group 6 (BAT3/BAT4/BAT5) ◄──── Group 2 (Cancel Logic + BAT5 Recovery)
         │
         ▼
Group 7 (Admin Screens)
         │
         ▼
Group 8 (Cross-cutting)
```

### Implementation Order

```
Phase A (Foundation): Entity/Schema SQL → Encryption → API Client → SerialNoGenerator
Phase B (Core):       RedemptionService → CouponService → ErrorMessageService
Phase C (EC Flow):    VpointController → ShoppingController mod → CouponDiscountProcess mod
Phase D (Native):     Native API endpoints (balance, exchanges, redeem)
Phase E (Batch):      BAT1 → BAT2 → BAT3 → BAT4
Phase F (Admin):      Card linkage summary → Member detail → Cancel redemption
Phase G (Polish):     Karte events → Structured logging → POS API → PG button disable
```

---

## Card Linkage — Extended Rules

### sp101 Routing — During Card Linkage Flow

> **Note:** During card linkage, sp101 verifies card validity only (no balance check). This routing is distinct from sp101 during V-Point redemption.

| Return Code | Meaning | Action |
|-------------|---------|--------|
| 00 | Card valid | Proceed to birthday authentication |
| 10 | No member record | Show error: card not found |
| 11 | Invalid member | Show error: card cannot be used |
| 14 | Not eligible for V-Points | Show error: cannot link |
| 22 | No linkage information | Show error: linkage info missing |
| 93 | Barcode conversion error (invalid BCD) | "バーコードが読み取れません。再度スキャンしてください。" |
| 94 | Barcode conversion error (expired) | "このカードは有効期限が切れています。" |
| All others | System / auth error | Show generic error; contact support |

### Card Linkage / Membership / Coupon Status Combinations

| Card Linked | App Member | V-Point Coupon | Behavior |
|-------------|-----------|----------------|----------|
| Yes | Active | Has coupons | Normal usage — customer can use coupons |
| Yes | Active | No coupons | Normal — no coupons to use |
| Yes | Withdrawn | Has coupons | Coupons retained (12-month archive) but **cannot exchange new** |
| Yes | Withdrawn | No coupons | Card auto-unlinked on withdrawal |
| No | Active | Has coupons | Coupons still valid; **cannot exchange new** (no card) |
| No | Active | No coupons | No V-Point functionality displayed |
| No | Withdrawn | Any | No action; historical records only |

> **UI Rule:** V-Point exchange UI shown/hidden based on: card linked + active membership. Existing coupons remain usable regardless of linkage state.

### Frontend Messages (Card Linkage UI)

| ID | Message (JP) | Context |
|----|-------------|---------|
| M01 | Vポイントの残高照会ができませんでした。 | sp101 failure — balance unavailable |
| M02 | Vポイントが足りません。 | Input amount > available balance |
| M03 | カード連携が完了しました。 | Successful card linkage |
| M04 | カード連携を解除しました。 | Successful card unlinkage |
| M05 | このカードは既に他のアカウントに連携されています。 | Card already linked to another member |
| M06 | 生年月日が一致しません。 | Birthday authentication mismatch |
| M07 | 有効期限内のスタンプはありません。 | No valid stamp records |

---

## CCCMK API — Encryption & Payloads

### AES-256-CBC Encryption
1. Take encryption key (A) → MD5 hash → repeat to 32 bytes → actual key (C)
2. Encrypt with key (C) + fixed IV + PKCS5Padding
3. Base64 encode → URL-encode if in query string

### Test Vector
- Plaintext: `1234567890123450`
- Key: `ABCDEF0123456789abcdef0123456789`
- IV: `abcdefghABCDEFGH`
- Result: `OZwiVXUG6xvb51YHjG4XC/1l2DrMWW2dGyBTYPgxPoQ=`

### sp101 Request Parameters (15 fields)
`alliance_cd`, `passwd` (enc), `gyotai_cd` (enc), `tenpo_cd` (enc), `kaiin_id_kbn` (=10, enc), `kaiin_id` (enc), `ninsho_kbn` (=0, enc), `ninsho_code` (=NULL, enc), `kaiin_no_yomitori_kbn` (=4 WEB, enc), `touroku_keiro` (=5 WEB, enc), `coupon_info` (=0, enc), `royalty_info` (=0, enc), `money_info` (=0, enc), `shori_date` (enc), `shori_time` (enc)

### sp201 Request Parameters (21 fields)
`alliance_cd`, `passwd` (enc), `gyotai_cd` (enc), `tenpo_cd` (enc), `kaiin_id_kbn` (=10, enc), `kaiin_id` (enc), `ninsho_kbn` (=0, enc), `ninsho_code` (=NULL, enc), `shori_date` (enc), `shori_time` (enc), `eigyou_date` (=shori_date, enc), `serial_no` (enc), `register_no` (=000001, enc), `denpyo_no` (enc), `retry_kbn` (=0 fixed, enc), `point_kbn` (73/74, enc), `cancel_kbn` (=0, enc), `moto_date` (enc, empty for redemption), `moto_serial_no` (enc, empty for redemption), `kangen_point` (enc), `uriage_kin` (=0, enc)

### Encrypted Empty String Rule (CRITICAL)

> **When a field is NULL but still required by the API, you MUST encrypt an empty string `""` — NOT skip the field or send null/blank.**

| Field | When to send encrypted empty string |
|-------|------------------------------------|
| `ninsho_code` | Always (ninsho_kbn=0 → no auth code needed, but field MUST be present as encrypted `""`) |
| `moto_date` | For redemption calls (point_kbn=73 — no original transaction) |
| `moto_serial_no` | For redemption calls (point_kbn=73 — no original serial) |

Omitting these fields or sending unencrypted null causes CCCMK parameter error (return_cd=`90`).

### sp101 Response Specification

**XML Structure:** `<root><header><body><row><data name="...">value</data>...</row></body><footer/><returnCode>XX</returnCode></root>`

**Routing:** Use `<returnCode>` at XML root level — this is **NOT encrypted**. All `<data>` values inside `<body>` are AES-256-CBC encrypted (decrypt each individually, no URL decoding needed).

**★ Conditional Encryption Rule:** `alliance_cd` in response is encrypted ONLY when `return_cd=00`; plaintext when `return_cd≠00`.

**Key Response Fields:**

| No. | Field | Type | Digits | Returned | Encrypted | Notes |
|-----|-------|------|--------|----------|-----------|-------|
| 8 | return_cd | Char | 2 | ◎ (always) | — | **NOT encrypted** — use `<returnCode>` at root for routing |
| **12** | **point** | Numeric | 9 | ● | ○ | **← Use for balance display. Excludes store-exclusive V Points.** |
| 13 | total_point | Numeric | 9 | ● | ○ | Not used by Alliance |
| 9 | tcard_flg | Char | 1 | ● | ○ | `1`: Card member; `0`: Online-only |
| 107 | kikankotei_total_point | Numeric | 8 | ◇ | ○ | Store-exclusive V Points (tab-separated repeating field) |

**Return Legend:** ● = Returned when `return_cd=00` OR `14`; ◎ = Always; ◇ = When store-exclusive V Points held

> **Important:** `return_cd=14` (Cannot be refunded) still returns balance fields (●). Card linkage blocked but balance data IS available.

### sp201 Response Specification

**Same XML structure and routing rule as sp101.** Use `<returnCode>` (unencrypted) for routing.

**Key Response Fields:**

| No. | Field | Type | Digits | Returned | Encrypted | Notes |
|-----|-------|------|--------|----------|-----------|-------|
| 12 | return_cd | Char | 2 | ◎ (always) | — | **NOT encrypted** — routing field |
| 13 | error_point | Numeric | 8 | △ | ○ | Points unable to deduct; `0` when success |
| **14** | **point** | Numeric | 9 | ● | ○ | **← Balance AFTER operation (post-deduction). Use for `new_balance` in Native API response.** |
| 15 | torihiki_date | Char | 8 | ● | ○ | Date processed by CCCMK point system (yyyymmdd) |

**Return Legend:** ● = Returned when `return_cd=00`; ◎ = Always; △ = As needed

**★ Same conditional encryption:** `alliance_cd` encrypted only when `return_cd=00`.

### Field Formatting Rules
- **tenpo_cd**: Fixed: `0000000002454` (constant — not user-dependent)
- **denpyo_no**: EC = order number left-zero-padded to 20 chars; Native = `00000000000000000000`
- **kaiin_id**: `dtb_customer_card_info.customer_number` (encrypted with AES-256-CBC)

---

## Batch Processing

### BAT1: SMCC File Retrieval (SFTP)
- **Schedule:** Every 30 minutes
- **SFTP:** Port 2222, public key auth; remote dir `/mrmax-prod-apn1-smcc/smcc2ec/{DATE}/`
- Retrieve → rename with timestamp → upload to S3
- **Alert:** No file during 10:00–11:00 → Slack notification at 11:05 (once/day)
- **SMCC file encoding:** ANK=EBCDIC, Kanji=IBM; record: Header → Data → Trailer → End
- Zero-record files (header-only) are valid

### BAT2: SMCC Data Import
- **Per-type processing (partial success — 1 error ≠ reject all):**
  - **type=10 (New):** INSERT `dtb_affiliated_card_info`; check no duplicate `customer_number`
  - **type=20 (Cancel):** Set `is_card_cancelled=1`; `is_valid=0` on linked card
  - **type=30 (Change):** UPDATE address/name fields only
  - **type=40 (Reissue):** Old card `is_valid→0`; new card `is_valid→1`
  - **type=50 (Update):** UPDATE expiry/renewal info
- **Encoding conversion:** EBCDIC(ANK) + IBM(Kanji) → UTF-8
- Slack notification: consolidated message with CSV attachment (column headers follow **E14 message key parameters** format from SMCC error message catalog)

#### BAT2 Validation Rules (11 checks)

| Check | Rule | On Failure |
|-------|------|------------|
| File format | Fixed-length record per spec | **Reject entire file** |
| Header | Must always be present | **Reject entire file** |
| Required fields | Fields marked ● not NULL | Exclude record |
| Numeric | Digits only, no signs | Exclude record |
| Char padding | Left-aligned, space-padded | Exclude record |
| Numeric padding | Right-aligned, zero-padded | Exclude record |
| Code range | data_type ∈ {10,20,30,40,50}; sex ∈ {1,2} | Exclude record |
| Date | YYYYMMDD; no future dates | Exclude record |
| Duplicate | No duplicate `customer_number` for type=10 | Exclude record |
| Correlation | type=20 requires existing valid card | Exclude record |
| Field length | No overflow or misalignment | Exclude record |

### BAT3: SP Recovery File

- **Schedule:** Daily at **14:30 JST**
- **Compression:** Standard ZIP (PKZIP) before S3 upload (v23, confirmed by client)

**Step 1 — Detect whether CCCMK retrieved previous SP file:**
- Check S3 `active/` prefix key for an HTTPS GET access log entry for the Day N SP file
- **If GET access logged** → Normal mode: query `status=6` records
- **If no GET access logged** → Merge mode: also include `status=3` records
- Fire **Retrieval Warning Slack alert** if SP file remains unretrieved

- **Query (v23):** Always includes:
  - `status=6` (Recovery/Resend — sp201 Code Type 2 OR BAT4 resendable errors 521..550)
- **Merge mode** (CCCMK didn't retrieve): additionally includes `status=3`
- **Post-write update:** `status=3, error_cd=Null` — applies to all picked records. For status=3 records re-included via merge, status remains 3.
- **Format:** 783 bytes/record, Shift_JIS (CP932), CRLF
- **File:** `URIxxxxSPyy.DAT` (xxxx=Alliance Code from Secrets Manager)
- **S3 encryption:** AES-256-SSE (file contains PII)
- **13 validation checks:** checks 4-6,9-11 = EXCLUDE; checks 7-8 = AUTO-FIX
- **Header-only file** sent even with 0 body records (heartbeat)
- **Redis lock** TTL=30min; `--dry-run` and `--verbose` flags

### BAT4: SE Result File

- **Schedule:** Daily at **11:30 JST**
- **Retrieve:** HTTPS GET from CCCMK EDI server
- **EDI endpoints:** PROD `https://edi.tpoint.jp/adi010.do`, STG `https://stg.edi.tpoint.jp/adi010.do`
- **Format:** 794 bytes/record, Shift_JIS
- **Error classification:**
  - Empty/000 → `status=4` (success)
  - 521-527, 536-538, 550 → `status=6` (Recovery/Resend; error_cd stored) — **BAT3 auto-picks** on next run
  - All other 5xx → `status=5` (permanent failure, admin investigation)

**BAT4 Resendable Error Codes (status=6) — BAT3 auto-picks:**
`521`, `522`, `523`, `524`, `525`, `526`, `527` (Invalid Member Error), `536` (Suspended Member F1), `537` (Suspended Member K1), `538` (Suspended Member K2), `550` (Invalid Member Other)

**BAT4 Non-Resendable Error Codes (status=5) — for point_kbn 73/74:**

| error_cd | Meaning (JP/EN) | 73 | 74 |
|----------|-----------------|:--:|:--:|
| `510` | 数値項目エラー / Numeric Field Error | ○ | ○ |
| `511` | 日付項目エラー / Date Field Error | ○ | ○ |
| `512` | 範囲外エラー / Invalid Range Error | ○ | ○ |
| `513` | 必須項目エラー / Missing Required Field Error | ○ | ○ |
| `514` | 排他制御エラー / Exclusive Control Error | ○ | ○ |
| `520` | 会員マスタエラー / Member Master Error | ○ | ○ |
| `528` | 会員番号不正 / Invalid Member Number | ○ | ○ |
| `555` | 符号不整合エラー / Sign Inconsistency Error | ○ | ○ |
| `573` | 重複処理エラー / Duplicate Processing Error | ○ | — |
| `580` | 紐付情報なし / No Linkage Information | ○ | ○ |
| `581` | サイトID不正 / Invalid Site ID | ○ | ○ |
| `582` | 会員ステータスエラー / Member Status Error | ○ | ○ |
| `583` | 取消対象なし / No Eligible Cancellation Target | — | ○ |
| `585` | 利用限度超過エラー / Usage Limit Exceeded Error | — | ○ |
| `589` | 会員情報なし / Member Information Not Found | ○ | ○ |
| `590` | 店舗限定:ID不正 / Store-Limited: Invalid ID | ○ | ○ |
| `591` | 店舗限定:適用期間外 / Store-Limited: Outside Period | ○ | ○ |
| `592` | TLSC復号エラー / TLSC Decryption Error | ○ | ○ |
| `593` | 店舗限定:有効期限切れ / Store-Limited: Expired | ○ | ○ |
- **Retry:** Exponential backoff 0s, 5s, 15s, 45s (max 4 attempts)
- **S3:** SE bucket `mrmax-prod-apn1-SE`; backup to `mrmax-prod-apn1-SE-{YYYYMMDD}`
- Redis lock; `--dry-run` and `--date=YYYYMMDD` flags
- **If SE file not found on EDI server:** Log warning, skip processing for that run; BAT4 retries on next scheduled execution (no error Slack alert)
- Slack: `"BAT4: {success}/{total} records recovered"`

### SE File Header Layout (794 bytes)

| # | Field | Type | Size | Value |
|---|-------|------|------|-------|
| 1 | Record Type | String | 10 | `@@HEADER@@` |
| 2 | Data Identifier | String | 8 | File-specific identifier |
| 3 | Alliance Code | String | 4 | Issued by CCCMK |
| 4 | Creation Date | String | 8 | YYYYMMDD |
| 5 | Creation Time | String | 6 | HH24MISS (24-hour) |
| 6 | Number of Data Records | Number | 8 | Number of body records |
| 7 | Record Length | String | 4 | Body data record length (excluding CRLF) |
| 8 | Reserve | String | 20 | Space padding |
| 9 | Length Adjustment | String | 724 | Space padding (to match body record length) |
| 10 | Line Feed | — | 2 | CRLF (0x0D0A) |

**SE File Body Record — Layout (794 bytes)**

The SE body echoes ALL SP body fields with 2 additional fields prepended: `error_code` + `error_points`.
**Structure:** `[error_code:3][error_points:8][SP body echo (fields 1–61):781][CRLF:2]` = **794 bytes**

| SE# | Field | Type | Size | Source | Notes |
|-----|-------|------|------|--------|-------|
| 1 | Error Code | String | 3 | CCCMK result | `000`/empty=success; 521-527,536-538,550=resendable; others=permanent failure |
| 2 | Error Points | String | 8 | CCCMK result | Non-zero only when `error_cd` ∈ {585}; otherwise fixed `00000000` |
| 3 | Business Type Code | String | 8 | SP echo | `gyotai_cd` |
| 4 | Store Code | String | 13 | SP echo | `tenpo_cd` |
| 5 | Member ID Category | String | 2 | SP echo | `kaiin_id_kbn` |
| 6 | Member ID | String | 100 | SP echo | `kaiin_id` |
| 7 | Date of Use | String | 8 | SP echo | `shori_date` |
| 8 | Time of Use | String | 6 | SP echo | `shori_time` |
| 9 | Business Start Date | String | 8 | SP echo | `eigyou_date` |
| **10** | **Serial Number** | String | 20 | SP echo | **`serial_no` — used to match DB record** |
| 11 | Register No. | String | 6 | SP echo | `register_no` |
| 12 | Invoice No. | String | 20 | SP echo | `denpyo_no` |
| 13 | Retry Category | String | 1 | SP echo | `retry_kbn` |
| 14 | Point Operation Category | String | 2 | SP echo | `point_kbn` (73/74) |
| 15 | Fixed Period ID | String | 16 | SP echo | Blank Filler |
| 16 | Store-Exclusive V Point Expiration Date | String | 8 | SP echo | Blank Filler |
| 17 | Cancel Category | String | 1 | SP echo | `cancel_kbn` |
| 18 | Original Transaction Usage Date | String | 8 | SP echo | `moto_date` |
| 19 | Original Transaction Serial Number | String | 20 | SP echo | `moto_serial_no` |
| 20 | Cancel points | Number | 8 | SP echo | `kangen_point` |
| 21–28 | Campaign/Visit/Exchange/Transfer/Credit/Other/Reserve1/Grade | Number | 8×8 | SP echo | Pad 0s |
| 29–39 | Reserve 3–13 Points | Number | 8×11 | SP echo | Pad 0s |
| 40 | System Usage Fee Flag | Number | 1 | SP echo | Fixed: `1` |
| 41 | Amount Subject to System Usage Fee | Number | 8 | SP echo | Pad 0s |
| 42 | Num Sales Points Subject to Fee | Number | 8 | SP echo | Pad 0s |
| 43 | Sales Amount Tax-Inclusive Flag | Number | 1 | SP echo | Fixed: `1` |
| 44 | Sales Amount | Number | 8 | SP echo | `uriage_kin` |
| 45 | Number of sales items | Number | 8 | SP echo | Pad 0s |
| 46 | V Member Number Reading Category | Number | 1 | SP echo | Fixed: `0` |
| 47 | V Member Number Digit Count Category | Number | 1 | SP echo | Fixed: `0` |
| 48 | Payment Method | Number | 1 | SP echo | Fixed: `9` |
| 49 | V Point Usage Flag | Number | 1 | SP echo | Fixed: `0` |
| 50 | Number of Customers | Number | 4 | SP echo | Fixed: `0001` |
| 51 | Registration Path | Number | 1 | SP echo | Fixed: `1` |
| 52 | Valid/Invalid Flag | String | 1 | SP echo | Fixed: `1` |
| 53 | V Point Site History Display Text | String | 30 | SP echo | Blank Filler |
| 54–63 | Individual Information 1–10 | String | 30×10 | SP echo | Blank Filler |
| 64 | Line Feed | — | 2 | — | CRLF (0x0D0A) |

**Byte verification:** 3+8+8+13+2+100+8+6+8+20+6+20+1+2+16+8+1+8+20+8+(8×8)+(8×11)+1+8+8+1+8+8+1+1+1+1+4+1+1+30+(30×10)+2 = **794**

> **Error Points (SE#2) rule for CR5 (point_kbn 73/74):** Only `error_cd=585` (Usage Limit Exceeded, 74 only) populates error_points with the actual value. All other error codes → fixed `00000000`.

> **BAT4 matching logic:** Parse SE body field #10 (`serial_no`) to find the corresponding `dct_vpoint_redeem_result` record with `status=3`. Then read SE#1 (`error_code`) to classify and update status.

### BAT5: Automated Cancel Processing (NEW — v23)

- **Schedule:** Flexible timing (client: "any available schedule"). Recommend **16:00 JST** to avoid BAT3 (14:30) and BAT4 (11:30)
- **Query:** `status=2 AND point_kbn=74` (Approved cancel records) — records approved by admin for cancellation
- **Processing per record:**
  1. Set `status=3` (Processing), `error_cd=Null`
  2. Call sp201 Cancel (point_kbn=74) with record data
  3. Route by code_type: code_type=1→`status=4` (Success), code_type=2→`status=6` (Recovery/Resend → BAT3), code_type=3→`status=5` (Failed)
  4. Update `return_cd`, `error_cd`, `get_return_date`, `program_name=5`
- **Redis lock** TTL=30min; `--dry-run` and `--verbose` flags
- **Slack:** `"BAT5: {success}/{failed}/{total} cancel redemptions processed"`

### SP File Header Layout (783 bytes)

| # | Field | Type | Size | Value |
|---|-------|------|------|-------|
| 1 | Record Type | Char | 10 | `@@HEADER@@` |
| 2 | Data Identifier | Char | 8 | `SPCOMMON` |
| 3 | Alliance Code | Char | 4 | Issued by CCCMK |
| 4 | Creation Date | Numeric | 8 | YYYYMMDD (**JST**) |
| 5 | Creation Time | Numeric | 6 | HH24MISS (**JST**) |
| 6 | Record Count | Numeric | 8 | Number of body records |
| 7 | Record Length | Numeric | 4 | Fixed: `0781` |
| 8 | Reserve | Char | 20 | Space padding |
| 9 | Length Adjustment | Char | 713 | Space padding |
| 10 | Line Feed | — | 2 | CRLF (0x0D0A) |

**SP File Body Record — 62-Field Layout (783 bytes)**

The SP body has 61 data fields + CRLF = 62 items. This is NOT the same as the API request fields.
The API request (sp201.do) has 21 fields; only a subset maps to the SP body. Many SP body fields
use fixed/default values for kbn 73/74.

**Fields NOT in SP body (API-only):** `alliance_cd` (header only), `passwd` (API auth only),
`ninsho_kbn` (API #7, not in body), `ninsho_code` (API #8, not in body), `retry_cnt` (DB internal only).

| SP# | Field | Type | Size | Source (kbn 73) | Source (kbn 74) |
|-----|-------|------|------|-----------------|-----------------|
| 1 | Business Type Code | Char | 8 | DB: `gyotai_cd` | DB: `gyotai_cd` |
| 2 | Store Code | Char | 13 | DB: `tenpo_cd` | DB: `tenpo_cd` |
| 3 | Member ID Category | Char | 2 | Fixed: `10` | Fixed: `10` |
| 4 | Member ID | Char | 100 | DB: `kaiin_id` | DB: `kaiin_id` |
| 5 | Date of Use | Char | 8 | DB: `shori_date` | DB: `shori_date` |
| 6 | Time of Use | Char | 6 | DB: `shori_time` | DB: `shori_time` |
| 7 | Business Start Date | Char | 8 | DB: `eigyou_date` | DB: `eigyou_date` |
| 8 | Serial Number | Char | 20 | DB: `serial_no` | DB: `serial_no` |
| 9 | Register No. | Char | 6 | DB: `register_no` | DB: `register_no` |
| 10 | Invoice No. | Char | 20 | DB: `denpyo_no` | DB: `denpyo_no` |
| 11 | Retry Category | Char | 1 | Fixed: `0` | Fixed: `0` |
| 12 | Point Operation Category | Char | 2 | DB: `point_kbn` (73) | DB: `point_kbn` (74) |
| 13 | Fixed Period ID | Char | 16 | Blank Filler | Blank Filler |
| 14 | Store-Exclusive V Point Expiration Date | Char | 8 | Blank Filler | Blank Filler |
| 15 | Cancel Category | Char | 1 | DB: `cancel_kbn` | DB: `cancel_kbn` |
| 16 | Original Transaction Usage Date | Char | 8 | DB: `moto_date` (blank if NULL) | DB: `moto_date` |
| 17 | Original Transaction Serial Number | Char | 20 | DB: `moto_serial_no` (blank if NULL) | DB: `moto_serial_no` |
| 18 | Points (rebate amount) | Num | 8 | DB: `kangen_point` | Fixed: `0` |
| 19–26 | Campaign/Visit/Exchange/Transfer/Credit/Other/Reserve1/Grade | Num | 8×8 | Pad 0s | Pad 0s |
| 27–37 | Reserve 3–13 Points | Num | 8×11 | Pad 0s | Pad 0s |
| 38 | System Usage Fee Flag | Num | 1 | Fixed: `1` | Fixed: `1` |
| 39 | Amount Subject to System Usage Fee | Num | 8 | Pad 0s | Pad 0s |
| 40 | Num Sales Points Subject to Fee | Num | 8 | Pad 0s | Pad 0s |
| 41 | Sales Amount Tax-Inclusive Flag | Num | 1 | Fixed: `1` | Fixed: `1` |
| 42 | Sales Amount | Num | 8 | DB: `uriage_kin` | Fixed: `0` |
| 43 | Number of sales items | Num | 8 | Pad 0s | Pad 0s |
| 44 | V Member Number Reading Category | Num | 1 | Fixed: `0` | Fixed: `0` |
| 45 | V Member Number Digit Count Category | Num | 1 | Fixed: `0` | Fixed: `0` |
| 46 | Payment Method | Num | 1 | Fixed: `9` | Fixed: `9` |
| 47 | V Point Usage Flag | Num | 1 | Fixed: `0` | Fixed: `0` |
| 48 | Number of Customers | Num | 4 | Fixed: `0001` | Fixed: `0001` |
| 49 | Registration Path | Num | 1 | Fixed: `1` | Fixed: `1` |
| 50 | Valid/Invalid Flag | Char | 1 | Fixed: `1` | Fixed: `1` |
| 51 | V Point Site History Display Text | Char | 30 | Blank Filler | Blank Filler |
| 52–61 | Individual Information 1–10 | Char | 30×10 | Blank Filler | Blank Filler |
| 62 | Line Feed | — | 2 | CRLF (0x0D0A) | CRLF (0x0D0A) |

**Byte verification:** 8+13+2+100+8+6+8+20+6+20+1+2+16+8+1+8+20+8+(8×8)+(8×11)+1+8+8+1+8+8+1+1+1+1+4+1+1+30+(30×10)+2 = **783**

All Char fields: left-aligned, space-padded. All Num fields: right-aligned, zero-padded.
Fields #5–#7, #16 use Char type (space-padded), NOT Num — per CCCMK spec.

---

## Database Schema — Core Tables

### dct_vpoint_redeem_result (32 columns)

| # | Column | Type | Null | Description |
|---|--------|------|------|-------------|
| 1 | id | INT(10) | ○ | PK, auto-increment |
| 2 | app_member_id | VARCHAR(13) | ○ | MrMax app member ID (`dtb_customer.ext_attr_text3`) |
| 3 | alliance_cd | VARCHAR(4) | ○ | CCCMK alliance code (common) |
| 5 | gyotai_cd | VARCHAR(8) | ○ | Fixed: 00000001 |
| 6 | tenpo_cd | VARCHAR(13) | ○ | Fixed: 0000000002454 |
| 7 | kaiin_id_kbn | VARCHAR(2) | ○ | Fixed: 10 (Site ID) |
| 8 | kaiin_id | VARCHAR(100) | ○ | Customer representative number (`dtb_customer_card_info.customer_number`) |
| 9 | ninsho_kbn | VARCHAR(1) | ○ | Fixed: 0 |
| 10 | ninsho_code | VARCHAR(32) | × | Fixed: NULL |
| 11 | shori_date | VARCHAR(8) | ○ | Processing date (yyyymmdd) **UTC** |
| 12 | shori_time | VARCHAR(6) | ○ | Processing time (hh24miss) **UTC** |
| 13 | eigyou_date | VARCHAR(8) | ○ | Business date (= shori_date) **UTC** |
| 14 | serial_no | VARCHAR(20) | ○ | **Unique key** — `[ServiceID:3][YYMMDD(JST):6][Seq:11]` |
| 15 | register_no | VARCHAR(6) | ○ | Fixed: 000001 |
| 16 | denpyo_no | VARCHAR(20) | ○ | EC=order# left-zero-padded to 20; Native=20 zeros |
| 17 | retry_kbn | INT(1) | ○ | Always 0 (no retry in CR5 Phase1) |
| 18 | retry_cnt | SMALLINT(1) | ○ | **Unique key** — Always 0 (no retry in CR5 Phase1) |
| 19 | point_kbn | INT(2) | ○ | **Unique key** — 73: Redemption, 74: Cancel |
| 20 | cancel_kbn | INT(1) | ○ | 0: Full cancellation (INSERT=0 fixed; UPDATE from API response echo) |
| 21 | moto_date | VARCHAR(8) | × | Original transaction date (NULL if point_kbn=73 redemption) |
| 22 | moto_serial_no | VARCHAR(20) | × | Original serial_no to cancel (NULL if point_kbn=73 redemption) |
| 23 | kangen_point | INT(8) | ○ | Points to redeem/cancel (absolute); cancel=0 for point_kbn=74 |
| 24 | uriage_kin | VARCHAR(8) | ○ | Fixed: 0 |
| 25 | return_cd | VARCHAR(2) | × | sp201 return code (NULL before API call) |
| 26 | get_return_date | DATETIME | ○ | Datetime return code received |
| 27 | create_date | DATETIME | ○ | Record creation |
| 28 | update_date | DATETIME | ○ | Record update |
| 29 | status | SMALLINT(1) | ○ | 0-7 state machine (default: 0). See Status State Machine section. |
| 30 | error_cd | VARCHAR(3) | × | BAT4 return code (SExxx file body) |
| 31 | program_name | VARCHAR(1) | ○ | 1:sp201, 2:sp201(Cancel), 3:BAT3, 4:BAT4, 5:BAT5, 6:Manual(query) |
| 32 | type | VARCHAR(1) | ○ | 1:API call, 2:file transfer |

> **serial_no Sharing Rule:** Redemption (point_kbn=73) and cancellation (point_kbn=74) records for the **same coupon share the same `serial_no`**. The serial_no is generated at redemption and reused for the cancel record. Sequence increments per service ID per JST date (not reset per operation type).

### dtb_customer_card_info (13 columns)

| Column | Type | Description |
|--------|------|-------------|
| id | INT (PK) | Auto-increment |
| app_member_id | VARCHAR(13) | MrMax app member ID |
| customer_number | VARCHAR(16) | カード作成顧客に紐づく一意の番号(不変) / Unique number associated with the customer who made the credit card (unchangeable) |
| member_group_number | VARCHAR(16) | Member group number |
| mrmax_id | VARCHAR(20) | カードに紐づく一意の番号(バーコード番号) / Unique number associated with the card (barcode number) |
| card_linkaged_dt | DATETIME | Date/time linked |
| card_dislinkaged_dt | DATETIME | Date/time unlinked |
| is_valid | TINYINT(1) | 1: Active, 0: Historical |
| is_card_cancelled | TINYINT(1) | 1: Card cancelled by SMCC |
| create_dt | DATETIME | Record creation |
| create_by | VARCHAR(100) | Batch/program that created record |
| update_dt | DATETIME | Record update |
| update_by | VARCHAR(100) | Batch/program that last updated record |

### dct_vpoint_exchanges (6 columns + 9 seed rows)

Exchange amount button master for Membership and Coupon List page.

| Column | Type | Null | Description |
|--------|------|------|-------------|
| id | VARCHAR(10) (PK) | No | Manually assigned key |
| display_name | VARCHAR(50) | No | Display text on button (e.g. "すべて", "¥100") |
| point_quantity | VARCHAR(10) | Yes | Point value (e.g. "100", "1000"); NULL for "すべて" (All) |
| coupon_banner | VARCHAR(255) | Yes | Banner image path or identifier (NULL = no banner) |
| display_status | INT(1) | No | 1: Display, 2: Hide (default: 1) |
| display_order | INT(1) | Yes | Display order ascending; NULL when display_status=2 |

**Seed rows (v25 — 9 rows):**

| id | display_name | point_quantity | coupon_banner | display_status | display_order |
|----|-------------|----------------|---------------|--------------|---------------|
| 1 | すべて | NULL | NULL | 1 | 1 |
| 2 | ¥100 | 100 | NULL | 1 | 2 |
| 3 | ¥300 | 300 | NULL | 1 | 3 |
| 4 | ¥500 | 500 | NULL | 1 | 4 |
| 5 | ¥1,000 | 1000 | NULL | 1 | 5 |
| 6 | ¥3,000 | 3000 | NULL | 1 | 6 |
| 7 | ¥5,000 | 5000 | NULL | 1 | 7 |
| 8 | ¥7,000 | 7000 | NULL | 1 | 8 |
| 9 | ¥10,000 | 10000 | NULL | 1 | 9 |

> Rows with `display_status=2` have `display_order=NULL`.

### dtb_card_application_info

| Column | Type | Null | Description |
|--------|------|------|-------------|
| id | INT UNSIGNED | — | Auto-increment PK |
| data_type | VARCHAR(2) | — | SMCC record type: 10/20/30/40/50 |
| received_date | VARCHAR(8) | — | File received date (YYYYMMDD) |
| cnt | INT UNSIGNED | — | Number of records processed for this data_type |
| create_dt | DATETIME | — | Record creation datetime (JST) |
| create_by | VARCHAR(100) | ○ | Batch that created the record |
| update_dt | DATETIME | — | Record update datetime (JST) |
| update_by | VARCHAR(100) | ○ | Batch that last updated the record |

### dtb_affiliated_card_info (Full Schema — SMCC Card Master)

**Updated daily by BAT2. 79 columns total: 75 SMCC file fields (No.1–75) + 1 internal flag + 4 audit columns (No.76–79).**

> **Field markers:** ● Required ▲ Set when host has info △ Set on change (data_type=30) ー Not set

| No. | Column | Type | Size | Null | 10 New | 20 Cancel | 30 Change | 40 Reissue | 50 Update | Description |
|-----|--------|------|------|------|--------|-----------|-----------|------------|-----------|-------------|
| PK | id | INT UNSIGNED | 10 | — | — | — | — | — | — | Auto-increment primary key |
| 1 | record_type | CHAR | 1 | ○ | ● | ● | ● | ● | ● | Fixed: "2" |
| 2 | data_type | CHAR | 2 | — | ● | ● | ● | ● | ● | 10=New, 20=Cancellation, 30=Change, 40=Reissue, 50=Update |
| 3 | member_group_number | CHAR | 9 | ○ | ● | ● | ● | ● | ● | Member group number (account-level invariant) |
| 4 | application_form_number | CHAR | 15 | ○ | ▲ | ー | ー | ー | ー | Membership application form number |
| 5 | member_type | CHAR | 1 | ○ | ● | ● | ● | ● | ● | "1"=Individual, "3"=Corporate |
| 6 | pin_number_allocation_type | CHAR | 1 | ○ | ● | ー | ー | ー | ー | "0"=Member requested, "1"=Assigned by card company |
| 7 | pin_number | CHAR | 4 | ○ | ● | ー | ー | ー | ー | Credit PIN — not disclosed |
| 8 | substitute_member_number | CHAR | 16 | ○ | ● | ● | ● | ● | ● | Credit membership number (post-reissue/replacement) |
| 9 | joining_date | CHAR | 8 | ○ | ● | ー | ー | ー | ー | Joining date (YYYYMMDD). ① Rejection/provisional approval/partner rejection/withdrawal → result registration date. ② New/replacement → card enrollment date. |
| 10 | application_registration_dt | CHAR | 8 | ○ | ▲ | ー | ー | ー | ー | Application form registration date (YYYYMMDD) |
| 11 | member_name_kanji | CHAR | 10 | ○ | ▲ | ー | △ | ▲ | ー | Member name in Kanji (left-aligned, trailing spaces) |
| 12 | member_name_kana | CHAR | 20 | ○ | ● | ー | △ | ● | ー | Member name in Kana (left-aligned, trailing spaces) |
| 13 | member_name_en | CHAR | 20 | ○ | ● | ー | △ | ● | ー | Romanized name |
| 14 | relationship_type | CHAR | 1 | ○ | ● | ● | ● | ● | ● | "0"=Primary member (fixed) |
| 15 | sex_type | CHAR | 1 | ○ | ● | ー | △ | ● | ー | "1"=Male, "2"=Female, "9"=Unknown |
| 16 | birthday | CHAR | 8 | ○ | ● | ー | △ | ● | ー | **YYYYMMDD — used for card linkage birthday auth** |
| 17 | zip_code | CHAR | 7 | ○ | ▲ | ー | △ | ▲ | ー | Home postal code |
| 18 | addr_kana | VARCHAR | 80 | ○ | ● | ー | △ | ● | ー | Address in Kana |
| 19 | addr_kanji | VARCHAR | 70 | ○ | ● | ー | △ | ● | ー | Address in Kanji |
| 20 | phone_number_home | VARCHAR | 15 | ○ | ▲ | ー | △ | ▲ | ー | Home phone number |
| 21 | phone_number_mobile | VARCHAR | 15 | ○ | ▲ | ー | △ | ▲ | ー | Mobile phone number |
| 22 | family_composition_type | SMALLINT | 1 | ○ | ▲ | ー | ー | ー | ー | "1"=Single, "2"=Married, "3"=With children, "9"=Unknown |
| 23 | is_living_together | SMALLINT | 1 | ○ | ▲ | ー | ー | ー | ー | "0"=Together, "1"=Separately |
| 24 | name_of_employer_kana | VARCHAR | 20 | ○ | ▲ | ー | △ | ▲ | ー | Employer name in Kana |
| 25 | name_of_employer_kanji | VARCHAR | 10 | ○ | ▲ | ー | △ | ▲ | ー | Employer name in Kanji |
| 26 | department_division_kana | VARCHAR | 10 | ○ | ▲ | ー | △ | ▲ | ー | Department name in Kana |
| 27 | department_division_kanji | VARCHAR | 10 | ○ | ▲ | ー | △ | ▲ | ー | Department name in Kanji |
| 28 | job_title_kana | VARCHAR | 10 | ○ | ▲ | ー | △ | ▲ | ー | Job title in Kana |
| 29 | job_title_kanji | VARCHAR | 10 | ○ | ▲ | ー | △ | ▲ | ー | Job title in Kanji |
| 30 | phone_number_work | VARCHAR | 15 | ○ | ▲ | ー | △ | ▲ | ー | Workplace phone number |
| 31 | joined_company_dt | CHAR | 4 | ○ | ▲ | ー | ー | ー | ー | Company entry date (YYMM) |
| 32 | zip_code_work | CHAR | 7 | ○ | ▲ | ー | △ | ▲ | ー | Workplace postal code |
| 33 | addr_work_kana | CHAR | 80 | ○ | ▲ | ー | △ | ▲ | ー | Workplace address in Kana |
| 34 | addr_work_kanji | CHAR | 70 | ○ | ▲ | ー | △ | ▲ | ー | Workplace address in Kanji |
| 35 | annual_income | CHAR | 5 | ○ | ▲ | ー | ー | ー | ー | Annual income (ten-thousand yen units) |
| 36 | send_type | SMALLINT | 1 | ○ | ● | ー | △ | ● | ー | "0"=Home, "1"=Workplace, "2"=Other |
| 37 | living_situation_type | SMALLINT | 1 | ○ | ▲ | ー | ー | ー | ー | Living situation code: "0"=Owned home (self-owned), "1"=Owned home (family-owned), "2"=Company/Government housing/Dormitory, "3"=Rented house (public/municipal), "4"=Rented apartment (private), "5"=Boarding/Apartment, "9"=Unknown |
| 38 | email_addr | CHAR | 25 | ○ | ▲ | ー | △ | ▲ | ー | Email address (half-width) |
| 39 | financial_institution_code | CHAR | 4 | ○ | ● | ー | △ | ● | ー | Financial institution code |
| 40 | branch_code | CHAR | 4 | ○ | ● | ー | △ | ● | ー | Branch code (last 4 digits) |
| 41 | subjects_type | SMALLINT | 1 | ○ | ● | ー | △ | ● | ー | "1"=Ordinary, "2"=Checking, "3"=Staff, "9"=Other |
| 42 | account_number | CHAR | 8 | ○ | ● | ー | △ | ● | ー | Account number (zero-padded) |
| 43 | account_holder | CHAR | 20 | ○ | ● | ー | △ | ● | ー | Account holder (Kana) |
| 44 | subscription_code | CHAR | 1 | ○ | ● | ー | ー | ー | ー | Subscription code |
| 45 | planned_graduation_year | CHAR | 4 | ○ | ▲ | ー | ー | ー | ー | Expected graduation year (YYYY) |
| 46 | card_expiration_date | CHAR | 4 | ○ | ● | ー | △ | ● | ● | Card expiration date (YYMM) |
| 47 | cancellation_type | SMALLINT | 1 | ○ | ● | ● | △ | ● | ● | "0"=Active, "1"=Cancelled |
| 48 | has_incident | SMALLINT | 1 | ○ | ● | ● | △ | ● | ● | "0"=No incident, "1"=Incident member |
| 49 | credence_type | SMALLINT | 1 | ○ | ● | ● | △ | ● | ● | "0"=Normal, "1"=Delinquent, "2"=Caution |
| 50 | is_update_stopped | SMALLINT | 1 | ○ | ● | ● | △ | ● | ● | "0"=No stop, "1"=Renewal stop |
| 51 | has_collect | SMALLINT | 1 | ○ | ● | ● | △ | ● | ● | "0"=No collection, "1"=Card collected |
| 52 | has_prohibited | SMALLINT | 1 | ○ | ● | ● | △ | ● | ● | "0"=No prohibition, "1"=Prohibited |
| 53 | spare_credence | VARCHAR | 4 | ○ | ー | ー | ー | ー | ー | Spare (credence section) |
| 54 | conversion_member_number | CHAR | 16 | ○ | ▲ | ー | ー | ● | ー | Previous member number before reissue |
| 55 | annual_fee_collection_dt | CHAR | 4 | ○ | ● | ー | ー | ー | ー | Annual fee collection date (YYMM) |
| 56 | recruit_group_code | VARCHAR | 5 | ○ | ▲ | ▲ | ▲ | ▲ | ▲ | Recruit group code, account basis, zero-left-padded, numeric. New: 00001–00003; Reissue: 00101–00103. |
| 57 | membership_card_number | VARCHAR | 16 | ○ | ▲ | ▲ | ▲ | ▲ | ▲ | Membership card number |
| 58 | partner_unique_area | VARCHAR | 20 | ○ | ▲ | ▲ | ▲ | ▲ | ▲ | Partner unique area |
| 59 | embossed_area | VARCHAR | 20 | ○ | ▲ | ▲ | ▲ | ▲ | ▲ | Embossed area |
| 60 | spare_info | CHAR | 2 | ○ | ー | ー | ー | ー | ー | Spare (partner info section) |
| 61 | mrmax_id | VARCHAR | 20 | — | ● | ● | ● | ● | ● | **Partner Customer 1 (提携先顧客1): MrMax ID** — 8桁(前詰め後ろスペース) ※英数タイプ / 8-char alphanumeric, left-aligned, trailing spaces |
| 62 | customer_number | VARCHAR | 20 | — | ● | ● | ● | ● | ● | **Representative customer number (12 chars) — Unique Key, Unchanging** |
| 63 | has_change_name | CHAR | 1 | ○ | ー | ー | △ | ● | ー | Name change flag: " "=No change, "1"=Changed. Targets: No.11–13, 15, 16 |
| 64 | has_change_addr | CHAR | 1 | ○ | ー | ー | △ | ● | ー | Address change flag. Targets: No.17–21, 38, 74 |
| 65 | has_change_work | CHAR | 1 | ○ | ー | ー | △ | ● | ー | Work change flag. Targets: No.24–30, 32–34 |
| 66 | has_change_payment_acc | CHAR | 1 | ○ | ー | ー | △ | ● | ー | Payment account change flag. Targets: No.39–43 |
| 67 | has_change_expiry_date | CHAR | 1 | ○ | ー | ー | △ | ● | ● | Expiry date change flag. Targets: No.46 |
| 68 | has_change_partner_info | CHAR | 1 | ○ | ー | ー | △ | ● | ー | Partner info change flag. Targets: No.56–62 |
| 69 | has_change_credence_type | CHAR | 1 | ○ | ー | ー | △ | ● | ● | Credence code change flag. Targets: No.47–53 |
| 70 | has_change_send_type | CHAR | 1 | ○ | ー | ー | △ | ● | ー | Send type change flag. Targets: No.36 |
| 71 | spare_change | VARCHAR | 3 | ○ | ー | ー | ー | ー | ー | Spare (change section) |
| 72 | member_number | CHAR | 16 | ○ | ● | ● | ● | ● | ● | Representative member number (latest) |
| 73 | repayment_type | CHAR | 14 | ○ | ● | ● | ● | ● | ● | Card code + repayment type (0–6) |
| 74 | email_addr_home | CHAR | 50 | ○ | ▲ | ー | △ | ▲ | ー | Home email address (full-width) |
| 75 | spare | VARCHAR | 108 | ○ | ー | ー | ー | ー | ー | Spare padding |
| — | is_card_cancelled | TINYINT(1) UNSIGNED | — | — | — | — | — | — | — | Internal: 1=Card cancelled (set by BAT2 type=20), default 0 |
| 76 | create_dt | DATETIME | — | — | — | — | — | — | — | Record creation datetime (JST) |
| 77 | create_by | VARCHAR | 100 | ○ | — | — | — | — | — | Batch that created the record |
| 78 | update_dt | DATETIME | — | — | — | — | — | — | — | Record update datetime (JST) |
| 79 | update_by | VARCHAR | 100 | ○ | — | — | — | — | — | Batch that last updated the record |

**Indexes:** UNIQUE KEY `(customer_number)`; INDEX on `customer_number`, `mrmax_id`, `data_type`, `is_card_cancelled`

**BAT2 per-type operation summary:**
- **type=10 (New):** INSERT all fields; reject if duplicate `customer_number`
- **type=20 (Cancellation):** UPDATE `is_card_cancelled=1`; also set `dtb_customer_card_info.is_valid=0` for linked card
- **type=30 (Change):** UPDATE address/name fields per change flags (has_change_*)
- **type=40 (Reissue):** UPDATE mrmax_id to new value; flip old `dtb_customer_card_info.is_valid→0`, new→1
- **type=50 (Update):** UPDATE card_expiration_date and renewal fields

### Timezone Rules

| Field | Timezone |
|-------|----------|
| shori_date, shori_time, eigyou_date | **UTC** |
| serial_no date component (YYMMDD) | **JST** |
| SP file header creation_date/time | **JST** |
| DB create_date, update_date | **UTC** || BAT cron schedules | **JST** |
| Admin display dates | **JST** |

### Cancellation Window Rule
- **Customer-side (CCCMK external constraint):** ≤ **12 months** from original transaction — sp201 Cancel returns code `15` ("No-cancellation error") after 12 months. This is enforced by CCCMK, not MrMax.
- **Admin-side (MrMax rule):** ≤ **365 days** (NOT 12 months) — `modify('-365 days')` in JST. MrMax enforces this in the admin cancel screen.
### SQL Required (Manual — No Migrations)

```sql
-- CREATE TABLE dct_vpoint_redeem_result (32 columns — passwd removed per v23)
-- CREATE TABLE dct_vpoint_exchanges (6 columns) + INSERT 9 seed rows (すべて/NULL + ¥100,¥300,¥500,¥1000,¥3000,¥5000,¥7000,¥10000)
-- ALTER TABLE dct_coupon_target ADD serial_no VARCHAR(20) NULL
-- INSERT INTO dcm_coupon (id=999999990001, type1=3, scope=1, number_of_use=1)
-- CREATE TABLE dtb_customer_card_info
-- CREATE TABLE dtb_affiliated_card_info (79 columns: 75 SMCC file fields + is_card_cancelled + create_dt/create_by/update_dt/update_by)
-- CREATE TABLE dtb_card_application_info
```

---

## Admin Screens

### Card Linkage Summary
- All-time totals: ①linked, ②dislinkaged
- Daily breakdown: ③新規, ④解約, ⑤連携人数, ⑥連携解除人数
- Date range filter (default: month 1st→today, max 366 days)
- WYSIWYG Excel export (PhpSpreadsheet) — exports exactly what admin sees on screen

#### Member Export Formats (v23)

**連携メンバー (Linked Members) Export — 5 columns:**

| Column | Description |
|--------|-------------|
| MrMax ID | mrmax_id |
| Customer Number | Representative customer number |
| Linkage Date | card_linkaged_dt |
| App Member ID | app_member_id |
| Member Name | Customer name |

**連携解除メンバー (Unlinked Members) Export — 3 columns:**

| Column | Description |
|--------|-------------|
| MrMax ID | mrmax_id |
| Customer Number | Representative customer number |
| Dislinkage Date | card_dislinkaged_dt |

### Cancel Redeemed V-Points (v23 Restructured)
- **(v23)** Screen path: Home / **Coupon Management** / V-Point Coupon Cancel
- **(v23)** New **search area** with filters: serial_no, member ID, date range, status
- **(v23)** Added **Process Type** column in result list (format: `type-point_kbn-return_cd`)
- **365-day** cancellation window (NOT 12 months) — `modify('-365 days')` in JST
- Single-attempt cancel (v23): sp201 Cancel → if NG → status=2 → BAT5/BAT3
- Audit log: admin user, timestamp, before/after status
- **Admin buttons disabled** when: coupon used+order cancelled, card cancelled, BAT2 type=20, coupon expired

### Admin 3-Button State Machine

| Button | JP Label | Transition | Enabled At |
|--------|----------|------------|------------|
| Apply Cancel | 利用キャンセル | 0→1 or 5→1 | status 0, 5 |
| Approve | 承認 | 1→2 (sp201 fails) or 1→4 (sp201 success) | status 1 |
| Cancel Application | 申請キャンセル | 1→0 | status 1 |

> Retry from status 5: both paths supported — 5→1 (direct retry) or 5→0→1 (reset then re-apply).

### Admin Cancel Status Display Labels (v4, updated v23)

| status | Display Label | Notes |
|--------------|--------------|-------|
| 0 | Not applied | — |
| 1 | Applied | sp201 Cancel in progress |
| 2 | Approved(xx) | Show sp201(Cancel) return code |
| 3 | Processing | BAT3 sent SP file |
| 4 | Completed cancel(xxx) | Show return code from sp201 or BAT4 |
| 5 | Failed cancel(xxx) | Show error code from BAT4 |
| 6 | Recovery(xx) | sp201 Cancel Code Type 2 — file recovery via BAT3 |
| 7 | CheckOut NG | GMO payment failed after sp201 success |

### Admin Button Enable Conditions (v23)

| Button | Enabled when latest record matches |
|--------|-------------------------------------|
| **Refund** (利用キャンセル) | `type=1`, `status=4`, `point_kbn=73`, `return_cd='00'`, `program_name=1` |
| **Approve** (承認) | `type=1`, `status=1`, `point_kbn=74`, `return_cd='00'`, `program_name=1` |
| **Cancel to apply** (申請キャンセル) | `type=1`, `status=1`, `point_kbn=74`, `return_cd='00'`, `program_name=1` |

### Payment Method Handling (v3)

#### Case4: Change Payment Info in Order Management (PG Button Disable)

| Case | GMO/Paidy | V-Point Coupon | Action |
|------|-----------|----------------|--------|
| Case1 | Yes | No | No change (keep current system) |
| Case2 | No | Yes | **Disable PG Multipayment Service buttons** |
| Case3 | Yes | Yes | **Disable PG Multipayment Service buttons** |

#### Case6: Payment Status List & Paidy Management Page

| Case | GMO/Paidy | V-Point Coupon | Action |
|------|-----------|----------------|--------|
| Case1 | Yes | No | No change (keep current system) |
| Case2 | No | Yes | **HIDE the order record from the list** |
| Case3 | Yes | Yes | No change (**keep visible** — GMO payment exists) |

> **Key distinction:** Case3 has PG buttons disabled (Case4) but order is KEPT in payment list (Case6). Only Case2 (V-Point-only, no GMO) is hidden.

- Case7 Change Mode Checkout: no new implementation needed
- No approval authorization control for cancel operations (operational process, not system-enforced RBAC)

---

## Native App — Key Rules

### UI Requirements
- Balance display: **"X,XXXpt"** on membership card screen
- sp101 failure: show **＊＊＊＊pt**
- Exchange buttons: default **3** visible → "Show more" expands to **9** (accordion)
- **"All" option first**, then ascending order (¥100→¥50,000)
- Buttons **disabled** if insufficient balance
- Coupon issued **immediately** on successful sp201
- **Refresh button** calls sp101 again

### API Endpoints & Response Schemas

#### `GET /api/v1/vpoint/balance` — V-Point Balance Inquiry
**Purpose:** Calls sp101 to fetch the customer's current V-Point balance. Displayed on the membership card screen. Returns formatted balance string for display and raw integer for button enable/disable logic.

```json
{"balance": "2,000pt", "raw_balance": 2000, "error_msg": null, "is_linked": true}
```
On sp101 failure: `{"balance": "＊＊＊＊pt", "raw_balance": null, "error_msg": "...", "is_linked": true}`

#### `GET /api/v1/vpoint/exchanges` — Exchange Denomination Buttons
**Purpose:** Returns all visible V-Point exchange denomination buttons (`display_status=1`, ordered by `display_order ASC`) from `dct_vpoint_exchanges`. Includes "すべて" (All, `point_quantity=NULL`) as the first option, followed by ¥100→¥10,000. Each button's `disabled` flag is computed as `point_quantity !== null && point_quantity > raw_balance` ("すべて" is never disabled). Backend always returns all visible rows — accordion (3 default / expand to all) is purely mobile app UI.

```json
{"exchanges": [{"id": "1", "display_name": "すべて", "point_quantity": null, "coupon_banner": "...", "disabled": false}, {"id": "2", "display_name": "¥100", "point_quantity": "100", "coupon_banner": "...", "disabled": false}, ...]}
```
> Accordion is **purely mobile app UI** — backend always returns all visible buttons.

> **Native App cancel:** `POST /api/v1/vpoint/redeem` (T14) failures use the **same single-attempt cancel logic as EC (v23)** — INSERT cancel record, single sp201 Cancel call, route by code_type: code_type=1→status=4, code_type=2→status=6 (BAT3/BAT5 recovery), code_type=3→status=5. `VpointRedemptionService::cancelRedemption()` is shared between EC and Native flows. **No retries.**

#### `POST /api/v1/vpoint/redeem` — Execute V-Point Redemption
**Purpose:** Executes the actual V-Point-to-coupon exchange. Calls sp201 (point_kbn=73) to deduct points from CCCMK, issues a digital coupon on success (`dct_coupon_target` with `serial_no`), and returns updated balance + coupon details + Karte analytics event payload for the mobile app to fire client-side.

```json
{"success": true, "coupon": {"id": 123, "serial_no": "A0326050600000000001", "amount": 1000}, "new_balance": "1,000pt", "karte_event": {"event": "vpoint_exchange", "data": {...}}}
```
On failure: sp201 cancel (single attempt, v23); returns `{"success": false, "error_msg": "..."}`

---

## Purchase History — Cancel Status Display (v4, updated v23)

| Condition | Display |
|-----------|--------|
| No cancellation | Coupon name only (no change) |
| Order cancelled, status = 1, 2, 3, 5, or 6 | Coupon name + error message mapped from `return_cd` per VpointErrorMessageService (sp201 cancel) — **red text** |
| Order cancelled, status = 4 | Coupon name + "✅ ポイント利用キャンセル済" |
| Full V-Point order (payment method = NULL) | Payment method row **not displayed** |

> - Error message derived from `dct_vpoint_redeem_result.return_cd` using VpointErrorMessageService
> - If BAT3 & BAT4 are executed, keep the error message from sp201(Cancel)
> - status read from `dct_vpoint_redeem_result.status`
> - (v25) Payment method = NULL for full V-Point orders — hide payment method row

---

## Karte Event Tracking (v4)

| Event Name | Trigger | Platform | Data Fields |
|-----------|---------|----------|-------------|
| `vpoint_exchange` | sp201 success (return_cd=00) | EC + Native | member_id, serial_no, exchange_amount, exchange_date |
| `vpoint_coupon_used` | Checkout completion / POS scan | EC + POS | order_id, coupon_amount, serial_no, usage_date |

- **EC**: Twig tracker template fires `krt('send', 'vpoint_exchange', {...})`
- **Native**: Backend returns `karte_event` payload in API JSON; mobile fires client-side
- **POS**: POS API response triggers Karte event on coupon barcode scan

---

## Return Code Classification (Quick Reference)

### sp201 Redemption Response (point_kbn=73, v23)

> Code Type 3 does NOT trigger sp201 Cancel — points were NOT deducted.

| Type | Codes | Status | Action |
|------|-------|--------|--------|
| 1 | 00 | 4 | Success — issue coupon |
| 2 | 04, 98 | 6 | Show error; wait for BAT3 (SPxxx recovery) |
| 3 | 05,10,11,14,15,16,17,18,22,23,41-44,52,53,80,90,92,99 | 5 | Show error MSG only (NO sp201 Cancel needed) |

### sp201 Cancel Response (point_kbn=74, v23)

| Type | Codes | Status | Action |
|------|-------|--------|--------|
| 1 | 00 | 4 | Cancel success |
| 2 | 04,11,16,18,80,92,98,99 | 6 | Show error; wait for BAT3 (SPxxx recovery) |
| 3 | 05,10,14,15,17,22,23,41-44,52,53,90 | 5 | Show error; cancel without connecting V-Point |

### sp101 Response

| Type | Codes | Action |
|------|-------|--------|
| 1 | 00 | Display balance |
| 2 | All others (04,10,14,16,18,22,23,80,90,92,93,94,98,99) | Display ＊＊＊＊pt |

---

## Status Transition Case Matrix

| Case | Flow | status | Record Action |
|------|------|--------|---------------|
| 1 | Redemption/Cancel → sp201 CodeType 1 (return_cd=00) | 4 | UPDATE type=1 row |
| 2 | Redemption/Cancel → sp201 CodeType 3 (show error only) | 5 | UPDATE type=1 row |
| 3 | Redemption/Cancel → sp201 CodeType 2 (timeout/HTTP error) → waiting for BAT3 | 6 | UPDATE type=1 row |
| 4 | BAT3 executed → SPxxx file created → waiting for BAT4 (SExxx) | 3 | **INSERT new type=2 row** (same serial_no) |
| 5 | BAT4 → No error_cd in SExxx → success | 4 | UPDATE type=2 row |
| 6 | BAT4 → error_cd ∈ {521..550 resend list} → eligible for resend | 6 | UPDATE type=2 row (BAT3 picks up again) |
| 7 | BAT4 → Other error_cd → not resolvable | remains as-is | UPDATE type=2 row (admin investigation) |
| 8 | Admin Refund → status 0→1→2 → BAT5 picks → sp201 cancel → follows cancel flow | 2→4/5/6 | UPDATE type=1 row |
| 9 | Checkout: redemption OK + GMO payment NG → status 4→7 → sp201 cancel | 7→follows cancel flow | INSERT cancel type=1 row |

---

## Error Messages — Complete Reference (for VpointErrorMessageService)

### sp101 Error Messages

| Code | JP Message |
|------|-----------|
| 00 | — (Normal) |
| 04 | エラーが発生したため、Vポイントの利用ができません。（04） |
| 10 | このカードは利用できません。（10） |
| 11 | このカードは利用できません。（11） |
| 14 | このカードはVポイントが利用できません（14） |
| 16 | エラーが発生したため、Vポイントの利用ができません。（16） |
| 18 | エラーが発生したため、Vポイントの利用ができません。（18） |
| 22 | — (No linkage information — card linkage only) |
| 23 | エラーが発生したため、Vポイントの利用ができません。（23） |
| 80 | システムメンテナンス中のため、Vポイントの利用ができません。（80） |
| 90 | エラーが発生したため、Vポイントの利用ができません。（90） |
| 92 | エラーが発生したため、Vポイントの利用ができません。（92） |
| 93 | — (Barcode conversion error — card linkage only) |
| 94 | — (Barcode conversion error/expired — card linkage only) |
| 98 | エラーが発生したため、Vポイントの利用ができません。（タイムアウト） |
| 99 | エラーが発生したため、Vポイントの利用ができません。（99） |

**Fallback:** If sp101 cannot get balance → display **＊＊＊＊pt**

### sp201 Error Messages

| CodeType | Code | JP Message |
|----------|------|-----------|
| 1 | 00 | — (Normal) |
| 2 | 04 | エラーが発生したため、Vポイントの利用ができません。（04） |
| 3 | 05 | エラーが発生したため、Vポイントの利用ができません。（05） |
| 3 | 10 | エラーが発生したため、Vポイントの利用ができません。（10） |
| 3 | 11 | エラーが発生したため、Vポイントの利用ができません。（11） |
| 3 | 14 | エラーが発生したため、Vポイントの利用ができません。（14） |
| 3 | 16 | エラーが発生したため、Vポイントの利用ができません。（16） |
| 3 | 17 | Vポイントが足りません。（17） |
| 3 | 18 | エラーが発生したため、Vポイントの利用ができません。（18） |
| 3 | 22 | エラーが発生したため、Vポイントの利用ができません。（22） |
| 3 | 23 | エラーが発生したため、Vポイントの利用ができません。（23） |
| 3 | 80 | システムメンテナンス中のため、Vポイントの利用ができません。（80） |
| 3 | 90 | エラーが発生したため、Vポイントの利用ができません。（90） |
| 3 | 92 | エラーが発生したため、Vポイントの利用ができません。（92） |
| 3 | 99 | エラーが発生したため、Vポイントの利用ができません。（99） |
| 2 | 98 | エラーが発生したため、Vポイントの利用ができません。（タイムアウト） |
| — | HTTP≠200 | エラーが発生したため、Vポイントの利用ができません。（xx） |
| — | Other | エラーが発生したため、Vポイントの利用ができません。（xx） |

### sp201 Cancel Error Messages

| CodeType | Code | JP Message | Action |
|----------|------|-----------|--------|
| 1 | 00 | — | status=4 |
| 2 | 04 | ご利用頂いたVポイントは翌日以降に戻ります。（04） | status=6; BAT3 recovery |
| 2 | 11 | 利用できないカードのため、利用ポイントのキャンセルができませんでした。（11） | status=6; BAT3 recovery |
| 2 | 16 | ご利用頂いたVポイントは翌日以降に戻ります。（16） | status=6; BAT3 recovery |
| 2 | 18 | ご利用頂いたVポイントは翌日以降に戻ります。（18） | status=6; BAT3 recovery |
| 2 | 80 | ご利用頂いたVポイントは翌日以降に戻ります。（80） | status=6; BAT3 recovery |
| 2 | 92 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（92） | status=6; BAT3 recovery |
| 2 | 98 | ご利用頂いたVポイントは翌日以降に戻ります。（タイムアウト） | status=6; BAT3 recovery |
| 2 | 99 | ご利用頂いたVポイントは翌日以降に戻ります。（99） | status=6; BAT3 recovery |
| 2 | HTTP≠200 | ご利用頂いたVポイントは翌日以降に戻ります。（xx） | status=6; BAT3 recovery |
| 2 | Other undefined | ご利用頂いたVポイントは翌日以降に戻ります。（xx） | status=6; BAT3 recovery |
| 3 | 05 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（05） | status=5 |
| 3 | 10 | 利用できないカードのため、利用ポイントのキャンセルができませんでした。（10） | status=5 |
| 3 | 14 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（14） | status=5 |
| 3 | 15 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（15） | status=5 |
| 3 | 17 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（17） | status=5 |
| 3 | 22 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（22） | status=5 |
| 3 | 23 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（23） | status=5 |
| 3 | 41 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（41） | status=5 |
| 3 | 43 | エラーが発生しました。ご注文時にご利用頂いたVポイントのうち、有効期限が切れているVポイントはお戻しができませんでした。（43） | status=5 |
| 3 | 53 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（53） | status=5 |
| 3 | 90 | エラーが発生しました。利用ポイントのキャンセルができませんでした。（90） | status=5 |

### Slack Alert Messages

| Event | Message |
|-------|---------|
| BAT1 no file | "WARN: SMCC file not received in 10:00–11:00 window" |
| BAT2 complete | "BAT2: {success} success, {errors} errors" |
| BAT3 SP created | "BAT3: SPxxxxxx created with {N} records" |
| BAT3 merge | "BAT3: Merged day N + N+1 ({total} records)" |
| BAT3 validation warning | "BAT3 WARN: {N} records excluded from SPxxxxxx — validation checks 4-6/9-11 failed" |
| BAT3 retrieval warning | "BAT3 WARN: CCCMK did not retrieve SPxxxxxx within expected window — merge mode active for next run" |
| BAT4 result | "BAT4: {success}/{total} records recovered" |
| SFTP error | "ERROR: SMCC SFTP connection failed: {details}" |

---

## Key Constants

| Constant | Value |
|----------|-------|
| Coupon master ID | 999999990001 |
| point_kbn (usage) | 73 |
| point_kbn (cancel) | 74 |
| Service ID (Native) | A03 |
| Service ID (EC) | A04 |
| gyotai_cd | 00000001 (fixed) |
| kaiin_id_kbn | 10 (Site ID, fixed) |
| ninsho_kbn | 0 (fixed) |
| register_no | 000001 (fixed, 6 chars) |
| cancel_kbn | 0 (full cancellation) |
| uriage_kin | 0 (fixed) |
| Exchange rate | 1 pt = ¥1 |
| Birthday attempts | 3 max |
| Cancel retries | 0 (single attempt; v23) |
| Admin cancel window | 365 days |
| Monthly exchange limit | 30,000 pt (net; canceled points restore limit; v25) |
| sp101 timeout | 3 seconds |
| SP record length | 783 bytes |
| SE record length | 794 bytes |
| SP encoding | Shift_JIS (CP932) |
| SP header record_type | `@@HEADER@@` (10 chars) |
| SP header data_id | `SPCOMMON` (8 chars) |
| SP header record_length | `0781` (fixed) |
| SP file naming | `URIxxxxSPyy.DAT` (xxxx=Alliance Code) |
| S3 encryption | AES-256-SSE |
| BAT4 resendable error_cds (→status=6) | 521-527, 536-538, 550 |
| BAT4 EDI PROD | `https://edi.tpoint.jp/adi010.do` |
| BAT4 EDI STG | `https://stg.edi.tpoint.jp/adi010.do` |
| SP S3 bucket | `mrmax-prod-apn1-SP` |
| SE S3 bucket | `mrmax-prod-apn1-SE` |

---

## Structured Logging Fields (T18)

| Operation | Log Fields |
|-----------|------------|
| sp101 | Trigger, Program name, Member ID, Serial Number, Point balance, Return code, Timestamp, request_id, duration_ms |
| sp201 | Trigger, Program name, Member ID, Serial Number, Before/After balance, Deduct amount, Return code, Timestamp, request_id, duration_ms |
| Coupon issue | Trigger, Program name, Member ID, Serial Number, Coupon target ID, Result, Timestamp |
| BAT3/BAT4 | Program name, Body count, Return code, Timestamp, file_name, records_processed |

---

## Open Items

| # | Item | Impact | Status |
|---|------|--------|--------|
| Q1 | Temp coupon reservation TTL (session/Redis) | Cleanup design | Open |
| Q2 | Payment method for full V-Point orders | `dtb_order` consistency | Open |
| Q3 | CouponDiscountProcess dual-mode (session vs DB) | T10 implementation | Open |
| Q4 | sp101 re-check balance reduced — auto-adjust or reject? | UX decision | Open |
| Q8 | Coupon hard-delete vs soft-delete on cancel | Data retention | Open |
| Q12 | V-Point coupon visual badge in history | Frontend design | Open |
| Q13 | Karte event naming convention | Analytics dashboard | Open |

### Known CRITICAL Gaps (from Gap Analysis)

| Gap | Description | Impact |
|-----|-------------|--------|
| Reissue for unlinked cards | What happens if type=40 reissue arrives but card is already unlinked? | BAT2 edge case |
| Minimum exchange amount | Is there a minimum V-Point exchange (e.g., ¥100)? Or can user enter any amount? | Validation rule |
| Session abandonment after sp201 | If user closes browser after sp201 OK but before GMO — coupon issued but order not placed | Orphaned coupon |

> **Full gap analysis:** `docs/CR5-Gap-Analysis-Queries.md` (46 queries with severity, impact, recommended workshops)
