# Lab 9 — Validate: Validation Report

**Platform:** Interval — quiz portal for the sAIDE website (IIT Ropar)
**Course:** AI511 — Human–Computer Interaction (Lab 9: Validate)
**Team:** Saaransh Garg (backend/API, RBAC) · Shlok Vaidya (frontend/UI)
**Typeset with:** Claude (Anthropic), via Claude Code
**Report date:** 13 October 2026 · **Scripted run recorded:** 2026-10-12T18:33:37Z · **Accessibility run recorded:** 2026-10-12T18:33:50Z
**Build under test:** working tree at HEAD (`d649294 start testing`) — API on `:4000`, web on `:5173`, driven in system Chromium (`/usr/bin/chromium`, Playwright 1.62.0).

**Question under test:** do the Lab 8 improvements actually fix the Lab 7 problems?

This report is the third in a chain, meaningful only read against its two predecessors: the Lab 7 evaluation ([`../lab7/report.md`](../lab7/report.md)) that found the problems, and the Lab 8 improvement log ([`../lab8/improvements.md`](../lab8/improvements.md)) that claims to have fixed them. The plan this report executes is fixed in [`evaluation-plan.md`](evaluation-plan.md); the inspection pass is recorded in [`inspection-findings.md`](inspection-findings.md).

---

## Executive Summary

Lab 7 showed both core tasks failing for every recorded run (0/7 each) behind two P0 defects. Lab 8 fixed both P0s plus a P1, and found two deeper latent defects. Lab 9 re-runs the *identical* two tasks as scripted Playwright flows under five fixture identities (N11–N15), re-grades the same ten Nielsen heuristics, runs a cognitive walkthrough of the formerly-broken student flow, and re-runs a limited accessibility audit across six screens — the three evaluation types named in the course material, with the user-based type executed as a deterministic scripted protocol rather than with human participants.

One caveat governs every number below and is restated wherever it bites. The five **N11–N15 identifiers are automated fixture accounts driven by a script, not human participants**. The recorded times are **automation wall-clock times for scripted steps, not human task durations**. The accessibility pass is a **custom structural audit, not a conformance test**, and it is not axe-based. Lab 9 therefore shows that the previously blocking defects no longer reproduce on the scripted path, and records inspection and accessibility observations against the Lab 7 baseline. It does **not** establish human usability, and it leaves the human-evaluation portion of the lab outstanding.

**Headline figure (computed from [`results.json`](results.json) and [`comparison.md`](comparison.md)):**

| Task | Lab 7 (before) | Lab 9 (after) |
|------|----------------|---------------|
| Task 1 — instructor publish quiz | 0/7 runs | **5/5 scripted runs completed** |
| Task 2 — student complete quiz | 0/7 runs | **5/5 scripted runs completed** |

Both flows now run end to end with zero recorded harness errors, where every Lab 7 run stopped at a blocker. The five heuristic findings that were non-zero in Lab 7 all fell to zero; the previously failing accessibility item is closed; one latent defect (a deep-link session race) was found and fixed while preparing the harness. No heuristic regressed, and no human usability claim is made.

---

## 1. Scripted Validation

### 1.1 Success criteria

The two tasks are the ones defined in Lab 5 ([`../lab5/user-tasks.md`](../lab5/user-tasks.md)) and used unchanged in Lab 7, so the before/after comparison stays like-for-like:

| | Task |
|---|---|
| **Task 1** | **Instructor** — draft → 4 question types → save rules → publish a *frozen* version (never mutate a live quiz). Lab 5 target: *under 5 minutes, without touching anything live*. |
| **Task 2** | **Student** — preflight → answer 4 question types on one surface → observe save state → submit → receipt. Lab 5 target: *first-time user under 3 minutes*. |

Four falsifiable targets are defined in [`evaluation-plan.md`](evaluation-plan.md) §2.1, each derived from the Lab 7 numbers rather than an arbitrary round figure. A target is scored as *met* only when the recorded values satisfy the stated inequality; nothing is asserted by hand:

| # | Task | Target | Lab 7 baseline | Rationale |
|---|------|--------|----------------|-----------|
| **T1** | Task 1 | Scripted flow completes in **≥ 90%** of runs (≥ 5 of 5 reach a visible published badge) | 0/7 = 0% | 5/5 is the only result that shows the flow works; the 10% grace absorbs a flake without hiding a defect. |
| **T2** | Task 2 | Scripted flow completes in **100%** of runs (5 of 5 reach a receipt) | 0/7 = 0% | The Lab 7 failure was a hard 403, not friction — there is no partial-credit version. |
| **T3** | Task 2 | **Automation time** median ≤ 180 s, every run ≤ 240 s | 67.4 s mean, whole failed-run elapsed (incl. timeout waits) | Recorded for traceability only; see the caveat in §1.5 — it is not a human time-on-task and does not validate Lab 5's 3-minute human target. |
| **T4** | Task 1 | **≤ 1 blocking error per run** (a blocking error is a step that stops the task: exception, 4xx/5xx, missing element, unreachable control) | 2/run (1 a P0) | Separates "the flow works" from "the flow has friction"; Task 1 has 14 scripted steps, Task 2 has 10. |

