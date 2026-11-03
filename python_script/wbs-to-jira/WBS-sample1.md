## Stories

### Story 1: BAT5 — Automated Cancel Processing
**Type:** Story | **Priority:** H | **Points:** 8 | **Sprint:** 2
**Assignee:** Dev 4 (Pavel) | **Status:** Pending

#### Story Overview
BAT5 is a new daily batch command (introduced in v23) that processes admin-approved V-Point cancellation records by calling the CCCMK sp201 Cancel API. When an admin approves a cancellation via the admin panel, the `dct_vpoint_redeem_result` record is set to `status=2` (Approved) with `point_kbn=74` (Cancel). BAT5 picks up these records in FIFO order (`id ASC`), selecting the latest record per `serial_no` via a `MAX(id)` subquery, and executes sp201 Cancel for each. Before each API call, the record is set to `status=3` (Processing) with `error_cd=NULL` and flushed to DB. The sp201 response `return_cd` is classified by code_type: type 1 (`return_cd=00`) sets `status=4` (Success), type 2 (recoverable codes: `04`,`11`,`16`,`18`,`80`,`92`,`98`,`99`) sets `status=6` (Recovery/Resend — picked up by BAT3 for SP file recovery), type 3 (all other permanent failure codes: `05`,`10`,`14`,`15`,`17`,`22`,`23`,`41`–`44`,`52`,`53`,`90`) sets `status=5` (Failed — admin investigation required). All updates set `program_name=5` (BAT5), `get_return_date`, `return_cd`, and `update_date`. The command uses Redis distributed lock (TTL=30min, non-blocking) to prevent concurrent execution, supports `--dry-run` (log-only, no DB writes/API calls/Slack) and `--limit=N` flags, and sends Slack notifications via `CommandTrait::sendMailBatch()` using `EMAIL_RECEIVE_BATCH` on batch start, completion with success/failed/recovery counts, and critical errors. Scheduled at 16:00 JST (07:00 UTC) daily — avoids BAT4 (11:30 JST) and BAT3 (14:30 JST). A single record failure must not abort the entire batch — each record is processed independently. Entity constants already defined: `POINT_KBN_CANCEL=74`, `STATUS_APPROVED=2`, `STATUS_PROCESSING=3`, `STATUS_COMPLETED=4`, `STATUS_FAILED=5`, `STATUS_RECOVERY_RESEND=6`, `PROGRAM_BAT5=5`. The `CccmkApiClient` (sp201 caller) does not exist in the codebase yet — part of a separate story (T4: CCCMK API Client).
- **Linked Requirements:** SRS §3.7 (`5.DB_modified.pdf`), CR5-Requirement-Change-Analysis-v23-v25 §3.7, CR5-Complete-Knowledge-Base §9.6, §13.2 (Code Type Classification), §14 (Cancel Flow)
- **Affected Components:** `Command/AutoCancelProcessingCommand.php`, `Repository/VpointRedeemResultRepository.php`, `Entity/VpointRedeemResult.php` (existing)
- **Scope:** Backend
- **Associated Epic:** CR5 — V-Point & Credit Card Linkage Integration

#### Sub-task List
- [ ] 1.1 — Create BAT5 Symfony Console Command (Backend, 8h)
- [ ] 1.2 — Build BAT5 Query Logic (Backend, 4h)
- [ ] 1.3 — Implement Redis Lock, Slack Notifications, and Dry-Run Mode (Backend, 6h)
- [ ] 1.4 — Write Unit Tests (Backend, 8h)
- [ ] 1.5 — BAT (Backend, 4h)

---
#### Sub-tasks:

##### Sub-task 1.1: Create BAT5 Symfony Console Command
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend
**Assignee:** Dev 4 (Pavel) | **Status:** Pending
###### Summary
Create `app/Customize/Command/AutoCancelProcessingCommand.php` — a Symfony Console command registered as `batch0505:auto-cancel-processing`. The command follows the established batch pattern from `SpRecoveryFileCommand` (BAT3): constructor dependency injection for EntityManager, Repository, Redis, and MessageBus; CLI options for `--dry-run` and `--limit`; uses `CommandTrait` for logging and mail dispatch. The main execute flow acquires a Redis lock, queries approved cancel records, iterates each record calling sp201 Cancel, classifies the response by code_type (1→status=4, 2→status=6, 3→status=5), updates the record with `program_name=5`, `return_cd`, `error_cd`, `get_return_date`, `update_date`, and sends Slack notifications on completion. The `CccmkApiClient` does not exist yet (separate story T4) — the constructor should include a placeholder or interface for the sp201 caller.
###### Requirement Details
Command registration: name `batch0505:auto-cancel-processing`, class `Customize\Command\AutoCancelProcessingCommand`. Constructor DI: `EntityManagerInterface`, `VpointRedeemResultRepository`, `RedisLock`, `MessageBusInterface` (Slack via CommandTrait), and a placeholder for `CccmkApiClient`. CLI options: `--dry-run` (`VALUE_NONE`, default false — log only, no DB/API/Slack), `--limit` (`VALUE_REQUIRED`, default null — cap records per run). Constants: `LOCK_RESOURCE='batch0505_auto_cancel'`, `LOCK_TTL=1800.0`. Exit codes: 0=success (including empty result set), 1=lock conflict. Trait: `use CommandTrait` providing `sendMailBatch()`, `logInfo()`, `logError()`, `logException()`, `getBatchNumber()`. Per-record processing flow: (1) Pre-call: set `status=3`, `error_cd=NULL`, flush; (2) Call sp201 Cancel with record parameters; (3) Classify `return_cd` → code_type; (4) Post-call: set status (4/5/6), `return_cd`, `error_cd`, `get_return_date`, `program_name=5`, `update_date`, flush; (5) Increment success/failed/recovery counters. sp201 Cancel parameters sourced from record: `alliance_cd`, `passwd`, `gyotai_cd`, `tenpo_cd`, `kaiin_id_kbn`, `kaiin_id`, `serial_no`, `register_no`, `denpyo_no`, `point_kbn=74`, `cancel_kbn=0`, `moto_date`, `moto_serial_no`, `kangen_point`; generated at call time: `shori_date`/`shori_time`/`eigyou_date` (UTC format), `retry_kbn=0`, `retry_cnt=0`, `uriage_kin=0`. Error handling: sp201 timeout → classify as `return_cd=98` → code_type=2 → status=6; sp201 connection error → log exception, set status=6, continue next record; unexpected exception in loop → log, Slack error, continue; unexpected exception outside loop → log, Slack error, release lock, exit 1.
- **Linked Requirements:** SRS §3.7, KB §9.6 (BAT5), §13.2 (Code Type Classification), §14 (Cancel Flow)
- **Affected Files:** `app/Customize/Command/AutoCancelProcessingCommand.php`
- **Scope:** Backend
###### Acceptance Criteria
- [ ] **Given** the command is registered, **When** running `php bin/console batch0505:auto-cancel-processing`, **Then** the command executes without errors
- [ ] **Given** approved cancel records exist, **When** BAT5 processes each record, **Then** pre-call update sets `status=3` and `error_cd=NULL` before sp201 call
- [ ] **Given** sp201 returns `return_cd=00`, **When** code_type is classified, **Then** record is set to `status=4` (Success) with `program_name=5`
- [ ] **Given** sp201 returns a recoverable code (e.g., `04`), **When** code_type is classified, **Then** record is set to `status=6` (Recovery/Resend)
- [ ] **Given** sp201 returns a permanent failure code (e.g., `05`), **When** code_type is classified, **Then** record is set to `status=5` (Failed)
- [ ] **Given** `--limit=2` is passed and 5 records exist, **When** BAT5 runs, **Then** only 2 records are processed
- [ ] **Given** no approved records exist, **When** BAT5 runs, **Then** it logs info and exits with code 0
- [ ] **Given** one record fails during processing, **When** the next record is processed, **Then** processing continues without aborting the batch
###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| `dct_vpoint_redeem_result` table | Schema | Must exist with status and cancel columns |
| `VpointRedeemResult` entity | Entity | Must have status constants 0–7 defined |
| `CccmkApiClient` (sp201 caller) | Blocks | Not yet implemented — stub or interface placeholder required |
| `CommandTrait` | Shared | Logging and mail dispatch |
| Sub-task 1.2 | Blocks | Query method must exist for record retrieval |
| Sub-task 1.3 | Blocks | Lock, Slack, dry-run logic integrated into execute flow |
###### Definition of Done
- [ ] Command registered and callable via `php bin/console batch0505:auto-cancel-processing`
- [ ] All dependencies injected via constructor (no `new` keyword for services)
- [ ] `--dry-run` and `--limit` options parsed correctly
- [ ] Uses `CommandTrait` for logging and mail dispatch
- [ ] Exit code 0 on success, 1 on lock conflict
- [ ] Per-record error handling — single failure doesn't abort batch
###### Questions
- [ ] `CccmkApiClient` (sp201 caller) does not exist in the codebase yet. Should BAT5 define an interface (`VpointCancelClientInterface`) now and stub the implementation, or wait for Story T4 to land first? (Blocks sp201 call implementation; affects constructor DI)
- [ ] Should BAT5 process records in a DB transaction per record (commit after each) or batch all updates in a single transaction? Per-record is safer (partial progress on failure) but slower.
###### Assumptions
- [ ] Command name follows BAT3 pattern: `batch0505:auto-cancel-processing` (human-readable suffix after batch ID)
- [ ] `--verbose` flag uses Symfony's inherited `-v`/`-vv`/`-vvv` behavior — no custom option needed
- [ ] `CommandTrait::getBatchNumber()` extracts `0505` from command name `batch0505:auto-cancel-processing` via regex `/^batch(\d+)/`, matching the existing BAT3 pattern

