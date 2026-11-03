# Work Breakdown Structure — JIRA Import Ready

## CR5: V-Point & Credit Card Linkage Integration

**Generated:** 2026-04-29
**Revised Estimate:** 420–540 hours (10–13 weeks, full team)

---

## Epic: CR5 — V-Point & Credit Card Linkage Integration

---

### Story 1: Database Schema Design & Creation

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] 4 new tables created with proper indexes and constraints
- [ ] ext_attr_text3 column added to dtb_customer
- [ ] All foreign key relationships documented
- [ ] Schema validated against requirement DB specs

#### Sub-tasks:
- [ ] Create dct_vpoint_redeem_result table (sp201 parameters & results, 40+ columns) — M
- [ ] Create dtb_customer_card_info table (card linkage history, is_valid constraint) — M
- [ ] Create dtb_affiliated_card_info table (SMCC card master data, 30+ columns) — M
- [ ] Create dtb_card_application_info table (daily import tracking) — S
- [ ] Add ext_attr_text3 (app_member_id) to dtb_customer — S
- [ ] Create indexes: app_member_id, card_linkaged_dt, is_valid, serial_no — S
- [ ] Write manual SQL migration scripts (no Doctrine migrations) — S
- [ ] Verify schema against requirement docs (5.DB, dtb_* sheets) — S

---

### Story 2: AES-256-CBC Encryption/Decryption Service

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Encrypts/decrypts fields per CCCMK spec (AES-256-CBC, PKCS5, base64)
- [ ] MD5 hash → key expansion to 256-bit implemented correctly
- [ ] Passes CCCMK-provided test vectors
- [ ] URL-encoding applied for query string parameters

#### Sub-tasks:
- [ ] Implement EncryptionService (encrypt/decrypt methods) — M
- [ ] Implement MD5 key expansion algorithm (hash → repeat to 32 bytes) — S
- [ ] Add base64 encoding/decoding and URL-encoding — S
- [ ] Unit tests with test vectors from Encryption.pdf — S
- [ ] Integration test: encrypt → send → decrypt response round-trip — S

---

### Story 3: sp101 API Client — Member Balance Inquiry

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Calls sp101.do API (POST) with 15 encrypted parameters
- [ ] Handles 12+ return codes (00, 04, 10, 11, 14, 16, 18, 22, 23, 80, 90, 92, 93, 94, 99)
- [ ] Returns balance on success; fallback display on failure
- [ ] Timeout handling (3s) with return code mapping

#### Sub-tasks:
- [ ] Implement CccmkApiClient::callSp101() with encrypted request building — M
- [ ] Implement sp101 response parser (XML, UTF-8) — S
- [ ] Map 12+ return codes to user-facing error messages — S
- [ ] Add timeout handling (3s network timeout → return code 04/98) — S
- [ ] Unit tests for each return code scenario — M
- [ ] Log request/response (excluding PII) — S

---

### Story 4: sp201 API Client — Point Operations

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] Calls sp201.do API (POST) for point usage (point_kbn=01) and cancellation (cancel_kbn=1)
- [ ] Handles 20+ return codes with appropriate error recovery
- [ ] Generates unique serial_no per day (20-digit)
- [ ] Stores all requests/responses in dct_vpoint_redeem_result before and after API call

#### Sub-tasks:
- [ ] Implement CccmkApiClient::callSp201() with encrypted request — M
- [ ] Implement sp201 response parser (XML, 20+ return codes) — M
- [ ] Implement serial_no generator (20-digit, unique per calendar day JST) — S
- [ ] Implement retry logic (retry_kbn=0 first attempt, 1 retry; max 2 retries) — S
- [ ] Implement sp201 cancel flow (cancel_kbn=1, same serial_no) — M
- [ ] Store request params in dct_vpoint_redeem_result BEFORE API call — S
- [ ] Update dct_vpoint_redeem_result with response AFTER API call — S
- [ ] Unit tests for usage, cancellation, timeout, double-request (code 05) — M

---

### Story 5: Card Linkage Service — Barcode & Link/Unlink

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Validates barcode (Code128, 8-digit, modulus 10 check digit)
- [ ] Authenticates member via birthday match against SMCC data
- [ ] Creates/updates card linkage records in dtb_customer_card_info
- [ ] Enforces single valid link per member constraint

