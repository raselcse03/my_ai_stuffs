# Work Breakdown Structure — JIRA Import Ready
## CR5 — V-Point & Credit Card Linkage Integration

**Generated:** 2026-05-12
**Source:** SRS-CR5-Requirement-Specification.md
**Total Stories:** 15
**Total Story Points:** 86
**Total Sprints:** 5

---

## Epic: CR5 — V-Point & Credit Card Linkage Integration

**Epic Description:**
> Integrate SMCC credit card membership with the MrMax EC platform, enabling card linkage via barcode scan, V-Point redemption (loyalty points to digital coupons), real-time API integration with CCCMK (sp101/sp201), and daily SFTP/HTTPS file transfers targeting 600,000 members.

---

### Story 1: V-Point Database Foundation & Entities

**Type:** Story | **Priority:** H | **Points:** 5 | **Sprint:** 1

#### Summary
Create all new database tables, entity classes, and repositories required for V-Point integration. This is the foundational story that every other CR5 story depends on — it establishes `dct_vpoint_redeem_result` (sp201 transaction log), `dct_vpoint_exchanges` (exchange denominations), `dtb_customer_card_info` (card linkage), `dtb_affiliated_card_info` (SMCC card master), `dtb_card_application_info` (import tracking), and adds `serial_no` to the existing `dct_coupon_target` table.

#### Requirement Details
Implements the database schema defined in SRS Sections 3.1–3.5, including all table definitions, column types, constraints, indexes, and seed data. The `dct_vpoint_redeem_result` table (31 columns) stores sp201 API request/response data for admin display and BAT3/BAT4 recovery. The `dct_vpoint_exchanges` table stores the 9 configurable exchange denominations. The `dtb_customer_card_info` table enforces a constraint of only 1 active (`is_valid=1`) linkage per `app_member_id`. The `serial_no` format follows `[ServiceID:3]+[YYMMDD(JST):6]+[Sequence:11]` with A03=Native, A04=EC prefixes.

- **Linked Requirements:** SRS Section 3.1 (dct_vpoint_redeem_result), Section 3.2 (dtb_customer_card_info), Section 3.3 (dtb_affiliated_card_info), Section 3.4 (dtb_card_application_info), Section 3.5 (ext_attr_text3), T1, T2, T3
- **Affected Components:** `app/Customize/Entity/`, `app/Customize/Repository/`, `schema/`
- **Scope:** Backend

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Database Foundation

#### Acceptance Criteria
- [ ] **Given** the database schema SQL is executed, **When** I inspect the database, **Then** `dct_vpoint_redeem_result` exists with all 31 columns, correct data types, NOT NULL constraints, and composite unique key on `(serial_no, retry_cnt, point_kbn)`
- [ ] **Given** the `dct_vpoint_exchanges` table is created and seeded, **When** I query the table, **Then** 9 rows exist with amounts ¥100, ¥300, ¥500, ¥1000, ¥3000, ¥5000, ¥10000, ¥30000, ¥50000
- [ ] **Given** a new `dtb_customer_card_info` record is inserted with `is_valid=1`, **When** a second record for the same `app_member_id` is inserted with `is_valid=1` without unsetting the first, **Then** the application-level constraint prevents duplicate active linkages
- [ ] **Given** `dtb_affiliated_card_info` is created, **When** I inspect the schema, **Then** all 30+ columns match the SMCC specification (customer_number, member_group_number, mrmax_id, data_type, name fields, etc.)
- [ ] **Given** `dtb_card_application_info` is created, **When** I insert an import record, **Then** the `data_type`, `record_count`, and `error_count` are stored correctly
- [ ] **Given** the `dct_coupon_target` ALTER is applied, **When** I inspect the table, **Then** a nullable `serial_no VARCHAR(20)` column exists
- [ ] **Given** the Entity classes are created, **When** `bin/console cache:clear` is run, **Then** no Doctrine mapping errors occur
- [ ] **Given** Repository classes are created, **When** they are injected via DI, **Then** basic CRUD operations (find, persist, flush) work on all new entities

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| None | — | This is the foundation story; no upstream dependencies |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | `serial_no` generated at exact midnight JST boundary | Date component reflects the correct JST calendar day, not UTC |
| 2 | Concurrent insert of two `is_valid=1` records for same `app_member_id` | Application-level lock/check prevents race condition; only one succeeds |
| 3 | `dct_vpoint_exchanges` amounts modified after coupons already issued | Existing coupons retain their original amounts; only new exchanges use updated config |
| 4 | `dtb_affiliated_card_info` record with 30+ columns containing max-length data | All columns can store full-length values without truncation |
| 5 | `serial_no` sequence rollover at 99999999999 | Extremely unlikely (>99B per day per prefix) — log warning if within 1% of max |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Schema misalignment with SMCC spec for `dtb_affiliated_card_info` | Medium | High | Cross-reference against `dtb_affiliated_card_info.pdf`; validate column count/types |
| Entity proxy cache invalidation issues | Low | Medium | Run `bin/console eccube:generate:proxies` after entity creation |
| Column type mismatch between Entity ORM mapping and SQL | Low | High | Add unit test verifying Doctrine schema validation passes |

#### Notes / Additional Information
- Manual SQL only — NO Doctrine migrations. SQL scripts go in `schema/` directory.
- `dtb_customer.ext_attr_text3` already exists (VARCHAR 13) for `app_member_id` — verify no ALTER needed.
- The `dct_vpoint_redeem_result` composite unique key is `(serial_no, retry_cnt, point_kbn)` per SRS.
- `cancel_status` default is `0` (Not applied).
- `program_name` values: 1=sp201, 2=sp201(Cancel), 3=BAT3, 4=BAT4, 5=Manual.

---

#### Sub-tasks:

##### Sub-task 1.1: Create SQL Schema Scripts for All New Tables
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Write manual SQL DDL scripts in `schema/` directory for:
- `CREATE TABLE dct_vpoint_redeem_result` with all 31 columns, indexes on `app_member_id`, `serial_no`, `cancel_status`, and composite unique key on `(serial_no, retry_cnt, point_kbn)`
- `CREATE TABLE dct_vpoint_exchanges` with `INSERT` for 9 seed rows
- `CREATE TABLE dtb_customer_card_info` with 12 columns
- `CREATE TABLE dtb_affiliated_card_info` with 30+ columns per SMCC spec
- `CREATE TABLE dtb_card_application_info` with 6 columns
- `ALTER TABLE dct_coupon_target ADD serial_no VARCHAR(20) NULL`

- **Affected Files:** `schema/cr5_vpoint_tables.sql`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] All 5 CREATE TABLE + 1 ALTER TABLE + 9 INSERT statements validated against MySQL 8.x
  - [ ] Column types, sizes, and defaults match SRS Sections 3.1–3.4 exactly
  - [ ] SQL executes cleanly on a fresh database
  - [ ] Composite unique key enforced on `dct_vpoint_redeem_result(serial_no, retry_cnt, point_kbn)`

---

##### Sub-task 1.2: Create VpointRedeemResult Entity & Repository
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create Doctrine Entity `app/Customize/Entity/VpointRedeemResult.php` mapping all 31 columns of `dct_vpoint_redeem_result`. Follow existing EC-Cube entity patterns (see `Coupon.php`, `CouponTarget.php`). Use `@ORM\Table`, `@ORM\Column` annotations with correct types. Include `@ORM\HasLifecycleCallbacks()` and `discriminator_type`. Create corresponding repository `app/Customize/Repository/VpointRedeemResultRepository.php` extending `AbstractRepository`. Add finder methods: `findByAppMemberId()`, `findBySerialNo()`, `findByCancelStatus()`, `findPendingForBat3()`.

- **Affected Files:** `app/Customize/Entity/VpointRedeemResult.php`, `app/Customize/Repository/VpointRedeemResultRepository.php`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] Entity maps all 31 columns with correct ORM annotations
  - [ ] Repository registered in Symfony DI container
  - [ ] `bin/console cache:clear` succeeds without mapping errors
  - [ ] Basic CRUD operations verified via unit test

---

##### Sub-task 1.3: Create VpointExchange Entity, Repository & Seed Data
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Create Entity `app/Customize/Entity/VpointExchange.php` for `dct_vpoint_exchanges` table with columns: `id`, `amount` (INT), `label` (VARCHAR), `sort_order` (INT), `is_active` (TINYINT), `create_date`, `update_date`. Create Repository `app/Customize/Repository/VpointExchangeRepository.php` with `findAllActiveSorted()` method returning denominations sorted ascending. Verify the 9 seed rows (¥100, ¥300, ¥500, ¥1,000, ¥3,000, ¥5,000, ¥10,000, ¥30,000, ¥50,000) load correctly.

- **Affected Files:** `app/Customize/Entity/VpointExchange.php`, `app/Customize/Repository/VpointExchangeRepository.php`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] Entity and Repository created with proper DI registration
  - [ ] `findAllActiveSorted()` returns 9 rows in ascending order
  - [ ] Cache clear succeeds

---

##### Sub-task 1.4: Create CustomerCardInfo Entity & Repository
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Create Entity `app/Customize/Entity/CustomerCardInfo.php` for `dtb_customer_card_info` (12 columns). Include: `id`, `appMemberId` (VARCHAR 13), `customerNumber` (VARCHAR 16), `memberGroupNumber` (VARCHAR 16), `mrmaxId` (VARCHAR 16), `cardLinkagedDt` (DATETIME nullable), `cardDislinkagedDt` (DATETIME nullable), `isValid` (TINYINT default 0), `isCardCancelled` (TINYINT default 0), `birthday` (VARCHAR 8), `createDate`, `updateDate`. Create Repository `app/Customize/Repository/CustomerCardInfoRepository.php` with methods: `findActiveByAppMemberId()`, `findByCustomerNumber()`, `deactivateAllForMember()`.

- **Affected Files:** `app/Customize/Entity/CustomerCardInfo.php`, `app/Customize/Repository/CustomerCardInfoRepository.php`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] Entity enforces single `is_valid=1` per `app_member_id` at application level
  - [ ] `findActiveByAppMemberId()` returns at most 1 record
  - [ ] `deactivateAllForMember()` sets all `is_valid=0` for given `app_member_id`
  - [ ] All datetime columns use proper timezone handling

---

##### Sub-task 1.5: Create AffiliatedCardInfo Entity & Repository
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create Entity `app/Customize/Entity/AffiliatedCardInfo.php` for `dtb_affiliated_card_info` with 30+ columns per SMCC spec (customer_number, member_group_number, mrmax_id, data_type, member_name_kanji, member_name_kana, sex, birthday, postal_code, address fields, phone, card_expiry_date, member_type, application_date, various status flags, create_date, update_date). Create Repository `app/Customize/Repository/AffiliatedCardInfoRepository.php` with methods: `findByMrmaxId()`, `findByCustomerNumber()`, `findByDataType()`.

- **Affected Files:** `app/Customize/Entity/AffiliatedCardInfo.php`, `app/Customize/Repository/AffiliatedCardInfoRepository.php`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] All 30+ columns mapped with correct ORM annotations
  - [ ] Repository supports filtering by data_type, mrmax_id, customer_number
  - [ ] Column names match SMCC specification exactly
  - [ ] Cache clear succeeds without mapping errors

---

##### Sub-task 1.6: Create CardApplicationInfo Entity & Repository
**Type:** Sub-task | **Estimate:** 1h | **Skill:** Backend

**Description:**
Create Entity `app/Customize/Entity/CardApplicationInfo.php` for `dtb_card_application_info` with columns: `id`, `importDate` (DATE), `dataType` (VARCHAR), `recordCount` (INT), `errorCount` (INT), `createDate` (DATETIME). Create Repository `app/Customize/Repository/CardApplicationInfoRepository.php` with `findByImportDate()` and `findByDataType()`.

- **Affected Files:** `app/Customize/Entity/CardApplicationInfo.php`, `app/Customize/Repository/CardApplicationInfoRepository.php`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] Entity and Repository follow existing patterns
  - [ ] `findByImportDate()` filters correctly by date range

---

##### Sub-task 1.7: Modify CouponTarget Entity — Add serial_no Column
**Type:** Sub-task | **Estimate:** 1h | **Skill:** Backend

**Description:**
Add `serial_no` property to existing `app/Customize/Entity/CouponTarget.php` with `@ORM\Column(name="serial_no", type="string", length=20, nullable=true)`. Add getter/setter methods. Do NOT remove or modify any existing properties.

- **Affected Files:** `app/Customize/Entity/CouponTarget.php`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] `serial_no` column mapped as nullable VARCHAR(20)
  - [ ] Getter `getSerialNo()` and setter `setSerialNo()` added
  - [ ] Existing CouponTarget functionality unaffected
  - [ ] Proxy regeneration succeeds: `bin/console eccube:generate:proxies`

---

##### Sub-task 1.8: Register Entities in Doctrine Configuration
**Type:** Sub-task | **Estimate:** 1h | **Skill:** Backend

**Description:**
Ensure all new entities are discoverable by Doctrine ORM. Verify `app/config/eccube/packages/doctrine.yaml` includes `app/Customize/Entity/` in entity mappings. Run `bin/console eccube:generate:proxies` to create proxy classes. Verify `bin/console cache:clear` succeeds and Doctrine schema validation reports no issues for new entities.

- **Affected Files:** `app/config/eccube/packages/doctrine.yaml`, `app/proxy/`
- **Parent Story:** Story 1
- **Definition of Done:**
  - [ ] All 5 new entities discovered by Doctrine
  - [ ] Proxy classes generated successfully
  - [ ] `cache:clear` completes without errors

---

### Story 2: CCCMK API Client & Encryption

**Type:** Story | **Priority:** H | **Points:** 5 | **Sprint:** 1

#### Summary
Build the CCCMK V-Point API client service supporting sp101 (balance inquiry) and sp201 (point usage/cancel) operations, along with the AES-256-CBC encryption service required for secure parameter transmission. This client handles request construction, encryption, HTTP communication with the CCCMK V-Point server, response parsing, error code mapping to Japanese messages, timeout handling (3s for sp101), and sp201 cancel retry logic (max 2 retries).

#### Requirement Details
Implements SRS Section 5.1 (AES-256-CBC encryption with MD5 key expansion), the sp101 balance inquiry API (16 return codes), sp201 point usage (point_kbn=73) and cancel (point_kbn=74) APIs, and the error message mapping service (31+ codes → Japanese messages). The encryption uses a CCCMK-issued key with MD5 expansion, PKCS5Padding, fixed IV, and base64+URL encoding. The test vector must produce `OZwiVXUG6xvb51YHjG4XC/1l2DrMWW2dGyBTYPgxPoQ=` from plaintext `1234567890123450`.

- **Linked Requirements:** SRS Section 5.1 (Encryption), Section 2.4 (sp101 sequence), Section 2.5 (sp201 sequence), Section 7 (Error Messages), T4, T16
- **Affected Components:** `app/Customize/Service/Vpoint/`
- **Scope:** Backend

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** V-Point API Infrastructure

#### Acceptance Criteria
- [ ] **Given** plaintext `1234567890123450`, key `ABCDEF0123456789abcdef0123456789`, IV `abcdefghABCDEFGH`, **When** `VpointEncryptionService::encrypt()` is called, **Then** the output equals `OZwiVXUG6xvb51YHjG4XC/1l2DrMWW2dGyBTYPgxPoQ=` (base64)
- [ ] **Given** the above ciphertext, **When** `VpointEncryptionService::decrypt()` is called, **Then** the output equals `1234567890123450`
- [ ] **Given** valid encrypted parameters, **When** `VpointApiClient::balanceInquiry()` is called, **Then** the request hits the sp101 endpoint with a 3-second timeout and returns parsed return code + balance
- [ ] **Given** a successful sp201 point usage call, **When** the response return_cd is `00`, **Then** the client returns success with deducted point amount
- [ ] **Given** an sp201 call that fails with timeout (return_cd=04/98), **When** cancel is triggered, **Then** the client retries cancel up to 2 times with incrementing `retry_cnt` (0→1→2)
- [ ] **Given** any sp101/sp201 return code, **When** `VpointErrorMessageService::getMessage()` is called, **Then** the correct Japanese error message string is returned per SRS Section 7
- [ ] **Given** sp101 returns a non-00 code and no balance can be retrieved, **When** the balance display is rendered, **Then** `＊＊＊＊pt` is shown
- [ ] **Given** all cancel retries fail, **When** the last retry completes, **Then** `cancel_status` is set to `3` (Processing) for BAT3/BAT4 recovery

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` entity required for storing sp201 results |
| CCCMK credentials | External | Alliance code, password, encryption key, IV must be provided by CCCMK |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | sp101 timeout at exactly 3 seconds | Request is cancelled; error message displayed; no partial data processed |
| 2 | sp201 response received but network drops before full body | Treat as timeout; trigger cancel flow |
| 3 | Encryption key contains non-ASCII characters | MD5 expansion handles raw bytes correctly |
| 4 | sp201 cancel succeeds on retry 1 after initial failure | `cancel_status=4` (Completed); no further retries |
| 5 | sp201 called with amount > actual balance (race condition) | Return code indicates insufficient points; no deduction occurs |
| 6 | Concurrent sp201 calls for same member with same serial_no | Server rejects with code 05 (duplicate); client handles gracefully |
| 7 | Base64 output contains `+`, `/`, `=` characters | URL-encoding applied correctly: `+`→`%2b`, `/`→`%2f`, `=`→`%3d` |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CCCMK test environment unavailable or unreliable | Medium | High | Create mock server for development; integration test against staging |
| Encryption key expansion differs from CCCMK's Java implementation | Low | Critical | Validate with provided test vector before any API calls |
| sp201 cancel retry logic creates duplicate cancellations | Low | High | Use unique `(serial_no, retry_cnt, point_kbn)` key; server-side idempotency |

#### Notes / Additional Information
- CCCMK PROD endpoint: `https://api.tpoint.jp/sp101.do` (balance), `https://api.tpoint.jp/sp201.do` (usage/cancel)
- MD5 key expansion: take CCCMK key → MD5 hash → repeat until 32 bytes
- point_kbn: 73=usage, 74=cancel
- cancel_kbn: 0=full cancellation
- Structured logging required for every sp101/sp201 call (trigger, program_name, member_id, serial_no, return_cd, timestamp)

---

#### Sub-tasks:

##### Sub-task 2.1: Implement VpointEncryptionService
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/VpointEncryptionService.php` implementing AES-256-CBC encryption with:
1. MD5 key expansion: `$key → md5($key, true)` repeated to 32 bytes
2. `encrypt($plaintext)`: AES-256-CBC + PKCS5Padding + base64 encode
3. `decrypt($ciphertext)`: base64 decode + AES-256-CBC decrypt + PKCS5 unpad
4. `encryptForUrl($plaintext)`: encrypt + urlencode
5. Constructor injects key and IV from environment variables (`CCCMK_ENCRYPTION_KEY`, `CCCMK_ENCRYPTION_IV`)
6. Validate with test vector from SRS Section 5.1

- **Affected Files:** `app/Customize/Service/Vpoint/VpointEncryptionService.php`
- **Parent Story:** Story 2
- **Definition of Done:**
  - [ ] Test vector produces exact expected ciphertext
  - [ ] Encrypt→Decrypt round-trip preserves original plaintext
  - [ ] URL encoding handles `+`, `/`, `=` correctly
  - [ ] Unit test covers all edge cases (empty string, max-length input, multibyte)

---

##### Sub-task 2.2: Implement VpointApiClient — sp101 Balance Inquiry
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/VpointApiClient.php` with method `balanceInquiry(string $kaiinId, string $allianceCd, string $passwd): array`. The method must:
1. Encrypt `kaiin_id` using `VpointEncryptionService`
2. Build HTTP GET request to sp101 endpoint with encrypted params
3. Set timeout to 3 seconds
4. Parse response (return_cd, balance, etc.)
5. Log request/response with structured format (SRS Section 7 logging requirements)
6. Return `['return_cd' => string, 'balance' => int|null, 'raw_response' => array]`
7. Handle all 16 sp101 return codes

Use Symfony `HttpClientInterface` for HTTP calls (DI-injected). Endpoint URL from env `CCCMK_SP101_URL`.

- **Affected Files:** `app/Customize/Service/Vpoint/VpointApiClient.php`
- **Parent Story:** Story 2
- **Definition of Done:**
  - [ ] Successful balance inquiry returns parsed balance amount
  - [ ] 3-second timeout enforced; timeout returns error gracefully
  - [ ] All 16 return codes handled without exceptions
  - [ ] Structured log entry written for every API call

---

##### Sub-task 2.3: Implement VpointApiClient — sp201 Point Usage & Cancel
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Add methods to `VpointApiClient.php`:
1. `pointUsage(array $params): array` — sp201 call with `point_kbn=73`. Params include: `alliance_cd`, `passwd`, `gyotai_cd`, `tenpo_cd`, `kaiin_id_kbn`, `kaiin_id`, `serial_no`, `shori_date`, `shori_time`, `eigyou_date`, `register_no`, `denpyo_no`, `point_kbn=73`, `cancel_kbn=0`, `kangen_point`, `uriage_kin=0`
2. `cancelUsage(array $params): array` — sp201 call with `point_kbn=74`, `cancel_kbn=1`, `moto_date`, `moto_serial_no`
3. `cancelWithRetry(array $params, int $maxRetries = 2): array` — wraps `cancelUsage` with retry logic, incrementing `retry_cnt` (0→1→2). Updates `dct_vpoint_redeem_result` after each attempt. If all retries fail, returns failure indicator for BAT3/BAT4 recovery.

Inject `VpointRedeemResultRepository` for DB operations. Encrypt `kaiin_id` before sending.

- **Affected Files:** `app/Customize/Service/Vpoint/VpointApiClient.php`
- **Parent Story:** Story 2
- **Definition of Done:**
  - [ ] sp201 usage call sends all required parameters correctly
  - [ ] sp201 cancel call includes `moto_date` and `moto_serial_no` from original usage
  - [ ] Retry logic increments `retry_cnt` and stops at max 2
  - [ ] `dct_vpoint_redeem_result.return_cd` updated after each API response
  - [ ] All 9 sp201 return codes and 6 sp201 cancel return codes handled

---

