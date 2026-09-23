# Lab 7: TEST — Verification & Automated Testing Suite

Interval includes a comprehensive automated test and verification suite (`apps/api/src/__tests__/portal.test.ts`) executed directly against the relational data store with native Node.js 24 test runner (`node:test` + `node:assert`).

---

## 1. Test Architecture & Coverage Matrix

| Area | Target Capabilities | Test Case | Status |
|---|---|---|---|
| **Security & Auth** | Scrypt cryptographic key derivation, token signing, role verification | `Auth & Security: password hashing and verification` | **PASS** |
| **RBAC & Memberships** | Course isolation, instructor/TA privilege vs student permissions | `Course & Membership Management` | **PASS** |
| **Quiz Versioning (G4)** | Immutability on publish, version clone semantics, draft editing | `Quiz Versioning & Immutability: Draft to Published clone cycle` | **PASS** |
| **Question Repositories** | Tagging, categorization, and cross-course bank reuse | `Question Banks & Tagging System` | **PASS** |
| **Accessibility & Time** | Extra time multipliers (1.5x / 2.0x) and accommodation extensions | `Student Accommodations: Extra time multiplier calculation` | **PASS** |
| **Auto-Grading** | Single, multiple, numeric with tolerances ($\pm \epsilon$), case-insensitive short text | `Auto-Grading Engine: all 4 question types` | **PASS** |
| **Policy Engine (G3)** | Focus monitoring, warning state, strict lock (HTTP 423) | `Integrity Policy Enforcement: warn vs strict locking` | **PASS** |
| **Idempotency (G2)** | Revision tracking, duplicate request deduplication, receipt generation | `Idempotent Answer Saves and Revision Reconciliation` | **PASS** |
| **Psychometrics & Stats** | Mean, median, score buckets, item difficulty, discrimination index | `Analytics & Item Psychometrics Calculation` | **PASS** |

---

## 2. Automated Test Execution

```bash
npm test
```

### Execution Log

```
▶ Interval E2E Verification & Test Suite
  ✔ Auth & Security: password hashing and verification (85.9ms)
  ✔ Course & Membership Management (70.2ms)
  ✔ Quiz Versioning & Immutability: Draft to Published clone cycle (35.0ms)
  ✔ Question Banks & Tagging System (31.6ms)
  ✔ Student Accommodations: Extra time multiplier calculation (62.7ms)
  ✔ Auto-Grading Engine: single, multiple, numeric with tolerance, short answer (0.3ms)
  ✔ Integrity Policy Enforcement: warn vs strict locking (67.5ms)
  ✔ Idempotent Answer Saves and Revision Reconciliation (68.4ms)
  ✔ Analytics & Item Psychometrics Calculation (106.7ms)
✔ Interval E2E Verification & Test Suite (529.8ms)

ℹ tests 9
ℹ suites 1
ℹ pass 9
ℹ fail 0
```

---

## 3. Concurrency & Integrity Verification

1. **Idempotent Saves (G2)**: Answers are stored with explicit incrementing `revision` counters. If the client retries an inflight payload or duplicate requests arrive out of order, the higher revision always wins and the server acknowledges the revision.
2. **Server Clock Authority**: No client clock is trusted for attempt expiry. The server checks UTC timestamps on every save, policy event, and finalize request, automatically triggering expiration if time runs out.
3. **Transaction Safety**: All quiz cloning, question batch importing, and grading operations run inside SQLite atomic transactions (`BEGIN` ... `COMMIT`/`ROLLBACK`) ensuring zero partial states.
