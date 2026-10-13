# Lab 9 — Validate: Evaluation Plan

**Project:** Interval — quiz portal for the sAIDE website (IIT Ropar).
**Date:** 13 October 2026
**Question:** did the Lab 8 improvements actually fix the Lab 7 problems?
**Build under test:** the current working tree at HEAD (`d649294 start testing`), served by
`pnpm dev:api` (Express, :4000) + `pnpm dev:web` (Vite, :5173) and driven in system Chromium
(`/usr/bin/chromium`, Playwright 1.62.0).

Companion to the Lab 7 report ([`../lab7/report.md`](../lab7/report.md)) and the Lab 8 improvement log
([`../lab8/improvements.md`](../lab8/improvements.md)).

---

## 1. Method selection

Per the three evaluation types covered in the course slides (Labs1-3, slides 8-10), each type answers a
different question and each is weak alone. All three were run on the improved build, in this order.

### 1.1 Usability Inspection — heuristic evaluation (no users needed)

**Why:** the Lab 7 heuristic pass rated all 10 Nielsen heuristics and produced a ranked issue list.
Re-running the *same* rubric on the same screens is the only way to say anything defensible about
"before vs. after" at the heuristic level — a different rubric would measure a different thing.
Cheap, fast, catches issues user tests never reach, and it re-validates the Lab 7 design judgements
that Lab 7 marked *Pass*, which user testing could not have done (a passing heuristic can still be
re-graded by a careless edit).

**How:** each of the 10 heuristics re-graded 0–4 on the flows for both Lab 5 tasks, walked through the
live build in Chromium and read against the current source. Every previous 2/3/4 rating is re-examined
individually and cited as *Fixed / Partially fixed / Not fixed / Regressed / New finding*.
Additionally a **cognitive walkthrough** of Task 2 (student attempt) was run, because Task 2's failure
mode in Lab 7 was *not* aesthetic but a broken execution path: at each step, "will the user know what to
do, see the control, and get feedback that it worked".

### 1.2 User-Based Evaluation — scripted task scenarios (automated stand-in)

**Why:** this is the method that produces the completion-rate and error-count metrics the targets in §2
are written against, and it is the only way here to check that the previously blocked flows can still be
driven end to end. Lab 7 recorded 0/7 on both tasks; re-running the identical task protocol is what turns
"we fixed the bug" into "the task path works again".

**How:** a scripted, task-scenario protocol driven by a Playwright harness
(`e2e/lab9-usertest.spec.ts`). The five N11–N15 identifiers are **fixture accounts provisioned through the
real registration and enrolment endpoints, not human participants**. Each account drives both Lab 5 tasks
through the real UI in its own fresh browser context (no shared session), with no stubbing of the
application. Every step is timed and scored; a step that raises, returns 4xx/5xx, or cannot find its
element counts as a blocking error.

**What this does and does not buy.** Being deterministic, it removes moderator variance and makes the
numbers reproducible, and it is strong evidence that a working path exists where Lab 7 had none. It is
**not** a substitute for a usability test with people: the script does not read, deliberate, hesitate, or
recover, so the recorded "times" are automation times and cannot validate Lab 5's human time criteria;
and subjective confusion is not captured at all. **The human study remains outstanding** and is the first
item in the plan to complete the project (§ report 3.3). The inspection pass and the cognitive walkthrough
partially cover the qualitative gap, but neither observes real users.

### 1.3 Accessibility Evaluation — limited structural audit

**Why:** Lab 7 recorded one hard accessibility failure (API errors never announced to assistive tech) plus
two *Partial* results. A re-check must look at those three specifically — the claim under test is "fixed" —
and catch anything the Lab 8 re-render broke (e.g. a form control that drops its label association).

**How:** a purpose-built in-page structural check (`e2e/lab9-a11y.spec.ts`) across six screens. It records
whether expected affordances are present in the DOM — landmarks and roles, form labels, live-region
presence, a focus-visible heuristic, tabbable counts, and skip-link presence — and it does not use
axe-core. It is **limited**: `oklch()` colour tokens could not be parsed, so no contrast ratio was
computed and WCAG 1.4.3 is unmeasured; keyboard operation was counted, not exercised; focus visibility is a
heuristic signal, not proof; and no screen-reader session was run, so announcement behaviour is unverified.
The audit supports a claim about structural presence, not a claim of WCAG conformance, and a real
conformance pass (axe, keyboard-only, contrast measurement, screen reader) is listed as remaining work.

### Why all three, and in this order