##### Sub-task 2.4: Implement VpointErrorMessageService
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/VpointErrorMessageService.php` with:
1. `getMessageForSp101(string $returnCd): string` — maps 16 sp101 return codes to Japanese messages
2. `getMessageForSp201(string $returnCd): string` — maps 9 sp201 return codes to Japanese messages
3. `getMessageForSp201Cancel(string $returnCd): string` — maps 6 sp201 cancel return codes to Japanese messages
4. `getCodeType(string $returnCd): int` — classifies return codes into Type 1/2/3 per SRS Section 7 response routing table

Messages stored as constants or loaded from translation files. Examples:
- sp201 code `05` → `エラーが発生したため、Vポイントの利用ができません。（05）`
- sp101 failure → display `＊＊＊＊pt`

- **Affected Files:** `app/Customize/Service/Vpoint/VpointErrorMessageService.php`
- **Parent Story:** Story 2
- **Definition of Done:**
  - [ ] All 31+ error codes mapped to correct Japanese messages per SRS
  - [ ] Code type classification matches SRS response routing table
  - [ ] No unmapped return codes — unknown codes return generic error message

---

##### Sub-task 2.5: Register Vpoint Services in DI Container
**Type:** Sub-task | **Estimate:** 1h | **Skill:** Backend

**Description:**
Register all new Vpoint services in `app/config/eccube/packages/services.yaml` or verify auto-wiring:
- `Customize\Service\Vpoint\VpointEncryptionService` (inject CCCMK_ENCRYPTION_KEY, CCCMK_ENCRYPTION_IV from env)
- `Customize\Service\Vpoint\VpointApiClient` (inject VpointEncryptionService, HttpClientInterface, VpointRedeemResultRepository)
- `Customize\Service\Vpoint\VpointErrorMessageService`

Add environment variables to `.env` / `.env.dist`: `CCCMK_ENCRYPTION_KEY`, `CCCMK_ENCRYPTION_IV`, `CCCMK_SP101_URL`, `CCCMK_SP201_URL`, `CCCMK_ALLIANCE_CD`, `CCCMK_PASSWD`.

- **Affected Files:** `app/config/eccube/packages/services.yaml`, `.env.dist`
- **Parent Story:** Story 2
- **Definition of Done:**
  - [ ] All services injectable via Symfony autowiring
  - [ ] Environment variables documented in `.env.dist`
  - [ ] `bin/console cache:clear` succeeds
  - [ ] Services instantiate without missing-dependency errors

---

##### Sub-task 2.6: Unit Tests for Encryption & API Client
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create unit tests in `codeception/unit/` or `tests/`:
1. `VpointEncryptionServiceTest.php` — test encrypt/decrypt with SRS test vector, round-trip, URL encoding, edge cases
2. `VpointApiClientTest.php` — mock HTTP responses for sp101/sp201, test timeout handling, retry logic, all return codes
3. `VpointErrorMessageServiceTest.php` — verify all error code → message mappings

- **Affected Files:** `tests/Unit/Service/Vpoint/VpointEncryptionServiceTest.php`, `tests/Unit/Service/Vpoint/VpointApiClientTest.php`, `tests/Unit/Service/Vpoint/VpointErrorMessageServiceTest.php`
- **Parent Story:** Story 2
- **Definition of Done:**
  - [ ] Test vector assertion passes
  - [ ] sp101 timeout at 3s tested
  - [ ] sp201 cancel retry logic tested with 0, 1, 2 retries
  - [ ] All error code mappings verified
  - [ ] Tests pass in CI pipeline

---

### Story 3: Card Linkage — Barcode Scan & Birthday Auth

**Type:** Story | **Priority:** H | **Points:** 5 | **Sprint:** 2

#### Summary
Implement the card linkage flow where a customer scans their SMCC credit card barcode (Code128, 8-digit), the system validates the barcode format using modulus 10 check digit (weight 2/1 from left), calls sp101 to verify the card, prompts for birthday authentication (max 3 attempts), and upon success creates a `dtb_customer_card_info` record with `is_valid=1`. This story covers the API controller endpoint, the card linkage service, barcode validation logic, birthday matching, and the frontend template for the linkage flow.

#### Requirement Details
Implements SRS Section 2.1 (Card Linkage Flow) and test cases CL-01 through CL-05. The barcode is Code128 format, 8 digits, validated with modulus 10 check digit (weight pattern 2/1 alternating from left). After barcode validation, sp101 is called to verify the card exists in the CCCMK system. On sp101 success (return_cd=00), the system prompts for birthday (YYYYMMDD format) and matches against `dtb_affiliated_card_info.birthday`. Maximum 3 birthday attempts before lockout. Only 1 valid linkage per `app_member_id` enforced. Status Decision Matrix handles data_type 10/20/30/40/50 scenarios.

- **Linked Requirements:** SRS Section 2.1 (Card Linkage Flow), Section 7.1 (Status Matrix), CL-01 to CL-05
- **Affected Components:** `app/Customize/Controller/`, `app/Customize/Service/`, `app/Customize/Entity/CustomerCardInfo.php`, `app/template/`
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Card Linkage

#### Acceptance Criteria
- [ ] **Given** a valid 8-digit barcode with correct modulus 10 check digit, **When** the customer scans it, **Then** the system accepts the barcode and proceeds to sp101 verification (CL-01)
- [ ] **Given** a barcode with incorrect check digit, **When** the customer scans it, **Then** error E93/E94 is displayed and no linkage is created (CL-02)
- [ ] **Given** sp101 returns code 00, **When** the birthday prompt is shown, **Then** the customer can enter their birthday in YYYYMMDD format
- [ ] **Given** a correct birthday matching `dtb_affiliated_card_info.birthday`, **When** submitted, **Then** a `dtb_customer_card_info` record is created with `is_valid=1` and `card_linkaged_dt` set
- [ ] **Given** an incorrect birthday, **When** the customer fails 3 attempts, **Then** the linkage is rejected with an appropriate error message (CL-03)
- [ ] **Given** the customer already has a valid linked card (`is_valid=1`), **When** they attempt to link a new card, **Then** the system prevents the linkage and shows "already linked" error (CL-04)
- [ ] **Given** a card reissue (data_type=40) occurred via BAT2, **When** the old card holder links the new card, **Then** old card `is_valid=0`, new card `is_valid=1` (CL-05)

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dtb_customer_card_info` and `dtb_affiliated_card_info` entities must exist |
| Story 2 | Blocked-by | sp101 API client needed for card verification |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | Barcode length ≠ 8 digits | Reject immediately before sp101 call |
| 2 | sp101 returns non-00 code | Show mapped error message; do not proceed to birthday |
| 3 | Birthday entered as partial (YYYY only) | Client-side validation rejects; requires full YYYYMMDD |
| 4 | Customer has `is_valid=0` records from previous unlinks | Allow re-linkage (new record with `is_valid=1`) |
| 5 | Card exists in `dtb_affiliated_card_info` but has `data_type=20` (cancelled) | Reject linkage; card is cancelled |
| 6 | Two sessions attempt linkage for same card simultaneously | First to complete wins; second gets "already linked" error |
| 7 | sp101 timeout during linkage | Show error; allow retry |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Modulus 10 check digit algorithm mismatch with barcode printer | Low | Medium | Verify against sample barcodes from SMCC |
| sp101 latency causes poor UX | Medium | Medium | 3-second timeout; loading spinner on frontend |
| Birthday data format inconsistency between systems | Low | High | Normalize to YYYYMMDD before comparison |

#### Notes / Additional Information
- Modulus 10 check digit: weight 2/1 alternating from **left**, NOT right (different from standard Luhn)
- sp101 call is required before birthday prompt — this confirms the card exists in CCCMK system
- The existing `BarcodeService.php` handles order barcodes with Luhn algorithm; this is a DIFFERENT check digit algorithm
- Template should work for both EC web (`/mypage/card-linkage`) and mobile (`/mobile/mypage/card-linkage`) routes

---

#### Sub-tasks:

##### Sub-task 3.1: Implement Barcode Validation — Modulus 10 Check Digit
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/CardLinkageService.php` with method `validateBarcode(string $barcode): array`. Implementation:
1. Verify length is exactly 8 digits
2. Apply modulus 10 check digit with weight pattern 2/1 alternating from left
3. Return `['isValid' => bool, 'cardNumber' => string|null, 'error' => string|null]`

The modulus 10 algorithm (weight 2/1 from left):
- Multiply each digit (except last) by weight (2,1,2,1,... from left)
- If product ≥ 10, sum its digits
- Sum all products
- Check digit = (10 - (sum mod 10)) mod 10
- Compare calculated check digit with last digit of barcode

- **Affected Files:** `app/Customize/Service/Vpoint/CardLinkageService.php`
- **Parent Story:** Story 3
- **Definition of Done:**
  - [ ] Valid barcode with correct check digit returns `isValid=true`
  - [ ] Invalid check digit returns `isValid=false` with error code E93/E94
  - [ ] Non-digit input rejected
  - [ ] Length ≠ 8 rejected
  - [ ] Unit test with 5+ test cases

---

##### Sub-task 3.2: Implement Card Linkage Service — sp101 + Birthday Auth
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Add methods to `CardLinkageService.php`:
1. `verifyCard(string $cardNumber): array` — calls `VpointApiClient::balanceInquiry()` with card's `customer_number` from `dtb_affiliated_card_info`. Returns sp101 result.
2. `authenticateBirthday(string $appMemberId, string $cardNumber, string $birthday, int $attempt): array` — matches birthday against `dtb_affiliated_card_info.birthday`. Tracks attempt count (max 3). Returns `['authenticated' => bool, 'attemptsRemaining' => int]`.
3. `linkCard(string $appMemberId, string $cardNumber, string $birthday): CustomerCardInfo` — creates `dtb_customer_card_info` record with `is_valid=1`, `card_linkaged_dt=now()`. Ensures no existing `is_valid=1` record for this `app_member_id`.
4. Status Decision Matrix check per data_type (10/20/30/40/50) before allowing linkage.

Inject: `VpointApiClient`, `CustomerCardInfoRepository`, `AffiliatedCardInfoRepository`.

- **Affected Files:** `app/Customize/Service/Vpoint/CardLinkageService.php`
- **Parent Story:** Story 3
- **Definition of Done:**
  - [ ] sp101 called before birthday prompt
  - [ ] Birthday comparison is exact match (YYYYMMDD)
  - [ ] 3-attempt limit enforced with remaining attempts tracked
  - [ ] Only 1 `is_valid=1` record exists after linkage
  - [ ] Status Decision Matrix applied per data_type

---

##### Sub-task 3.3: Create Card Linkage API Controller
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Full-stack

**Description:**
Create `app/Customize/Controller/Mypage/CardLinkageController.php` with routes:
1. `GET /mypage/card-linkage` + `GET /mobile/mypage/card-linkage` — render linkage page (barcode scanner + manual input)
2. `POST /mypage/card-linkage/verify` — accept barcode → validate → sp101 → return result
3. `POST /mypage/card-linkage/authenticate` — accept birthday → authenticate → return result
4. `POST /mypage/card-linkage/confirm` — create linkage record → return success

Use Symfony Form validation. CSRF protection on all POST endpoints. Return JSON for AJAX calls from frontend.

- **Affected Files:** `app/Customize/Controller/Mypage/CardLinkageController.php`
- **Parent Story:** Story 3
- **Definition of Done:**
  - [ ] All routes registered and accessible
  - [ ] CSRF protection enabled on POST endpoints
  - [ ] Input validation (barcode format, birthday format)
  - [ ] JSON responses for AJAX calls
  - [ ] Proper error handling with localized messages

---

##### Sub-task 3.4: Create Card Linkage Frontend Templates
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

**Description:**
Create Twig templates for card linkage flow:
1. `app/template/default/Mypage/card_linkage.twig` — main page with barcode scanner area (Code128), manual 8-digit input field, submit button
2. `app/template/default/Mypage/card_linkage_birthday.twig` — birthday input form with YYYYMMDD fields, attempt counter display, submit button
3. `app/template/default/Mypage/card_linkage_result.twig` — success/failure result display
4. JavaScript for AJAX flow: barcode scan → verify → birthday → confirm (no page reloads between steps)
5. Mobile-responsive layout compatible with both web and mobile routes

Follow existing template patterns from `app/template/default/Mypage/`.

- **Affected Files:** `app/template/default/Mypage/card_linkage.twig`, `app/template/default/Mypage/card_linkage_birthday.twig`, `app/template/default/Mypage/card_linkage_result.twig`
- **Parent Story:** Story 3
- **Definition of Done:**
  - [ ] Barcode scanner input accepts Code128 format
  - [ ] Birthday input validates YYYYMMDD client-side
  - [ ] Attempt counter shows remaining attempts (e.g., "残り2回")
  - [ ] Success message displays linked card info
  - [ ] Error messages displayed in Japanese per error code
  - [ ] Works on both EC web and mobile routes

---

##### Sub-task 3.5: Unit & Integration Tests for Card Linkage
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Create tests covering CL-01 through CL-05 acceptance test cases:
1. CL-01: Valid barcode + birthday → successful linkage
2. CL-02: Invalid barcode check digit → error displayed
3. CL-03: Valid barcode + wrong birthday (3 attempts) → rejected
4. CL-04: Already linked → duplicate prevention
5. CL-05: Card reissue (data_type=40) → old inactive, new active
6. Modulus 10 check digit calculation with multiple test values

- **Affected Files:** `tests/Unit/Service/Vpoint/CardLinkageServiceTest.php`
- **Parent Story:** Story 3
- **Definition of Done:**
  - [ ] All 5 CL-xx test cases pass
  - [ ] Check digit validation tested with valid/invalid inputs
  - [ ] Birthday matching tested with correct/incorrect values

---

### Story 4: Card Linkage — Unlink & Member Withdrawal

**Type:** Story | **Priority:** H | **Points:** 3 | **Sprint:** 2

#### Summary
Implement the card unlinking flow (customer-initiated) and member withdrawal handling. Unlinking requires checking for active coupons (warn the customer), code authentication, then setting `is_valid=0` and recording `card_dislinkaged_dt`. Member withdrawal extends this by also updating the withdrawal status in `dtb_customer`. Re-enrollment after withdrawal is treated as a completely new registration with a new `app_member_id`.

#### Requirement Details
Implements SRS Section 2.2 (Unlink) and Section 2.3 (Withdrawal). Unlinking flow: check if member has active V-Point coupons → if yes, display warning message → require code authentication (existing auth mechanism) → set `dtb_customer_card_info.is_valid=0`, set `card_dislinkaged_dt=now()`. Withdrawal flow: check card linkage → check active coupons → display warning → set `is_valid=0` → update `dtb_customer` withdrawal status. Test cases CL-06 (withdrawal triggers dislinkage) and CL-07 (re-enrollment = new registration).

- **Linked Requirements:** SRS Section 2.2 (Unlink Flow), Section 2.3 (Withdrawal Flow), CL-06, CL-07
- **Affected Components:** `app/Customize/Controller/Mypage/`, `app/Customize/Service/Vpoint/CardLinkageService.php`, `app/template/`
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Card Linkage

#### Acceptance Criteria
- [ ] **Given** a customer with a linked card and active V-Point coupons, **When** they initiate unlink, **Then** a warning message is shown listing the active coupons that will be affected
- [ ] **Given** a customer confirms unlinking after the warning, **When** code authentication succeeds, **Then** `dtb_customer_card_info.is_valid` is set to `0` and `card_dislinkaged_dt` is recorded
- [ ] **Given** a customer with a linked card, **When** they initiate membership withdrawal, **Then** all linked cards get `is_valid=0` and the withdrawal status is updated (CL-06)
- [ ] **Given** a withdrawn member re-enrolls, **When** they create a new account, **Then** they get a new `app_member_id` and can link a card fresh — no carryover from previous membership (CL-07)
- [ ] **Given** a customer with no linked card, **When** they try to unlink, **Then** the system shows "no card linked" message
- [ ] **Given** unlink is successful, **When** the customer views their mypage, **Then** the card linkage section shows "unlinked" status

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dtb_customer_card_info` entity required |
| Story 3 | Soft-dependency | Linkage must exist before unlinking is meaningful |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | Customer unlinks while a V-Point coupon is being used in an active checkout | Coupon remains valid for the in-progress order; unlink proceeds |
| 2 | Customer unlinks then immediately tries to re-link same card | Allowed — new `dtb_customer_card_info` record with `is_valid=1` |
| 3 | Withdrawal triggered while BAT3/BAT4 recovery is in progress for the member | Recovery continues using existing records; unlink recorded |
| 4 | Customer has multiple historical `is_valid=0` records | No impact on current unlink; new record added or last updated |
| 5 | Code authentication times out during unlink | Unlink not processed; customer must restart |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Active coupon check misses coupons in checkout pipeline | Low | Medium | Check both `dct_coupon_target` and session/Redis for in-progress coupons |
| Withdrawal process doesn't cascade to card linkage correctly | Low | High | Transaction wraps both `dtb_customer` update and card deactivation |

#### Notes / Additional Information
- Code authentication for unlink uses the existing authentication mechanism (not birthday-based)
- Active coupon check queries `dct_coupon_target` WHERE `customer_id` matches AND `coupon_id=999999990001` AND status is active AND not expired
- Withdrawal handling may need to integrate with existing withdrawal controller — check for existing hooks/events

---

#### Sub-tasks:

##### Sub-task 4.1: Implement Unlink Logic in CardLinkageService
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Add methods to `app/Customize/Service/Vpoint/CardLinkageService.php`:
1. `checkActiveCoupons(string $appMemberId): array` — query `dct_coupon_target` for active V-Point coupons (coupon_id=999999990001, not expired, not used)
2. `unlinkCard(string $appMemberId): bool` — set `is_valid=0`, record `card_dislinkaged_dt=now()` on the active `dtb_customer_card_info` record. Uses database transaction.
3. `handleWithdrawal(string $appMemberId): bool` — deactivate all linked cards for the member, then trigger existing withdrawal flow. Wraps in single transaction.

- **Affected Files:** `app/Customize/Service/Vpoint/CardLinkageService.php`
- **Parent Story:** Story 4
- **Definition of Done:**
  - [ ] `checkActiveCoupons()` returns list of active V-Point coupons
  - [ ] `unlinkCard()` sets `is_valid=0` and records `card_dislinkaged_dt`
  - [ ] `handleWithdrawal()` deactivates all cards in a transaction
  - [ ] Re-linkage allowed after unlink

---

##### Sub-task 4.2: Create Unlink Controller Actions & Routes
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Full-stack

**Description:**
Add routes to `CardLinkageController.php` (or create new controller if separation preferred):
1. `GET /mypage/card-linkage/unlink` + `GET /mobile/mypage/card-linkage/unlink` — show unlink confirmation page with active coupon warnings
2. `POST /mypage/card-linkage/unlink/confirm` — process unlink after code auth
3. Integrate with existing code authentication mechanism

- **Affected Files:** `app/Customize/Controller/Mypage/CardLinkageController.php`
- **Parent Story:** Story 4
- **Definition of Done:**
  - [ ] Active coupon warning displayed before unlink confirmation
  - [ ] Code authentication required before processing
  - [ ] CSRF protection on POST endpoints
  - [ ] Success/failure messages displayed

---

##### Sub-task 4.3: Integrate Card Deactivation into Withdrawal Flow
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Hook into the existing member withdrawal process (likely an EventListener or Controller modification) to call `CardLinkageService::handleWithdrawal()` when a member withdraws. Check for existing withdrawal controller/event subscriber in `app/Customize/Controller/Mypage/` and add the card deactivation step within the same transaction.

- **Affected Files:** `app/Customize/Controller/Mypage/` (existing withdrawal controller), `app/Customize/Service/Vpoint/CardLinkageService.php`
- **Parent Story:** Story 4
- **Definition of Done:**
  - [ ] Withdrawal triggers card deactivation for all linked cards
  - [ ] Both operations in same database transaction
  - [ ] Re-enrollment creates fresh `app_member_id` with no carryover (CL-07)

---

##### Sub-task 4.4: Create Unlink Frontend Templates
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

**Description:**
Create Twig templates:
1. `app/template/default/Mypage/card_unlink.twig` — unlink confirmation page showing:
   - Currently linked card info (masked card number)
   - Warning message if active V-Point coupons exist (list coupon names + amounts)
   - Confirmation button + cancel button
2. `app/template/default/Mypage/card_unlink_result.twig` — success/failure result

- **Affected Files:** `app/template/default/Mypage/card_unlink.twig`, `app/template/default/Mypage/card_unlink_result.twig`
- **Parent Story:** Story 4
- **Definition of Done:**
  - [ ] Active coupon warning displayed prominently
  - [ ] Card info masked for security
  - [ ] Success message on completed unlink
  - [ ] Works on both web and mobile routes

---

##### Sub-task 4.5: Unit Tests for Unlink & Withdrawal
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Create tests covering CL-06 and CL-07:
1. CL-06: Withdrawal deactivates all linked cards
2. CL-07: Re-enrollment creates new app_member_id
3. Active coupon detection test
4. Unlink with no existing linkage → graceful handling
5. Unlink followed by re-link → new record created

- **Affected Files:** `tests/Unit/Service/Vpoint/CardLinkageUnlinkTest.php`
- **Parent Story:** Story 4
- **Definition of Done:**
  - [ ] CL-06 and CL-07 test cases pass
  - [ ] Edge cases covered (no linkage, re-link after unlink)

---

### Story 5: SFTP File Import — BAT1 & BAT2

**Type:** Story | **Priority:** H | **Points:** 8 | **Sprint:** 2

#### Summary
Implement two batch processes: BAT1 retrieves SMCC credit card member files via SFTP every 30 minutes from the SMCC server, stores them in S3; BAT2 processes the stored files by converting EBCDIC(ANK)+IBM(Kanji) encoding to UTF-8, parsing fixed-length records, validating per data_type (10/20/30/40/50), importing valid records to `dtb_affiliated_card_info` and `dtb_customer_card_info`, and sending Slack notifications with CSV error attachments. Zero-record files (header-only) are valid. If no file is received during 10:00–11:00, a Slack alert is sent at 11:05.

#### Requirement Details
Implements SRS Section 2.4 (SFTP processing steps), Section 6.1 (BAT2 Import Validation), and the Status Decision Matrix for data_type 10/20/30/40/50. BAT1 connects to SMCC SFTP server (PROD port 2222), downloads files from `/mrmax-prod-apn1-smcc/smcc2ec/{DATE}/`, renames and stores in S3. BAT2 performs character encoding conversion (EBCDIC/IBM → UTF-8), validates 11 rules (file format, header, required fields, numeric/char padding, code ranges, date validation, duplicate check, correlation, field length), and imports records with partial-success semantics (invalid records excluded, valid continue). Slack notifications include success/error counts; error details attached as CSV with E14 message key as header.

- **Linked Requirements:** SRS Section 2.4 (SFTP file transfer), Section 6.1 (BAT2 validation rules), Status Decision Matrix
- **Affected Components:** `app/Customize/Command/`, `app/Customize/Service/Vpoint/`, `app/Customize/Service/FileSFTPService.php`
- **Scope:** Backend

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Batch Processing

#### Acceptance Criteria
- [ ] **Given** BAT1 is scheduled, **When** it runs every 30 minutes, **Then** it connects to SMCC SFTP at `__.___.___.___:2222`, downloads files from `/mrmax-prod-apn1-smcc/smcc2ec/{DATE}/`, and stores them in S3
- [ ] **Given** no file is received between 10:00–11:00, **When** the clock reaches 11:05, **Then** a Slack alert is sent to the configured channel
- [ ] **Given** a downloaded file with EBCDIC(ANK)+IBM(Kanji) encoding, **When** BAT2 processes it, **Then** the content is correctly converted to UTF-8 without data loss
- [ ] **Given** a file with mixed valid and invalid records, **When** BAT2 processes it, **Then** valid records are imported to `dtb_affiliated_card_info`/`dtb_customer_card_info` and invalid records are excluded (partial success)
- [ ] **Given** records fail validation during import, **When** Slack notification is sent, **Then** the message includes error counts and a CSV attachment with E14 message key as header and error data as rows
- [ ] **Given** a data_type=10 (New) record, **When** the member is not yet registered, **Then** a new `dtb_affiliated_card_info` record is created
- [ ] **Given** a data_type=20 (Cancel) record, **When** the member has an active linked card, **Then** `is_card_cancelled=1` and `is_valid=0` are set on `dtb_customer_card_info`
- [ ] **Given** a data_type=40 (Reissue) record, **When** processed, **Then** old card gets `is_valid=0` and new card gets `is_valid=1` in `dtb_customer_card_info`
- [ ] **Given** a zero-record file (header + trailer only, no body), **When** BAT2 processes it, **Then** it completes successfully without errors (valid empty file)
- [ ] **Given** BAT2 runs, **When** import completes, **Then** `dtb_card_application_info` is updated with import_date, data_type, record_count, and error_count

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dtb_affiliated_card_info`, `dtb_customer_card_info`, `dtb_card_application_info` entities required |
| SMCC SFTP access | External | SFTP credentials, IP, port, path must be configured |
| S3 bucket | Infrastructure | S3 bucket for file storage must be provisioned |
| Slack webhook | Infrastructure | Slack webhook URL for notifications |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | SFTP connection timeout/failure | Log error; retry next scheduled run (30 min); Slack alert if repeated |
| 2 | File partially downloaded (network interruption mid-transfer) | Detect via trailer record mismatch; reject entire file |
| 3 | Duplicate file (same file name re-downloaded) | Idempotent: skip if already processed (check by filename in S3) |
| 4 | EBCDIC encoding contains rare Kanji characters | IBM → UTF-8 mapping handles all JIS Level 1/2 Kanji |
| 5 | data_type=20 (Cancel) for a member not in the system | Exclude record; log warning |
| 6 | data_type=40 (Reissue) but old card not found | Exclude record; log warning; include in CSV error attachment |
| 7 | data_type=10 (New) with duplicate mrmax_id + customer_number | Exclude record per validation rule |
| 8 | File arrives after 11:00 but before next BAT1 run | BAT1 picks it up on next 30-min cycle; 11:05 Slack alert may have already fired |
| 9 | Extremely large file (10,000+ records) | Process in batches; memory-efficient streaming; transaction per batch |
| 10 | S3 upload failure after SFTP download | Retry S3 upload; keep local file until confirmed stored |
| 11 | Multiple files in the date directory | Process all files sequentially; each file independent |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| EBCDIC/IBM encoding conversion errors | Medium | High | Use PHP `iconv` or `mbstring` with explicit encoding names; validate with sample files from SMCC |
| SFTP connectivity issues in production | Medium | Medium | Implement retry with exponential backoff; Slack alerting for repeated failures |
| Large file processing causes memory exhaustion | Low | High | Stream-process records; don't load entire file into memory |
| BAT2 validation logic mismatches SMCC specification | Medium | High | Validate against sample files provided by SMCC; comprehensive unit tests for each validation rule |
| Partial import leaves database in inconsistent state | Low | Medium | Use database transactions per batch; rollback on critical failures |

#### Notes / Additional Information
- BAT1 and BAT2 are separate Symfony console commands, triggered by cron
- Existing `FileSFTPService.php` provides SFTP connectivity — extend or create dedicated SMCC SFTP service
- SMCC SFTP uses port 2222 (not standard 22)
- SMCC SFTP path: `/mrmax-prod-apn1-smcc/smcc2ec/{DATE}/` where `{DATE}` is `YYYYMMDD`
- Character encoding: ANK fields use EBCDIC, Kanji fields use IBM encoding — both must be converted to UTF-8
- File structure: Header record → Body records (variable count) → Trailer record → End record
- Slack notification uses existing Slack integration pattern — check for `SlackService` or webhook helper in codebase
- The 11 BAT2 validation rules are defined in SRS Section 6.1

---

#### Sub-tasks:

##### Sub-task 5.1: Create BAT1 SFTP Retrieval Command
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend/DevOps

**Description:**
Create Symfony console command `app/Customize/Command/SmccFileRetrieveCommand.php` (BAT1):
1. Register as `app:smcc:retrieve` command
2. Connect to SMCC SFTP server using env vars (`SMCC_SFTP_HOST`, `SMCC_SFTP_PORT=2222`, `SMCC_SFTP_USER`, `SMCC_SFTP_PASSWORD`)
3. Navigate to `/mrmax-prod-apn1-smcc/smcc2ec/{DATE}/` directory (DATE = today YYYYMMDD)
4. Download all new files (skip already-downloaded by checking S3 for existing key)
5. Upload to S3 bucket (`SMCC_S3_BUCKET`) with key `smcc/incoming/{DATE}/{filename}`
6. Log download results (file count, sizes, timestamps)
7. Implement 11:05 Slack alert: if no file downloaded during 10:00–11:00 window AND current time is 11:05, send Slack notification
8. Use existing `FileSFTPService` or create `SmccSftpService` extending it for SMCC-specific configuration

Cron schedule: `*/30 * * * *` (every 30 minutes)

- **Affected Files:** `app/Customize/Command/SmccFileRetrieveCommand.php`, `app/Customize/Service/Vpoint/SmccSftpService.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] Command connects to SMCC SFTP on port 2222
  - [ ] Files downloaded from correct directory path with date substitution
  - [ ] Files uploaded to S3 with correct key structure
  - [ ] Duplicate file detection prevents re-download
  - [ ] 11:05 Slack alert fires when no file received in 10:00–11:00 window
  - [ ] Command is idempotent (safe to run multiple times)