#### Sub-tasks:
- [ ] Implement BarcodeValidator (Code128 format, modulus 10 weight 2/1) — S
- [ ] Implement CardLinkageService::linkCard() with birthday auth — M
- [ ] Implement CardLinkageService::unlinkCard() with is_valid=0 update — S
- [ ] Implement getCardLinkageStatus() for member detail display — S
- [ ] Handle card reissue scenario (old is_valid=0, new is_valid=1) — S
- [ ] Handle member withdrawal → automatic dislinkage — S
- [ ] Unit tests: valid/invalid barcode, birthday match/mismatch, reissue, concurrent link prevention — M

---

### Story 6: V-Point Redemption Service — Orchestration

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] Orchestrates sp101 (balance check) → sp201 (point usage) → coupon issuance flow
- [ ] Handles GMO skip logic when full V-Point payment
- [ ] Handles partial failure: sp201 success + GMO fail → sp201 cancel
- [ ] Records all operations for BAT3/4 recovery

#### Sub-tasks:
- [ ] Implement VPointRedemptionService::getBalance() — calls sp101, returns balance — S
- [ ] Implement VPointRedemptionService::redeemPoints() — calls sp201, issues coupon — M
- [ ] Implement VPointRedemptionService::cancelRedemption() — sp201 cancel — M
- [ ] Implement full V-Point payment detection (skip GMO call) — S
- [ ] Implement partial failure handling (sp201 OK + GMO fail → cancel) — M
- [ ] Implement recovery data recording (dct_vpoint_redeem_result) — S
- [ ] Unit tests: all flow combinations (success, partial fail, timeout, double-request) — M

---

### Story 7: BAT1 — SMCC File Retrieval (SFTP)

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Retrieves files from SMCC SFTP server every 30 minutes
- [ ] Stores retrieved files in S3 bucket with rename
- [ ] Alerts via Slack if no file received during 10:00-11:00 window
- [ ] Public key authentication implemented

#### Sub-tasks:
- [ ] Implement SmccSftpClient with public key auth (phpseclib) — M
- [ ] Implement BAT1 command: SFTP GET → S3 upload with rename — M
- [ ] Implement 30-minute scheduling (cron/scheduler) — S
- [ ] Implement 10:00-11:00 window alert logic (Slack webhook) — S
- [ ] Handle SFTP errors: timeout, auth failure, no file found — S
- [ ] Unit/integration tests with SFTP mock — M

---

### Story 8: BAT2 — SMCC Data Import & Validation

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] Parses SMCC fixed-length file (Shift_JIS/EBCDIC encoding)
- [ ] Validates 5 data types (10/20/30/40/50) with distinct rules
- [ ] Imports valid records to dtb_affiliated_card_info + dtb_customer_card_info
- [ ] Partial success: invalid records excluded, valid records processed
- [ ] Slack notification with success/error counts

#### Sub-tasks:
- [ ] Implement SMCC file parser (fixed-length, encoding conversion) — M
- [ ] Implement validation for data_type 10 (New): all required fields, no duplicate mrmax_id — M
- [ ] Implement validation for data_type 20 (Cancel): member exists, mark cancelled — S
- [ ] Implement validation for data_type 30 (Change): update specific fields — S
- [ ] Implement validation for data_type 40 (Reissue): old card invalid, new card valid — M
- [ ] Implement validation for data_type 50 (Update): renewal info update — S
- [ ] Implement dtb_affiliated_card_info record creation/update — M
- [ ] Implement dtb_customer_card_info status update based on data_type — M
- [ ] Implement Slack notification (success/error count report) — S
- [ ] Unit tests for each data_type, validation edge cases — M

---

### Story 9: BAT3 — Create SP Recovery File

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] Queries dct_vpoint_redeem_result for failed sp201 transactions
- [ ] Creates fixed-length SP file (783 bytes/record, Shift_JIS, CRLF)
- [ ] Applies 13 validation checks before file creation
- [ ] Handles file merge (day N not retrieved → merge with N+1)
- [ ] Uploads to S3/HTTPS for CCCMK retrieval
- [ ] Creates header-only file if no errors

#### Sub-tasks:
- [ ] Implement SP file generator: header record (783 bytes, fixed fields) — M
- [ ] Implement SP file generator: body records from dct_vpoint_redeem_result — M
- [ ] Implement 13 validation checks on file content — M
- [ ] Implement file merge logic (check CCCMK retrieval status, merge if missed) — M
- [ ] Implement ZIP compression and S3 upload — S
- [ ] Implement header-only file for zero-error days — S
- [ ] Implement Slack notification on file generation/merge events — S
- [ ] Unit tests: file format, validation checks, merge scenarios — M

---