---

##### Sub-task 1.2: Build BAT5 Query Logic
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend
**Assignee:** Dev 4 (Pavel) | **Status:** Pending
###### Summary
Add a new repository method `findApprovedCancels(?int $limit = null): VpointRedeemResult[]` to `VpointRedeemResultRepository` that returns admin-approved cancel records eligible for BAT5 processing. The query filters `point_kbn=74` AND `status=2`, selects the latest record per `serial_no` using a `MAX(id)` subquery scoped to `point_kbn=74`, and orders by `id ASC` for FIFO processing. An optional `$limit` parameter caps the result count.
###### Requirement Details
Query logic (DQL): `SELECT v FROM dct_vpoint_redeem_result v WHERE v.point_kbn=74 AND v.status=2 AND v.id = (SELECT MAX(v2.id) FROM dct_vpoint_redeem_result v2 WHERE v2.serial_no=v.serial_no AND v2.point_kbn=74) ORDER BY v.id ASC`. The subquery ensures only the most recent cancel record per `serial_no` is processed when multiple cancel records exist (e.g., re-approval after previous BAT5 failure). Edge cases: no records with status=2 → return empty array `[]`; multiple cancel records for same `serial_no` → return only highest `id`; records with `point_kbn=73` and `status=2` → excluded by filter; `$limit=0` → treated as no limit. Must use parameterized queries via Doctrine QueryBuilder (no raw SQL concatenation).
- **Linked Requirements:** SRS §3.7 (BAT5 query), KB §9.6
- **Affected Files:** `app/Customize/Repository/VpointRedeemResultRepository.php`
- **Scope:** Backend
###### Acceptance Criteria
- [ ] **Given** records with `point_kbn=74` and `status=2`, **When** `findApprovedCancels()` is called, **Then** only those records are returned
- [ ] **Given** two cancel records for the same `serial_no` with different `id` values, **When** queried, **Then** only the record with the highest `id` is returned
- [ ] **Given** results, **When** examining the order, **Then** records are sorted by `id ASC` (FIFO)
- [ ] **Given** `$limit=2` and 5 eligible records, **When** queried, **Then** only 2 records are returned
- [ ] **Given** no eligible records, **When** queried, **Then** an empty array is returned
- [ ] **Given** the query implementation, **When** inspecting code, **Then** parameterized queries are used (no SQL concatenation)
###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| `dct_vpoint_redeem_result` table | Schema | Table must exist with `status`, `point_kbn`, `serial_no` columns |
| `VpointRedeemResult` entity | Entity | Entity must map all required columns |
###### Definition of Done
- [ ] Method added to `VpointRedeemResultRepository`
- [ ] Filters: `point_kbn=74` AND `status=2` AND latest per `serial_no`
- [ ] Results ordered by `id ASC` (FIFO)
- [ ] `$limit` parameter applied when non-null
- [ ] Uses parameterized queries (no SQL concatenation)
###### Questions
- [ ] The subquery `MAX(v2.id)` assumes `id` is auto-increment and higher `id` = newer record. If records are ever inserted out of order (e.g., manual SQL inserts), this could pick the wrong record. Should we use `MAX(v2.create_date)` instead?
- [ ] Should `findApprovedCancels()` also filter on `type` column (`type=1` for API call)? Or is `point_kbn=74 AND status=2` sufficient? The `type` column distinguishes API calls (1) from file transfers (2).
- [ ] Performance concern: with 600,000 members, the `dct_vpoint_redeem_result` table could grow large. Is there an index on `(point_kbn, status)` or `(status, point_kbn)`? If not, one should be added.
###### Assumptions
- [ ] A `serial_no` will only ever have one record with `status=2` at a time. If admin re-approves after BAT5 failure, the old record transitions to status=5/6 before a new approval sets status=2. Therefore duplicate `serial_no` + `status=2` should not occur.
- [ ] The subquery also filters `point_kbn=74` (not just the outer query) to ensure the "latest per serial_no" comparison is scoped to cancel records only. Redemption records (point_kbn=73) sharing the same serial_no are excluded from the MAX(id) calculation.