---

##### Sub-task 5.2: Implement EBCDIC/IBM to UTF-8 Encoding Converter
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SmccEncodingService.php`:
1. `convertAnkField(string $ebcdicBytes): string` — convert EBCDIC-encoded ANK field to UTF-8
2. `convertKanjiField(string $ibmBytes): string` — convert IBM-encoded Kanji field to UTF-8
3. `convertRecord(string $rawRecord, array $fieldSpec): array` — parse a fixed-length record using field specification (position, length, encoding type) and convert all fields

Use PHP `iconv()` with source encodings:
- ANK: `EBCDIC-JP-KANA` or `IBM-037` (verify correct codepage with SMCC)
- Kanji: `IBM-930` or `IBM-939` (Japanese EBCDIC with Kanji)

Include validation: if conversion produces replacement characters or errors, flag the record.

- **Affected Files:** `app/Customize/Service/Vpoint/SmccEncodingService.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] ANK fields converted correctly (alphanumeric + katakana)
  - [ ] Kanji fields converted correctly (all JIS Level 1/2 Kanji)
  - [ ] Conversion errors detected and flagged
  - [ ] Unit tests with known input/output pairs

---

##### Sub-task 5.3: Create BAT2 File Parser — Fixed-Length Record Processing
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SmccFileParserService.php`:
1. `parseFile(string $filePath): SmccFileResult` — main entry point
2. Parse header record → extract file metadata (record count, date, etc.)
3. Parse body records → convert encoding → extract fields per fixed-length specification
4. Parse trailer record → verify record count matches body count
5. Handle zero-record files (header + trailer only) as valid
6. Return `SmccFileResult` object with `headers`, `records[]`, `trailer`, `errors[]`

Create DTO: `app/Customize/DTO/SmccFileResult.php` and `SmccRecord.php`.

Field specification for each data_type (positions and lengths) defined per SMCC spec.

- **Affected Files:** `app/Customize/Service/Vpoint/SmccFileParserService.php`, `app/Customize/DTO/SmccFileResult.php`, `app/Customize/DTO/SmccRecord.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] Header parsed correctly with metadata extraction
  - [ ] Body records parsed per fixed-length field specification
  - [ ] Trailer record count validated against actual body count
  - [ ] Zero-record files processed without error
  - [ ] Encoding conversion applied to each field

---

##### Sub-task 5.4: Implement BAT2 Validation Engine
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SmccValidationService.php` implementing all 11 validation rules from SRS Section 6.1:

1. File format — fixed-length record per specification → reject entire file
2. Header — must always be present → reject entire file
3. Required fields — fields marked ● must not be NULL → exclude record
4. Numeric fields — digits only, no signs → exclude record
5. Char padding — left-aligned, space-padded → exclude record
6. Numeric padding — right-aligned, zero-padded → exclude record
7. Code range — `data_type ∈ {10,20,30,40,50}`, `sex ∈ {1,2}` → exclude record
8. Date validation — YYYYMMDD format, no future dates → exclude record
9. Duplicate check — no duplicate `mrmax_id + customer_number` for type=10 → exclude record
10. Correlation — type=20 requires existing valid card → exclude record
11. Field length — no overflow or misalignment → exclude record

Each validation returns structured error info for CSV attachment generation.

- **Affected Files:** `app/Customize/Service/Vpoint/SmccValidationService.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] All 11 validation rules implemented
  - [ ] File-level failures (rules 1-2) reject entire file
  - [ ] Record-level failures (rules 3-11) exclude individual records
  - [ ] Error details structured for CSV export (E14 message key format)
  - [ ] Unit test for each validation rule with valid and invalid input

---

##### Sub-task 5.5: Implement BAT2 Import Service — Data Type Processing
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SmccImportService.php`:
1. `importRecords(SmccFileResult $fileResult): ImportResult` — main orchestrator
2. Process records by data_type per Status Decision Matrix:
   - **10 (New):** Insert new `dtb_affiliated_card_info` record. If member registered, allow barcode linkage.
   - **20 (Cancel):** Set `is_card_cancelled=1`, `is_valid=0` on `dtb_customer_card_info` for linked members.
   - **30 (Change):** Update address/name fields only on `dtb_affiliated_card_info`.
   - **40 (Reissue):** Old card `is_valid=0`, create new card record, transfer linkage if applicable.
   - **50 (Update):** Update expiry/renewal info on `dtb_affiliated_card_info`.
3. Use database transactions per batch (configurable batch size, e.g., 100 records)
4. Update `dtb_card_application_info` with import counts per data_type
5. Return `ImportResult` with success_count, error_count, errors[]

Inject: `AffiliatedCardInfoRepository`, `CustomerCardInfoRepository`, `CardApplicationInfoRepository`, `EntityManagerInterface`.

- **Affected Files:** `app/Customize/Service/Vpoint/SmccImportService.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] All 5 data types processed correctly per Status Decision Matrix
  - [ ] Partial success: valid records imported, invalid excluded
  - [ ] `dtb_card_application_info` updated with accurate counts
  - [ ] Database transactions prevent partial corruption
  - [ ] Data_type=40 reissue correctly transfers linkage

---

##### Sub-task 5.6: Create BAT2 Console Command
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Create Symfony console command `app/Customize/Command/SmccFileImportCommand.php` (BAT2):
1. Register as `app:smcc:import` command
2. Retrieve latest unprocessed file from S3
3. Call `SmccFileParserService::parseFile()` → `SmccValidationService::validate()` → `SmccImportService::importRecords()`
4. Send Slack notification with import summary:
   - Success: "SMCC import complete: {N} records imported, {M} errors"
   - If errors: attach CSV file with E14 message key as header and error data rows
5. Mark file as processed (move S3 key to `smcc/processed/` prefix)
6. Support `--dry-run` flag (parse + validate without importing)

- **Affected Files:** `app/Customize/Command/SmccFileImportCommand.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] Command orchestrates parse → validate → import pipeline
  - [ ] Slack notification sent on completion with counts
  - [ ] CSV error attachment includes E14 headers and error details
  - [ ] Dry-run mode available
  - [ ] Processed files moved in S3

---

##### Sub-task 5.7: Implement Slack Notification with CSV Attachment
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Create or extend `app/Customize/Service/Vpoint/SmccSlackNotificationService.php`:
1. `sendImportReport(ImportResult $result): void` — sends Slack message with import summary
2. `sendNoFileAlert(): void` — sends 11:05 alert when no file received
3. For error reports: generate CSV string with E14 message key as header, error data rows as body. Upload as Slack file attachment.
4. Use existing Slack integration pattern (check for `SlackService`, webhook configuration)

- **Affected Files:** `app/Customize/Service/Vpoint/SmccSlackNotificationService.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] Import report message sent to correct Slack channel
  - [ ] CSV error attachment with correct E14 header format
  - [ ] No-file alert sent at 11:05 trigger
  - [ ] Slack failures logged but don't block import process

---

##### Sub-task 5.8: Unit & Integration Tests for BAT1/BAT2
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create comprehensive tests:
1. `SmccEncodingServiceTest.php` — encoding conversion with known EBCDIC/IBM → UTF-8 pairs
2. `SmccFileParserServiceTest.php` — header/body/trailer parsing, zero-record file, malformed file
3. `SmccValidationServiceTest.php` — test each of 11 validation rules individually
4. `SmccImportServiceTest.php` — test all 5 data types, partial success, transaction rollback
5. `SmccFileRetrieveCommandTest.php` — mock SFTP, test file download, S3 upload, 11:05 alert logic
6. Integration test: full pipeline from raw file → parsed → validated → imported

- **Affected Files:** `tests/Unit/Service/Vpoint/SmccEncodingServiceTest.php`, `tests/Unit/Service/Vpoint/SmccFileParserServiceTest.php`, `tests/Unit/Service/Vpoint/SmccValidationServiceTest.php`, `tests/Unit/Service/Vpoint/SmccImportServiceTest.php`, `tests/Unit/Command/SmccFileRetrieveCommandTest.php`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] All 11 validation rules tested independently
  - [ ] All 5 data types tested with valid/invalid data
  - [ ] Zero-record file test passes
  - [ ] Encoding conversion tested with sample data
  - [ ] Full pipeline integration test passes

---

##### Sub-task 5.9: Cron Configuration & Environment Variables
**Type:** Sub-task | **Estimate:** 1h | **Skill:** DevOps

**Description:**
Configure batch execution:
1. Add cron entries for BAT1 (`*/30 * * * *`) and BAT2 (triggered after BAT1 or separate schedule)
2. Add environment variables to `.env.dist`:
   - `SMCC_SFTP_HOST`, `SMCC_SFTP_PORT=2222`, `SMCC_SFTP_USER`, `SMCC_SFTP_PASSWORD`
   - `SMCC_SFTP_PATH=/mrmax-prod-apn1-smcc/smcc2ec/`
   - `SMCC_S3_BUCKET`, `SMCC_S3_PREFIX=smcc/`
   - `SMCC_SLACK_WEBHOOK_URL`, `SMCC_SLACK_CHANNEL`
3. Update Docker batch configuration (`docker-compose.batch.dev.yml`, `Dockerfile-batch`) if batch commands run in batch container
4. Add commands to `taskdef-batch.json` if using ECS scheduled tasks

- **Affected Files:** `.env.dist`, `docker-compose.batch.dev.yml`, `taskdef-batch.json`
- **Parent Story:** Story 5
- **Definition of Done:**
  - [ ] BAT1 cron runs every 30 minutes
  - [ ] BAT2 triggered appropriately (after BAT1 or on schedule)
  - [ ] All environment variables documented
  - [ ] Batch container configuration updated

---

## Cross-Story Dependencies

| Story | Depends On | Type | Details |
|-------|-----------|------|---------|
| Story 2 | Story 1 | Hard | API client needs `VpointRedeemResult` entity for storing sp201 results |
| Story 3 | Story 1 | Hard | Card linkage needs `CustomerCardInfo` and `AffiliatedCardInfo` entities |
| Story 3 | Story 2 | Hard | Card verification requires sp101 API client |
| Story 4 | Story 1 | Hard | Unlink needs `CustomerCardInfo` entity |
| Story 4 | Story 3 | Soft | Linkage must exist before unlink is meaningful |
| Story 5 | Story 1 | Hard | Import needs `AffiliatedCardInfo`, `CustomerCardInfo`, `CardApplicationInfo` entities |

## Suggested Sprint Allocation

| Sprint | Stories | Total Points | Sprint Goal |
|--------|---------|-------------|-------------|
| Sprint 1 | Story 1, Story 2 | 10 | Database foundation + API client infrastructure |
| Sprint 2 | Story 3, Story 4, Story 5 | 16 | Card linkage (link/unlink) + SFTP file import |

## Risk Summary (Across All Stories)

| # | Risk | Affected Stories | Likelihood | Impact | Mitigation |
|---|------|-----------------|-----------|--------|-----------|
| 1 | CCCMK test environment unavailable | Story 2, 3 | Medium | High | Mock server for development; early integration test |
| 2 | SMCC file encoding conversion errors | Story 5 | Medium | High | Sample file validation; comprehensive unit tests |
| 3 | Schema mismatch with SMCC spec | Story 1, 5 | Medium | High | Cross-reference original PDF spec |
| 4 | Encryption algorithm mismatch | Story 2 | Low | Critical | Test vector validation before any API calls |
| 5 | SFTP connectivity in production | Story 5 | Medium | Medium | Retry logic; Slack alerting |
| 6 | Birthday format inconsistency | Story 3 | Low | Medium | Normalize to YYYYMMDD before comparison |

## Assumptions

- CCCMK will provide test environment credentials (alliance_cd, passwd, encryption key, IV) before Sprint 1 start
- SMCC will provide sample SFTP files for encoding/validation testing before Sprint 2
- S3 bucket and Slack webhook are already provisioned by DevOps
- The existing `FileSFTPService.php` pattern can be extended for SMCC SFTP connection
- `dtb_customer.ext_attr_text3` column already exists and is populated with `app_member_id`
- The modulus 10 check digit algorithm (weight 2/1 from left) is confirmed by SMCC barcode specification
- EC-Cube proxy generation works with all new entities (no custom generator conflicts)
- Serial number sequence is managed at application level (not database sequence) to support A03/A04 prefixes

### Story 6: V-Point EC Checkout — Balance Inquiry & Exchange Modal (STEP1)

**Type:** Story | **Priority:** H | **Points:** 5 | **Sprint:** 3

#### Summary
Implement the STEP1 phase of V-Point checkout: the customer views their V-Point balance (via sp101), enters a desired exchange amount, and clicks "Exchange" to create a temporary coupon reservation stored in Redis (or PHP session as fallback). No sp201 API call occurs in this step — the reservation is a local placeholder that STEP2 (Story 7) later converts into a real coupon. This story owns the `VpointController` balance and reserve endpoints, the `VpointCouponService` clone/session management, and Redis reservation logic.

#### Requirement Details
Implements SRS STEP1-1 (balance display + exchange input + "Exchange" button) and STEP1-2 (UI confirmation only, no backend call). When the customer navigates to the checkout page and has a linked card, the system calls sp101 to retrieve their V-Point balance. The customer enters an exchange amount (must be ≤ balance and ≤ order total) and clicks "Exchange." This creates a reservation JSON object in Redis (`vpoint_reserve:{customer_id}`, TTL 30 min) or `$_SESSION['vpoint_coupon_reservation']`:
```json
{"coupon_id": 999999990001, "customer_id": 12345, "discount_price": 1000, "serial_no": null, "status": "RESERVED", "sp101_balance": 2000, "reserved_at": "2026-05-12T10:30:00+09:00"}
```
If sp101 returns error or return code 04/no-return, the error message is displayed and "Exchange" is blocked. If the order total is revised downward after a V-Point coupon is applied such that coupon > revised total, the system returns the customer to STEP1-1 to re-enter the exchange amount.

- **Linked Requirements:** SRS STEP1-1 (Balance → Exchange), STEP1-2 (Confirmation display), Section 2.4 (sp101 sequence), Section 7 (Error Messages)
- **Affected Components:** `app/Customize/Controller/VpointController.php`, `app/Customize/Service/Vpoint/VpointCouponService.php`, `app/Customize/Service/EC/RedisService.php`
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** V-Point EC Checkout

#### Acceptance Criteria
- [ ] **Given** a logged-in customer with a linked card, **When** they reach the checkout page, **Then** the system calls sp101 and displays the V-Point balance as "X,XXXpt"
- [ ] **Given** sp101 returns an error or return code 04, **When** the balance section renders, **Then** "＊＊＊＊pt" is shown and the Exchange button is disabled with an error message
- [ ] **Given** a valid balance of 2,000pt, **When** the customer enters 1,000 and clicks "Exchange," **Then** a reservation JSON is stored in Redis with key `vpoint_reserve:{customer_id}`, TTL 30 min, status=RESERVED
- [ ] **Given** Redis is unavailable, **When** the customer clicks "Exchange," **Then** the reservation is stored in `$_SESSION['vpoint_coupon_reservation']` with session-lifetime TTL
- [ ] **Given** the customer enters an amount > balance, **When** they click "Exchange," **Then** a validation error is shown ("入力されたポイントが残高を超えています")
- [ ] **Given** the customer enters an amount > order total, **When** they click "Exchange," **Then** a validation error is shown and the amount is capped at the order total
- [ ] **Given** a V-Point coupon is already applied and the order total decreases (quantity change), **When** coupon > revised total, **Then** the reservation is cleared and the customer returns to STEP1-1 to re-enter
- [ ] **Given** a reservation exists and the customer navigates away, **When** 30 minutes elapse, **Then** the Redis key expires and the reservation is gone
- [ ] **Given** STEP1-2, **When** the confirmation is displayed, **Then** no backend call is made — only UI display of the reserved amount

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` and `VpointExchange` entities required |
| Story 2 | Blocked-by | `VpointApiClient::balanceInquiry()` and `VpointErrorMessageService` required for sp101 calls |
| Story 3 | Soft-dependency | Card linkage must exist for the customer to have a linked card |
| Story 8 | Co-dependent | Frontend Twig templates consume the JSON endpoints created here |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | Customer has linked card but sp101 times out (3s) | Display "＊＊＊＊pt"; disable Exchange button; show error message |
| 2 | Customer opens two browser tabs and reserves in both | Second reservation overwrites first (same Redis key per customer_id) |
| 3 | Redis TTL expires during checkout confirmation step | STEP2 detects missing reservation and returns customer to STEP1-1 |
| 4 | Customer enters 0 as exchange amount | Validation rejects — minimum amount is ¥1 (or ¥100 per denomination) |
| 5 | Customer's balance changes between sp101 call and "Exchange" click | No issue at STEP1 — STEP2 re-verifies with sp101 before sp201 |
| 6 | Order total is ¥0 (all items removed after V-Point applied) | Clear reservation; redirect to cart |
| 7 | Customer has no linked card | V-Point section is hidden entirely on checkout page |
| 8 | Session/Redis stores reservation but customer logs out | Session destroyed; Redis TTL expires independently |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| sp101 latency degrades checkout page load time | Medium | Medium | Lazy-load balance via AJAX after page render; 3s timeout |
| Redis unavailability in production | Low | Medium | Fallback to PHP session; log warning for monitoring |
| Reservation TTL too short for slow shoppers | Low | Low | TTL configurable via env var (`VPOINT_RESERVE_TTL=1800`) |
| Race condition: two tabs overwrite reservation | Low | Low | Last write wins is acceptable — STEP2 re-verifies balance |

#### Notes / Additional Information
- `VpointController` is a new controller at `app/Customize/Controller/VpointController.php`
- Routes: `POST /shopping/vpoint/balance` (AJAX), `POST /shopping/vpoint/reserve` (AJAX)
- `coupon_id=999999990001` is the sentinel V-Point coupon ID used across the system
- The reservation does NOT call sp201 — that happens in Story 7 (STEP2)
- Redis key pattern: `vpoint_reserve:{customer_id}` — uses existing `RedisService` from `app/Customize/Service/EC/RedisService.php`
- `VpointCouponService` methods: `storeCouponClone()`, `getCouponClone()`, `clearCouponClone()`
- The `CouponDiscountProcess` must read from the reservation when `coupon_id=999999990001` to compute the discount

---

#### Sub-tasks:

##### Sub-task 6.1: Create VpointController — Balance Endpoint
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Controller/VpointController.php` with route `POST /shopping/vpoint/balance` (AJAX endpoint). Implementation:
1. Verify user is logged in and has a linked card (`CustomerCardInfoRepository::findActiveByAppMemberId()`)
2. Call `VpointApiClient::balanceInquiry()` using the customer's `kaiin_id` (from `dtb_customer_card_info.customer_number`)
3. On success (return_cd=00): return `JsonResponse` with `{balance: int, formatted: "X,XXXpt", error: null}`
4. On failure: return `{balance: null, formatted: "＊＊＊＊pt", error: "error message from VpointErrorMessageService"}`
5. CSRF protection via Symfony token
6. Log sp101 call result (structured logging)

- **Affected Files:** `app/Customize/Controller/VpointController.php`
- **Parent Story:** Story 6
- **Definition of Done:**
  - [ ] Route registered and returns JSON
  - [ ] sp101 called with correct customer credentials
  - [ ] Balance formatted with thousands separator + "pt" suffix
  - [ ] Error cases return "＊＊＊＊pt" with Japanese error message
  - [ ] CSRF token validated on POST
  - [ ] Unauthenticated/unlinked users receive 403/appropriate error

---

##### Sub-task 6.2: Create VpointController — Reserve Exchange Endpoint
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Add route `POST /shopping/vpoint/reserve` to `VpointController.php`. Implementation:
1. Accept JSON body: `{amount: int}`
2. Validate: `amount > 0`, `amount ≤ sp101_balance` (from cached balance or re-query), `amount ≤ order_total`
3. Build reservation JSON:
   ```json
   {"coupon_id": 999999990001, "customer_id": <id>, "discount_price": <amount>, "serial_no": null, "status": "RESERVED", "sp101_balance": <balance>, "reserved_at": "<ISO8601 JST>"}
   ```
4. Store in Redis: `RedisService::set("vpoint_reserve:{customer_id}", json, TTL)` — TTL from env `VPOINT_RESERVE_TTL` (default 1800s)
5. Fallback: if Redis fails, store in `$_SESSION['vpoint_coupon_reservation']`
6. Return `JsonResponse` with `{success: true, reservation: {...}}`
7. Add route `DELETE /shopping/vpoint/reserve` to clear an existing reservation

- **Affected Files:** `app/Customize/Controller/VpointController.php`
- **Parent Story:** Story 6
- **Definition of Done:**
  - [ ] Reservation stored in Redis with correct key and TTL
  - [ ] Session fallback works when Redis is unavailable
  - [ ] Amount validation: >0, ≤ balance, ≤ order total
  - [ ] DELETE endpoint clears reservation from both Redis and session
  - [ ] CSRF protection on all endpoints
  - [ ] Concurrent requests for same customer overwrite cleanly

---