### Story 10: BAT4 — Process SP Result File

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Retrieves result file from CCCMK EDI server via HTTPS GET
- [ ] Parses fixed-length result file
- [ ] Updates dct_vpoint_redeem_result with final recovery status
- [ ] Handles file not found (retry next day)

#### Sub-tasks:
- [ ] Implement HTTPS GET client for CCCMK EDI (IP whitelist, Basic Auth) — M
- [ ] Implement result file parser (fixed-length, Shift_JIS) — M
- [ ] Update dct_vpoint_redeem_result status based on result codes — S
- [ ] Handle file not found: log, retry next day — S
- [ ] Issue coupon for recovered transactions (if recovery success) — S
- [ ] Slack notification on BAT4 completion/errors — S
- [ ] Unit/integration tests — M

---

### Story 11: EC Checkout — V-Point Exchange Flow

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] V-Point exchange modal added to checkout (STEP1-1→STEP3)
- [ ] Numeric keyboard for point input
- [ ] Max input = available balance (validated client + server side)
- [ ] Skip GMO payment if full V-Point payment
- [ ] Error handling: sp201 fail → show message, allow retry
- [ ] sp201 cancel on payment failure

#### Sub-tasks:
- [ ] Controller: VPointCheckoutController (STEP1-1 → STEP3 flow) — M
- [ ] Template: V-Point exchange modal (radio button active/disabled control) — M
- [ ] JavaScript: numeric keyboard, amount validation, button state management — M
- [ ] Backend: integrate VPointRedemptionService with checkout flow — M
- [ ] Backend: GMO skip logic (full V-Point payment detection) — S
- [ ] Backend: sp201 cancel on GMO payment failure — M
- [ ] Error message display per sp201 return code — S
- [ ] Frontend/backend tests for all flow combinations — M

---

### Story 12: Native App — V-Point Exchange Screens

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] Membership card screen shows V-Point balance with refresh
- [ ] Coupon exchange buttons (3→9 accordion, "All" option first, ascending order)
- [ ] Buttons disabled if insufficient balance
- [ ] Coupon issued on successful exchange
- [ ] Fallback ****pt display on sp101 error

#### Sub-tasks:
- [ ] API endpoint: GET /api/vpoint/balance (calls sp101) — S
- [ ] API endpoint: POST /api/vpoint/redeem (calls sp201, issues coupon) — M
- [ ] API endpoint: GET /api/vpoint/exchanges (available exchange amounts) — S
- [ ] Template: Membership card V-Point balance display + refresh button — M
- [ ] Template: Coupon exchange accordion (3→9 buttons, disable logic) — M
- [ ] Template: Coupon exchange confirmation dialog — S
- [ ] Error handling: ****pt display, disabled buttons, error messages — S
- [ ] Tests for all native app API endpoints — M

---

### Story 13: Admin — Card Linkage Summary

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Daily/weekly/monthly counts of linked/unlinked members by data_type
- [ ] Date range picker (period selectable)
- [ ] Excel export functionality
- [ ] Responsive admin template

#### Sub-tasks:
- [ ] Controller: CardLinkageSummaryController with date range filters — M
- [ ] Service: Aggregation queries (optimized, indexed) — M
- [ ] Template: Summary table (daily/weekly/monthly toggle, data_type breakdown) — M
- [ ] Feature: Excel export with formatted data — S
- [ ] Tests: Query correctness for different date ranges — S

---

### Story 14: Admin — Member Search & Detail Enhancement

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] Card linkage status checkbox filter on member list
- [ ] Member detail shows: linkage status, linkage date, link history
- [ ] Manual dislinkage button with V-Point coupon warning
- [ ] V-Point coupon exchange history on member detail

#### Sub-tasks:
- [ ] Modify member list search: add "Linked"/"Not Linked" checkbox filters — M
- [ ] Enhance member detail page: linkage status, dates, history section — M
- [ ] Implement dislinkage button: check active coupons, show warning dialog, confirm → unlink — M
- [ ] Add V-Point coupon exchange history display to member detail — S
- [ ] Tests: search filter, detail display, dislinkage workflow — M

---

### Story 15: Admin — V-Point Cancel Redemption

**Priority:** High
**Story Points:** 5
**Acceptance Criteria:**
- [ ] Search transactions by serial_no or member
- [ ] Call sp201 cancel with cancel_kbn=1
- [ ] 12-month cancellation window enforced
- [ ] Audit log: admin user, timestamp, before/after state
- [ ] Coupon invalidated on successful cancel