---

##### Sub-task 1.3: Implement Redis Lock, Slack Notifications, and Dry-Run Mode
**Type:** Sub-task | **Estimate:** 6h | **Skill:** Backend
**Assignee:** Dev 4 (Pavel) | **Status:** Pending
###### Summary
Implement three cross-cutting concerns within the BAT5 command: (1) Redis distributed lock with 30-minute TTL and non-blocking acquisition following the BAT3 pattern (`RedisLock::createLockNotWait()`), released in `finally` block; (2) Slack notifications via `CommandTrait::sendMailBatch()` using `EMAIL_RECEIVE_BATCH` env var on batch start, completion with success/failed/recovery counts, and critical errors — no Slack on empty result set or lock conflict; (3) Dry-run mode (`--dry-run`) that acquires the lock but skips all DB writes, sp201 API calls, and Slack notifications, logging each skipped action with a `DRY-RUN:` prefix.
###### Requirement Details
Redis lock: resource `batch0505_auto_cancel`, TTL 1800.0s (30min), non-blocking via `createLockNotWait()`, acquire at start of `execute()`, release in `finally`. Lock conflict → log error, exit code 1, no Slack (follows BAT3 pattern). Slack notification events: (1) Batch start — subject `[BAT5] Auto Cancel Processing Started`, content `Processing {N} approved cancel record(s)` (only when N > 0); (2) Batch complete — subject `[BAT5] Auto Cancel Processing Complete`, content `Results: {success} success, {failed} failed, {recovery} recovery, {total} total`; (3) Critical error — subject `[BAT5] Auto Cancel Processing Error`, content `Unexpected error: {exception message}`; (4) Empty result set — no Slack, info log only. Dry-run behavior: lock=acquired (prevents concurrent dry-runs), query=executed (read-only), pre-call status update=skipped (log `DRY-RUN: Would set status=3`), sp201 call=skipped (log `DRY-RUN: Would call sp201 Cancel`), post-call update=skipped, Slack=skipped, DB flush=skipped, exit code=0.
- **Linked Requirements:** KB §9.6 (BAT5 lock/notifications), BAT3 pattern (`SpRecoveryFileCommand.php`)
- **Affected Files:** `app/Customize/Command/AutoCancelProcessingCommand.php`
- **Scope:** Backend
###### Acceptance Criteria
- [ ] **Given** no other BAT5 instance running, **When** lock is acquired, **Then** processing proceeds normally
- [ ] **Given** another BAT5 instance holds the lock, **When** a new instance starts, **Then** it logs error and exits with code 1 without any processing
- [ ] **Given** an exception occurs during processing, **When** the finally block executes, **Then** the Redis lock is released
- [ ] **Given** records are found, **When** BAT5 starts processing, **Then** a Slack notification with subject `[BAT5] Auto Cancel Processing Started` is sent
- [ ] **Given** processing completes, **When** results are tallied, **Then** a Slack notification with success/failed/recovery counts is sent
- [ ] **Given** no approved records exist, **When** BAT5 runs, **Then** no Slack notification is sent (info log only)
- [ ] **Given** `--dry-run` is passed, **When** BAT5 runs, **Then** no sp201 API calls, no DB writes, and no Slack notifications occur
- [ ] **Given** `--dry-run` is passed, **When** BAT5 starts, **Then** the Redis lock is still acquired to prevent concurrent dry-runs
###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| `RedisLock` service | Infrastructure | Must be available for lock operations |
| `CommandTrait::sendMailBatch()` | Shared | Slack notification dispatch |
| `EMAIL_RECEIVE_BATCH` env var | Configuration | Must be configured in all environments |
###### Definition of Done
- [ ] Redis lock acquired before any processing; released in `finally`
- [ ] Lock conflict returns exit code 1
- [ ] Slack sent on: batch start, batch complete, critical error
- [ ] No Slack sent on empty result set or lock conflict
- [ ] Dry-run mode: no API calls, no DB writes, no Slack — log-only output
- [ ] Dry-run mode: Redis lock still acquired to prevent concurrent runs
###### Questions
- [ ] Should lock conflict trigger a Slack notification? BAT3 does NOT send Slack on lock failure — just logs and exits. Should BAT5 follow the same pattern, or is lock conflict important enough to alert? (Recommend: follow BAT3 pattern — no Slack)
- [ ] Should Slack notifications include the list of processed serial_nos, or just summary counts? For small batches (1-5 records), including serial_nos aids debugging. For large batches, it would be too verbose. (Recommend: counts only; serial_nos in logs)
###### Assumptions
- [ ] Dry-run mode still acquires Redis lock to prevent concurrent dry-runs with confusing interleaved output. Lock is released in `finally` as normal.
- [ ] `EMAIL_RECEIVE_BATCH` env var is already configured in all environments (dev, stag, prod). No new env var is needed for BAT5 Slack notifications. (Verified — exists in all 3 taskdefs)
- [ ] Dry-run mode skips Slack notifications entirely to prevent false alerts during testing