##### Sub-task 6.3: Implement VpointCouponService — Reservation Management
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/VpointCouponService.php` with methods:
1. `storeCouponClone(int $customerId, array $reservation): void` — store reservation in Redis/session
2. `getCouponClone(int $customerId): ?array` — retrieve reservation from Redis, fallback to session
3. `clearCouponClone(int $customerId): void` — delete from both Redis and session
4. `isReservationValid(int $customerId): bool` — check reservation exists and hasn't expired
5. `getReservedAmount(int $customerId): int` — shorthand for reading `discount_price` from clone

Inject `RedisService` and `SessionInterface`. Handle Redis connection failures gracefully with session fallback and log warnings.

- **Affected Files:** `app/Customize/Service/Vpoint/VpointCouponService.php`
- **Parent Story:** Story 6
- **Definition of Done:**
  - [ ] Store/get/clear operations work with Redis
  - [ ] Session fallback transparent to callers
  - [ ] `isReservationValid()` checks expiry and existence
  - [ ] Redis connection failures logged, not thrown

---

##### Sub-task 6.4: Integrate CouponDiscountProcess with V-Point Reservation
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Modify `app/Customize/Service/PurchaseFlow/Processor/CouponDiscountProcess.php` to handle the V-Point sentinel coupon (`coupon_id=999999990001`):
1. In the discount calculation flow, detect when `coupon_id=999999990001`
2. Read `discount_price` from `VpointCouponService::getCouponClone()` instead of the normal coupon table
3. Apply as a fixed-amount discount (not percentage)
4. If reservation is missing/expired, skip the V-Point discount and log a warning
5. If `discount_price > order_total` (quantity decrease scenario), flag for STEP1-1 re-entry

Do NOT modify the core discount flow for regular coupons — V-Point is additive logic only.

- **Affected Files:** `app/Customize/Service/PurchaseFlow/Processor/CouponDiscountProcess.php`
- **Parent Story:** Story 6
- **Definition of Done:**
  - [ ] V-Point coupon detected by sentinel `coupon_id=999999990001`
  - [ ] Discount amount read from Redis/session reservation, not coupon table
  - [ ] Regular coupon processing unaffected
  - [ ] Over-total scenario detected and flagged
  - [ ] Missing reservation handled gracefully (no crash)

---

##### Sub-task 6.5: Environment Configuration & DI Registration
**Type:** Sub-task | **Estimate:** 1h | **Skill:** Backend

**Description:**
1. Add environment variables to `.env.dist`:
   - `VPOINT_RESERVE_TTL=1800` (30 minutes, configurable)
   - `VPOINT_SENTINEL_COUPON_ID=999999990001`
2. Register `VpointCouponService` in DI container (auto-wire or `services.yaml`)
3. Register `VpointController` routes (annotation-based routing, verify auto-discovery)
4. Verify `bin/console cache:clear` succeeds with new services

- **Affected Files:** `.env.dist`, `app/config/eccube/packages/services.yaml`
- **Parent Story:** Story 6
- **Definition of Done:**
  - [ ] Environment variables documented
  - [ ] All new services auto-wirable
  - [ ] Routes accessible after cache clear
  - [ ] No missing-dependency errors

---

##### Sub-task 6.6: Unit Tests for STEP1 Balance & Reservation
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create tests:
1. `VpointControllerTest.php` — test balance endpoint (success, sp101 failure, unlinked user, unauthenticated); test reserve endpoint (valid amount, over-balance, over-total, zero amount)
2. `VpointCouponServiceTest.php` — test store/get/clear with mock Redis; test session fallback; test TTL expiry
3. `CouponDiscountProcessVpointTest.php` — test V-Point discount applied from reservation; test missing reservation; test over-total flag

- **Affected Files:** `tests/Unit/Controller/VpointControllerTest.php`, `tests/Unit/Service/Vpoint/VpointCouponServiceTest.php`, `tests/Unit/Service/PurchaseFlow/CouponDiscountProcessVpointTest.php`
- **Parent Story:** Story 6
- **Definition of Done:**
  - [ ] Balance endpoint tested with all sp101 outcomes
  - [ ] Reserve endpoint validated for all boundary conditions
  - [ ] Session fallback verified in tests
  - [ ] CouponDiscountProcess V-Point path tested independently

---

### Story 7: V-Point EC Checkout — Order Execution & Coupon Issue (STEP2/STEP3)

**Type:** Story | **Priority:** H | **Points:** 8 | **Sprint:** 3

#### Summary
Implement the STEP2 (order execution) and STEP3 (order complete) phases of V-Point checkout. STEP2 re-verifies the V-Point balance via sp101, generates a serial number (prefix A04), inserts a `dct_vpoint_redeem_result` record, calls sp201 to redeem points, issues a real coupon on success, handles full/partial V-Point payment (skip/call GMO), and implements the cancel retry logic (Cancel→Retry1→Retry2→cancel_status=3→BAT3/BAT4) when GMO fails. STEP3 displays the order confirmation with applied coupon details.

#### Requirement Details
Implements SRS STEP2 (order execution sequence) and STEP3 (order complete). The STEP2 orchestration:
1. sp101 re-verify balance → if NG or balance < reserved → clear reservation, return to STEP1-1 with "Vポイントが足りません。"
2. Generate `serial_no` with prefix A04: `A04` + `YYMMDD(JST)` + `[Sequence:11]`
3. Insert `dct_vpoint_redeem_result` with `return_cd=NULL` (pre-call)
4. Call sp201 (`point_kbn=73`) → update `return_cd` in `dct_vpoint_redeem_result`
5. sp201 OK → issue REAL coupon: insert `dct_coupon_target` with `status=ACTIVE`, `serial_no`, `coupon_id=999999990001`
6. Full V-Point (coupon ≥ order total) → skip GMO payment entirely
7. Partial V-Point (coupon < order total) → call GMO for remainder
8. GMO NG → trigger sp201 Cancel (`cancel_kbn=1`, `point_kbn=74`) with retry: Cancel→Retry1(`retry_cnt=1`)→Retry2(`retry_cnt=2`)→`cancel_status=3`→BAT3/BAT4 recovery

`VpointRedemptionService` is the orchestrator with `redeem()` method. `VpointCouponService::issueCoupon()` creates the real coupon.

- **Linked Requirements:** SRS STEP2 (Order Execution), STEP3 (Order Complete), Section 2.5 (sp201 sequence), Cancel retry logic
- **Affected Components:** `app/Customize/Service/Vpoint/VpointRedemptionService.php`, `app/Customize/Service/Vpoint/VpointCouponService.php`, `app/Customize/Controller/ShoppingController.php`, `app/Customize/Entity/VpointRedeemResult.php`
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** V-Point EC Checkout

#### Acceptance Criteria
- [ ] **Given** a valid reservation exists, **When** STEP2 begins, **Then** sp101 is re-called to verify the balance is still sufficient
- [ ] **Given** sp101 re-verify returns insufficient balance, **When** the check fails, **Then** the reservation is cleared, an error "Vポイントが足りません。" is displayed, and the customer returns to STEP1-1
- [ ] **Given** balance is sufficient, **When** sp201 is called, **Then** a `dct_vpoint_redeem_result` record exists with `return_cd=NULL` before the call and is updated with the actual `return_cd` after
- [ ] **Given** sp201 returns success (return_cd=00), **When** the coupon is issued, **Then** `dct_coupon_target` contains a new record with `status=ACTIVE`, `serial_no` prefixed A04, and `coupon_id=999999990001`
- [ ] **Given** the V-Point coupon covers the full order total, **When** proceeding to payment, **Then** GMO payment is skipped entirely and the order completes with ¥0 payment
- [ ] **Given** the V-Point coupon is partial (less than order total), **When** proceeding to payment, **Then** GMO is called for the remainder amount
- [ ] **Given** GMO payment fails after sp201 succeeded, **When** cancel is triggered, **Then** sp201 Cancel is called with `point_kbn=74`, `cancel_kbn=1`, and retried up to 2 times
- [ ] **Given** all cancel retries fail, **When** retry 2 completes, **Then** `cancel_status=3` is set and the record is queued for BAT3/BAT4 recovery
- [ ] **Given** sp201 cancel succeeds on retry 1, **When** the cancel completes, **Then** `cancel_status=4` is set and no further retries occur
- [ ] **Given** STEP3 (order complete), **When** the confirmation page renders, **Then** the V-Point coupon amount and remaining balance are displayed

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` entity, `dct_coupon_target.serial_no` column |
| Story 2 | Blocked-by | `VpointApiClient` (sp101, sp201, cancelWithRetry) |
| Story 6 | Blocked-by | Reservation must exist from STEP1 before STEP2 can execute |
| Story 10 | Produces-for | `cancel_status=3` records are consumed by BAT3/BAT4 |
| GMO Plugin | External | `GmoPaymentGateway4` plugin must support conditional skip |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | sp201 succeeds but GMO call times out (network) | Trigger cancel flow; if cancel succeeds, order not placed; if cancel fails, cancel_status=3 |
| 2 | sp201 call returns return_cd=05 (duplicate serial_no) | Regenerate serial_no with new sequence; retry sp201 once |
| 3 | Customer's balance decreases between STEP1 reserve and STEP2 verify | sp101 re-verify catches this; clear reservation, return to STEP1-1 |
| 4 | Full V-Point payment (coupon = order total) with ¥0 to GMO | Skip GMO entirely; `Payment` method set to "V-Point Full" or equivalent |
| 5 | Partial V-Point: GMO succeeds but DB commit fails after | Both sp201 usage and GMO charge are committed; order must be created or both reversed |
| 6 | sp201 returns timeout (return_cd=04) | Treat as failure; trigger cancel flow |
| 7 | Cancel retry 1 succeeds | Set cancel_status=4; do NOT call retry 2 |
| 8 | Serial_no sequence collision at same millisecond | Use atomic counter (Redis INCR or DB sequence) for sequence portion |
| 9 | Order contains only digital products (no shipping) | V-Point flow unchanged; full/partial logic still applies |
| 10 | Customer refreshes page during STEP2 processing | Idempotency: check if sp201 already called for this order's serial_no |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| GMO + sp201 transaction atomicity failure | Low | Critical | Use saga pattern: sp201 first → GMO second → cancel sp201 if GMO fails |
| Serial_no collision under high concurrency | Low | Medium | Use Redis INCR for atomic sequence generation |
| cancel_status=3 records accumulate if BAT3/BAT4 not running | Low | High | Monitoring alert if cancel_status=3 count exceeds threshold |
| Full V-Point bypass of GMO conflicts with payment plugin assumptions | Medium | High | Test GMO plugin behavior with ¥0 amount; may need custom PaymentMethod |
| sp201 idempotency not guaranteed by CCCMK | Low | High | Use unique serial_no per attempt; never re-send same serial_no |

#### Notes / Additional Information
- `VpointRedemptionService::redeem()` is the single entry point for STEP2 orchestration
- Serial_no format: `A04` + `YYMMDD` (JST) + 11-digit sequence = 20 chars total
- `program_name=1` for sp201 usage, `program_name=2` for sp201 cancel
- The cancel flow inserts additional rows in `dct_vpoint_redeem_result` with `point_kbn=74` and incrementing `retry_cnt`
- GMO skip for full V-Point may require a custom `PaymentMethodInterface` implementation or conditional bypass in `ShoppingController`
- `VpointCouponService::issueCoupon()` creates the `dct_coupon_target` record — this is the "REAL" coupon vs. the reservation clone

---

#### Sub-tasks:

##### Sub-task 7.1: Implement VpointRedemptionService — Orchestration
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/VpointRedemptionService.php` with main method `redeem(Customer $customer, Order $order): RedemptionResult`. Orchestration flow:
1. Retrieve reservation via `VpointCouponService::getCouponClone()`
2. Re-verify balance: `VpointApiClient::balanceInquiry()` → if NG or balance < reserved amount, clear clone, return FAIL with "Vポイントが足りません。"
3. Generate `serial_no`: `SerialNoGenerator::generate('A04')` (atomic, JST-based)
4. Insert `dct_vpoint_redeem_result` with `return_cd=NULL`, `program_name=1`, `cancel_status=0`
5. Call `VpointApiClient::pointUsage()` → update `return_cd`
6. If sp201 OK: call `VpointCouponService::issueCoupon()` → return SUCCESS with coupon details
7. If sp201 NG: clear reservation, return FAIL with error message
8. Clear reservation clone after successful redemption

Create DTO: `app/Customize/DTO/RedemptionResult.php` with properties: `success`, `coupon`, `errorMessage`, `cancelStatus`.

Inject: `VpointApiClient`, `VpointCouponService`, `VpointRedeemResultRepository`, `EntityManagerInterface`.

- **Affected Files:** `app/Customize/Service/Vpoint/VpointRedemptionService.php`, `app/Customize/DTO/RedemptionResult.php`
- **Parent Story:** Story 7
- **Definition of Done:**
  - [ ] Full STEP2 orchestration in single `redeem()` method
  - [ ] sp101 re-verification before sp201 call
  - [ ] `dct_vpoint_redeem_result` insert before sp201, update after
  - [ ] Serial_no generated with A04 prefix and JST date
  - [ ] Reservation cleared on success
  - [ ] All failure paths return structured `RedemptionResult`

---

##### Sub-task 7.2: Implement VpointCouponService — issueCoupon
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Add `issueCoupon()` method to `app/Customize/Service/Vpoint/VpointCouponService.php`:
1. `issueCoupon(Customer $customer, int $amount, string $serialNo): CouponTarget` — creates a real `dct_coupon_target` record:
   - `coupon_id = 999999990001`
   - `customer_id = $customer->getId()`
   - `discount_price = $amount`
   - `serial_no = $serialNo`
   - `status = Constant::COUPON_STATUS_ACTIVE` (or equivalent)
   - `create_date = now(JST)`
   - `update_date = now(JST)`
2. Persist and flush via `EntityManagerInterface`
3. Return the created `CouponTarget` entity

Also add `findActiveVpointCoupon(int $customerId): ?CouponTarget` — finds active V-Point coupon for a customer.

- **Affected Files:** `app/Customize/Service/Vpoint/VpointCouponService.php`
- **Parent Story:** Story 7
- **Definition of Done:**
  - [ ] `dct_coupon_target` record created with correct sentinel coupon_id
  - [ ] `serial_no` stored on the coupon target
  - [ ] Coupon queryable by customer_id and coupon_id=999999990001
  - [ ] Status set to ACTIVE

---

##### Sub-task 7.3: Implement Serial Number Generator
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SerialNoGenerator.php`:
1. `generate(string $prefix): string` — generates serial_no in format `{prefix}{YYMMDD}{sequence:11}`
2. Prefix: `A04` for EC, `A03` for Native (Story 9)
3. Date: JST `YYMMDD` (e.g., `260512` for 2026-05-12)
4. Sequence: 11-digit zero-padded, atomically incremented
5. Use Redis `INCR` on key `vpoint_serial_seq:{prefix}:{YYMMDD}` with daily TTL (48h)
6. Fallback to database sequence if Redis unavailable
7. Total length: 3 + 6 + 11 = 20 characters

- **Affected Files:** `app/Customize/Service/Vpoint/SerialNoGenerator.php`
- **Parent Story:** Story 7
- **Definition of Done:**
  - [ ] Serial numbers are unique across concurrent requests
  - [ ] Format matches `[A03|A04][YYMMDD][00000000001-99999999999]`
  - [ ] Redis atomic increment prevents collisions
  - [ ] Daily sequence resets at midnight JST
  - [ ] Fallback to DB works if Redis unavailable

---

##### Sub-task 7.4: Implement GMO Cancel & sp201 Cancel Retry Flow
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Add cancel handling to `VpointRedemptionService`:
1. `handleGmoFailure(Order $order, string $serialNo): CancelResult` — called when GMO payment fails after sp201 succeeded:
   a. Call `VpointApiClient::cancelUsage()` with `cancel_kbn=1`, `point_kbn=74`
   b. Insert `dct_vpoint_redeem_result` row with `point_kbn=74`, `retry_cnt=0`, `program_name=2`
   c. If cancel OK → set `cancel_status=1` (Cancelled) → return success
   d. If cancel NG → retry with `retry_cnt=1` → if OK → `cancel_status=1`
   e. If retry 1 NG → retry with `retry_cnt=2` → if OK → `cancel_status=1`
   f. If retry 2 NG → set `cancel_status=3` (Processing/BAT3) → return failure for BAT recovery
2. Each retry inserts a new `dct_vpoint_redeem_result` row with incremented `retry_cnt`
3. Original sp201 row's `cancel_status` also updated: 0→2 (on GMO fail), then 2→1 or 2→3

Create DTO: `app/Customize/DTO/CancelResult.php`.

- **Affected Files:** `app/Customize/Service/Vpoint/VpointRedemptionService.php`, `app/Customize/DTO/CancelResult.php`
- **Parent Story:** Story 7
- **Definition of Done:**
  - [ ] Cancel called with correct `point_kbn=74`, `cancel_kbn=1`
  - [ ] `moto_date` and `moto_serial_no` reference original usage
  - [ ] Retry logic: 0→1→2 with separate `dct_vpoint_redeem_result` rows
  - [ ] `cancel_status` correctly transitions: 0→2→1 (success) or 0→2→3 (BAT recovery)
  - [ ] Failure returns structured result for BAT3/BAT4

---

##### Sub-task 7.5: Integrate V-Point Redemption into ShoppingController
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Full-stack

**Description:**
Modify `app/Customize/Controller/ShoppingController.php` to integrate V-Point redemption into the checkout flow:
1. In the order confirmation/execution action (likely `checkout` or `confirm` route):
   a. Before GMO payment: check if V-Point reservation exists via `VpointCouponService::getCouponClone()`
   b. If exists: call `VpointRedemptionService::redeem()`
   c. If redeem SUCCESS:
      - Full V-Point (coupon ≥ total): skip GMO, complete order directly
      - Partial V-Point: reduce payment amount, proceed to GMO for remainder
   d. If redeem FAIL: redirect back to checkout with error message
2. On GMO failure (after sp201 success): call `VpointRedemptionService::handleGmoFailure()`
3. STEP3 (complete page): pass V-Point coupon details to template for display

Carefully integrate with existing GMO plugin flow (`GmoPaymentGateway4`). Use events or decorator pattern if direct modification is too invasive.

- **Affected Files:** `app/Customize/Controller/ShoppingController.php`
- **Parent Story:** Story 7
- **Definition of Done:**
  - [ ] V-Point redemption executes before GMO payment
  - [ ] Full V-Point: ¥0 to GMO (or GMO skipped)
  - [ ] Partial V-Point: correct remainder amount to GMO
  - [ ] GMO failure triggers cancel retry flow
  - [ ] STEP3 displays V-Point coupon details
  - [ ] Existing non-V-Point checkout flow unaffected

---

##### Sub-task 7.6: Unit & Integration Tests for STEP2/STEP3
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create tests:
1. `VpointRedemptionServiceTest.php`:
   - Successful redemption: sp101 OK → sp201 OK → coupon issued
   - sp101 re-verify fails: reservation cleared, error returned
   - sp201 fails: no coupon issued, error returned
   - Full V-Point: coupon ≥ order total
   - Partial V-Point: coupon < order total
2. `VpointCancelFlowTest.php`:
   - Cancel succeeds on first try → cancel_status=1
   - Cancel fails, retry 1 succeeds → cancel_status=1
   - All retries fail → cancel_status=3
   - Each retry creates separate `dct_vpoint_redeem_result` row
3. `SerialNoGeneratorTest.php`:
   - Format validation, uniqueness, daily reset, JST date
4. Integration: full checkout flow with V-Point (mock sp101/sp201/GMO)

- **Affected Files:** `tests/Unit/Service/Vpoint/VpointRedemptionServiceTest.php`, `tests/Unit/Service/Vpoint/VpointCancelFlowTest.php`, `tests/Unit/Service/Vpoint/SerialNoGeneratorTest.php`
- **Parent Story:** Story 7
- **Definition of Done:**
  - [ ] All redemption paths tested (success, sp101 fail, sp201 fail)
  - [ ] Cancel retry logic tested for 0, 1, 2 retries
  - [ ] Serial number format and uniqueness verified
  - [ ] Full/partial V-Point payment tested
  - [ ] Integration test covers complete STEP2→STEP3 flow

---

### Story 8: V-Point Checkout Frontend (Twig)

**Type:** Story | **Priority:** H | **Points:** 5 | **Sprint:** 3

#### Summary
Build the Twig frontend templates and JavaScript for the V-Point checkout experience, implementing the UI states per Figma (Pu2–Pu5) across STEP1-1 (balance display + exchange input), STEP1-2 (confirmation), STEP2 (processing/loading), and STEP3 (order complete with coupon). This includes radio button selection states, numeric input validation, AJAX calls to the VpointController endpoints, and responsive mobile/desktop layout integrated into the existing EC-Cube checkout templates.

#### Requirement Details
Implements the Figma-defined UI controls:
- **Pu2**: Radio "V-Point利用" not selected → section disabled/collapsed
- **Pu3**: Radio selected → section active, balance displayed, exchange input enabled
- **Pu4**: Numeric input field, max value = current balance, validation on blur/change
- **Pu5**: Change radio to another option → keep V-Point value but disable section (preserve for re-selection)
- **Pu4 re-select**: Re-select V-Point radio → re-enable with preserved amount

STEP1-1: Balance display (AJAX call to `/shopping/vpoint/balance`), numeric input field, "交換する" (Exchange) button. STEP1-2: Confirmation of reserved amount. STEP2: Loading spinner during sp201 processing. STEP3: Order confirmation showing V-Point coupon applied and remaining balance.

- **Linked Requirements:** Figma Pu2, Pu3, Pu4, Pu5, STEP1-1, STEP1-2, STEP2, STEP3 UI requirements
- **Affected Components:** `app/template/default/Shopping/`, `html/user_data/assets/js/`
- **Scope:** Frontend

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** V-Point EC Checkout

#### Acceptance Criteria
- [ ] **Given** a customer with a linked card on the checkout page, **When** the page loads, **Then** the V-Point radio option appears (Pu2 state: not selected, section disabled)
- [ ] **Given** the V-Point radio is selected (Pu3), **When** activated, **Then** balance is fetched via AJAX and displayed as "X,XXXpt", and the exchange input field is enabled
- [ ] **Given** the exchange input (Pu4), **When** the customer enters a value > balance, **Then** client-side validation shows an error and prevents submission
- [ ] **Given** the exchange input, **When** the customer enters a non-numeric value, **Then** only digits are accepted (input filter)
- [ ] **Given** the V-Point radio is deselected (Pu5), **When** another radio is chosen, **Then** the V-Point value is preserved but the section is disabled
- [ ] **Given** V-Point was previously deselected (Pu5), **When** re-selected, **Then** the section re-enables with the previously entered amount (Pu4 re-select)
- [ ] **Given** the customer clicks "交換する," **When** the AJAX call to `/shopping/vpoint/reserve` succeeds, **Then** STEP1-2 confirmation is displayed showing the reserved amount
- [ ] **Given** STEP2 is processing, **When** sp201 is running, **Then** a loading overlay/spinner is displayed and form submission is blocked
- [ ] **Given** STEP3 (order complete), **When** the page renders, **Then** the V-Point coupon amount is shown with label "Vポイント利用: -¥X,XXX"
- [ ] **Given** sp101 returns an error, **When** the balance section renders, **Then** "＊＊＊＊pt" is shown with the error message and input is disabled
- [ ] **Given** a mobile viewport, **When** the checkout page renders, **Then** the V-Point section is fully responsive and usable

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 6 | Blocked-by | `VpointController` AJAX endpoints must exist |
| Story 7 | Blocked-by | STEP2/STEP3 backend processing must be implemented |
| Figma designs | External | UI specifications Pu2–Pu5 must be finalized |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | AJAX balance call times out (3s+ network) | Show loading state → then "＊＊＊＊pt" with retry link |
| 2 | Customer rapidly clicks "Exchange" multiple times | Debounce: disable button on first click until AJAX response |
| 3 | JavaScript disabled | V-Point section does not render (progressive enhancement) |
| 4 | Customer enters amount with leading zeros (e.g., "0100") | Parse as integer 100; display as "100" |
| 5 | Browser back button after STEP1-2 confirmation | Return to STEP1-1 with preserved amount |
| 6 | Very small viewport (320px) | Input and button stack vertically; no horizontal overflow |
| 7 | Balance is exactly ¥0 | Display "0pt"; disable Exchange button; show "ポイントがありません" |
| 8 | Customer modifies cart quantity while V-Point is applied | PurchaseFlow recalculates; if coupon > total, return to STEP1-1 |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Figma design not finalized by Sprint 3 start | Medium | Medium | Implement with placeholder styling; refine when designs arrive |
| AJAX calls conflict with existing checkout JavaScript | Medium | Medium | Namespace V-Point JS; test with existing coupon/payment scripts |
| Mobile layout breaks with existing checkout CSS | Low | Medium | Test on iOS Safari, Chrome Android; use existing responsive patterns |
| Radio state management conflicts with EC-Cube form handling | Medium | Medium | Use data attributes and custom JS, not Symfony form widget rendering |

#### Notes / Additional Information
- Integrate into existing `app/template/default/Shopping/index.twig` (checkout page) — do NOT create a separate checkout page
- Confirmation page: modify `app/template/default/Shopping/confirm.twig` to show V-Point coupon line
- Complete page: modify `app/template/default/Shopping/complete.twig`
- CSS should follow existing `html/user_data/assets/css/` patterns
- JavaScript: use jQuery (already loaded in EC-Cube) — no new framework dependencies
- CSRF token for AJAX: extract from existing form or meta tag
- Japanese text strings should use EC-Cube `trans` filter where applicable

---

#### Sub-tasks:

##### Sub-task 8.1: Create V-Point Section in Checkout Template (STEP1-1)
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Frontend

**Description:**
Modify `app/template/default/Shopping/index.twig` to add V-Point section:
1. Add radio button group for payment/coupon options including "Vポイント利用" option
2. Pu2 state (not selected): V-Point section collapsed/disabled, grey styling
3. Pu3 state (selected): section expands, AJAX call to `/shopping/vpoint/balance`, display balance
4. Balance display area: "現在のポイント残高: X,XXXpt" (or "＊＊＊＊pt" on error)
5. Pu4: Numeric input field with label "利用ポイント:", max attribute set to balance value
6. "交換する" button — triggers AJAX POST to `/shopping/vpoint/reserve`
7. Position within the order detail section, after delivery info and before payment method
8. Include CSRF token in AJAX calls

