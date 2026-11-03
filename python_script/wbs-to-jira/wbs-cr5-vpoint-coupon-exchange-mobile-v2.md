# Work Breakdown Structure (WBS) — Revised v3

## CR5 — V-Point ↔ MrMax Coupon Exchange (Mobile)

| Field                  | Value                                                |
| ---------------------- | ---------------------------------------------------- |
| **Source SRS**         | `docs/srs/SRS_CR5_VPoint_Coupon_Exchange.md`         |
| **Generated**          | 2026-05-19                                           |
| **Total Stories**      | 14                                                   |
| **Total Hours**        | 716h (90 days)                                       |
| **Estimated Duration** | 10 weeks                                             |

---

## Story List

| ID        | Story                                                        | Hours    | Priority |
| --------- | ------------------------------------------------------------ | -------- | -------- |
| CR5-001   | [Mobile] Navigation Drawer V-Point Menu Integration          | 32h      | P0       |
| CR5-002   | [Mobile] Linkage Status UI on Membership & Coupon Screens    | 64h      | P0       |
| CR5-003   | [Mobile] Barcode Scanner for Card Linkage                    | 80h      | P0       |
| CR5-004   | [Mobile] Privacy Consent & Birthday Verification             | 40h      | P0       |
| CR5-005   | [Mobile] Email Authentication & Linkage Completion           | 64h      | P0       |
| CR5-006   | [Mobile] V-Point Balance API Integration (sp101)             | 32h      | P0       |
| CR5-007   | [Mobile] V-Point Balance Display UI                          | 64h      | P0       |
| CR5-008   | [Mobile] Exchange Button Configuration & UI                  | 48h      | P0       |
| CR5-009   | [Mobile] Manual Point Input & Validation                     | 32h      | P1       |
| CR5-010   | [Mobile] Exchange API Integration (sp201) with Retry Logic   | 32h      | P0       |
| CR5-011   | [Mobile] Exchange Confirmation Popup & Success Flow          | 48h      | P0       |
| CR5-012   | [Mobile] Exchanged Coupon Detail Screen                      | 56h      | P1       |
| CR5-013   | [Mobile] V-Point Linkage Cancellation Flow                   | 92h      | P1       |
| CR5-014   | [Mobile] Karte Event Tracking Implementation                 | 32h      | P1       |
| **Total** |                                                              | **716h** |          |

---

## Detailed Stories & Sub-tasks

---

### CR5-001: [Mobile] Navigation Drawer V-Point Menu Integration

**Overview:** Update Navigation Drawer to show "Vポイント連携設定" for unlinked users and "Vポイント連携解除" for linked users. This is the main entry point for V-Point features.

**Total Hours:** 32h (4 days)

#### Sub-tasks

| ID         | Summary                                                                                  | Layer        | Hours |
| ---------- | ---------------------------------------------------------------------------------------- | ------------ | ----- |
| CR5-001-01 | [iOS] Modified Membership API for card linkage status and membership model class         | Domain/Data  | 6h    |
| CR5-001-02 | [Android] Modified Membership API for card linkage status and membership model class     | Domain/Data  | 6h    |
| CR5-001-03 | [iOS] Update navigation drawer menu UI and dynamic menu switching                        | Presentation | 4h    |
| CR5-001-04 | [Android] Update navigation drawer menu UI and dynamic menu switching                    | Presentation | 4h    |
| CR5-001-05 | [iOS] Add navigation actions for V-Point screens                                         | Presentation | 2h    |
| CR5-001-06 | [Android] Add navigation actions for V-Point screens                                     | Presentation | 2h    |
| CR5-001-07 | [iOS] Write Unit tests and BAT tests                                                     | Test         | 4h    |
| CR5-001-08 | [Android] Write Unit tests and BAT tests                                                 | Test         | 4h    |

---

### CR5-002: [Mobile] Linkage Status UI on Membership & Coupon Screens

**Overview:** Display linkage status banner/prompt on Membership Card and Coupon List screens. Unlinked users see "カード連携するとVポイント利用が可能です" banner with "カードを連携する" CTA button. Linked users see V-Point exchange area.