---

##### Sub-task 1.4: Write Unit Tests
**Type:** Sub-task | **Estimate:** 8h | **Skill:** Backend
**Assignee:** Dev 4 (Pavel) | **Status:** Pending
###### Summary
Write PHPUnit unit tests in `tests/Customize/Command/AutoCancelProcessingCommandTest.php` following the `SpRecoveryFileCommandTest` (BAT3) pattern. Tests cover 8 groups: query eligibility (4 tests), sp201 code_type routing (5 tests covering all 23 return codes), pre-call update verification (2 tests), Redis lock (3 tests), dry-run mode (5 tests), Slack notification dispatch (4 tests), empty result set (2 tests), and field update verification (4 tests). All dependencies mocked via `$this->createMock()` — no real DB, Redis, or API calls. Estimated 29 test methods with ~78 assertions.
###### Requirement Details
Test groups and methods: (1) Query Eligibility — T01: `testQueryFetchesOnlyPointKbn74AndStatus2`, T02: `testQueryReturnsLatestRecordPerSerialNo`, T03: `testQueryOrdersByIdAscForFifoProcessing`, T04: `testQueryRespectsLimitParameter`; (2) Code Type Routing — T05: `testCodeType1SetsStatus4` (return_cd=00→status=4), T06: `testCodeType2SetsStatus6` (e.g., return_cd=04→status=6), T07: `testCodeType2AllRecoverableCodes` (04,11,16,18,80,92,98,99), T08: `testCodeType3SetsStatus5` (e.g., return_cd=05→status=5), T09: `testCodeType3AllPermanentCodes` (05,10,14,15,17,22,23,41,42,43,44,52,53,90); (3) Pre-Call Update — T10: `testPreCallSetsStatus3AndClearsErrorCd`, T11: `testPreCallUpdatePersistsBeforeApiCall`; (4) Redis Lock — T12: `testLockAcquiredSuccessfully`, T13: `testLockConflictExitsWithCode1`, T14: `testLockReleasedInFinallyBlock`; (5) Dry-Run — T15: `testDryRunNoApiCalls`, T16: `testDryRunNoDbWrites`, T17: `testDryRunNoSlackNotifications`, T18: `testDryRunExitsWithCode0`, T19: `testDryRunStillAcquiresLock`; (6) Slack — T20: `testSlackSentOnBatchStart`, T21: `testSlackSentOnBatchComplete`, T22: `testSlackSentOnCriticalError`, T23: `testNoSlackOnEmptyResultSet`; (7) Empty Set — T24: `testEmptyResultSetExitsSuccessfully`, T25: `testEmptyResultSetLogsInfo`; (8) Field Updates — T26: `testProgramNameSetTo5`, T27: `testGetReturnDateSetOnApiResponse`, T28: `testReturnCdStoredFromApiResponse`, T29: `testUpdateDateRefreshed`. Test data fixture: `createApprovedCancelRecord()` helper producing a `VpointRedeemResult` with `point_kbn=74`, `status=2`, and realistic field values.
- **Linked Requirements:** KB §9.6, §13.2 (all 23 return codes)
- **Affected Files:** `tests/Customize/Command/AutoCancelProcessingCommandTest.php`
- **Scope:** Backend
###### Acceptance Criteria
- [ ] **Given** the test suite, **When** `phpunit` is run, **Then** all 29 test methods pass
- [ ] **Given** code_type routing tests (T07, T09), **When** tested with all 23 return codes, **Then** each code routes to the correct status
- [ ] **Given** dry-run tests, **When** `--dry-run` is active, **Then** no API calls, DB writes, or Slack dispatches occur
- [ ] **Given** lock conflict test, **When** lock is unavailable, **Then** exit code is 1 and no processing occurs
- [ ] **Given** the test class, **When** inspecting mocks, **Then** all dependencies are mocked (no real DB, Redis, or API calls)
###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Sub-tasks 1.1–1.3 | Blocks | All BAT5 functionality must be implemented before comprehensive testing |
| `SpRecoveryFileCommandTest.php` | Pattern | Test structure follows BAT3 test pattern |
###### Definition of Done
- [ ] All test cases implemented and passing
- [ ] Test class follows `SpRecoveryFileCommandTest` structure
- [ ] All dependencies mocked (no real DB, Redis, or API calls)
- [ ] Code type routing tested for all 23 return codes (00 + 8 recoverable + 14 permanent)
- [ ] Test file at `tests/Customize/Command/AutoCancelProcessingCommandTest.php`
###### Questions
- [ ] Should T07 and T09 use `@dataProvider` for parameterized testing of all return codes, or individual test methods per code? `@dataProvider` is cleaner but produces less readable failure output. BAT3 tests use individual methods. (Recommend: `@dataProvider`)
- [ ] Should tests cover the scenario where sp201 API throws an exception (connection timeout, network error) rather than returning a `return_cd`? This is distinct from `return_cd=98` which is a valid response. (Recommend: add 2 exception tests)
###### Assumptions
- [ ] The `CccmkApiClient` (or its interface) will be mocked in tests. Since the service doesn't exist yet, tests will mock a `callable` or interface placeholder that returns a `return_cd` string. When T4 lands, tests update the mock type.
- [ ] `EntityManager::flush()` ordering is testable via PHPUnit's `$this->at()` or `withConsecutive()` method expectations to verify pre-call flush happens before the API call mock is invoked.
- [ ] Test count (29) and assertion count (~78) are estimates. Actual count may vary during implementation, especially if `@dataProvider` is used for code_type routing.