- **Affected Files:** `app/template/default/Shopping/index.twig`
- **Parent Story:** Story 8
- **Definition of Done:**
  - [ ] Radio button toggles V-Point section visibility
  - [ ] Balance fetched and displayed via AJAX on radio select
  - [ ] Numeric input with max validation
  - [ ] "交換する" button sends reservation AJAX
  - [ ] CSRF token included in AJAX requests
  - [ ] Section positioned correctly in checkout flow

---

##### Sub-task 8.2: Implement Radio State Management JavaScript (Pu2-Pu5)
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

**Description:**
Create `app/template/default/Shopping/vpoint_checkout.js` (inline or external):
1. **Pu2→Pu3**: On radio select "Vポイント利用" → expand section, fetch balance, enable input
2. **Pu3→Pu5**: On radio change to another option → collapse section but preserve input value in data attribute
3. **Pu5→Pu4**: On re-select "Vポイント利用" → expand section, restore preserved value
4. Debounce "交換する" button (prevent double-submit)
5. Client-side validation: amount must be numeric, > 0, ≤ balance, ≤ order total
6. AJAX error handling: show error messages inline below the input field
7. Loading states: spinner on balance fetch and reservation call

- **Affected Files:** `app/template/default/Shopping/index.twig` (script block or external JS file)
- **Parent Story:** Story 8
- **Definition of Done:**
  - [ ] All Pu2↔Pu3↔Pu4↔Pu5 transitions work smoothly
  - [ ] Value preserved on radio deselect/reselect
  - [ ] Input validation prevents invalid submissions
  - [ ] Debounce prevents double-submit
  - [ ] Error messages displayed inline

---

##### Sub-task 8.3: STEP1-2 Confirmation Display
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

**Description:**
After successful reservation AJAX response:
1. Replace input area with confirmation display: "Vポイント利用: ¥X,XXX (X,XXXpt交換)"
2. Show "変更する" (Change) link to return to STEP1-1 (clear reservation, re-enable input)
3. Integrate into the checkout form so the reserved amount is visible when scrolling to order summary
4. Update order total display to reflect V-Point discount

- **Affected Files:** `app/template/default/Shopping/index.twig`
- **Parent Story:** Story 8
- **Definition of Done:**
  - [ ] Confirmation replaces input after successful reservation
  - [ ] "変更する" link clears reservation and returns to input state
  - [ ] Order total updates to show discount
  - [ ] No additional backend call (UI-only transition)

---

##### Sub-task 8.4: STEP2 Loading State & STEP3 Completion Display
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Frontend

**Description:**
1. **STEP2 loading**: When checkout form is submitted with V-Point reservation active:
   - Display full-page loading overlay with spinner and message "注文処理中..."
   - Prevent form re-submission (disable submit button)
   - Handle timeout/error: remove overlay, show error message
2. **STEP3 complete**: Modify `app/template/default/Shopping/complete.twig`:
   - Add V-Point coupon line in order summary: "Vポイント利用: -¥X,XXX"
   - Show remaining balance if available: "Vポイント残高: X,XXXpt"
3. Modify `app/template/default/Shopping/confirm.twig`:
   - Show V-Point discount line in order confirmation summary

- **Affected Files:** `app/template/default/Shopping/confirm.twig`, `app/template/default/Shopping/complete.twig`, `app/template/default/Shopping/index.twig`
- **Parent Story:** Story 8
- **Definition of Done:**
  - [ ] Loading overlay displays during STEP2 processing
  - [ ] Form re-submission prevented
  - [ ] Confirm page shows V-Point discount line
  - [ ] Complete page shows V-Point amount and remaining balance
  - [ ] Non-V-Point orders display unchanged

---

##### Sub-task 8.5: Responsive CSS & Mobile Optimization
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Frontend

**Description:**
1. Style V-Point section to match existing EC-Cube checkout design patterns
2. Mobile breakpoints: stack radio + input vertically below 768px
3. Touch-friendly: minimum 44px tap targets for radio buttons and Exchange button
4. Test on: iOS Safari, Android Chrome, desktop Chrome/Firefox
5. Follow existing CSS conventions in `html/user_data/assets/css/`
6. Add CSS either inline in template or in `html/user_data/assets/css/vpoint.css`

- **Affected Files:** `html/user_data/assets/css/vpoint.css` or inline styles in template
- **Parent Story:** Story 8
- **Definition of Done:**
  - [ ] Desktop layout: inline radio + input + button
  - [ ] Mobile layout: stacked vertically, full-width input
  - [ ] 44px minimum tap targets
  - [ ] No horizontal scroll on 320px viewport
  - [ ] Visual consistency with existing checkout design

---

##### Sub-task 8.6: Frontend Manual Testing & Browser Compatibility
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Frontend

**Description:**
Manual testing checklist:
1. Desktop Chrome: full flow STEP1-1 → STEP1-2 → STEP2 → STEP3
2. Desktop Firefox: same flow
3. iOS Safari (mobile): responsive layout, touch interactions, AJAX calls
4. Android Chrome (mobile): same as iOS
5. Edge cases: back button, refresh, logout during checkout, slow network
6. Accessibility: tab navigation, screen reader compatibility for radio buttons and input labels
7. Document any Figma discrepancies for designer review

- **Affected Files:** (testing only — no file changes)
- **Parent Story:** Story 8
- **Definition of Done:**
  - [ ] All 4 browsers tested
  - [ ] Full checkout flow verified on mobile
  - [ ] No JavaScript console errors
  - [ ] Accessibility: labels, tab order, ARIA attributes verified
  - [ ] Known issues documented if any

---

### Story 9: V-Point Native App Integration

**Type:** Story | **Priority:** M | **Points:** 5 | **Sprint:** 4

#### Summary
Expose V-Point functionality to the MrMax native mobile app via three REST API endpoints: balance inquiry, exchange denominations list, and point redemption. The native app presents a dedicated V-Point UI with 9 exchange buttons (¥100–¥50,000) in a 3+accordion layout, different from the EC web free-input approach. Redemption uses `gyotai_cd=00000001` (Native) and serial_no prefix `A03`. On successful redemption, the API returns a coupon object and a Karte event payload for analytics tracking.

#### Requirement Details
Three API endpoints under `/api/v1/vpoint/`:
1. **GET /api/v1/vpoint/balance** — calls sp101, returns `{balance, raw_balance, error_msg, is_linked}`. Balance formatted as "X,XXXpt"; on failure returns "＊＊＊＊pt".
2. **GET /api/v1/vpoint/exchanges** — returns the 9 denominations from `dct_vpoint_exchanges` with disabled flags (amount > balance → disabled), plus `show_all_first=false` (default: show 3, expand to 9).
3. **POST /api/v1/vpoint/redeem** — full redemption: sp101 verify → generate serial_no (A03) → sp201 (gyotai_cd=00000001) → issue coupon → return `{success, coupon, new_balance, karte_event}`.

The native app UI renders 9 buttons: "すべて" (All balance) first, then ascending ¥100→¥50,000. Default display shows 3 buttons + accordion toggle to reveal all 9. The backend returns all 9 denominations; the app handles the 3+accordion display logic.

- **Linked Requirements:** SRS Native App V-Point section, API contract for mobile app, Karte event specification
- **Affected Components:** `app/Customize/Controller/Api/VpointApiController.php`, `app/Customize/Service/Vpoint/VpointRedemptionService.php`
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** V-Point Native App

#### Acceptance Criteria
- [ ] **Given** a linked native app user, **When** `GET /api/v1/vpoint/balance` is called, **Then** the response contains `{balance: 2000, raw_balance: 2000, formatted: "2,000pt", error_msg: null, is_linked: true}`
- [ ] **Given** sp101 fails, **When** the balance endpoint is called, **Then** `{balance: null, formatted: "＊＊＊＊pt", error_msg: "<Japanese message>", is_linked: true}`
- [ ] **Given** the user has no linked card, **When** the balance endpoint is called, **Then** `{balance: null, formatted: null, error_msg: null, is_linked: false}`
- [ ] **Given** a balance of 2,000pt, **When** `GET /api/v1/vpoint/exchanges` is called, **Then** 9 exchange options are returned with amounts > 2,000 marked as `disabled: true`, plus an "All" option with `amount: 2000`
- [ ] **Given** a valid exchange selection, **When** `POST /api/v1/vpoint/redeem` is called with `{amount: 1000}`, **Then** sp201 is called with `gyotai_cd=00000001` and serial_no prefix `A03`
- [ ] **Given** redemption succeeds, **When** the response is returned, **Then** it contains `{success: true, coupon: {id, amount, serial_no, expires_at}, new_balance: 1000, karte_event: {event_name: "vpoint_redeem", properties: {...}}}`
- [ ] **Given** redemption fails (sp201 error), **When** the response is returned, **Then** `{success: false, error_msg: "<Japanese message>", coupon: null}`
- [ ] **Given** the "All" button is selected, **When** the user redeems, **Then** the full balance amount is used (not a fixed denomination)
- [ ] **Given** the API is called without authentication, **When** the request is received, **Then** 401 Unauthorized is returned

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_exchanges` entity/seed data, `dct_vpoint_redeem_result` entity |
| Story 2 | Blocked-by | `VpointApiClient` for sp101/sp201 calls |
| Story 7 | Reuses | `VpointRedemptionService`, `VpointCouponService`, `SerialNoGenerator` |
| Native App Team | External | App team must implement frontend UI consuming these endpoints |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | "All" selected but balance changes between exchanges list and redeem call | sp101 re-verify in redeem catches the change; error returned if insufficient |
| 2 | Exchange amount not matching any denomination (API abuse) | Accept any valid amount ≤ balance; denominations are UI suggestion only |
| 3 | Concurrent redeem calls from same user (double-tap) | Idempotency: second call sees coupon already issued; return existing coupon |
| 4 | User's card is unlinked between balance check and redeem | sp101 re-verify fails; return error with `is_linked: false` |
| 5 | Balance is less than minimum denomination (¥100) | Only "All" button is enabled; denomination buttons all disabled |
| 6 | API rate limiting | Return 429 Too Many Requests if >10 requests/minute per user |
| 7 | Karte event payload fails to serialize | Redeem still succeeds; karte_event returned as null with warning logged |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Native app team delays API integration | Medium | Medium | Provide Swagger/OpenAPI spec early; mock server for parallel development |
| Karte event format changes mid-sprint | Low | Low | Karte payload defined as JSON object; easy to modify |
| API authentication mechanism differs from existing POS API | Low | Medium | Reuse existing `Api/PosController.php` auth pattern (Bearer token) |
| gyotai_cd mismatch with CCCMK registration | Low | High | Confirm `00000001` is registered for Native channel with CCCMK |

#### Notes / Additional Information
- Follow existing API patterns in `app/Customize/Controller/Api/PosController.php` and `Api/CouponController.php`
- Authentication: Bearer token (same as existing mobile API endpoints)
- `gyotai_cd=00000001` for Native (vs EC web `gyotai_cd` from env)
- Serial_no prefix `A03` for Native (vs `A04` for EC)
- Karte event payload: `{event_name: "vpoint_redeem", properties: {amount, serial_no, customer_id, balance_before, balance_after, channel: "native"}}`
- The "All" denomination is dynamic — its amount equals the current balance, not a fixed value
- The `show_all_first` flag tells the app whether to show all 9 buttons initially or just 3+accordion; default is `false` (3+accordion)

---

#### Sub-tasks:

##### Sub-task 9.1: Create VpointApiController — Balance Endpoint
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Create `app/Customize/Controller/Api/VpointApiController.php` with route `GET /api/v1/vpoint/balance`:
1. Authenticate via Bearer token (follow existing `PosController` pattern)
2. Identify customer from token → check `CustomerCardInfoRepository::findActiveByAppMemberId()`
3. If not linked: return `{balance: null, formatted: null, error_msg: null, is_linked: false}`
4. Call `VpointApiClient::balanceInquiry()`
5. On success: return `{balance: int, raw_balance: int, formatted: "X,XXXpt", error_msg: null, is_linked: true}`
6. On failure: return `{balance: null, formatted: "＊＊＊＊pt", error_msg: "...", is_linked: true}`
7. Response format: JSON with `Content-Type: application/json`

- **Affected Files:** `app/Customize/Controller/Api/VpointApiController.php`
- **Parent Story:** Story 9
- **Definition of Done:**
  - [ ] Route registered and accessible with Bearer token auth
  - [ ] Unlinked user returns `is_linked: false`
  - [ ] Balance formatted with thousands separator
  - [ ] sp101 failure returns "＊＊＊＊pt"
  - [ ] 401 for unauthenticated requests

---

##### Sub-task 9.2: Create VpointApiController — Exchanges Endpoint
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Add route `GET /api/v1/vpoint/exchanges` to `VpointApiController.php`:
1. Fetch current balance (reuse sp101 or accept `?balance=XXXX` query param from client cache)
2. Query `VpointExchangeRepository::findAllActiveSorted()` → 9 denominations
3. Build response array with "All" first:
   ```json
   {
     "exchanges": [
       {"id": 0, "amount": <balance>, "label": "すべて", "disabled": false},
       {"id": 1, "amount": 100, "label": "100pt", "disabled": false},
       ...
       {"id": 9, "amount": 50000, "label": "50,000pt", "disabled": true}
     ],
     "show_all_first": false
   }
   ```
4. Mark `disabled: true` where `amount > balance`
5. "All" amount = current balance (dynamic); disabled if balance ≤ 0

- **Affected Files:** `app/Customize/Controller/Api/VpointApiController.php`
- **Parent Story:** Story 9
- **Definition of Done:**
  - [ ] 9 denominations + "All" = 10 items returned
  - [ ] Disabled flag correct based on balance
  - [ ] "All" amount equals current balance
  - [ ] Sorted: All first, then ¥100→¥50,000 ascending

---

##### Sub-task 9.3: Create VpointApiController — Redeem Endpoint
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Add route `POST /api/v1/vpoint/redeem` to `VpointApiController.php`:
1. Accept JSON body: `{amount: int}`
2. Validate amount > 0, amount ≤ balance
3. Call `VpointRedemptionService::redeemNative(Customer $customer, int $amount)`:
   a. sp101 re-verify balance
   b. Generate serial_no with prefix `A03`
   c. Insert `dct_vpoint_redeem_result` with `gyotai_cd=00000001`, `program_name=1`
   d. Call sp201 (`point_kbn=73`)
   e. Issue coupon via `VpointCouponService::issueCoupon()`
4. Build Karte event payload: `{event_name: "vpoint_redeem", properties: {amount, serial_no, customer_id, balance_before, balance_after, channel: "native"}}`
5. On success: `{success: true, coupon: {id, amount, serial_no, expires_at}, new_balance: int, karte_event: {...}}`
6. On failure: `{success: false, error_msg: "...", coupon: null, karte_event: null}`

Add `redeemNative()` method to `VpointRedemptionService` — similar to `redeem()` but without reservation/GMO logic, using A03 prefix and native gyotai_cd.

- **Affected Files:** `app/Customize/Controller/Api/VpointApiController.php`, `app/Customize/Service/Vpoint/VpointRedemptionService.php`
- **Parent Story:** Story 9
- **Definition of Done:**
  - [ ] Full sp101→sp201→coupon flow in single API call
  - [ ] Serial_no uses A03 prefix
  - [ ] `gyotai_cd=00000001` sent to sp201
  - [ ] Karte event payload returned on success
  - [ ] sp201 failure returns error message, no coupon
  - [ ] Concurrent double-tap handled (idempotency check)

---

##### Sub-task 9.4: API Documentation & Swagger Spec
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Full-stack

**Description:**
Create or update Swagger/OpenAPI specification in `swagger/` directory:
1. Document all 3 V-Point API endpoints with request/response schemas
2. Include authentication requirements (Bearer token)
3. Document error codes and response structures
4. Add example requests/responses for each endpoint
5. Share with native app team for parallel development

- **Affected Files:** `swagger/vpoint-api.yaml`
- **Parent Story:** Story 9
- **Definition of Done:**
  - [ ] All 3 endpoints documented with schemas
  - [ ] Example requests/responses included
  - [ ] Authentication documented
  - [ ] Error responses documented
  - [ ] Shared with native app team

---

##### Sub-task 9.5: Unit & Integration Tests for Native API
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create tests:
1. `VpointApiControllerTest.php`:
   - Balance: linked user success, linked user sp101 fail, unlinked user, unauthenticated
   - Exchanges: correct disabled flags, "All" dynamic amount, sorted order
   - Redeem: success flow, sp201 failure, insufficient balance, double-tap idempotency
2. `VpointRedemptionServiceNativeTest.php`:
   - Native-specific: A03 prefix, gyotai_cd=00000001
   - Karte event payload structure
3. Authentication tests: valid token, expired token, missing token

- **Affected Files:** `tests/Unit/Controller/Api/VpointApiControllerTest.php`, `tests/Unit/Service/Vpoint/VpointRedemptionServiceNativeTest.php`
- **Parent Story:** Story 9
- **Definition of Done:**
  - [ ] All endpoints tested with valid/invalid inputs
  - [ ] Auth tests cover all token scenarios
  - [ ] Native-specific parameters verified (A03, gyotai_cd)
  - [ ] Karte event structure validated

---

### Story 10: SP Recovery & Result File Batches (BAT3 + BAT4)

**Type:** Story | **Priority:** H | **Points:** 8 | **Sprint:** 4

#### Summary
Implement two batch processes for V-Point cancel recovery: BAT3 generates SP (cancel request) files for records where online cancel retries failed (`cancel_status=2`), uploads to S3 with AES-256-SSE encryption, and updates status to `cancel_status=3`; BAT4 downloads SE (cancel result) files from CCCMK via HTTPS, parses the results, and updates `cancel_status` to 4 (success) or 5 (error) based on the response. Together they provide the asynchronous recovery path for V-Point cancellations that couldn't be completed in real-time during checkout.

#### Requirement Details
**BAT3 (SP File Generation):**
- Schedule: daily morning run
- Query: `dct_vpoint_redeem_result WHERE cancel_status=2`
- File format: 783 bytes/record, Shift_JIS(CP932), CRLF line endings
- 13 validation checks: checks 4-6 and 9-11 → EXCLUDE record; checks 7-8 → AUTO-FIX
- File naming: `URIxxxxSPyy.DAT` (xxxx=Alliance Code from AWS Secrets Manager, yy=sequence)
- Upload to S3 with AES-256-SSE encryption
- After upload: update `cancel_status` 2→3, `retry_cnt=0`
- Empty file: header only (0 body records) — still uploaded
- File merge: if CCCMK hasn't retrieved previous day's file, merge new records into existing file
- Redis lock (TTL=30min) to prevent concurrent execution
- 3 Slack alert categories: validation warning, S3 upload failed, retrieval warning
- Supports `--dry-run` and `--verbose` CLI options

**BAT4 (SE File Processing):**
- Schedule: daily afternoon run
- Download: HTTPS GET from `edi.tpoint.jp/adi010.do` (PROD)
- File format: 794 bytes/record, Shift_JIS
- Parse SE file → match `serial_no` against `dct_vpoint_redeem_result (cancel_status=3)`
- Result mapping: `error_cd="000"` → `cancel_status=4` (Completed); `error_cd≠"000"` → `cancel_status=5` (Error) + store error_cd
- Skip records where `cancel_status≠3` (idempotent re-processing)
- `program_name=4` (BAT4) written to result records
- Move processed file to backup folder in S3
- Redis lock, `--dry-run`, `--date=YYYYMMDD` CLI options
- Retry on download failure: exponential backoff 0s, 5s, 15s, 45s (max 4 attempts)
- Slack notification on completion/errors

- **Linked Requirements:** SRS BAT3 (SP File), BAT4 (SE File), Section 6.2 (SP validation), Section 6.3 (SE parsing), cancel_status state machine
- **Affected Components:** `app/Customize/Command/`, `app/Customize/Service/Vpoint/`
- **Scope:** Backend

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Batch Processing — Cancel Recovery

#### Acceptance Criteria
- [ ] **Given** `dct_vpoint_redeem_result` contains records with `cancel_status=2`, **When** BAT3 runs, **Then** an SP file is generated with correct format (783 bytes/record, Shift_JIS, CRLF)
- [ ] **Given** the SP file is generated, **When** uploaded to S3, **Then** AES-256-SSE encryption is applied and the file key follows `URIxxxxSPyy.DAT` naming
- [ ] **Given** records have `cancel_status=2`, **When** BAT3 completes successfully, **Then** those records are updated to `cancel_status=3` and `retry_cnt=0`
- [ ] **Given** SP validation checks 4-6 or 9-11 fail for a record, **When** BAT3 processes it, **Then** the record is EXCLUDED from the file and a Slack validation warning is sent
- [ ] **Given** SP validation checks 7-8 fail for a record, **When** BAT3 processes it, **Then** the fields are AUTO-FIXED and the record is included
- [ ] **Given** no records have `cancel_status=2`, **When** BAT3 runs, **Then** a header-only file (0 body records) is uploaded
- [ ] **Given** CCCMK has not retrieved the previous day's SP file, **When** BAT3 runs, **Then** new records are merged into the existing file
- [ ] **Given** BAT4 runs, **When** it downloads the SE file from CCCMK, **Then** the file is retrieved via HTTPS GET from `edi.tpoint.jp/adi010.do`
- [ ] **Given** an SE record with `error_cd="000"`, **When** BAT4 processes it, **Then** the matching `dct_vpoint_redeem_result` record is updated to `cancel_status=4`
- [ ] **Given** an SE record with `error_cd≠"000"`, **When** BAT4 processes it, **Then** the matching record is updated to `cancel_status=5` with the error_cd stored
- [ ] **Given** an SE record whose `serial_no` matches a `dct_vpoint_redeem_result` with `cancel_status≠3`, **When** BAT4 processes it, **Then** the record is SKIPPED (idempotent)
- [ ] **Given** the SE file download fails, **When** BAT4 retries, **Then** exponential backoff is applied: 0s, 5s, 15s, 45s (max 4 attempts)
- [ ] **Given** BAT3 is already running (Redis lock held), **When** another instance starts, **Then** the second instance exits immediately with a warning
- [ ] **Given** `--dry-run` flag, **When** BAT3 or BAT4 runs, **Then** no database updates or file uploads occur; output shows what would happen

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` entity with `cancel_status` field |
| Story 7 | Produces-for | `cancel_status=2` records created by failed cancel retries in STEP2 |
| AWS Secrets Manager | External | Alliance Code for file naming retrieved from Secrets Manager |
| CCCMK EDI endpoint | External | `edi.tpoint.jp/adi010.do` must be accessible from production |
| S3 bucket | Infrastructure | S3 bucket for SP/SE file storage |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | BAT3: All records fail validation (checks 4-6) | Header-only file uploaded; all records get Slack validation warning |
| 2 | BAT3: S3 upload fails after file generation | Retry S3 upload 3 times; on final failure, Slack alert, records stay at cancel_status=2 for next run |
| 3 | BAT3: Redis lock acquisition fails (previous run still active) | Exit with code 0 and log warning; Slack alert if lock age > 45 min |
| 4 | BAT4: SE file contains serial_no not in our database | Skip record; log warning |
| 5 | BAT4: SE file is empty (0 records) | Complete successfully; no database updates |
| 6 | BAT4: HTTPS download returns 404 (no file available) | Complete successfully; log "no SE file available" |
| 7 | BAT4: Same SE file processed twice (re-run) | Idempotent: skip records where cancel_status already 4 or 5 |
| 8 | BAT3: File merge — previous day's file has 100 records, today adds 50 | Merged file has 150 records with updated header/trailer counts |
| 9 | BAT3: --verbose flag shows each record's validation result | Console output: "Record {serial_no}: PASS/FAIL (check N)" per record |
| 10 | BAT4: --date=YYYYMMDD processes a specific date's SE file | Override today's date for download path; useful for reprocessing |
| 11 | Character encoding: Shift_JIS contains 0x5C (yen sign / backslash) | Proper CP932 encoding used (not plain Shift_JIS) to handle 0x5C correctly |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| CCCMK EDI endpoint unavailable or URL changes | Low | High | URL configurable via env var; exponential backoff; Slack alert |
| SP file format mismatch with CCCMK specification | Medium | High | Validate against CCCMK-provided sample SP file; byte-level testing |
| SE file parsing error due to encoding issues | Medium | Medium | Use CP932 (not plain Shift_JIS); validate with sample SE file |
| Alliance Code rotation in Secrets Manager | Low | Medium | Cache with TTL; refresh on each BAT3 run |
| S3 SSE encryption configuration incorrect | Low | Medium | Verify `x-amz-server-side-encryption: AES256` header in upload |
| File merge logic corrupts existing file | Low | High | Backup existing file before merge; validate merged file byte count |