**Total Hours:** 64h (8 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-002-01 | [iOS] Design UI component for unlinked user                                                      | Presentation | 6h    |
| CR5-002-02 | [Android] Design UI component for unlinked user                                                  | Presentation | 6h    |
| CR5-002-03 | [iOS] Implement `LinkagePromptAlert` buttons action for cardholder & non-cardholder              | Presentation | 4h    |
| CR5-002-04 | [Android] Implement `LinkagePromptAlert` buttons action for cardholder & non-cardholder          | Presentation | 4h    |
| CR5-002-05 | [iOS] Add linkage status check to Membership screen and UI state handle                          | Presentation | 4h    |
| CR5-002-06 | [Android] Add linkage status check to Membership screen and UI state handle                      | Presentation | 4h    |
| CR5-002-07 | [iOS] Add linkage status check to Special Coupon screen and UI state handle                      | Presentation | 4h    |
| CR5-002-08 | [Android] Add linkage status check to Special Coupon screen and UI state handle                  | Presentation | 4h    |
| CR5-002-09 | [iOS] Integrate the UI component in membership screen with conditional V-Point area              | Presentation | 4h    |
| CR5-002-10 | [Android] Integrate the UI component in membership screen with conditional V-Point area          | Presentation | 4h    |
| CR5-002-11 | [iOS] Update special coupon list UI with conditional V-Point area                                | Presentation | 6h    |
| CR5-002-12 | [Android] Update special coupon list UI with conditional V-Point area                            | Presentation | 6h    |
| CR5-002-13 | [iOS] Write Unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-002-14 | [Android] Write Unit tests and BAT tests                                                         | Test         | 4h    |

---

### CR5-003: [Mobile] Barcode Scanner for Card Linkage

**Overview:** Implement barcode scanner screen (st1, st2, st3) that allows users to scan their physical MrMax membership card barcode for V-Point linkage.

**Total Hours:** 80h (10 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-003-01 | [iOS] Create BarcodeScanner UI (st1, st2, st3 states)                                            | Presentation | 16h   |
| CR5-003-02 | [Android] Create BarcodeScanner UI (st1, st2, st3 states)                                        | Presentation | 16h   |
| CR5-003-03 | [iOS] Scan barcode functionality, Digit and Check digit verification manually                    | Domain       | 4h    |
| CR5-003-04 | [Android] Scan barcode functionality, Digit and Check digit verification manually                | Domain       | 4h    |
| CR5-003-05 | [iOS] API integration for card validity check with app_member_id & mrmax_id parameter            | Domain/Data  | 8h    |
| CR5-003-06 | [Android] API integration for card validity check with app_member_id & mrmax_id parameter        | Domain/Data  | 8h    |
| CR5-003-07 | [iOS] Implement camera permission handling and manual entry fallback                             | Presentation | 8h    |
| CR5-003-08 | [Android] Implement camera permission handling and manual entry fallback                         | Presentation | 8h    |
| CR5-003-09 | [iOS] Write Unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-003-10 | [Android] Write Unit tests and BAT tests                                                         | Test         | 4h    |

---

### CR5-004: [Mobile] Privacy Consent & Birthday Verification

**Overview:** Display privacy consent screen after barcode scan, then verify user identity by matching birthday with the scanned card number.

**Total Hours:** 40h (5 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-004-01 | [iOS] Design Date of Birth Screen and display the validation text                                | Presentation | 4h    |
| CR5-004-02 | [Android] Design Date of Birth Screen and display the validation text                            | Presentation | 4h    |
| CR5-004-03 | [iOS] Date of Birth Verification API integration with proper parameter from user info            | Domain/Data  | 8h    |
| CR5-004-04 | [Android] Date of Birth Verification API integration with proper parameter from user info        | Domain/Data  | 8h    |
| CR5-004-05 | [iOS] Implement date picker for birthday input                                                   | Presentation | 4h    |
| CR5-004-06 | [Android] Implement date picker for birthday input                                               | Presentation | 4h    |
| CR5-004-07 | [iOS] Write Unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-004-08 | [Android] Write Unit tests and BAT tests                                                         | Test         | 4h    |

---

### CR5-005: [Mobile] Email Authentication & Linkage Completion

**Overview:** Send authentication code to user's registered email, verify the code, and complete V-Point linkage.

**Total Hours:** 64h (8 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-005-01 | [iOS] Store linkage status in local storage (SharedPreferences/Room)                             | Data         | 4h    |
| CR5-005-02 | [Android] Store linkage status in local storage (SharedPreferences/Room)                         | Data         | 4h    |
| CR5-005-03 | [iOS] Create email auth UI and 10-minute countdown timer                                         | Presentation | 8h    |
| CR5-005-04 | [Android] Create email auth UI and 10-minute countdown timer                                     | Presentation | 8h    |
| CR5-005-05 | [iOS] Implement email OTP verify & resend OTP API integration                                    | Domain/Data  | 8h    |
| CR5-005-06 | [Android] Implement email OTP verify & resend OTP API integration                                | Domain/Data  | 8h    |
| CR5-005-07 | [iOS] Implement email troubleshooting guidance UI                                                | Presentation | 4h    |
| CR5-005-08 | [Android] Implement email troubleshooting guidance UI                                            | Presentation | 4h    |
| CR5-005-09 | [iOS] Create Linkage Success UI with navigation to homepage                                      | Presentation | 4h    |
| CR5-005-10 | [Android] Create Linkage Success UI with navigation to homepage                                  | Presentation | 4h    |
| CR5-005-11 | [iOS] Write Unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-005-12 | [Android] Write Unit tests and BAT tests                                                         | Test         | 4h    |

---

### CR5-006: [Mobile] V-Point Balance API Integration (sp101)

**Overview:** Implement sp101 Member Inquiry API to retrieve user's V-Point balance with error code handling.

**Total Hours:** 32h (4 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer       | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ----------- | ----- |
| CR5-006-01 | [iOS] Add sp101 endpoint to interface                                                            | Data        | 4h    |
| CR5-006-02 | [Android] Add sp101 endpoint to interface                                                        | Data        | 4h    |
| CR5-006-03 | [iOS] Implement error code mapping (04, 10, 11, 14, 80, 98)                                     | Data        | 4h    |
| CR5-006-04 | [Android] Implement error code mapping (04, 10, 11, 14, 80, 98)                                 | Data        | 4h    |
| CR5-006-05 | [iOS] Handle timeout and retry logic                                                             | Data        | 4h    |
| CR5-006-06 | [Android] Handle timeout and retry logic                                                         | Data        | 4h    |
| CR5-006-07 | [iOS] Write Unit tests and BAT tests                                                             | Test        | 4h    |
| CR5-006-08 | [Android] Write Unit tests and BAT tests                                                         | Test        | 4h    |

---

### CR5-007: [Mobile] V-Point Balance Display UI

**Overview:** Display V-Point balance on Membership Card and Coupon List screens with refresh functionality, loading states, and masked display for errors.

**Total Hours:** 64h (8 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-007-01 | [iOS] Create v-point balance sealed class and add balance LiveData to ViewModels                  | Presentation | 4h    |
| CR5-007-02 | [Android] Create v-point balance sealed class and add balance LiveData to ViewModels              | Presentation | 4h    |
| CR5-007-03 | [iOS] Create v-point custom UI component                                                         | Presentation | 4h    |
| CR5-007-04 | [Android] Create v-point custom UI component                                                     | Presentation | 4h    |
| CR5-007-05 | [iOS] Add V-Point balance area to Membership and Coupon layouts                                  | Presentation | 8h    |
| CR5-007-06 | [Android] Add V-Point balance area to Membership and Coupon layouts                              | Presentation | 8h    |
| CR5-007-07 | [iOS] Implement refresh button, loading state, and auto-refresh on resume                        | Presentation | 8h    |
| CR5-007-08 | [Android] Implement refresh button, loading state, and auto-refresh on resume                    | Presentation | 8h    |
| CR5-007-09 | [iOS] Implement masked balance display ("＊＊＊＊pt") for errors                                 | Presentation | 4h    |
| CR5-007-10 | [Android] Implement masked balance display ("＊＊＊＊pt") for errors                             | Presentation | 4h    |
| CR5-007-11 | [iOS] Write Unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-007-12 | [Android] Write Unit tests and BAT tests                                                         | Test         | 4h    |

---

### CR5-008: [Mobile] Exchange Button Configuration & UI

**Overview:** Implement configurable exchange amount buttons fetched from backend with accordion expand/collapse and disabled state logic.

**Total Hours:** 48h (6 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-008-01 | [iOS] Fetch button configuration through API and store locally                                   | Domain/Data  | 4h    |
| CR5-008-02 | [Android] Fetch button configuration through API and store locally                               | Domain/Data  | 4h    |
| CR5-008-03 | [iOS] Create v-point list with layout                                                            | Presentation | 8h    |
| CR5-008-04 | [Android] Create v-point list with layout                                                        | Presentation | 8h    |
| CR5-008-05 | [iOS] Implement accordion expand/collapse animation (3 default → up to 9)                        | Presentation | 4h    |
| CR5-008-06 | [Android] Implement accordion expand/collapse animation (3 default → up to 9)                    | Presentation | 4h    |
| CR5-008-07 | [iOS] Implement button disabled state based on balance and "すべて" button                       | Presentation | 4h    |
| CR5-008-08 | [Android] Implement button disabled state based on balance and "すべて" button                   | Presentation | 4h    |
| CR5-008-09 | [iOS] Write Unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-008-10 | [Android] Write Unit tests and BAT tests                                                         | Test         | 4h    |

---

### CR5-009: [Mobile] Manual Point Input & Validation

**Overview:** Allow users to manually enter exchange point amount with numeric keyboard and client-side validation.

**Total Hours:** 32h (4 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-009-01 | [iOS] Add manual input UI with numeric-only keyboard                                             | Presentation | 4h    |
| CR5-009-02 | [Android] Add manual input UI with numeric-only keyboard                                         | Presentation | 4h    |
| CR5-009-03 | [iOS] Implement real-time validation and E01 error display                                       | Presentation | 8h    |
| CR5-009-04 | [Android] Implement real-time validation and E01 error display                                   | Presentation | 8h    |
| CR5-009-05 | [iOS] Write unit tests for validation                                                            | Test         | 4h    |
| CR5-009-06 | [Android] Write unit tests for validation                                                        | Test         | 4h    |

---

### CR5-010: [Mobile] Exchange API Integration (sp201) with Retry Logic

**Overview:** Implement sp201 Point Operation API with automatic retry (attempt → retry1 → retry2 → cancel) and error handling.

**Total Hours:** 32h (4 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer       | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ----------- | ----- |
| CR5-010-01 | [iOS] Add sp201 and sp201 cancel endpoints to `MrMaxAuthApi`                                     | Data        | 4h    |
| CR5-010-02 | [Android] Add sp201 and sp201 cancel endpoints to `MrMaxAuthApi`                                 | Data        | 4h    |
| CR5-010-03 | [iOS] Implement retry logic (attempt → retry1 → retry2 → cancel) in Repository                  | Data        | 8h    |
| CR5-010-04 | [Android] Implement retry logic (attempt → retry1 → retry2 → cancel) in Repository              | Data        | 8h    |
| CR5-010-05 | [iOS] Implement error code mapping (04, 05, 17, 80)                                              | Data        | 4h    |
| CR5-010-06 | [Android] Implement error code mapping (04, 05, 17, 80)                                          | Data        | 4h    |

---

### CR5-011: [Mobile] Exchange Confirmation Popup & Success Flow

**Overview:** Display confirmation dialog before exchange and handle success/failure UI states with navigation to coupon list.

**Total Hours:** 48h (6 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-011-01 | [iOS] Create exchange v-point alert dialog with layout                                           | Presentation | 8h    |
| CR5-011-02 | [Android] Create exchange v-point alert dialog with layout                                       | Presentation | 8h    |
| CR5-011-03 | [iOS] Display exchange amount, post-exchange balance, and disclaimers                             | Presentation | 4h    |
| CR5-011-04 | [Android] Display exchange amount, post-exchange balance, and disclaimers                         | Presentation | 4h    |
| CR5-011-05 | [iOS] Create `ExchangeSuccessFragment` with "クーポンListへ" navigation                          | Presentation | 4h    |
| CR5-011-06 | [Android] Create `ExchangeSuccessFragment` with "クーポンListへ" navigation                      | Presentation | 4h    |
| CR5-011-07 | [iOS] Handle loading states and error display in dialog                                          | Presentation | 4h    |
| CR5-011-08 | [Android] Handle loading states and error display in dialog                                      | Presentation | 4h    |
| CR5-011-09 | [iOS] Write unit tests                                                                           | Test         | 4h    |
| CR5-011-10 | [Android] Write unit tests                                                                       | Test         | 4h    |

---

### CR5-012: [Mobile] Exchanged Coupon Detail Screen

**Overview:** Display exchanged coupon with barcode for POS scanning, usage instructions, and warnings.

**Total Hours:** 56h (7 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-012-01 | [iOS] Refresh Coupon list API & Update the UI                                                    | Presentation | 8h    |
| CR5-012-02 | [Android] Refresh Coupon list API & Update the UI                                                | Presentation | 8h    |
| CR5-012-03 | [iOS] Update coupon details API & Dynamic banner integration                                     | Domain/Data  | 8h    |
| CR5-012-04 | [Android] Update coupon details API & Dynamic banner integration                                 | Domain/Data  | 8h    |
| CR5-012-05 | [iOS] Add usage instructions, warnings, validity period, and conditions                          | Presentation | 8h    |
| CR5-012-06 | [Android] Add usage instructions, warnings, validity period, and conditions                      | Presentation | 8h    |
| CR5-012-07 | [iOS] Write unit tests                                                                           | Test         | 4h    |
| CR5-012-08 | [Android] Write unit tests                                                                       | Test         | 4h    |

---

### CR5-013: [Mobile] V-Point Linkage Cancellation Flow

**Overview:** Allow users to cancel their V-Point linkage with email verification and warnings about coupon loss.

**Total Hours:** 92h (12 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-013-01 | [iOS] API integration for card validity check with error handling                                | Domain/Data  | 8h    |
| CR5-013-02 | [Android] API integration for card validity check with error handling                            | Domain/Data  | 8h    |
| CR5-013-03 | [iOS] Unlink V-Point Alert Integration                                                           | Presentation | 8h    |
| CR5-013-04 | [Android] Unlink V-Point Alert Integration                                                       | Presentation | 8h    |
| CR5-013-05 | [iOS] Unlink API integration & OTP send                                                          | Domain/Data  | 8h    |
| CR5-013-06 | [Android] Unlink API integration & OTP send                                                      | Domain/Data  | 8h    |
| CR5-013-07 | [iOS] OTP Verification & Unlinking API Integration                                               | Domain/Data  | 8h    |
| CR5-013-08 | [Android] OTP Verification & Unlinking API Integration                                           | Domain/Data  | 8h    |
| CR5-013-09 | [iOS] OTP resend & other logic handle                                                            | Presentation | 6h    |
| CR5-013-10 | [Android] OTP resend & other logic handle                                                        | Presentation | 6h    |
| CR5-013-11 | [iOS] Unit Test Integration & check                                                              | Test         | 4h    |
| CR5-013-12 | [Android] Unit Test Integration & check                                                          | Test         | 4h    |
| CR5-013-13 | [iOS] BAT cases generation & verification                                                        | Test         | 4h    |
| CR5-013-14 | [Android] BAT cases generation & verification                                                    | Test         | 4h    |

---

### CR5-014: [Mobile] Karte Event Tracking Implementation

**Overview:** Implement Karte event tracking for coupon exchange (`coupon_exchange`) and usage (`coupon_use`) events.

**Total Hours:** 32h (4 days)

#### Sub-tasks

| ID         | Summary                                                                                          | Layer        | Hours |
| ---------- | ------------------------------------------------------------------------------------------------ | ------------ | ----- |
| CR5-014-01 | [iOS] Add Karte event types                                                                      | Data         | 4h    |
| CR5-014-02 | [Android] Add Karte event types                                                                  | Data         | 4h    |
| CR5-014-03 | [iOS] Trigger Coupon exchange event after sp201 (exchange API) success                           | Presentation | 4h    |
| CR5-014-04 | [Android] Trigger Coupon exchange event after sp201 (exchange API) success                       | Presentation | 4h    |
| CR5-014-05 | [iOS] Trigger Coupon use event after coupon redemption                                           | Presentation | 4h    |
| CR5-014-06 | [Android] Trigger Coupon use event after coupon redemption                                       | Presentation | 4h    |
| CR5-014-07 | [iOS] Write unit tests and BAT tests                                                             | Test         | 4h    |
| CR5-014-08 | [Android] Write unit tests and BAT tests                                                         | Test         | 4h    |

---

## Sprint Allocation (Starting May 18, 2026)

### Sprint 1: May 18 - May 29 (96h capacity — iOS + Android)

| Story   | Hours | Focus                       |
| ------- | ----- | --------------------------- |
| CR5-001 | 32h   | Navigation Drawer           |
| CR5-002 | 64h   | Linkage Status UI           |

### Sprint 2: Jun 1 - Jun 12 (96h capacity — iOS + Android)

| Story   | Hours | Focus                          |
| ------- | ----- | ------------------------------ |
| CR5-003 | 80h   | Barcode Scanner                |
| Buffer  | 16h   |                                |

### Sprint 3: Jun 15 - Jun 26 (96h capacity — iOS + Android)

| Story   | Hours | Focus                          |
| ------- | ----- | ------------------------------ |
| CR5-004 | 40h   | Privacy & Birthday             |
| CR5-005 | 64h   | Email Auth (start)             |

### Sprint 4: Jun 29 - Jul 10 (96h capacity — iOS + Android)

| Story             | Hours | Focus                          |
| ----------------- | ----- | ------------------------------ |
| CR5-006           | 32h   | sp101 API                      |
| CR5-007           | 64h   | Balance Display UI             |

### Sprint 5: Jul 13 - Jul 24 (96h capacity — iOS + Android)

| Story   | Hours | Focus                          |
| ------- | ----- | ------------------------------ |
| CR5-008 | 48h   | Exchange Buttons               |
| CR5-009 | 32h   | Manual Input                   |
| Buffer  | 16h   |                                |

### Sprint 6: Jul 27 - Aug 7 (96h capacity — iOS + Android)

| Story   | Hours | Focus                          |
| ------- | ----- | ------------------------------ |
| CR5-010 | 32h   | sp201 API                      |
| CR5-011 | 48h   | Confirmation Popup             |
| Buffer  | 16h   |                                |

### Sprint 7: Aug 10 - Aug 21 (96h capacity — iOS + Android)

| Story   | Hours | Focus                          |
| ------- | ----- | ------------------------------ |
| CR5-012 | 56h   | Coupon Detail                  |
| CR5-014 | 32h   | Karte Tracking                 |
| Buffer  | 8h    |                                |

### Sprint 8: Aug 24 - Sep 4 (96h capacity — iOS + Android)

| Story   | Hours | Focus                          |
| ------- | ----- | ------------------------------ |
| CR5-013 | 92h   | Cancellation                   |

**Estimated Completion: September 4, 2026**

---

## Summary

| Metric                    | Value              |
| ------------------------- | ------------------ |
| **Total Stories**         | 14                 |
| **Total Sub-tasks**       | 108                |
| **Total Hours**           | 716h               |
| **Per-platform Hours**    | 358h               |
| **Working Days**          | 90                 |
| **Estimated Sprints**     | 8 (2-week sprints) |

### Key Changes from v2:

1. ✅ All stories prefixed with [Mobile]
2. ✅ Each subtask duplicated for [iOS] and [Android] platforms
3. ✅ Story hours doubled to reflect both platform efforts
4. ✅ Subtasks updated to match PDF backlog breakdown
5. ✅ Removed "Story X:" prefix from story names
6. ✅ Sprint allocation updated for dual-platform capacity (96h/sprint)

---

_Generated from CR5 V-Point Coupon Exchange Backlog — Revised May 19, 2026_