---

##### Sub-task 1.5: BAT
**Type:** Sub-task | **Estimate:** 4h | **Skill:** Backend
**Assignee:** Dev 4 (Pavel) | **Status:** Pending
###### Summary
Create the Build Acceptance Test (BAT) document for Story 1, covering verification of the complete BAT5 automated cancel processing pipeline. Test scenarios validate: command registration and CLI options, query eligibility for `point_kbn=74 AND status=2` with FIFO ordering, sp201 code_type routing for all 23 return codes, Redis lock acquisition and conflict handling, Slack notification dispatch on start/complete/error, dry-run mode producing no side effects, per-record error isolation, field update correctness (`program_name=5`, `get_return_date`, `return_cd`, `update_date`), and cron schedule verification (16:00 JST daily).
###### Requirement Details
BAT covers: (1) Command callable via `php bin/console batch0505:auto-cancel-processing`, (2) Query returns only `point_kbn=74 AND status=2` records in FIFO order, (3) Code type 1→status=4, type 2→status=6, type 3→status=5 verified for all 23 return codes, (4) Redis lock prevents concurrent runs (exit code 1 on conflict), (5) Slack notifications sent on batch start, complete with counts, critical errors, (6) No Slack on empty result set or lock conflict, (7) `--dry-run` skips all side effects (no DB writes, no API calls, no Slack), (8) `--limit=N` caps record processing, (9) Empty result set exits with code 0, (10) Single record failure doesn't abort batch, (11) Pre-call update sets status=3 and error_cd=NULL before sp201 call.
- **Linked Requirements:** SRS §3.7, KB §9.6
- **Affected Files:** BAT document
- **Scope:** Backend
###### Acceptance Criteria
- [ ] **Given** the BAT document, **When** reviewed, **Then** it covers command registration, query logic, code_type routing, lock, Slack, dry-run, limit, empty set, and error isolation
- [ ] **Given** each BAT test case, **When** executed against the deployed BAT5 command, **Then** all pass
###### Dependencies
| Dependency | Type | Details |
|-----------|------|---------|
| Sub-tasks 1.1–1.4 | All | All implementation and tests must be complete |
###### Definition of Done
- [ ] BAT document covers all Story 1 deliverables
- [ ] All test cases executable and passing