#### Notes / Additional Information
- Batch command naming: follow existing pattern `Batch032Command.php` (BAT3) and `Batch033Command.php` (BAT4) — next available numbers after Batch031
- Alternative naming: `VpointSpFileCommand.php` and `VpointSeFileCommand.php` for clarity
- `cancel_status` state machine: 0(initial)→2(cancel failed)→3(BAT3 processed)→4(BAT4 success)/5(BAT4 error)
- SP file: 783 bytes per record is FIXED — pad/truncate fields to exact byte widths
- SE file: 794 bytes per record — fixed-length, different field layout from SP
- Alliance Code from Secrets Manager: use AWS SDK `SecretsManagerClient::getSecretValue()`
- Redis lock key: `vpoint_bat3_lock` / `vpoint_bat4_lock` with TTL=1800s
- Slack channels may differ from BAT1/BAT2 channels — configurable via env
- `program_name=3` for BAT3 records, `program_name=4` for BAT4 records
- The 13 SP validation checks are enumerated in SRS Section 6.2

---

#### Sub-tasks:

##### Sub-task 10.1: Create BAT3 SP File Generator Service
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SpFileGeneratorService.php`:
1. `generateSpFile(array $records): string` — builds SP file content:
   - Header record: file date, alliance code, record count
   - Body records: 783 bytes each, Shift_JIS(CP932) encoding, CRLF
   - Each record: serialize `dct_vpoint_redeem_result` fields into fixed-width byte positions
2. `validateRecord(VpointRedeemResult $record): ValidationResult` — applies 13 validation checks:
   - Checks 1-3: format/structure (PASS required)
   - Checks 4-6: EXCLUDE record on failure
   - Checks 7-8: AUTO-FIX on failure (pad/trim fields)
   - Checks 9-11: EXCLUDE record on failure
   - Checks 12-13: format/structure (PASS required)
3. `mergeFiles(string $existingContent, string $newContent): string` — merge new records into existing SP file, update header/trailer counts
4. File encoding: PHP `mb_convert_encoding('UTF-8', 'CP932')` for each field
5. Pad fields to exact byte widths per CCCMK specification

- **Affected Files:** `app/Customize/Service/Vpoint/SpFileGeneratorService.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] SP file output is exactly 783 bytes per body record
  - [ ] Shift_JIS(CP932) encoding applied correctly
  - [ ] CRLF line endings
  - [ ] All 13 validation checks implemented
  - [ ] Auto-fix for checks 7-8 works correctly
  - [ ] File merge preserves existing records and updates counts

---

##### Sub-task 10.2: Create BAT3 Console Command
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Command/VpointSpFileCommand.php` (BAT3):
1. Register as `app:vpoint:sp-generate` (or `batch032:vpoint-sp-generate`)
2. Acquire Redis lock `vpoint_bat3_lock` (TTL=1800s) — exit if locked
3. Query `VpointRedeemResultRepository::findByCancelStatus(2)`
4. Call `SpFileGeneratorService::generateSpFile()` with validated records
5. Retrieve Alliance Code from AWS Secrets Manager
6. Build filename: `URIxxxxSPyy.DAT`
7. Check for un-retrieved previous file → merge if exists
8. Upload to S3 with `ServerSideEncryption=AES256`
9. Update records: `cancel_status` 2→3, `retry_cnt=0`, `program_name=3`
10. Send Slack notifications:
    - Validation warnings (excluded records)
    - S3 upload failure
    - Retrieval warning (previous file not picked up)
11. Support `--dry-run` (no DB/S3 changes) and `--verbose` (per-record output)
12. Release Redis lock

- **Affected Files:** `app/Customize/Command/VpointSpFileCommand.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] Redis lock prevents concurrent execution
  - [ ] Records queried by `cancel_status=2`
  - [ ] Alliance Code retrieved from Secrets Manager
  - [ ] File uploaded to S3 with AES-256-SSE
  - [ ] Records updated to `cancel_status=3` after successful upload
  - [ ] File merge works when previous file exists
  - [ ] `--dry-run` produces output without side effects
  - [ ] `--verbose` shows per-record validation results
  - [ ] 3 Slack alert categories sent appropriately

---

##### Sub-task 10.3: Create BAT4 SE File Parser Service
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Vpoint/SeFileParserService.php`:
1. `parseSeFile(string $content): array` — parse SE file (794 bytes/record, Shift_JIS):
   - Header record: file date, alliance code, record count
   - Body records: extract `serial_no`, `error_cd`, and other fields from fixed positions
   - Trailer record: verify record count
2. `convertEncoding(string $rawContent): string` — Shift_JIS to UTF-8 conversion
3. Return array of `SeRecord` DTOs: `{serial_no, error_cd, raw_data}`

Create DTO: `app/Customize/DTO/SeRecord.php`.

- **Affected Files:** `app/Customize/Service/Vpoint/SeFileParserService.php`, `app/Customize/DTO/SeRecord.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] 794 bytes/record parsed correctly
  - [ ] `serial_no` and `error_cd` extracted from correct byte positions
  - [ ] Shift_JIS to UTF-8 encoding conversion correct
  - [ ] Header/trailer record count validation
  - [ ] Empty file handled gracefully

---

##### Sub-task 10.4: Create BAT4 Console Command
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Command/VpointSeFileCommand.php` (BAT4):
1. Register as `app:vpoint:se-process` (or `batch033:vpoint-se-process`)
2. Acquire Redis lock `vpoint_bat4_lock` (TTL=1800s) — exit if locked
3. Download SE file via HTTPS GET from `edi.tpoint.jp/adi010.do` (PROD endpoint from env var)
4. Retry with exponential backoff: 0s, 5s, 15s, 45s (max 4 attempts)
5. Parse file via `SeFileParserService::parseSeFile()`
6. For each SE record:
   a. Lookup `dct_vpoint_redeem_result` by `serial_no` WHERE `cancel_status=3`
   b. If not found or `cancel_status≠3` → skip (idempotent)
   c. `error_cd="000"` → update `cancel_status=4`, `program_name=4`
   d. `error_cd≠"000"` → update `cancel_status=5`, store `error_cd`, `program_name=4`
7. Move processed file to backup folder in S3: `vpoint/se-backup/{YYYYMMDD}/{filename}`
8. Send Slack notification with completion summary: processed count, success/error counts
9. Support `--dry-run` and `--date=YYYYMMDD` CLI options
10. Release Redis lock

- **Affected Files:** `app/Customize/Command/VpointSeFileCommand.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] HTTPS download with exponential backoff retry
  - [ ] SE records matched by `serial_no` against `cancel_status=3` records
  - [ ] `error_cd="000"` → `cancel_status=4`; others → `cancel_status=5`
  - [ ] Idempotent: skip if `cancel_status≠3`
  - [ ] File backed up to S3 after processing
  - [ ] `--dry-run` shows what would happen without changes
  - [ ] `--date` allows reprocessing a specific date
  - [ ] Slack notification on completion/errors
  - [ ] Redis lock prevents concurrent execution

---

##### Sub-task 10.5: Implement Slack Notification Service for BAT3/BAT4
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Create or extend `app/Customize/Service/Vpoint/VpointBatchSlackService.php`:
1. **BAT3 notifications:**
   - `sendValidationWarning(array $excludedRecords): void` — list of records excluded with reasons
   - `sendUploadFailure(string $filename, string $error): void` — S3 upload failure alert
   - `sendRetrievalWarning(): void` — CCCMK hasn't retrieved previous day's file
   - `sendBat3Summary(int $total, int $included, int $excluded, int $autoFixed): void`
2. **BAT4 notifications:**
   - `sendBat4Summary(int $processed, int $success, int $errors): void` — completion summary
   - `sendDownloadFailure(string $url, int $attempts): void` — HTTPS download failure
3. Channel configurable via env: `VPOINT_BAT_SLACK_CHANNEL`, `VPOINT_BAT_SLACK_WEBHOOK`
4. Use existing Slack integration pattern from codebase

- **Affected Files:** `app/Customize/Service/Vpoint/VpointBatchSlackService.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] All 3 BAT3 alert categories implemented
  - [ ] BAT4 completion and error notifications work
  - [ ] Slack channel configurable via env
  - [ ] Notification failures logged but don't block batch execution

---

##### Sub-task 10.6: AWS Secrets Manager Integration for Alliance Code
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend/DevOps

**Description:**
Create `app/Customize/Service/Vpoint/VpointSecretsService.php`:
1. `getAllianceCode(): string` — retrieve from AWS Secrets Manager using AWS SDK
2. Secret name configurable via env: `VPOINT_SECRET_NAME`
3. Cache the value for the duration of the batch run (no re-fetch per record)
4. Handle Secrets Manager unavailability: throw clear exception with message
5. Use existing AWS SDK setup from codebase (check for `Aws\SecretsManager\SecretsManagerClient`)

- **Affected Files:** `app/Customize/Service/Vpoint/VpointSecretsService.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] Alliance Code retrieved from Secrets Manager
  - [ ] Value cached per batch run
  - [ ] Clear error message if Secrets Manager unavailable
  - [ ] Secret name configurable via env var

---

##### Sub-task 10.7: Environment Configuration & Cron Setup
**Type:** Sub-task | **Estimate:** 2h | **Skill:** DevOps

**Description:**
1. Add environment variables to `.env.dist`:
   - `VPOINT_SE_DOWNLOAD_URL=https://edi.tpoint.jp/adi010.do`
   - `VPOINT_SP_S3_BUCKET`, `VPOINT_SP_S3_PREFIX=vpoint/sp/`
   - `VPOINT_SE_S3_BACKUP_PREFIX=vpoint/se-backup/`
   - `VPOINT_SECRET_NAME` (AWS Secrets Manager secret name)
   - `VPOINT_BAT_SLACK_WEBHOOK`, `VPOINT_BAT_SLACK_CHANNEL`
   - `VPOINT_BAT3_REDIS_LOCK_TTL=1800`
   - `VPOINT_BAT4_REDIS_LOCK_TTL=1800`
   - `VPOINT_BAT4_RETRY_MAX=4`
2. Configure cron schedules:
   - BAT3: `0 6 * * *` (daily 06:00 AM JST)
   - BAT4: `0 14 * * *` (daily 02:00 PM JST)
3. Update batch Docker/ECS configuration (`taskdef-batch.json`, `docker-compose.batch.dev.yml`)

- **Affected Files:** `.env.dist`, `taskdef-batch.json`, `docker-compose.batch.dev.yml`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] All environment variables documented in `.env.dist`
  - [ ] Cron schedules configured for both BAT3 and BAT4
  - [ ] Batch container can execute both commands
  - [ ] ECS task definitions updated if applicable

---

##### Sub-task 10.8: Unit & Integration Tests for BAT3/BAT4
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create comprehensive tests:
1. `SpFileGeneratorServiceTest.php`:
   - Correct file format (783 bytes/record)
   - Shift_JIS encoding output
   - All 13 validation checks individually
   - Auto-fix for checks 7-8
   - File merge with existing content
   - Empty file (header only)
2. `SeFileParserServiceTest.php`:
   - Correct parsing (794 bytes/record)
   - `serial_no` and `error_cd` extraction
   - Encoding conversion
   - Empty file handling
3. `VpointSpFileCommandTest.php`:
   - Redis lock acquisition/release
   - `cancel_status` transition 2→3
   - `--dry-run` produces no side effects
   - S3 upload mock
4. `VpointSeFileCommandTest.php`:
   - HTTPS download with mock server
   - Exponential backoff retry logic
   - `cancel_status` 3→4 (success) and 3→5 (error)
   - Idempotent re-processing
   - `--date` flag override
5. Integration: BAT3 generates file → BAT4 processes result → verify final states

- **Affected Files:** `tests/Unit/Service/Vpoint/SpFileGeneratorServiceTest.php`, `tests/Unit/Service/Vpoint/SeFileParserServiceTest.php`, `tests/Unit/Command/VpointSpFileCommandTest.php`, `tests/Unit/Command/VpointSeFileCommandTest.php`
- **Parent Story:** Story 10
- **Definition of Done:**
  - [ ] SP file byte-level format validated
  - [ ] All 13 SP validation checks tested
  - [ ] SE file parsing tested with sample data
  - [ ] Retry logic tested with simulated failures
  - [ ] State transitions verified for all cancel_status values
  - [ ] Dry-run mode verified for both commands
  - [ ] Integration test: BAT3→BAT4 end-to-end

### Story 11: V-Point Coupon Display, History & Purchase Status

**Type:** Story | **Priority:** M | **Points:** 8 | **Sprint:** 5

#### Summary
Modify the EC coupon list and purchase history screens so that V-Point checkout coupons (`coupon_id=999999990001`) are excluded from the active coupon list but appear on the Used/Expired tab, merged and date-sorted with other coupons. Add cancel-status indicators to purchase history items that used V-Point redemption, and implement a dynamic V-Point denomination banner powered by `dct_vpoint_exchanges` data.

#### Requirement Details
Three distinct changes: (1) Filter `coupon_id=999999990001` out of the active EC coupon list returned by `getAllSpecialMyCoupons()`, but include them in the history returned by `getCouponHistory()` — combined with Native App/Shop coupons in a single date-sorted list (DESC by `update_date`), removing the current type-based separation. Native app / shop coupons follow existing behavior with no change. V-Point coupons are identified by a `source_type` flag on `dct_coupon_target`. (2) In purchase history, display cancel status from `dct_vpoint_redeem_result.cancel_status` matched by `serial_no` from `dct_coupon_target`: no cancel → coupon name only; status 2/3 → "※ ポイント利用キャンセル処理中"; status 4 → "✅ ポイント利用キャンセル済"; status 5 → processing message + error from sp201(Cancel) per [7.Error MSG] sheet. (3) Dynamic coupon banner via `VpointBannerService` that reads denomination rows from `dct_vpoint_exchanges`.

- **Linked Requirements:** SRS Coupon Display rules, Section 7 (Error Messages), dct_coupon_target.source_type, dct_vpoint_redeem_result.cancel_status
- **Affected Components:** `app/Customize/Repository/CouponTargetRepository.php`, `app/Customize/Controller/CouponController.php`, `app/Customize/Controller/Api/CouponController.php`, `app/Customize/Controller/Api/V2/CouponController.php`, `app/Customize/Service/CouponService.php`, `app/Customize/Service/VpointBannerService.php` (new), `app/template/default/Mypage/` (coupon list, history, purchase detail Twig templates)
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Coupon & Purchase Status Display

#### Acceptance Criteria
- [ ] **Given** a customer with V-Point checkout coupons (coupon_id=999999990001), **When** the active EC coupon list is loaded, **Then** those coupons do NOT appear in the active list
- [ ] **Given** a customer with used/expired V-Point coupons, **When** the Used/Expired tab is loaded, **Then** V-Point coupons appear intermixed with other coupon types, sorted by `update_date DESC`
- [ ] **Given** used/expired coupons from EC, Native App, and Shop sources, **When** displayed on the Used/Expired tab, **Then** all types appear in a single combined list — NOT separated by source type
- [ ] **Given** a Native App or Shop V-Point coupon, **When** displayed, **Then** behavior is unchanged from the existing implementation
- [ ] **Given** a purchase history item with `cancel_status=0` or no cancel record, **When** the purchase detail is shown, **Then** only the coupon name is displayed
- [ ] **Given** a purchase history item with `cancel_status=2` or `cancel_status=3`, **When** the purchase detail is shown, **Then** "※ ポイント利用キャンセル処理中" is displayed below the coupon name
- [ ] **Given** a purchase history item with `cancel_status=4`, **When** the purchase detail is shown, **Then** "✅ ポイント利用キャンセル済" is displayed below the coupon name
- [ ] **Given** a purchase history item with `cancel_status=5`, **When** the purchase detail is shown, **Then** the processing message AND the sp201(Cancel) error from [7.Error MSG] sheet are displayed
- [ ] **Given** `dct_vpoint_exchanges` has denomination rows, **When** the V-Point banner is rendered, **Then** the banner dynamically displays the current denomination values

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` entity and `dct_vpoint_exchanges` entity must exist |
| Story 7 | Blocked-by | V-Point coupons must be created via STEP2 checkout to have history data |
| Story 9 | Blocked-by | `dct_coupon_target.serial_no` populated to join against `dct_vpoint_redeem_result` |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | Customer has only V-Point coupons and no other coupons in history | Used/Expired tab shows only V-Point coupons; active tab is empty |
| 2 | `dct_vpoint_redeem_result` record missing for a `serial_no` | Treat as cancel_status=0; display coupon name only |
| 3 | `cancel_status` transitions during page view (e.g., BAT4 updates from 2→4) | Next page load shows updated status; no real-time push required |
| 4 | `dct_vpoint_exchanges` table is empty | Banner falls back to static default denominations or is hidden |
| 5 | Customer has hundreds of history records (pagination) | Existing pagination applies to the combined sorted list |
| 6 | cancel_status=5 but error message column is NULL | Show processing message without error detail; log warning |
| 7 | Same serial_no appears in multiple `dct_vpoint_redeem_result` rows (retry_cnt > 0) | Use the row with the highest `retry_cnt` for display status |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| `getCouponHistory()` performance degradation from removing type separation and adding JOIN | Medium | Medium | Add index on `dct_coupon_target.serial_no`; test with 1000+ records |
| Native App API consumers expect separated coupon lists | Low | High | Verify API response contract; Native App coupons follow existing behavior |
| cancel_status label requirements change after SRS revision | Low | Low | Extract labels to translation file for easy update |
| Banner denomination data cached too aggressively | Low | Low | Use short-TTL cache (5 min) or invalidate on admin update |

#### Notes / Additional Information
- `CouponTargetRepository::getCouponHistory()` at line 744 is the main method to modify — remove type-based grouping, add combined sort
- `CouponTargetRepository::getAllSpecialMyCoupons()` at line 592 needs a WHERE clause excluding `coupon_id=999999990001`
- `VpointBannerService` is a new service reading from `VpointExchangeRepository`
- The cancel_status join: `dct_coupon_target.serial_no = dct_vpoint_redeem_result.serial_no`
- For cancel_status=5, look up the specific error message from the [7.Error MSG] sheet using the `return_cd` stored in `dct_vpoint_redeem_result`

---

#### Sub-tasks:

##### Sub-task 11.1: Modify CouponTargetRepository — Exclude V-Point from Active List
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Modify `app/Customize/Repository/CouponTargetRepository.php::getAllSpecialMyCoupons()` (line ~592) to add a WHERE clause: `AND ct.coupon_id != 999999990001` (or filter by `source_type`). This ensures V-Point checkout coupons do not appear in the customer's active coupon tab. Verify that `CouponController.php` (line ~100) and API CouponControllers that call this method display the filtered result.

- **Affected Files:** `app/Customize/Repository/CouponTargetRepository.php`, `app/Customize/Controller/CouponController.php`, `app/Customize/Controller/Api/CouponController.php`, `app/Customize/Controller/Api/V2/CouponController.php`
- **Parent Story:** Story 11
- **Definition of Done:**
  - [ ] `getAllSpecialMyCoupons()` excludes coupon_id=999999990001
  - [ ] Active coupon tab shows zero V-Point checkout coupons
  - [ ] Non-V-Point coupons unaffected
  - [ ] API endpoints return consistent filtered results

##### Sub-task 11.2: Modify CouponTargetRepository — Combined History Sort
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Modify `app/Customize/Repository/CouponTargetRepository.php::getCouponHistory()` (line ~744) to:
1. Include V-Point coupons (coupon_id=999999990001) in the used/expired result set
2. Remove the current separation by coupon type — merge all types into a single collection
3. Sort the combined result by `update_date DESC`
4. Ensure Native App and Shop coupon behavior remains identical (no regression)

Update `CouponService::getCouponHistory()` (line ~2101) if it post-processes the repository result into separate arrays.

- **Affected Files:** `app/Customize/Repository/CouponTargetRepository.php`, `app/Customize/Service/CouponService.php`
- **Parent Story:** Story 11
- **Definition of Done:**
  - [ ] Used/Expired tab shows combined list sorted by update_date DESC
  - [ ] V-Point coupons appear intermixed with other types
  - [ ] No regression for non-V-Point coupons
  - [ ] Pagination works with combined list

##### Sub-task 11.3: Purchase History Cancel Status Display
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Full-stack

**Description:**
Add cancel status indicators to purchase history detail:
1. Create a method in `CouponService` (or repository) to fetch `dct_vpoint_redeem_result.cancel_status` by joining on `serial_no` from `dct_coupon_target`, selecting the row with the highest `retry_cnt`
2. Pass cancel_status to Twig template context in the purchase detail controller
3. In the purchase detail Twig template, render:
   - cancel_status 0/null: coupon name only
   - cancel_status 2 or 3: `<span class="text-warning">※ ポイント利用キャンセル処理中</span>`
   - cancel_status 4: `<span class="text-success">✅ ポイント利用キャンセル済</span>`
   - cancel_status 5: processing message + error from `VpointErrorMessageService` using `return_cd`
4. Handle missing `dct_vpoint_redeem_result` records gracefully (treat as status 0)

- **Affected Files:** `app/Customize/Service/CouponService.php`, `app/Customize/Repository/CouponTargetRepository.php`, `app/template/default/Mypage/` (purchase detail template)
- **Parent Story:** Story 11
- **Definition of Done:**
  - [ ] Each cancel_status value displays the correct label
  - [ ] Missing redeem records treated as no-cancel
  - [ ] cancel_status=5 shows error detail from return_cd
  - [ ] No N+1 queries — batch-load cancel statuses

##### Sub-task 11.4: VpointBannerService — Dynamic Denomination Banner
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Full-stack

**Description:**
Create `app/Customize/Service/VpointBannerService.php`:
1. Inject `VpointExchangeRepository`
2. Method `getDenominations(): array` — fetch all active rows from `dct_vpoint_exchanges`, return formatted denomination list
3. Cache result with 5-minute TTL (Symfony cache or Redis)
4. Create/update the Twig template for the V-Point coupon banner to render denominations dynamically
5. Register service in DI container (auto-wiring)

- **Affected Files:** `app/Customize/Service/VpointBannerService.php` (new), `app/template/default/` (banner template)
- **Parent Story:** Story 11
- **Definition of Done:**
  - [ ] Banner renders current denominations from database
  - [ ] Cache prevents DB hit on every page load
  - [ ] Empty table → banner hidden or shows fallback
  - [ ] Denomination formatting: ¥X,XXX

##### Sub-task 11.5: Unit Tests — Coupon Display & History
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Write unit tests covering:
1. `getAllSpecialMyCoupons()` excludes V-Point coupons
2. `getCouponHistory()` returns combined sorted list
3. Cancel status resolution logic (all 5 status values + missing record)
4. `VpointBannerService::getDenominations()` with populated and empty tables
5. Edge case: multiple `dct_vpoint_redeem_result` rows for same serial_no → highest retry_cnt wins

- **Affected Files:** `tests/Customize/Repository/CouponTargetRepositoryTest.php`, `tests/Customize/Service/VpointBannerServiceTest.php` (new)
- **Parent Story:** Story 11
- **Definition of Done:**
  - [ ] All test cases pass
  - [ ] Covers happy path and edge cases
  - [ ] No false positives from test data setup

---

### Story 12: Admin — Card Linkage Summary & Member Detail

**Type:** Story | **Priority:** M | **Points:** 8 | **Sprint:** 4

#### Summary
Build an admin dashboard page showing card linkage statistics (all-time totals and daily breakdowns with date-range filtering) and enhance the member detail page with card linkage status, linkage history, an "Unlink Card" button with warning modal, and a V-Point coupon exchange history section. Include Excel export of the summary report.

#### Requirement Details
Two admin-facing features: (1) **Card Linkage Summary page** — displays all-time aggregate totals (① linked count, ② dislinked count) and a date-range-filtered daily breakdown table with columns: Date | 新規(New) | 解約(Cancel) | 連携人数(Linkage) | 連携解除人数(Dislinkage), plus a 累計(Subtotal) row at the bottom. Default date range is current month 1st → today; maximum range is 366 days. Data is sourced from `dtb_customer_card_info` records grouped by date and `is_valid` status transitions. Excel export (PhpSpreadsheet .xlsx) produces a WYSIWYG file matching the displayed columns and respecting the active date filter. (2) **Member Detail Enhancement** — on the existing admin customer detail page, add: card linkage status (Yes/No), linkage date, linkage history timeline, an "Unlink Card" button with a warning modal about active V-Point coupons, and a V-Point coupon exchange history table showing serial_no, amount, date, and status.

- **Linked Requirements:** SRS Admin Card Linkage Summary, SRS Admin Member Detail Enhancement
- **Affected Components:** `app/Customize/Controller/Admin/Customer/CustomerEditController.php`, `app/Customize/Controller/Admin/CardLinkage/` (new), `app/Customize/Service/Admin/CardLinkageService.php` (new), `app/Customize/Service/Admin/CustomerDetailService.php`, `app/Customize/Repository/CustomerCardInfoRepository.php` (new or existing), `app/template/admin/Customer/edit.twig`, `app/template/admin/CardLinkage/` (new)
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Admin Card & Member Management

#### Acceptance Criteria
- [ ] **Given** an admin user navigates to the Card Linkage Summary page, **When** the page loads, **Then** all-time totals for linked and dislinked counts are displayed
- [ ] **Given** default date range (month 1st → today), **When** the summary table renders, **Then** each day within the range shows columns: Date, 新規, 解約, 連携人数, 連携解除人数
- [ ] **Given** a date range exceeding 366 days, **When** the admin submits the filter, **Then** a validation error is displayed
- [ ] **Given** the summary table is displayed, **When** the admin clicks "Excel Export," **Then** a .xlsx file is downloaded with identical columns and data matching the current filter
- [ ] **Given** a 累計(Subtotal) row, **When** the table renders, **Then** the subtotal row sums all daily values for each column
- [ ] **Given** an admin views a customer's detail page, **When** the customer has an active card linkage, **Then** "Card Linkage: Yes" with linkage date is displayed
- [ ] **Given** the admin clicks "Unlink Card," **When** the customer has active V-Point coupons, **Then** a warning modal explains that unlinking will affect active V-Point coupons
- [ ] **Given** the member detail page, **When** the V-Point exchange history section renders, **Then** it shows serial_no, amount, date, and current status for each exchange

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dtb_customer_card_info` entity must exist |
| Story 3 | Blocked-by | Card linkage/unlinkage operations must be functional to produce data |
| phpoffice/phpspreadsheet | Library | Already in composer.json (^1.24) |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | No card linkage records exist in the system | Summary shows all zeros; daily table is empty |
| 2 | Date range spans a month boundary with no activity on some days | Days with no activity show 0 in all columns |
| 3 | Customer linked, unlinked, then re-linked on the same day | Each event counted: 1 new + 1 cancel + 1 new = 2 new, 1 cancel for that day |
| 4 | Excel export with 366 days of data | File generates within 30s; no memory overflow |
| 5 | Unlink button clicked for customer with no active V-Point coupons | No warning; proceeds directly to confirmation |
| 6 | Multiple linkage history entries for same customer | History timeline shows all entries chronologically |
| 7 | Admin views member who has never linked a card | "Card Linkage: No" displayed; unlink button hidden |
| 8 | Date filter set to future date range | No data returned; table empty; no error |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Large date range query performance (366 days × many customers) | Medium | Medium | Aggregate query with GROUP BY date; add date index on `dtb_customer_card_info` |
| PhpSpreadsheet memory usage on large exports | Low | Medium | Use streaming writer; limit to 366-day max range |
| Card linkage history table design not finalized | Low | Medium | Derive from `dtb_customer_card_info` insert/update timestamps |
| Admin page layout conflicts with existing Customer Edit layout | Low | Low | Use EC-Cube admin section/accordion pattern |