**Secondary (tracked, not pass/fail):** per-step time distribution, to show where remaining friction sits.

**Deliberately not targeted:** SUS (it requires a post-task questionnaire from human participants, a different protocol that was not run), and strict-integrity lock behaviour (Lab 7 §3.4 established synthetic `blur` events are not recognised by design; the lock path is exercised by API tests, and the study runs the quiz with policy `warn` so a lock cannot abort a run).

### 1.2 Choice of validation methods

All three evaluation types from the course (Labs 1–3, slides 8–10) were addressed, in the order inspection → user-based → accessibility. Each answers a different question and is weak alone:

| Method | What it answers | Why run here |
|--------|-----------------|--------------|
| **1. Usability inspection** (heuristic evaluation + cognitive walkthrough) | Does the interface violate known principles? | Re-running the **same 10 heuristics and 0–4 scale** as Lab 7 is the only way to make a defensible before/after claim; it also re-checks the Lab 7 *Passes*. This is a qualitative expert pass over the current source and build, not a guarantee of accessibility or usability. |
| **2. User-based evaluation** (scripted task scenarios) | Can the defined task be completed on the current build? | The only method producing the T1–T4 metrics (completion rate, per-run time, error count). Run as a deterministic Playwright protocol under five fixture identities — see §1.3 — so it demonstrates completability on the scripted path, not human usability. |
| **3. Accessibility evaluation** (structural audit) | Are the expected structural affordances present in the DOM? | Lab 7 recorded one hard a11y *Fail* and two *Partials*; the "fixed" claim must be re-checked, and a re-render-heavy UI change is exactly what silently breaks a11y. The audit's limits are set out in §2.4. |

Running one method alone gives a one-sided verdict; the three are mutually reinforcing and each covers some of the others' blind spots. None of them substitutes for observing real people.

### 1.3 Fixture accounts and harness

The five N11–N15 identifiers are **not human participants**. They are fixture identities ([`fixtures.json`](fixtures.json)) used to provision five distinct student accounts through the real registration and course-enrolment endpoints. Every account is genuine in the database and logs in through the real auth path; none is a mock. The accounts are driven by a Playwright harness ([`../../e2e/lab9-usertest.spec.ts`](../../e2e/lab9-usertest.spec.ts)) that executes both task scripts five times, once per account. The identifiers appear in [`results.json`](results.json) and here only as run labels.

Because the driver is a script, the study captures only what the script can observe: whether each step finds its control, whether the request succeeds, and how long the step took. It does not capture hesitation, confusion, or a participant's own account of the experience. Those require human participants, which this pass did not have.

### 1.4 Procedure and instrumentation

Each of the five runs executes both task scripts against the live build in its **own fresh browser context** (no shared session or storage), with no stubbing of the application. Every step is timed and scored, with a 20 s timeout; a step that raises an exception, returns 4xx/5xx, or cannot find its element counts as a blocking error. Per-run records are written to [`results.json`](results.json).

**Fixture.** Task 2 uses *"Lab9 Validation Checkpoint"* (quiz 55, version 64, AI511): published, `quiz_type = anytime`, `integrity_policy = warn`, `show_scores = immediate`, 4 questions (all four types), `attempts_allowed = 20` (raised for the retest). Added additively — no seed data modified. Task 1 provisions a fresh zero-question draft per run.

**Computation.** No figure asserted by hand — [`compare.py`](compare.py) reads the Lab 7 and Lab 9 files and emits the tables. A target is *met* only when the numbers satisfy the inequality in §1.1.

### 1.5 Results

| Target | Threshold | Recorded | Met? |
|--------|-----------|----------|------|
| T1 Task 1 completion | ≥ 90% (≥5/5) | 5/5 = 100% | Met |
| T2 Task 2 completion | 100% (5/5) | 5/5 = 100% | Met |
| T3 Task 2 automation time | median ≤ 180 s, all ≤ 240 s | median 4.8 s, max 6.0 s | Met (as automation time) |
| T4 Task 1 blocking errors | ≤ 1 / run (max) | max 0, mean 0.0 | Met |