#### Sub-tasks:
- [ ] Controller: CancelRedemptionController (search, cancel action) — M
- [ ] Service: Call sp201 cancel, verify within 12-month window — S
- [ ] Template: Transaction search, cancel button, confirmation dialog — M
- [ ] Audit log: record admin user, action, timestamp — S
- [ ] Tests: successful cancel, expired window (>12mo), sp201 error handling — S

---

### Story 16: Coupon Management Enhancement

**Priority:** High
**Story Points:** 5
**Acceptance Criteria:**
- [ ] Admin can create digital V-Point coupons (type1=3, scope=1)
- [ ] Coupon denomination configuration (¥100, ¥300, ¥1000, etc.)
- [ ] V-Point coupon display in used/expired coupon screen (combined sort by date)

#### Sub-tasks:
- [ ] Modify admin coupon creation form: add V-Point coupon type fields — M
- [ ] Implement dct_vpoint_exchanges configuration (exchange amounts, sort order) — S
- [ ] Modify used/expired coupon display: combined sort, V-Point coupon identification — S
- [ ] Tests: coupon creation, display, sorting — S

---

### Story 17: SFTP & HTTPS Infrastructure Setup

**Priority:** High
**Story Points:** 5
**Acceptance Criteria:**
- [ ] AWS Transfer Family configured for SMCC SFTP
- [ ] Static IP addresses provisioned and whitelisted
- [ ] Public key authentication configured
- [ ] HTTPS endpoint configured for CCCMK file transfer
- [ ] SSL/TLS certificates installed (trusted CA for PROD, self-signed for STG)

#### Sub-tasks:
- [ ] Configure AWS Transfer Family (SFTP server) — M
- [ ] Provision and register static IPs (PROD: 54.150.166.146, 18.176.29.207) — S
- [ ] Set up public key exchange with SMCC — S
- [ ] Configure HTTPS endpoint for CCCMK EDI file hosting — S
- [ ] SSL/TLS certificate installation and validation — S

---

### Story 18: Configuration & Environment Setup

**Priority:** High
**Story Points:** 3
**Acceptance Criteria:**
- [ ] All environment variables configured (PROD/STG/DEV)
- [ ] Encryption keys stored in AWS Secrets Manager
- [ ] Slack webhook configured for BAT alerts
- [ ] IP whitelist documented and applied

#### Sub-tasks:
- [ ] Define environment variables: SMCC_SFTP_*, CCCMK_EDI_*, ENCRYPTION_* — S
- [ ] Store secrets in AWS Secrets Manager (alliance_cd, passwd, encryption_key, IV) — S
- [ ] Configure Slack webhook for BAT monitoring alerts — S
- [ ] Document IP whitelist (SMCC + CCCMK) — S

---

### Story 19: Unit Testing

**Priority:** High
**Story Points:** 8
**Acceptance Criteria:**
- [ ] 40+ unit tests covering core business logic
- [ ] All encryption test vectors pass
- [ ] All return code handling tested
- [ ] Barcode validation edge cases covered

#### Sub-tasks:
- [ ] EncryptionService tests (encrypt/decrypt with CCCMK test vectors) — S
- [ ] BarcodeValidator tests (valid/invalid barcodes, check digit edge cases) — S
- [ ] CardLinkageService tests (link, unlink, reissue, concurrent prevention) — M
- [ ] VPointRedemptionService tests (balance, redeem, cancel, error codes) — M
- [ ] BAT file parsing tests (each data_type, validation checks) — M
- [ ] SP file generation tests (format, header, body, merge logic) — M

---

### Story 20: Integration & End-to-End Testing

**Priority:** High
**Story Points:** 13
**Acceptance Criteria:**
- [ ] Full BAT1→BAT2→BAT3→BAT4 workflow tested
- [ ] API encryption round-trip tested with mock CCCMK server
- [ ] EC checkout + V-Point + GMO payment flow tested end-to-end
- [ ] Error recovery scenarios verified

#### Sub-tasks:
- [ ] Set up SFTP mock server (Docker) — M
- [ ] Set up CCCMK API mock (sp101/sp201 responses by return code) — M
- [ ] BAT workflow integration test (file retrieve → import → SP create → result process) — L
- [ ] EC checkout flow test (V-Point exchange → payment → coupon) — M
- [ ] Error recovery test (sp201 timeout → BAT3 → BAT4 → reconciliation) — M
- [ ] Performance test: 600k records batch processing — M

---

### Story 21: Security Review & Hardening

**Priority:** High
**Story Points:** 5
**Acceptance Criteria:**
- [ ] AES-256-CBC implementation reviewed and verified
- [ ] No PII in application logs
- [ ] SQL injection prevention verified (parameterized queries)
- [ ] API key/cert management documented
- [ ] Input validation at all system boundaries