#### Notes / Additional Information
- PhpSpreadsheet is already available (`composer.json` line 67: `"phpoffice/phpspreadsheet": "^1.24"`)
- Follow existing admin Excel export patterns (see `app/Customize/Service/Admin/ExportPdfService.php` for export service patterns)
- `CustomerCardInfoRepository` needs aggregate queries: `COUNT(*) GROUP BY DATE(create_date), is_valid`
- Unlink Card action should call the existing card unlinkage service from Story 3
- V-Point exchange history for member detail: query `dct_vpoint_redeem_result` WHERE `customer_id = :id`
- Admin routing convention: `/admin/card-linkage/summary`, `/admin/card-linkage/export`

---

#### Sub-tasks:

##### Sub-task 12.1: CardLinkageService — Aggregate Statistics & Daily Breakdown
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Admin/CardLinkageService.php`:
1. Method `getAllTimeTotals(): array` — returns `['linked' => int, 'dislinked' => int]` from `dtb_customer_card_info`
2. Method `getDailyBreakdown(\DateTime $from, \DateTime $to): array` — returns array of `['date' => 'YYYY-MM-DD', 'new' => int, 'cancel' => int, 'linkage' => int, 'dislinkage' => int]` grouped by date
3. Method `calculateSubtotals(array $breakdown): array` — sums each column
4. Validate date range ≤ 366 days; throw `\InvalidArgumentException` if exceeded
5. Use Doctrine DQL or QueryBuilder with `GROUP BY DATE(create_date)` for performance

- **Affected Files:** `app/Customize/Service/Admin/CardLinkageService.php` (new), `app/Customize/Repository/CustomerCardInfoRepository.php`
- **Parent Story:** Story 12
- **Definition of Done:**
  - [ ] All-time totals return correct counts
  - [ ] Daily breakdown groups by date correctly
  - [ ] Subtotal row sums verified
  - [ ] 366-day max enforced
  - [ ] Days with no activity included as zeros

##### Sub-task 12.2: Admin Card Linkage Summary Controller & Twig Template
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Full-stack

**Description:**
Create `app/Customize/Controller/Admin/CardLinkage/CardLinkageController.php`:
1. Route `GET /admin/card-linkage/summary` — renders summary page with date filter form
2. Default date range: current month 1st (`new \DateTime('first day of this month')`) → today
3. Pass `allTimeTotals`, `dailyBreakdown`, `subtotals`, `dateFrom`, `dateTo` to Twig
4. Create `app/template/admin/CardLinkage/summary.twig`:
   - Date range picker (from/to inputs with validation)
   - All-time summary cards (linked count, dislinked count)
   - Daily breakdown table: Date | 新規 | 解約 | 連携人数 | 連携解除人数
   - 累計 row at table bottom
   - "Excel Export" button linking to export route
5. Follow EC-Cube admin layout conventions (extends `@admin/default_frame.twig`)

- **Affected Files:** `app/Customize/Controller/Admin/CardLinkage/CardLinkageController.php` (new), `app/template/admin/CardLinkage/summary.twig` (new)
- **Parent Story:** Story 12
- **Definition of Done:**
  - [ ] Page renders with default date range
  - [ ] Date filter updates table via form submission
  - [ ] 366-day validation shown as flash error
  - [ ] Table displays all columns with subtotal row
  - [ ] Admin navigation accessible

##### Sub-task 12.3: Excel Export — Card Linkage Summary
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Add route `GET /admin/card-linkage/export` to `CardLinkageController.php`:
1. Accept date range parameters (same as summary page)
2. Use `PhpOffice\PhpSpreadsheet\Spreadsheet` to generate .xlsx:
   - Header row: 日付, 新規, 解約, 連携人数, 連携解除人数
   - Data rows from `CardLinkageService::getDailyBreakdown()`
   - 累計 row at bottom with SUM formulas or values
   - Column auto-width; header row bold
3. Return `StreamedResponse` with Content-Type `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
4. Filename: `card_linkage_summary_{from}_{to}.xlsx`

- **Affected Files:** `app/Customize/Controller/Admin/CardLinkage/CardLinkageController.php`
- **Parent Story:** Story 12
- **Definition of Done:**
  - [ ] .xlsx file downloads with correct data
  - [ ] Columns match displayed table (WYSIWYG)
  - [ ] Date filter respected in export
  - [ ] File opens correctly in Excel/LibreOffice

##### Sub-task 12.4: Member Detail — Card Linkage Status & Unlink
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Full-stack

**Description:**
Enhance `app/Customize/Controller/Admin/Customer/CustomerEditController.php`:
1. Fetch `dtb_customer_card_info` for the customer — pass linkage status (Yes/No), linkage date, and history records to Twig
2. Update `app/template/admin/Customer/edit.twig`:
   - New section "カード連携情報" (Card Linkage Info): Status badge (Yes=green, No=gray), linkage date
   - Linkage history timeline (date, action: linked/unlinked)
   - "Unlink Card" button (hidden if not linked)
   - Warning modal (JavaScript): "この会員のVポイントクーポンが無効になります。連携解除しますか？" — shown only when active V-Point coupons exist
3. Unlink action: `POST /admin/customer/{id}/unlink-card` — calls existing card unlinkage service, redirects back with flash message

- **Affected Files:** `app/Customize/Controller/Admin/Customer/CustomerEditController.php`, `app/template/admin/Customer/edit.twig`, `app/Customize/Service/Admin/CustomerDetailService.php`
- **Parent Story:** Story 12
- **Definition of Done:**
  - [ ] Linkage status and date displayed correctly
  - [ ] History timeline shows all link/unlink events
  - [ ] Warning modal appears when V-Point coupons are active
  - [ ] Unlink action works and updates database
  - [ ] Button hidden for non-linked customers

##### Sub-task 12.5: Member Detail — V-Point Exchange History Section
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Full-stack

**Description:**
Add a "Vポイント交換履歴" (V-Point Exchange History) section to the customer detail page:
1. Query `dct_vpoint_redeem_result` WHERE `customer_id = :id`, ordered by `create_date DESC`
2. Display table: Serial No | 交換金額(Amount) | 交換日(Date) | ステータス(Status)
3. Status column shows cancel_status label (same labels as Story 11 purchase history)
4. Paginate if >20 records (or use accordion/expandable)

- **Affected Files:** `app/Customize/Controller/Admin/Customer/CustomerEditController.php`, `app/template/admin/Customer/edit.twig`
- **Parent Story:** Story 12
- **Definition of Done:**
  - [ ] Exchange history table renders with correct data
  - [ ] Status labels match Story 11 definitions
  - [ ] Empty state shown when no exchanges exist
  - [ ] No N+1 queries

##### Sub-task 12.6: Unit Tests — Card Linkage Summary & Member Detail
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Write unit/functional tests:
1. `CardLinkageService::getAllTimeTotals()` with various data scenarios
2. `CardLinkageService::getDailyBreakdown()` — correct grouping, zero-fill days, boundary dates
3. 366-day max validation
4. Excel export response headers and content
5. Member detail: linkage status resolution, unlink action, V-Point history query

- **Affected Files:** `tests/Customize/Service/Admin/CardLinkageServiceTest.php` (new), `tests/Customize/Controller/Admin/CardLinkage/CardLinkageControllerTest.php` (new)
- **Parent Story:** Story 12
- **Definition of Done:**
  - [ ] All tests pass
  - [ ] Aggregate query edge cases covered
  - [ ] Export produces valid .xlsx

---

### Story 13: Admin — V-Point Cancel Redemption

**Type:** Story | **Priority:** M | **Points:** 5 | **Sprint:** 5

#### Summary
Build an admin interface for cancelling V-Point redemptions via the sp201(Cancel) API. Admins search by serial_no or member, view redemption details from `dct_vpoint_redeem_result`, and execute cancellations through a state machine with approval workflow. The system enforces a 365-day cancellation window, retries sp201 up to 3 times with backoff, and writes audit log entries.

#### Requirement Details
Implements the admin V-Point cancel redemption workflow: (1) Search by `serial_no` or customer — displays `dct_vpoint_redeem_result` record details (serial_no, amount, date, status, return codes). (2) Cancel State Machine with button actions: "利用キャンセル" (Apply Cancel) transitions 0→1 or 5→1 (enabled at status 0 or 5); "承認" (Approve) transitions 1→2 (if sp201 fails) or 1→4 (if sp201 succeeds) (enabled at status 1); "申請キャンセル" (Cancel Application) transitions 1→0 (enabled at status 1). (3) sp201 cancel call with `cancel_kbn=1`, up to 3 retries with exponential backoff (2s, 5s). (4) 365-day cancellation window: reject if `create_date < modify('-365 days')` in JST. (5) Audit log: admin user, timestamp, before/after cancel_status. (6) Successful cancel → invalidate the associated coupon. (7) Button disable rules: disabled when coupon used + order cancelled, card cancelled, BAT2 data_type=20, or coupon expired. (8) Cancel status display labels include return codes: "Approved(xx)", "Completed cancel(xxx)", "Failed cancel(xxx)".

- **Linked Requirements:** SRS Admin V-Point Cancel, cancel_status state machine, sp201(Cancel) specification, [7.Error MSG] sheet
- **Affected Components:** `app/Customize/Controller/Admin/Vpoint/VpointCancelController.php` (new), `app/Customize/Service/Admin/VpointCancelService.php` (new), `app/Customize/Service/Vpoint/VpointApiClient.php`, `app/template/admin/Vpoint/cancel.twig` (new), `app/template/admin/Vpoint/cancel_detail.twig` (new)
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Admin V-Point Management

#### Acceptance Criteria
- [ ] **Given** an admin enters a serial_no, **When** they search, **Then** the matching `dct_vpoint_redeem_result` record is displayed with full details
- [ ] **Given** a record with cancel_status=0, **When** the admin clicks "利用キャンセル," **Then** the status transitions to 1
- [ ] **Given** a record with cancel_status=5, **When** the admin clicks "利用キャンセル," **Then** the status transitions to 1 (retry path)
- [ ] **Given** a record with cancel_status=1, **When** the admin clicks "承認" and sp201 succeeds, **Then** the status transitions to 4 and the associated coupon is invalidated
- [ ] **Given** a record with cancel_status=1, **When** the admin clicks "承認" and sp201 fails after 3 retries, **Then** the status transitions to 2
- [ ] **Given** a record with cancel_status=1, **When** the admin clicks "申請キャンセル," **Then** the status transitions back to 0
- [ ] **Given** a redemption older than 365 days (JST), **When** the admin attempts cancellation, **Then** an error message is displayed and the action is blocked
- [ ] **Given** any cancel status transition, **When** the transition completes, **Then** an audit log record is written with admin user, timestamp, and before/after status
- [ ] **Given** a coupon that was used in a cancelled order, **When** the admin views the record, **Then** the cancel buttons are disabled
- [ ] **Given** cancel_status=4 with return_cd=xxx, **When** the status is displayed, **Then** it shows "Completed cancel(xxx)"

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` entity with cancel_status column |
| Story 2 | Blocked-by | `VpointApiClient` for sp201 cancel calls |
| Story 7 | Blocked-by | Redemption records must exist to cancel |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | sp201 cancel call times out on all 3 retries | Status transitions to 2 (Failed); error logged; admin notified |
| 2 | Admin clicks "承認" twice rapidly (double-submit) | CSRF token prevents duplicate; second request rejected |
| 3 | Redemption is exactly 365 days old (boundary) | Cancellation allowed; 366 days → blocked |
| 4 | Two admins attempt to cancel the same record simultaneously | Optimistic locking or DB-level check prevents double-transition |
| 5 | Network error between sp201 response and DB commit | Cancel_status remains at 1; admin can retry "承認" |
| 6 | serial_no not found in search | "No records found" message displayed |
| 7 | BAT2 data_type=20 flag set on the record | All cancel buttons disabled; tooltip explains reason |
| 8 | Card was cancelled after redemption but before admin cancel attempt | Cancel buttons disabled; tooltip: "カード連携解除済" |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| sp201 cancel API intermittent failures | Medium | High | 3 retries with backoff (2s, 5s); status 2 allows manual retry |
| State machine transition bugs | Medium | High | Exhaustive unit tests for every valid/invalid transition |
| 365-day window timezone edge cases | Low | Medium | Explicitly use JST (`Asia/Tokyo`) in all date calculations |
| Audit log table not yet designed | Low | Medium | Use existing EC-Cube admin log mechanism or add to `dct_vpoint_redeem_result` audit columns |

#### Notes / Additional Information
- State machine transitions: `0→1, 5→1` (Apply), `1→4` (Approve success), `1→2` (Approve fail), `1→0` (Cancel Application)
- Invalid transitions (e.g., 0→4, 2→1) must be rejected with clear error messages
- sp201 cancel uses same `VpointApiClient` as redemption but with `cancel_kbn=1`
- Backoff schedule: 1st retry at 2s, 2nd retry at 5s — total max wait ~7s
- Coupon invalidation: set `dct_coupon_target.del_flg = 1` or equivalent
- Admin route convention: `/admin/vpoint/cancel`, `/admin/vpoint/cancel/{serial_no}`

---

#### Sub-tasks:

##### Sub-task 13.1: VpointCancelService — State Machine & Business Logic
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/Admin/VpointCancelService.php`:
1. Method `applyCancel(VpointRedeemResult $record, AdminUser $admin): void` — validates transition (0→1 or 5→1), updates status, writes audit
2. Method `approve(VpointRedeemResult $record, AdminUser $admin): int` — calls sp201 cancel (cancel_kbn=1) with up to 3 retries (sleep 2s, 5s), transitions 1→4 on success or 1→2 on failure, invalidates coupon on success
3. Method `cancelApplication(VpointRedeemResult $record, AdminUser $admin): void` — transitions 1→0
4. Method `validateCancellationWindow(VpointRedeemResult $record): bool` — checks `create_date >= now()->modify('-365 days')` in JST
5. Method `isButtonDisabled(VpointRedeemResult $record): array` — returns `['disabled' => bool, 'reason' => string]` checking: coupon used+order cancelled, card cancelled, BAT2 data_type=20, coupon expired
6. Private method `writeAuditLog(...)` — records admin_id, timestamp, before_status, after_status, serial_no
7. All transitions validate current state before applying; throw `\LogicException` on invalid transition

- **Affected Files:** `app/Customize/Service/Admin/VpointCancelService.php` (new)
- **Parent Story:** Story 13
- **Definition of Done:**
  - [ ] All valid transitions work correctly
  - [ ] Invalid transitions throw exception
  - [ ] sp201 retry with backoff implemented
  - [ ] 365-day window enforced in JST
  - [ ] Audit log written for every transition
  - [ ] Coupon invalidated on successful cancel

##### Sub-task 13.2: Admin Cancel Controller & Search
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Full-stack

**Description:**
Create `app/Customize/Controller/Admin/Vpoint/VpointCancelController.php`:
1. Route `GET /admin/vpoint/cancel` — search form with serial_no and member ID fields
2. Route `GET /admin/vpoint/cancel/{serial_no}` — detail view showing dct_vpoint_redeem_result record
3. Route `POST /admin/vpoint/cancel/{serial_no}/apply` — triggers applyCancel()
4. Route `POST /admin/vpoint/cancel/{serial_no}/approve` — triggers approve()
5. Route `POST /admin/vpoint/cancel/{serial_no}/cancel-application` — triggers cancelApplication()
6. All POST routes protected by CSRF token
7. Flash messages for success/error; redirect back to detail page

- **Affected Files:** `app/Customize/Controller/Admin/Vpoint/VpointCancelController.php` (new)
- **Parent Story:** Story 13
- **Definition of Done:**
  - [ ] Search by serial_no returns correct record
  - [ ] Search by member shows all their redemptions
  - [ ] State transition buttons call correct service methods
  - [ ] CSRF protection on all POST routes
  - [ ] Error messages displayed in Japanese

##### Sub-task 13.3: Admin Cancel Twig Templates
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

**Description:**
Create admin templates:
1. `app/template/admin/Vpoint/cancel.twig` — search form with serial_no / member ID inputs, results table
2. `app/template/admin/Vpoint/cancel_detail.twig` — detail view:
   - Record info: serial_no, customer, amount, exchange date, retry_cnt, return_cd
   - Current cancel_status with label including return code: "Completed cancel(xxx)", "Failed cancel(xxx)", "Approved(xx)"
   - State machine buttons: 利用キャンセル, 承認, 申請キャンセル — enabled/disabled per current status and business rules
   - Disabled button tooltip explaining reason (coupon used, card cancelled, etc.)
   - Confirmation modal before each state transition
3. Extends `@admin/default_frame.twig`; uses EC-Cube admin CSS classes

- **Affected Files:** `app/template/admin/Vpoint/cancel.twig` (new), `app/template/admin/Vpoint/cancel_detail.twig` (new)
- **Parent Story:** Story 13
- **Definition of Done:**
  - [ ] Search form functional
  - [ ] Detail page shows all record fields
  - [ ] Buttons correctly enabled/disabled per status
  - [ ] Confirmation modals prevent accidental clicks
  - [ ] Status labels include return codes

##### Sub-task 13.4: Unit Tests — Cancel State Machine & Service
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Write unit tests:
1. Every valid state transition (0→1, 5→1, 1→4, 1→2, 1→0)
2. Every invalid state transition (0→4, 2→1, 3→1, 4→1, etc.) → exception
3. 365-day window boundary: exactly 365 days (allowed), 366 days (blocked)
4. sp201 retry: mock API to fail twice then succeed → status 4
5. sp201 retry: mock API to fail 3 times → status 2
6. Button disable logic: all 4 disable conditions
7. Audit log written for each transition
8. Coupon invalidation on successful cancel

- **Affected Files:** `tests/Customize/Service/Admin/VpointCancelServiceTest.php` (new)
- **Parent Story:** Story 13
- **Definition of Done:**
  - [ ] All state transitions tested
  - [ ] Boundary date test passes
  - [ ] Retry logic verified with mocks
  - [ ] 100% coverage of state machine logic

---

### Story 14: Admin — Payment & Order Management

**Type:** Story | **Priority:** L | **Points:** 3 | **Sprint:** 5

#### Summary
Adjust the admin order management screens to handle V-Point payment scenarios: disable GMO payment information buttons for orders with V-Point-only or mixed payment, and hide V-Point-only orders from the payment status list and Paidy management views. No new features — this story applies conditional visibility rules to existing admin UI based on payment type combinations.

#### Requirement Details
Implements payment-type-aware admin UI rules across two cases: (1) **Case4 — Change Payment Info** on the order edit page (`/admin/order/{id}/edit`): For Case2 (No GMO, Yes V-Point) and Case3 (Yes GMO, Yes V-Point), disable the PG Multipayment Service payment information buttons (refund, capture, cancel, etc.) since V-Point portion is not GMO-managed. For Case1 (Yes GMO, No V-Point), no change. (2) **Case6 — Payment Status List & Paidy Management**: For Case2 (No GMO, Yes V-Point), hide the order record from the payment status list and Paidy management list since there is no GMO transaction to manage. For Case1 (Yes GMO, No V-Point) and Case3 (Yes GMO, Yes V-Point), no change — these orders remain visible. Case7 (Change Mode Checkout) has been verified to need no new implementation.

- **Linked Requirements:** SRS Case4 (Payment Info), SRS Case6 (Payment Status), SRS Case7 (Change Mode)
- **Affected Components:** `app/Customize/Controller/Admin/Order/EditController.php`, `app/template/admin/Order/edit.twig`, `app/template/admin/Order/index.twig`, `app/Customize/Service/Admin/OrderService.php`
- **Scope:** Full-stack

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Admin Payment Management

#### Acceptance Criteria
- [ ] **Given** an order with Case1 (Yes GMO, No V-Point), **When** admin views the order edit page, **Then** GMO payment buttons are displayed and functional (no change)
- [ ] **Given** an order with Case2 (No GMO, Yes V-Point), **When** admin views the order edit page, **Then** GMO payment buttons (PG Multipayment Service) are disabled/hidden
- [ ] **Given** an order with Case3 (Yes GMO, Yes V-Point), **When** admin views the order edit page, **Then** GMO payment buttons are disabled/hidden
- [ ] **Given** an order with Case2 (No GMO, Yes V-Point), **When** admin views the payment status list, **Then** the order is NOT shown in the list
- [ ] **Given** an order with Case1 (Yes GMO, No V-Point), **When** admin views the payment status list, **Then** the order IS shown (no change)
- [ ] **Given** an order with Case3 (Yes GMO, Yes V-Point), **When** admin views the payment status list, **Then** the order IS shown (no change)
- [ ] **Given** an order with Case2 (No GMO, Yes V-Point), **When** admin views Paidy management, **Then** the order is NOT shown
- [ ] **Given** Case7 (Change Mode Checkout), **When** the admin reviews the order, **Then** no new behavior is needed (verified existing logic handles it)

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 7 | Blocked-by | V-Point checkout must create orders with the V-Point payment flag |
| Story 9 | Soft-dependency | Order records with V-Point coupons must exist for testing |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | Order originally Case1, then V-Point coupon added via admin edit | Payment type re-evaluated; buttons updated accordingly |
| 2 | Order has GMO payment of ¥0 (full V-Point discount) | Treated as Case2 (No effective GMO); buttons disabled |
| 3 | Paidy order with partial V-Point discount (Case3) | Order visible in Paidy list; GMO buttons disabled on edit page |
| 4 | V-Point coupon cancelled after order placed | Payment type reverts to Case1 if GMO exists; buttons re-enabled |
| 5 | Admin searches payment status list with no V-Point orders | List unchanged; no filtering logic triggered |
| 6 | Existing non-V-Point orders | Zero behavioral change; regression-free |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Incorrect payment type detection (false Case2/Case3) | Medium | High | Unit test all payment type combinations; use explicit V-Point coupon check |
| Hiding orders from payment list disrupts admin workflows | Low | Medium | Document the behavior for admin users; add tooltip explaining why order is hidden |
| GMO plugin update overrides template changes | Low | Medium | Changes in app/template/admin/ override plugin templates per EC-Cube convention |