Inspection first, because it is free and directs the scripted run at the right places; inspection also finds
*latent* defects that a fixed script never reaches. The scripted task run second, because it is the only
source of the quantitative before/after and shows whether the previously blocked path works. Accessibility
last, because a11y regressions are exactly the kind of thing a big re-render-heavy UI change silently
introduces. Any single method alone would have produced a one-sided verdict: inspection alone can pass a
heuristic that is unusable in practice; a scripted run can complete while a11y is broken; an a11y check can
be clean while the flow is confusing. None of the three substitutes for a study with real participants.

---

## 2. Key user tasks and measurable targets

The two tasks are the ones defined in Lab 5 ([`../lab5/user-tasks.md`](../lab5/user-tasks.md)) and tested in
Lab 7 — unchanged, so the comparison stays valid.

| | Task |
|---|---|
| **Task 1** | **Instructor:** create and publish an integrity-protected quiz — draft → questions (4 types) → preview → publish a *frozen* version, never mutating a live quiz. Lab 5 target: *under 5 minutes, without touching anything live*. |
| **Task 2** | **Student:** complete and submit a quiz without losing work — preflight → answer 4 question types on one surface → observe save state → submit → receipt. Lab 5 target: *first-time user under 3 minutes*. |

### 2.1 Targets

Four targets, written to be falsifiable and derived from the Lab 7 numbers (where possible the threshold is
Lab 7's observed failure value improved by a margin, not an arbitrary round number). A target is scored as
*met* only when the recorded values in `results.json` satisfy the stated inequality.

| # | Task | Target | Lab 7 baseline (before) | Why this number |
|---|------|--------|--------------------------|-----------------|
| **T1** | Task 1 | **Scripted flow completes in ≥ 90% of runs** (≥ 5 of 5 runs reach a visible published-version badge) | **0/7 = 0%** | The P0 detachment + publish failures made 0% the floor. 5/5 is the only result that says "the flow works"; 90% leaves one grace run for a flake rather than hiding a real defect. |
| **T2** | Task 2 | **Scripted flow completes in 100% of runs** (5 of 5 reach a submission receipt) | **0/7 = 0%** | Task 2's Lab 7 failure was a hard 403, not friction — there is no partial-credit version of it. Anything below 100% means a blocker remains. |
| **T3** | Task 2 | **Automation time median ≤ 180 s**, every run under 240 s | 67.4 s mean, whole failed-run elapsed (incl. the sequential timeout waits of every step that never succeeded) | Lab 7's figure is a whole failed-run elapsed time, not a completion time and not time-to-first-blocker. This threshold is recorded for traceability; it is an **automation** time, not a human time-on-task, so it does **not** validate Lab 5's 3-minute human criterion. Task 1's recorded time additionally includes API fixture setup before login. |
| **T4** | Task 1 | **≤ 1 blocking error per run** (a *blocking* error = a step that stops the task: exception, 4xx/5xx, missing element, unreachable control) | 2 blocking errors per run, 1 of them a P0 | Isolates "the flow works" from "the flow has friction". Task 1 has more moving parts (14 steps) than Task 2 (10), so it gets its own error target rather than sharing Task 2's. |

**Secondary (not pass/fail, tracked for the report):** per-step time distribution, to show *where*
remaining friction sits.

Deliberately **not** targeted: SUS score (it needs a post-task questionnaire from human participants, a
different protocol that was not run), and strict-integrity lock behaviour (Lab 7 §3.4 already notes
synthetic `blur` events are not recognised by design; the lock path is exercised by API-level tests
instead, and the policy settings are `warn` for this run so a lock cannot abort it).

### 2.2 Fixture accounts

The five identifiers N11–N15 are **fixture accounts, not human participants**. They are a fresh roster
(none of the 7 identities reported in Lab 7), provisioned via the real registration and course-enrolment
endpoints, and each drives the scripted protocol once from its own browser context. Five independent runs
give a small spread across repetitions of the same deterministic script; because there are no human
participants, no claim about real-user completion rate or Nielsen's *5-is-enough* cohort applies here.

### 2.3 Environment

Warm server, no cold-start in the measurements. Same machine, same Chromium, same viewport for all five
runs. Each run gets an isolated browser context, so one run's state cannot leak into another's.

---

## 3. Falsifiability

Results are recorded to `results.json` and `a11y.json` with per-step timings and exact error strings, and the
before/after table in the report is computed from those files rather than asserted. A target is only
written as *met* if the numbers in `results.json` satisfy the inequality in the table above. The recorded
run dates come from the files themselves (`results.json` 2026-10-12T18:33:37Z, `a11y.json`
2026-10-12T18:33:50Z).