#### Sub-tasks:
- [ ] Code review: encryption implementation against CCCMK spec — S
- [ ] Log audit: verify no PII (kaiin_id, birthday, etc.) in logs — S
- [ ] SQL review: all queries use parameterized bindings — S
- [ ] Api key storage review: AWS Secrets Manager usage — S
- [ ] Input validation: barcode, birthday, point amounts, serial_no — S

---

### Story 22: Documentation & Deployment Preparation

**Priority:** Medium
**Story Points:** 5
**Acceptance Criteria:**
- [ ] Internal API documentation (sp101/sp201 wrapper)
- [ ] Admin user guide (card management, V-Point operations)
- [ ] Batch job monitoring runbook
- [ ] Deployment checklist (PROD/STG)
- [ ] Error code reference (troubleshooting guide)

#### Sub-tasks:
- [ ] Write internal API doc (V-Point endpoints, request/response format) — S
- [ ] Write admin user guide (linkage summary, dislinkage, cancel) — S
- [ ] Write BAT monitoring runbook (Slack alerts, error resolution steps) — S
- [ ] Create deployment checklist (env vars, keys, IP whitelist, cert, cron) — S
- [ ] Create error code reference (sp101/sp201 codes → user actions) — S

---

## Dependencies

| Story | Depends On | Type |
|-------|-----------|------|
| Story 2 (Encryption) | CCCMK encryption key + IV + test vectors | External |
| Story 3 (sp101) | Story 2 (Encryption) + Story 1 (DB) | Finish-to-Start |
| Story 4 (sp201) | Story 2 (Encryption) + Story 1 (DB) | Finish-to-Start |
| Story 5 (Card Linkage) | Story 1 (DB) | Finish-to-Start |
| Story 6 (Redemption) | Story 3 (sp101) + Story 4 (sp201) + Story 5 (Card Linkage) | Finish-to-Start |
| Story 7 (BAT1) | Story 17 (SFTP Infra) | Finish-to-Start |
| Story 8 (BAT2) | Story 1 (DB) + Story 7 (BAT1) | Finish-to-Start |
| Story 9 (BAT3) | Story 1 (DB) + Story 4 (sp201) | Finish-to-Start |
| Story 10 (BAT4) | Story 9 (BAT3) + Story 17 (HTTPS Infra) | Finish-to-Start |
| Story 11 (EC Checkout) | Story 6 (Redemption Service) | Finish-to-Start |
| Story 12 (Native App) | Story 6 (Redemption Service) | Finish-to-Start |
| Story 13 (Admin Summary) | Story 1 (DB) + Story 5 (Card Linkage) | Finish-to-Start |
| Story 14 (Admin Detail) | Story 5 (Card Linkage) + Story 13 (Admin Summary) | Finish-to-Start |
| Story 15 (Admin Cancel) | Story 4 (sp201) | Finish-to-Start |
| Story 16 (Coupon Mgmt) | Story 1 (DB) | Finish-to-Start |
| Story 19 (Unit Testing) | Stories 2-6 | Finish-to-Start |
| Story 20 (Integration) | Stories 7-16 | Finish-to-Start |
| Story 21 (Security) | Stories 2-4 | Finish-to-Start |

---

## Suggested Sprint Allocation

| Sprint | Stories | Focus | Total Points |
|--------|---------|-------|-------------|
| Sprint 1 (Weeks 1-2) | 1, 2, 17, 18 | Foundation: DB, Encryption, Infrastructure, Config | 29 |
| Sprint 2 (Weeks 3-4) | 3, 4, 5, 7 | Core Services: sp101, sp201, Card Linkage, BAT1 | 37 |
| Sprint 3 (Weeks 5-6) | 6, 8, 9 | Orchestration: Redemption Service, BAT2, BAT3 | 39 |
| Sprint 4 (Weeks 7-8) | 10, 11, 12 | User-Facing: BAT4, EC Checkout, Native App | 34 |
| Sprint 5 (Weeks 9-10) | 13, 14, 15, 16 | Admin Screens: Summary, Detail, Cancel, Coupon | 26 |
| Sprint 6 (Weeks 11-13) | 19, 20, 21, 22 | Quality: Testing, Security, Docs, Deployment | 31 |

**Total Story Points: 196**
**Total Estimated Effort: 420–540 hours**
**Team Size Recommendation: 3-4 developers + 1 QA + 1 DevOps (part-time)**