#### Notes / Additional Information
- V-Point payment detection: check if order has a coupon with `coupon_id=999999990001`
- GMO payment detection: check `gmo_payment_gateway_payment_status` is not null
- `EditController.php` already injects `PaymentService` (line ~194) — add V-Point flag to the template context
- `app/template/admin/Order/edit.twig` (line ~228+): wrap GMO button section in `{% if not has_vpoint_payment %}` conditional
- `app/template/admin/Order/index.twig` (line ~1768): add WHERE clause or Twig filter to exclude Case2 orders from payment status list
- No RBAC changes needed — operational process covers authorization per SRS

---

#### Sub-tasks:

##### Sub-task 14.1: Payment Type Detection Helper
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Add methods to `app/Customize/Service/Admin/OrderService.php` (or create a helper):
1. Method `hasVpointPayment(Order $order): bool` — returns true if order has a coupon with coupon_id=999999990001
2. Method `hasGmoPayment(Order $order): bool` — returns true if `gmo_payment_gateway_payment_status` is not null
3. Method `getPaymentCase(Order $order): int` — returns 1 (GMO only), 2 (V-Point only), or 3 (both)
4. Pass the payment case to Twig context in `EditController.php`

- **Affected Files:** `app/Customize/Service/Admin/OrderService.php`, `app/Customize/Controller/Admin/Order/EditController.php`
- **Parent Story:** Story 14
- **Definition of Done:**
  - [ ] Payment case correctly identified for all 3 scenarios
  - [ ] Template context includes payment case value
  - [ ] No false positives for non-V-Point orders

##### Sub-task 14.2: Admin Order Edit — Disable GMO Buttons for V-Point Orders
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Frontend

**Description:**
Modify `app/template/admin/Order/edit.twig`:
1. Wrap GMO PG Multipayment Service button section in a conditional: `{% if payment_case == 1 %}` (show buttons) `{% else %}` (hide or disable with tooltip) `{% endif %}`
2. For Case2 and Case3: replace buttons with a notice: "Vポイント決済を含む注文のため、GMO決済操作は無効です"
3. Ensure Paidy-related buttons follow the same logic
4. Test with orders of all 3 payment cases

- **Affected Files:** `app/template/admin/Order/edit.twig`
- **Parent Story:** Story 14
- **Definition of Done:**
  - [ ] Case1 orders: all GMO buttons visible and functional
  - [ ] Case2 orders: GMO buttons hidden/disabled with notice
  - [ ] Case3 orders: GMO buttons hidden/disabled with notice
  - [ ] No JavaScript errors on page load

##### Sub-task 14.3: Payment Status List — Filter V-Point-Only Orders
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Full-stack

**Description:**
Modify the payment status list and Paidy management queries:
1. In `app/Customize/Controller/Admin/Order/OrderController.php` (or the relevant admin controller that serves the payment status list), add a query condition to exclude orders where `getPaymentCase() == 2` (V-Point only, no GMO)
2. Alternatively, add a LEFT JOIN filter in the QueryBuilder: exclude orders that have `coupon_id=999999990001` AND `gmo_payment_gateway_payment_status IS NULL`
3. Ensure Case1 and Case3 orders remain visible
4. Apply same filter to Paidy management list (`app/template/admin/Order/index.twig` line ~1772)

- **Affected Files:** `app/Customize/Controller/Admin/Order/OrderController.php`, `app/Customize/Service/Admin/OrderService.php`, `app/template/admin/Order/index.twig`
- **Parent Story:** Story 14
- **Definition of Done:**
  - [ ] Case2 orders hidden from payment status list
  - [ ] Case2 orders hidden from Paidy management
  - [ ] Case1 and Case3 orders visible (no regression)
  - [ ] Query performance acceptable with added filter

##### Sub-task 14.4: Unit Tests — Payment Type & Admin UI Rules
**Type:** Sub-task | **Estimate:** 2h | **Skill:** Backend

**Description:**
Write unit tests:
1. `getPaymentCase()` returns correct case for: GMO-only, V-Point-only, mixed, neither
2. `hasVpointPayment()` with various coupon configurations
3. Payment status list query: verify Case2 excluded, Case1/Case3 included
4. Edge case: order with cancelled V-Point coupon reverts to Case1

- **Affected Files:** `tests/Customize/Service/Admin/OrderServiceTest.php`
- **Parent Story:** Story 14
- **Definition of Done:**
  - [ ] All payment type scenarios tested
  - [ ] Filter logic verified
  - [ ] No regression in existing order queries

---

### Story 15: POS API, Karte Events & Structured Logging

**Type:** Story | **Priority:** M | **Points:** 5 | **Sprint:** 5

#### Summary
Extend the POS API to handle V-Point coupon scans, implement Karte analytics event tracking for V-Point operations across EC and Native channels, and establish structured JSON logging for all V-Point operations (sp101, sp201, coupon issue, BAT3, BAT4) to support operational monitoring and debugging.

#### Requirement Details
Three cross-cutting concerns: (1) **POS API**: When `coupon_id=999999990001` is scanned at POS, the discount amount must be read from `dct_vpoint_redeem_result.kangen_point` (not from `dcm_coupon.discount_price` which is 0 for V-Point coupons). Mark the coupon as USED and fire a Karte event. (2) **Karte Events**: Two new event types — `vpoint_exchange` (fired on sp201 success, properties: member_id, serial_no, exchange_amount, exchange_date; sent from both EC and Native channels) and `vpoint_coupon_used` (fired on checkout completion or POS scan, properties: order_id, coupon_amount, serial_no, usage_date; sent from EC and POS). EC events use Twig tracker templates following the `Block/Tracker/` pattern with `krt('send', ...)`. Native events return a `karte_event` payload in the JSON API response. (3) **Structured Logging**: All V-Point operations must write structured JSON logs including: Trigger, Program name, Member ID, Serial Number, key values, Return code, Timestamp. This applies to sp101, sp201, coupon issue, BAT3, BAT4, and manual admin operations.

- **Linked Requirements:** SRS POS API V-Point section, Karte event specification, Structured logging requirements
- **Affected Components:** `app/Customize/Controller/Api/PosController.php`, `app/Customize/Service/Vpoint/VpointApiClient.php`, `app/Customize/Service/Vpoint/VpointCouponService.php`, `app/Customize/Service/CouponService.php`, `app/template/default/Block/Tracker/` (new Karte templates), `app/Customize/Service/VpointLoggerService.php` (new)
- **Scope:** Backend

#### Associated Epic
- **Epic:** CR5 — V-Point & Credit Card Linkage Integration
- **Parent Requirement:** Integration & Observability

#### Acceptance Criteria
- [ ] **Given** POS scans coupon_id=999999990001, **When** the POS API processes the scan, **Then** the discount is read from `dct_vpoint_redeem_result.kangen_point` (not `dcm_coupon.discount_price`)
- [ ] **Given** a V-Point coupon is scanned at POS, **When** the scan succeeds, **Then** the coupon is marked as USED in `dct_coupon_target`
- [ ] **Given** a V-Point coupon is scanned at POS, **When** the scan succeeds, **Then** a `vpoint_coupon_used` Karte event is fired
- [ ] **Given** sp201 redemption succeeds (EC or Native), **When** the coupon is issued, **Then** a `vpoint_exchange` Karte event is fired with member_id, serial_no, exchange_amount, exchange_date
- [ ] **Given** a V-Point coupon is used at EC checkout, **When** the order completes, **Then** a `vpoint_coupon_used` Karte event is fired with order_id, coupon_amount, serial_no, usage_date
- [ ] **Given** EC channel event, **When** the tracker template renders, **Then** `krt('send', 'vpoint_exchange', {...})` or `krt('send', 'vpoint_coupon_used', {...})` is output in the page HTML
- [ ] **Given** Native channel event, **When** the API responds, **Then** the JSON response includes a `karte_event` object with event_name and properties
- [ ] **Given** any V-Point operation (sp101, sp201, coupon issue, BAT3, BAT4, manual cancel), **When** the operation executes, **Then** a structured JSON log entry is written with: Trigger, Program name, Member ID, Serial Number, key values, Return code, Timestamp

#### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Story 1 | Blocked-by | `dct_vpoint_redeem_result` entity with `kangen_point` column |
| Story 2 | Blocked-by | `VpointApiClient` for sp101/sp201 logging integration points |
| Story 7 | Blocked-by | EC checkout V-Point flow must exist for Karte event integration |
| Story 10 | Blocked-by | Native API must exist for Native Karte event payload |

#### Corner Cases & Edge Scenarios
| # | Scenario | Expected Behavior |
|---|---------|-------------------|
| 1 | POS scans coupon_id=999999990001 but no matching `dct_vpoint_redeem_result` record | Return error to POS; do not apply discount; log warning |
| 2 | POS scans V-Point coupon that is already USED | Return "coupon already used" error; no duplicate usage |
| 3 | Karte event payload serialization fails | Primary operation (POS scan, checkout) still succeeds; Karte event returned as null; error logged |
| 4 | Structured log destination unavailable (disk full, CloudWatch issue) | Operations continue; log failure does not block business flow |
| 5 | sp201 returns error — should still log the failed attempt | Structured log written with error return_cd and failure details |
| 6 | BAT3/BAT4 processes thousands of records | Each record writes individual structured log entry; batch-level summary log at end |
| 7 | `kangen_point` is 0 or NULL in `dct_vpoint_redeem_result` | POS returns error; do not apply ¥0 discount; log anomaly |
| 8 | Multiple Karte events fire for same transaction (retry scenario) | Karte handles idempotently via serial_no; duplicate events are acceptable |

#### Risks
| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| POS API response time degradation from added DB lookups | Medium | Medium | Optimize query; `dct_vpoint_redeem_result` indexed on serial_no |
| Karte event format specification not finalized | Low | Low | Use flexible JSON structure; property names easy to rename |
| Structured logging volume impacts CloudWatch costs | Medium | Low | Use log levels appropriately; INFO for success, ERROR for failures |
| Existing POS API tests break from V-Point coupon handling | Low | Medium | Add V-Point test cases alongside existing tests; no modification to non-V-Point flow |

#### Notes / Additional Information
- `PosController.php` is at `app/Customize/Controller/Api/PosController.php`
- Existing Karte tracker templates are in `app/template/default/Block/Tracker/` (purchase-event-js.twig, cart-event-js.twig, etc.)
- Follow the `krt('send', 'event_name', {properties})` pattern used in existing tracker templates
- `TagLogTrackingService` and `ScriptTrackingServiceExtension` are the existing tracking services — extend or reference for patterns
- For structured logging, consider a `VpointLoggerService` that wraps Monolog with a JSON formatter channel
- EC-Cube uses `log_info()` / `log_error()` helpers — the structured logger should augment, not replace these
- POS API V-Point coupon: `serial_no` from `dct_coupon_target` → lookup `dct_vpoint_redeem_result.kangen_point` for the actual discount value
- `kangen_point` column stores the redemption amount that was exchanged via sp201

---

#### Sub-tasks:

##### Sub-task 15.1: POS API — V-Point Coupon Scan Handling
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Modify `app/Customize/Controller/Api/PosController.php` to handle V-Point coupon scans:
1. Detect `coupon_id=999999990001` in the scanned coupon data
2. Lookup `dct_coupon_target` by coupon scan to get `serial_no`
3. Lookup `dct_vpoint_redeem_result` by `serial_no` to get `kangen_point`
4. Use `kangen_point` as the discount amount (NOT `dcm_coupon.discount_price` which is 0)
5. Validate: coupon not already USED, `kangen_point` > 0, record exists
6. Mark coupon as USED in `dct_coupon_target`
7. Fire `vpoint_coupon_used` Karte event (via logger/event dispatcher)
8. Return standard POS success response with discount amount

- **Affected Files:** `app/Customize/Controller/Api/PosController.php`, `app/Customize/Service/CouponService.php`
- **Parent Story:** Story 15
- **Definition of Done:**
  - [ ] V-Point coupon scan returns correct discount from kangen_point
  - [ ] Coupon marked as USED after successful scan
  - [ ] Error returned for missing/invalid/already-used coupons
  - [ ] Non-V-Point coupon flow unaffected
  - [ ] Karte event fired on success

##### Sub-task 15.2: Karte Event Templates — EC Channel
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Frontend

**Description:**
Create Karte tracker templates in `app/template/default/Block/Tracker/`:
1. `vpoint-exchange-event-js.twig` — fires on sp201 success (checkout confirmation page):
   ```javascript
   krt('send', 'vpoint_exchange', {
     member_id: '{{ member_id }}',
     serial_no: '{{ serial_no }}',
     exchange_amount: {{ exchange_amount }},
     exchange_date: '{{ exchange_date }}'
   });
   ```
2. `vpoint-coupon-used-event-js.twig` — fires on checkout completion (thank-you page):
   ```javascript
   krt('send', 'vpoint_coupon_used', {
     order_id: '{{ order_id }}',
     coupon_amount: {{ coupon_amount }},
     serial_no: '{{ serial_no }}',
     usage_date: '{{ usage_date }}'
   });
   ```
3. Register templates as EC-Cube blocks (if required by the Block/Tracker system)
4. Pass required variables from controller to Twig context
5. Follow existing tracker template patterns (e.g., `purchase-event-js.twig`)

- **Affected Files:** `app/template/default/Block/Tracker/vpoint-exchange-event-js.twig` (new), `app/template/default/Block/Tracker/vpoint-coupon-used-event-js.twig` (new)
- **Parent Story:** Story 15
- **Definition of Done:**
  - [ ] `krt('send', ...)` calls render correctly in page source
  - [ ] Variables populated from controller context
  - [ ] Templates only render when V-Point events apply
  - [ ] No JavaScript errors in browser console

##### Sub-task 15.3: Karte Event Payload — Native Channel
**Type:** Sub-task | **Estimate:** 3h | **Skill:** Backend

**Description:**
Modify the Native API response for V-Point operations:
1. In the Native V-Point redemption endpoint (from Story 10), ensure the JSON response includes:
   ```json
   {
     "karte_event": {
       "event_name": "vpoint_exchange",
       "properties": {
         "member_id": "...",
         "serial_no": "...",
         "exchange_amount": 1000,
         "exchange_date": "2026-05-12"
       }
     }
   }
   ```
2. For POS coupon usage, include `vpoint_coupon_used` event in POS API response
3. On failure: `karte_event: null` — do not block the primary response
4. Create a `KarteEventBuilder` helper class or method to construct event payloads consistently across EC and Native

- **Affected Files:** `app/Customize/Controller/Api/PosController.php`, `app/Customize/Controller/Api/V2/CouponController.php` (or relevant Native API controller)
- **Parent Story:** Story 15
- **Definition of Done:**
  - [ ] Native redemption response includes karte_event object
  - [ ] POS response includes karte_event object
  - [ ] Failed serialization returns null without blocking response
  - [ ] Event payload structure matches Karte specification

##### Sub-task 15.4: VpointLoggerService — Structured JSON Logging
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend

**Description:**
Create `app/Customize/Service/VpointLoggerService.php`:
1. Wraps Monolog logger (injected via DI) with a dedicated `vpoint` channel
2. Method `logOperation(string $trigger, string $programName, array $context): void`
   - `$trigger`: 'sp101', 'sp201', 'sp201_cancel', 'coupon_issue', 'bat3', 'bat4', 'manual'
   - `$programName`: human-readable program identifier
   - `$context`: `['member_id' => ..., 'serial_no' => ..., 'return_cd' => ..., ...]`
3. Output format: structured JSON with fields: `trigger`, `program_name`, `member_id`, `serial_no`, `key_values`, `return_code`, `timestamp` (ISO 8601 JST)
4. Integrate into existing V-Point call sites:
   - `VpointApiClient` — log sp101/sp201 calls and responses
   - `VpointCouponService` — log coupon issuance
   - BAT3/BAT4 commands — log each record processed
   - `VpointCancelService` — log manual admin cancellations
5. Use log level INFO for success, ERROR for failures, WARNING for anomalies
6. Configure Monolog channel in `app/config/packages/monolog.yaml` (or equivalent EC-Cube config)

- **Affected Files:** `app/Customize/Service/VpointLoggerService.php` (new), `app/Customize/Service/Vpoint/VpointApiClient.php`, `app/Customize/Service/Vpoint/VpointCouponService.php`, `app/config/packages/` (monolog config)
- **Parent Story:** Story 15
- **Definition of Done:**
  - [ ] All V-Point operations write structured JSON logs
  - [ ] Log entries contain all required fields
  - [ ] Log level appropriate per operation outcome
  - [ ] Existing log_info/log_error calls not broken
  - [ ] Logs parseable by CloudWatch/ELK

##### Sub-task 15.5: Unit Tests — POS V-Point, Karte Events & Logging
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend

**Description:**
Write unit tests:
1. POS API: V-Point coupon scan reads kangen_point, not discount_price
2. POS API: already-used coupon returns error
3. POS API: missing dct_vpoint_redeem_result returns error
4. Karte event builder: correct payload structure for both event types
5. Karte event builder: null returned on serialization failure
6. VpointLoggerService: structured log output contains all required fields
7. VpointLoggerService: correct log levels for success/failure
8. Integration: POS scan triggers both coupon usage and Karte event and structured log

- **Affected Files:** `tests/Customize/Controller/Api/PosControllerTest.php`, `tests/Customize/Service/VpointLoggerServiceTest.php` (new)
- **Parent Story:** Story 15
- **Definition of Done:**
  - [ ] All test cases pass
  - [ ] POS V-Point flow fully covered
  - [ ] Karte event payloads validated
  - [ ] Structured log output verified


---

## Cross-Story Dependencies

| Story | Depends On | Type | Details |
|-------|-----------|------|---------|
| Story 1 | None | — | Foundation — no upstream dependencies |
| Story 2 | Story 1 | Schema | Entities required for API response storage |
| Story 3 | Story 2 | Service | sp101 API client needed for barcode verification |
| Story 4 | Story 3 | Logic | Card linkage must exist before unlink/withdrawal |
| Story 5 | Story 1 | Schema | Import tables must exist before BAT1/BAT2 |
| Story 6 | Story 1, Story 2 | Schema + Service | Entities + sp101 API client needed |
| Story 7 | Story 6 | Flow | STEP1 reservation must exist before STEP2 execution |
| Story 8 | Story 6, Story 7 | API | Backend endpoints must be ready for frontend integration |
| Story 9 | Story 2, Story 7 | Service | API client + redemption service patterns |
| Story 10 | Story 7 | Data | cancel_status=3 records generated by Story 7 cancel flow |
| Story 11 | Story 7 | Data | V-Point coupons must be issuable before display/history |
| Story 12 | Story 3 | Data | Card linkage data must exist for admin summary |
| Story 13 | Story 7 | Service | Redemption records must exist for admin cancel |
| Story 14 | Story 7 | Logic | V-Point payment method must be implemented |
| Story 15 | Story 7, Story 10 | Service | Redemption + BAT flows must exist for POS/Karte/logging |

## Suggested Sprint Allocation

| Sprint | Stories | Total Points | Sprint Goal |
|--------|---------|-------------|-------------|
| Sprint 1 | Story 1, Story 2 | 10 SP | Database foundation + CCCMK API client with encryption |
| Sprint 2 | Story 3, Story 4, Story 5 | 16 SP | Card linkage (scan/unlink/withdrawal) + SFTP file import |
| Sprint 3 | Story 6, Story 7, Story 8 | 18 SP | Complete EC checkout V-Point exchange flow (STEP1→STEP3) |
| Sprint 4 | Story 9, Story 10, Story 12 | 21 SP | Native app integration + BAT3/BAT4 recovery + Admin summary |
| Sprint 5 | Story 11, Story 13, Story 14, Story 15 | 21 SP | Coupon display + Admin cancel + Payment handling + POS/Karte/Logging |

## Risk Summary (Across All Stories)

| # | Risk | Affected Stories | Likelihood | Impact | Mitigation |
|---|------|-----------------|-----------|--------|-----------|
| 1 | CCCMK encryption spec ambiguity | Story 2, 6, 7, 9 | Medium | High | Validate against test vector early; confirm with CCCMK staging |
| 2 | EBCDIC→UTF-8 conversion for Japanese (IBM encoding) | Story 5 | Medium | High | Obtain sample files from SMCC; thorough character testing |
| 3 | sp201 failure after point deduction (money flow risk) | Story 7, 10 | Low | Critical | BAT3/BAT4 recovery path; structured logging; Slack alerts |
| 4 | Redis key TTL/session alignment during checkout | Story 6, 7 | Medium | Medium | Configure TTL > checkout session timeout; document settings |
| 5 | Shift_JIS encoding correctness for SP file generation | Story 10 | Medium | High | Use CP932 (Windows-31J); validate with CCCMK EDI test server |
| 6 | POS API backward compatibility | Story 15 | Low | High | Regression test all existing coupon flows before deployment |
| 7 | Manual SQL coordination across environments | Story 1 | Medium | High | Version SQL scripts; include in deployment checklist |
| 8 | CCCMK credential availability (alliance_cd, passwd) | Story 2, all API stories | Medium | Critical | Track as external dependency; use placeholders from Secrets Manager |
| 9 | Cancel state machine edge transitions | Story 13 | Medium | Medium | Exhaustive state transition tests; document all valid paths |
| 10 | Excel export performance for large date ranges | Story 12 | Low | Medium | Paginate query; stream XLSX output for large datasets |

## Assumptions

- CCCMK/SMCC will provide production API credentials (alliance_cd, passwd, encryption key, IV) before Sprint 2
- The `dtb_customer.ext_attr_text3` column already exists and stores `app_member_id` — no ALTER needed
- Redis is available in all environments (dev, staging, production)
- PhpSpreadsheet library is already available in the project dependencies
- SMCC SFTP server will be accessible from the EC platform's production IPs
- Mobile app team handles native UI implementation; backend only provides API endpoints
- POS system team coordinates barcode scan changes; EC team modifies API response only
- Manual SQL scripts are executed by DevOps/DBA before code deployment in each environment
- Karte SDK/JS library is already integrated in the frontend templates
- Exchange rate is fixed at 1 pt = ¥1 (no dynamic conversion)
- Serial number sequence is managed at application level (not database sequence) to support A03/A04 prefixes
- Coupon master record (id=999999990001) is pre-seeded via SQL before Story 7

## Traceability Matrix

| SRS Requirement | Description | Story | Sub-tasks | Status |
|----------------|-------------|-------|-----------|--------|
| Req 1 | Card Linkage — Barcode scan | Story 3 | 3.1–3.5 | ✅ Covered |
| Req 2 | Card Linkage — SFTP daily file import | Story 5 | 5.1–5.9 | ✅ Covered |
| Req 3 | Card Linkage — Status management | Story 3, Story 4 | 3.1–3.5, 4.1–4.5 | ✅ Covered |
| Req 4 | V-Point — sp101 balance inquiry | Story 2, Story 6 | 2.1–2.4, 6.1–6.6 | ✅ Covered |
| Req 5 | V-Point — sp201 point usage/cancel | Story 2, Story 7 | 2.1–2.4, 7.1–7.6 | ✅ Covered |
| Req 6 | V-Point — AES-256-CBC encryption | Story 2 | 2.2 | ✅ Covered |
| Req 7 | EC Checkout — V-Point exchange modal | Story 6, Story 7, Story 8 | 6.1–6.6, 7.1–7.6, 8.1–8.6 | ✅ Covered |
| Req 8 | Native App — V-Point balance + exchange | Story 9 | 9.1–9.5 | ✅ Covered |
| Req 9 | Coupon — V-Point coupon creation/history | Story 7, Story 11, Story 15 | 7.3, 11.1–11.5, 15.1 | ✅ Covered |
| Req 10 | Batch — BAT1 SFTP retrieval | Story 5 | 5.1–5.2 | ✅ Covered |
| Req 11 | Batch — BAT2 validation/import | Story 5 | 5.3–5.7 | ✅ Covered |
| Req 12 | Batch — BAT3 SP recovery file | Story 10 | 10.1–10.4 | ✅ Covered |
| Req 13 | Batch — BAT4 SP result file | Story 10 | 10.5–10.8 | ✅ Covered |
| Req 14 | File Transfer — HTTPS fixed-length | Story 10 | 10.3, 10.5 | ✅ Covered |
| Req 15 | Admin — Card linkage summary | Story 12 | 12.1–12.3 | ✅ Covered |
| Req 16 | Admin — Member detail + manual unlink | Story 12 | 12.4–12.5 | ✅ Covered |
| Req 17 | Admin — V-Point cancel redemption | Story 13 | 13.1–13.4 | ✅ Covered |
| Req 18 | Common — Error message handling | Story 2 | 2.3 | ✅ Covered |
| Req 19 | Admin — Payment method PG button control | Story 14 | 14.1–14.2 | ✅ Covered |
| Req 20 | Admin — Payment Status List filtering | Story 14 | 14.3 | ✅ Covered |
| Req 21 | Admin — Change Mode Checkout (no impl) | Story 14 | 14.4 (verification only) | ✅ Covered |
| Req 22 | EC Frontend — Purchase history cancel status | Story 11 | 11.3 | ✅ Covered |