**Per-run results** (times are scripted-step automation times, not human task durations)

| Run | Fixture | Task 1 | Task 2 |
|-----|---------|--------|--------|
| 1 | N11 | 12.2 s, 0 err, 14/14 steps | 6.0 s, 0 err, 10/10 steps |
| 2 | N12 | 5.7 s, 0 err, 14/14 steps | 4.8 s, 0 err, 10/10 steps |
| 3 | N13 | 6.5 s, 0 err, 14/14 steps | 4.7 s, 0 err, 10/10 steps |
| 4 | N14 | 6.2 s, 0 err, 14/14 steps | 4.5 s, 0 err, 10/10 steps |
| 5 | N15 | 6.1 s, 0 err, 14/14 steps | 5.0 s, 0 err, 10/10 steps |

The recorded times are whole scripted-run elapsed times. Task 1's figure includes API fixture setup before login; Task 2's does not. Task 1 median is 6.2 s (run 1's 12.2 s is the outlier, consistent with a first-run warm-up); Task 2 median is 4.8 s with a 6.0 s maximum. **These are not evidence that a first-time human user finishes in seconds.** The script performs no reading, deliberation, or recovery, so the figures validate the *existence of a working path*, not the Lab 5 human time criterion. T3 is therefore reported as an automation-time threshold that was met, with the human target left unvalidated.

### 1.6 Before-and-after comparison with Lab 7

| Metric | Lab 7 (before) | Lab 9 (after) | Change |
|--------|----------------|---------------|--------|
| Task 1 completion | 0/7 runs | 5/5 scripted runs | +100 pts |
| Task 2 completion | 0/7 runs | 5/5 scripted runs | +100 pts |
| Task 1 blocking errors / run | 2.0 | 0.0 | −2.0 |
| Task 2 blocking errors / run | 4.0 | 0.0 | −4.0 |
| Task 1 recorded time | 38.2 s median (whole failed run) | 6.2 s median (whole scripted run) | not comparable |
| Task 2 recorded time | 67.5 s median (whole failed run) | 4.8 s median (whole scripted run) | not comparable |

> Lab 7's durations are **whole failed-run elapsed times**, including the sequential timeout waits of every step that never succeeded — they are not time-to-first-blocker and not completion times. The Lab 9 times are whole scripted-run automation times (Task 1 includes API fixture setup before login). Neither column measures human time-on-task, and the two are **not** comparable as a speed claim.

---

## 2. Inspection & Accessibility

Source: [`inspection-findings.md`](inspection-findings.md) and [`a11y.json`](a11y.json). Each verdict cites the file and line that proves it.

### 2.1 Heuristic re-evaluation — Lab 7 vs Lab 9

The same ten Nielsen heuristics and the same 0–4 scale, re-applied like-for-like:

| # | Heuristic | Lab 7 | Lab 9 | Verdict |
|---|-----------|-------|-------|---------|
| 1 | Visibility of system status | 2 | 0 | **Improved** — save indicator with `role="status"`; dashboard error banner now `role="alert"` (I-A). |
| 2 | Match between system & real world | 0 | 0 | Holds. |
| 3 | User control & freedom | 1 | 0 | **Improved** — explicit Back buttons. |
| 4 | Consistency & standards | 0 | 0 | Holds. |
| 5 | Error prevention | 3 | 0 | **Improved** — `assertStaff` → `assertMember` (`routes/quizzes.ts:195`). |
| 6 | Recognition rather than recall | 0 | 0 | Holds. |
| 7 | Flexibility & efficiency of use | 1 | 1 | **Unchanged** — ⌘K palette + arrow paging exist; Ctrl+S / Ctrl+Enter still absent (I-B). |
| 8 | Aesthetic & minimalist design | 0 | 0 | Holds. |
| 9 | Recognise, diagnose, recover from errors | 3 | 0 | **Improved** — error text + `role="alert"` + retry. |
| 10 | Help & documentation | 1 | 0 | **Improved** — per-setting descriptions + preflight rules card. |

Raw scores: Lab 7 = `[2,0,1,0,3,0,1,0,3,1]` → **2 Major, 1 Minor, 3 Cosmetic, 4 clean**. Lab 9 = `[0,0,0,0,0,0,1,0,0,0]` → **1 Cosmetic, 9 clean**. Five heuristics improved (H1, H3, H5, H9, H10); none regressed; H7 is unchanged and remains the single outstanding cosmetic finding (I-B). This is an inspection judgement, not an accessibility guarantee.

### 2.2 Cognitive walkthrough — Task 2

Lab 7's Task 2 failure was a broken execution path, not aesthetics. Re-walked step-by-step ("know what to do / see the control / get feedback"): **no step fails the walkthrough.** The two elements that most directly answer Lab 7's complaints — the **preflight disclosure** (`QuizPreflightPage.tsx:257-268`) and the **tri-state save indicator** `pending / saving / saved` with `role="status"` (`AttemptPage.tsx:1160-1184`) — are both present. The walkthrough is a qualitative reasoning exercise over the source and build, not a session with users, and it is not a full usability or accessibility guarantee. Full table in [`inspection-findings.md`](inspection-findings.md) §2.

### 2.3 Status of the Lab 7 issues

| ID | Lab 7 item | Status |
|----|-----------|--------|
| I-1 | H5 — students silently denied quiz list (P0) | **Fixed** — `assertMember` |
| I-2 | H9 — no diagnosis for missing content (P0) | **Fixed** — error banner + retry |
| I-3 | H10 — no help for settings | **Fixed** — per-setting descriptions |
| I-4 | H3 — no back/cancel in editor | **Fixed** — Back button |
| I-5 | A11y error announcement | **Addressed** — `role="alert"` present on the error surfaces |
| I-6 | Editor hit non-existent routes (404) | **Fixed** — repointed (Lab 8 §3.1) |
| I-7 | Hard refresh bounced users to /login | **Fixed** — `ready` flag (Lab 8 §3.2) |
| I-A | Dashboard error banner had no live region | **Fixed in Lab 9** — `role="alert"` |
| I-F | Deep-link session race cleared token | **Fixed in Lab 9** — see §2.5 |

### 2.4 Accessibility — limited structural audit

The audit ([`e2e/lab9-a11y.spec.ts`](../../e2e/lab9-a11y.spec.ts) → [`a11y.json`](a11y.json)) runs a purpose-built in-page structural check across six screens (login, student dashboard/course/preflight, instructor dashboard, editor): **55 checks, 49 passed, 6 failed, 0 flagged as hard failures.** What that summary does and does not mean:

- The six failures are all the same item — **no skip-link** on any of the six screens (I-C). The harness classifies skip-link as a *cosmetic* failure, so it is excluded from the `hard_failed` count; "0 hard failures" therefore does not mean "no failures".
- **Contrast was not evaluated.** Every `contrast-*` check records `unparsed fg=oklch(...) bg=oklch(...)`: the tokens are in `oklch()`, the parser could not compute a ratio, and the harness recorded a pass by default. No contrast ratio was measured, so WCAG 1.4.3 is neither confirmed nor refuted by this audit.
- **Focus visibility was not proven.** The `focus-visible` check inspects computed `outline`/`box-shadow` presence — a heuristic signal, not evidence that a focus indicator is actually rendered and visible.
- **Keyboard operability was approximated.** The `keyboard-tabbables` check counts tabbable elements (5 to 48 per screen); it does not exercise the flows by keyboard and cannot show that everything is operable.
- **No screen-reader verification was performed.** The audit checks that live regions and roles are present in the DOM; it does not run a screen reader, so announcement behaviour is unverified. The Lab 7 error-announcement item is closed by *code presence* (`role="alert"` on the error surfaces, confirmed in the DOM), not by an assistive-technology session.
- The harness does not use axe-core; it is a custom structural check, so it covers only the specific properties it probes, not WCAG 2.1 AA as a whole.

| Check | Criterion | Result |
|-------|-----------|--------|
| Landmarks / roles | 1.3.1, 4.1.2 | Pass — structural presence |
| Form labels | 1.3.1, 3.3.2 | Pass — all visible inputs labelled |
| Live regions present | 4.1.3 | Pass — region present in DOM (not announcement-tested) |
| Focus visible | 2.4.7 | Heuristic only — not proof |
| Contrast (body/text/button) | 1.4.3 | Not evaluated — `oklch` unparsed |
| Keyboard tabbables | 2.1.1 | Pass — count only |
| Error announcement (I-A) | 4.1.3 | Pass — `role="alert"` present |
| Skip link | 2.4.1 | Fail ×6 — I-C open |

**Verdict.** The Lab 7 hard *Fail* (error announcement) is addressed at the code level, and the last surviving instance — the per-course dashboard banner — now carries `role="alert"` (I-A, verified in `a11y.json`). Everything else in this section is a limited structural observation. The audit does **not** demonstrate WCAG 2.1 AA conformance, and it does not replace an axe run, keyboard-only testing, contrast measurement, or a screen-reader session.

### 2.5 Defect found and fixed during validation prep

Preparing the validation harness surfaced one real defect that the earlier checks had not exercised:

- **I-F — deep-link session race (Major, session).** An aborted `/auth/me` request (React StrictMode remount, or an in-flight `page.goto`) was caught by the auth provider's generic `catch` and cleared the stored token, bouncing a logged-in user to `/login` on any deep link. It surfaced as the Task 1 harness failing at `open-editor` before it could proceed. **Fix:** `apps/web/src/auth.tsx` now only clears the session on a real HTTP `401/403`, ignores `AbortError`/network blips, and re-flips `ready` on login/register/sso. The defect and its fix are recorded in [`inspection-findings.md`](inspection-findings.md) §4.

### 2.6 Open items carried forward

| ID | Severity | Issue | Fix |
|----|----------|-------|-----|
| I-B | Cosmetic (H7) | No Ctrl+S / Ctrl+Enter in editor | bind on editor form |
| I-C | Cosmetic (a11y) | No skip-link | add as first focusable element |
| I-D | Minor (a11y) | No focus-on-first-question on attempt start | focus on mount |
| I-E | Cosmetic | ⌘K only power-user affordance | ship with I-B |

None blocks either scripted task; all are quality/enablement items.

---

## 3. Validation Summary

### 3.1 Automated targets

| Target | Threshold | Recorded | Met? |
|--------|-----------|----------|------|
| T1 Task 1 completion | ≥ 90% | 5/5 (100%) | Met |
| T2 Task 2 completion | 100% | 5/5 (100%) | Met |
| T3 Task 2 automation time | ≤ 180 s / ≤ 240 s | 4.8 s median / 6.0 s max | Met as automation time |
| T4 Task 1 blocking errors | ≤ 1 / run (max) | max 0, mean 0.0 | Met |

### 3.2 What is still pending

- **Human validation remained outstanding.** No human participants took part in Lab 9. The scripted protocol exercised the flows deterministically but did not observe real users, so the Lab 5 human criteria (instructor under 5 minutes; first-time student under 3 minutes) are unvalidated, and SUS was not collected.
- **Accessibility coverage is incomplete.** Contrast was never measured (`oklch` tokens unparsed); focus visibility and keyboard operability are inspected only heuristically; no screen-reader session was run. See §2.4.
- **Open cosmetic/minor items** I-B, I-C, I-D, I-E (none blocking).
- **Stale E2E fixture** — `exam-platform.spec.ts` needs a re-seed (the access-code seed postdates the on-disk DB); not a product defect (see [`inspection-findings.md`](inspection-findings.md) §4).
- **Deferred scope** from Lab 6 §7 (Postgres migration, media/math rendering, SSO, Docker/monitoring) — outside the validated core. No completion percentage is claimed for the deferred work.

### 3.3 Plan to complete the project

1. **Close I-C and I-D** (small, testable a11y fixes) — this would clear the six recorded structural failures, but would not by itself establish conformance; contrast and screen-reader behaviour would still be unverified.
2. **Ship I-B / I-E** (editor shortcuts) with the existing save/publish handlers.
3. **Measure contrast** with a real ratio computation and add a keyboard-only pass and a screen-reader pass, then re-run the audit.
4. **Run the human study** — recruit real participants, collect time-on-task and SUS, and re-score T1–T4 against human data; only then can the Lab 5 criteria be asserted.
5. **Re-run [`compare.py`](compare.py)** after any change so the numbers stay computed, and keep T1–T4 as the standing regression gate.

---

## Appendix A — Viva prep

Full question bank in [`viva-notes.md`](viva-notes.md): the Labs 4→9 journey (gaps G1–G4 → two tasks → build → P0s → fixes → validation) and the three Lab 3 evaluation types.

## Appendix B — Evidence index

| Artifact | Path |
|----------|------|
| Evaluation plan | `docs/lab9/evaluation-plan.md` |
| Inspection findings | `docs/lab9/inspection-findings.md` |
| User-based harness | `e2e/lab9-usertest.spec.ts` |
| Accessibility harness | `e2e/lab9-a11y.spec.ts` |
| Raw user results | `docs/lab9/results.json` |
| Raw a11y results | `docs/lab9/a11y.json` |
| Roster + fixture | `docs/lab9/fixtures.json` |
| Before/after computation | `docs/lab9/compare.py` → `comparison.md` |
| Screenshots | `docs/lab9/screenshots/` |
| Lab 7 baseline | `docs/lab7/report.md` |
| Lab 8 improvements | `docs/lab8/improvements.md` |
| Lab 5 tasks | `docs/lab5/user-tasks.md` |
| Fixed during validation | `apps/web/src/auth.tsx`, `apps/web/src/pages/DashboardPage.tsx` |